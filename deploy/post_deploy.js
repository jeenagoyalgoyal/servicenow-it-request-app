/**
 * Post-deploy fixes, run as admin in Scripts - Background (deploy.py does this).
 * Handles what the REST Table API can't set:
 *  - UI Policy actions linked to their policies
 *  - Access controls (table, field and client-callable Script Include)
 * Placeholders __SCOPE__ / __TABLE__ / __APP__ are filled in by deploy.py.
 * Safe to re-run.
 */
var SCOPE = '__SCOPE__', TABLE = '__TABLE__', APP = '__APP__';
var report = [];

function one(table, query) {
    var gr = new GlideRecord(table);
    gr.addEncodedQuery(query);
    gr.setLimit(1);
    gr.query();
    return gr.next() ? gr : null;
}

// ---------- UI Policy actions ----------
var POLICIES = {
    'Require justification for high-cost requests': [['justification', 'true', 'true', 'ignore']],
    'Lock priority': [['priority', 'ignore', 'ignore', 'true']],
    'Lock closed requests': [['category', 'ignore', 'ignore', 'true'], ['estimated_cost', 'ignore', 'ignore', 'true'],
        ['justification', 'ignore', 'ignore', 'true'], ['impact', 'ignore', 'ignore', 'true'],
        ['urgency', 'ignore', 'ignore', 'true']]
};
var old = new GlideRecord('sys_ui_policy_action');
old.addQuery('table', TABLE);
old.query();
var removed = old.getRowCount();
old.deleteMultiple();
var made = 0;
for (var desc in POLICIES) {
    var pol = one('sys_ui_policy', 'table=' + TABLE + '^short_description=' + desc);
    if (!pol) { report.push('MISSING policy ' + desc); continue; }
    POLICIES[desc].forEach(function (a) {
        var act = new GlideRecord('sys_ui_policy_action');
        act.initialize();
        act.setValue('ui_policy', pol.getUniqueValue());
        act.setValue('table', TABLE);
        act.setValue('field', a[0]);
        act.setValue('visible', a[1]);
        act.setValue('mandatory', a[2]);
        act.setValue('disabled', a[3]);
        act.setValue('sys_scope', APP);
        if (act.insert()) made++;
    });
}
report.push('ui policy actions: removed ' + removed + ', created ' + made);

// ---------- Access controls ----------
function roleId(name) {
    var r = one('sys_user_role', 'name=' + name);
    return r ? r.getUniqueValue() : '';
}
function opId(name) { return one('sys_security_operation', 'name=' + name).getUniqueValue(); }
function typeId(name) { return one('sys_security_type', 'name=' + name).getUniqueValue(); }

function acl(type, op, name, desc, role, script) {
    var gr = one('sys_security_acl', 'name=' + name + '^operation=' + opId(op) + '^description=' + desc);
    var isNew = !gr;
    if (isNew) {
        gr = new GlideRecord('sys_security_acl');
        gr.initialize();
    }
    gr.setValue('type', typeId(type));
    gr.setValue('operation', opId(op));
    gr.setValue('name', name);
    gr.setValue('description', desc);
    gr.setValue('active', true);
    gr.setValue('admin_overrides', true);
    gr.setValue('advanced', !!script);
    gr.setValue('script', script || '');
    gr.setValue('sys_scope', APP);
    var id = isNew ? gr.insert() : (gr.update() && gr.getUniqueValue());
    if (!id) {
        report.push('FAIL acl ' + op + ' ' + name + ': ' + gr.getLastErrorMessage());
        return;
    }
    if (role) {
        var link = one('sys_security_acl_role', 'sys_security_acl=' + id + '^sys_user_role=' + roleId(role));
        if (!link) {
            link = new GlideRecord('sys_security_acl_role');
            link.initialize();
            link.setValue('sys_security_acl', id);
            link.setValue('sys_user_role', roleId(role));
            link.insert();
        }
    }
    report.push('ok acl ' + op + ' ' + name.replace(TABLE, '<table>') + (role ? ' [' + role + ']' : ''));
}

var REQUESTER = "answer = (current.getValue('requested_for') == gs.getUserID()) ||\n" +
                "         (current.getValue('opened_by') == gs.getUserID());";
acl('record', 'read', TABLE, 'Agents can read all requests', SCOPE + '.agent');
acl('record', 'read', TABLE, 'Requesters can read their own requests', null, REQUESTER);
acl('record', 'create', TABLE, 'Any logged-in user can create a request', 'snc_internal');
acl('record', 'write', TABLE, 'Agents can update requests', SCOPE + '.agent');
acl('record', 'write', TABLE + '.priority', 'Only admins can override priority', 'admin');
acl('record', 'delete', TABLE, 'Only admins can delete requests', 'admin');
acl('client_callable_script_include', 'execute', 'RequestUtils',
    'Logged-in users can call RequestUtils from the form (GlideAjax)', 'snc_internal');

report.forEach(function (line) { gs.info(line); });
