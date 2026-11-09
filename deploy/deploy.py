#!/usr/bin/env python3
"""Deploy the IT Service Request app to a ServiceNow instance with the REST Table API.

Usage:  python3 deploy/deploy.py
Safe to re-run: each record is looked up by its key and updated in place.
Creates: scoped app, table (extends Task), fields, choices, number prefix,
Script Include, Business Rules, event + notification, Client Scripts,
UI Policies, Scripted REST API and an application menu.
"""
import os
import sys

from sn import USER, api, find

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAILED = []


def read(rel):
    with open(os.path.join(ROOT, rel), encoding='utf-8') as f:
        return f.read()


def upsert(table, query, fields, label):
    rec = find(table, query)
    if rec:
        status, data = api('PATCH', f'/api/now/table/{table}/{rec["sys_id"]}', fields)
        action = 'updated'
    else:
        status, data = api('POST', f'/api/now/table/{table}', fields)
        action = 'created'
    if status not in (200, 201):
        FAILED.append(label)
        print(f'  FAIL  {label}: HTTP {status} {str(data)[:300]}')
        return None
    print(f'  ok    {label} ({action})')
    return data['result']['sys_id']


def main():
    vendor = find('sys_properties', 'name=glide.appcreator.company.code', 'value')['value']
    scope = f'x_{vendor}_itreq'
    table = f'{scope}_service_request'
    event = f'{scope}.request.closed'
    print(f'Scope: {scope}   Table: {table}\n')

    def scoped(s):
        return (s.replace('x_scope_it_service_request', table)
                 .replace('x_scope.request.closed', event)
                 .replace('x_scope.RequestUtils', f'{scope}.RequestUtils'))

    print('Application')
    app = upsert('sys_app', f'scope={scope}', {
        'name': 'IT Service Request', 'scope': scope, 'version': '1.0.0',
        'short_description': 'IT service requests with automatic priority, routing and approvals',
        'active': 'true'}, 'scoped app')
    if not app:
        sys.exit(1)
    # Records created over REST go into the user's current application.
    admin = find('sys_user', f'user_name={USER}')['sys_id']
    upsert('sys_user_preference', f'user={admin}^name=apps.current_app',
           {'user': admin, 'name': 'apps.current_app', 'value': app}, 'current app = IT Service Request')
    base = {'sys_scope': app}

    print('\nTable and fields')
    task = find('sys_db_object', 'name=task')['sys_id']
    upsert('sys_db_object', f'name={table}', {
        **base, 'name': table, 'label': 'IT Service Request', 'super_class': task,
        'create_access_controls': 'true'}, f'table {table}')
    fields = [
        ('requested_for', {'internal_type': 'reference', 'reference': 'sys_user',
                           'column_label': 'Requested for', 'mandatory': 'true'}),
        ('category', {'internal_type': 'string', 'max_length': '40', 'choice': '1',
                      'column_label': 'Category', 'mandatory': 'true'}),
        ('estimated_cost', {'internal_type': 'integer', 'column_label': 'Estimated cost',
                            'default_value': '0'}),
        ('justification', {'internal_type': 'string', 'max_length': '1000',
                           'column_label': 'Justification'}),
    ]
    for element, attrs in fields:
        upsert('sys_dictionary', f'name={table}^element={element}',
               {**base, 'name': table, 'element': element, 'active': 'true', **attrs},
               f'field {element}')
    for seq, (value, label) in enumerate([('hardware', 'Hardware'), ('software', 'Software'),
                                          ('access', 'Access'), ('network', 'Network')], 1):
        upsert('sys_choice', f'name={table}^element=category^value={value}^language=en',
               {**base, 'name': table, 'element': 'category', 'value': value, 'label': label,
                'sequence': str(seq * 10), 'language': 'en', 'inactive': 'false'},
               f'choice {value}')
    upsert('sys_number', f'category={table}', {**base, 'category': table, 'prefix': 'ITREQ',
           'number': '1000', 'maximum_digits': '7'}, 'number prefix ITREQ')

    print('\nServer logic')
    upsert('sys_script_include', f'name=RequestUtils^sys_scope={app}', {
        **base, 'name': 'RequestUtils', 'client_callable': 'true', 'access': 'public',
        'active': 'true', 'description': 'Priority matrix, routing, duplicate check, GlideAjax',
        'script': scoped(read('server/script_includes/RequestUtils.js'))}, 'Script Include RequestUtils')
    rules = [
        ('Default requested for', 'default_requested_for.js', 'before', 10, True, False, ''),
        ('Prevent duplicate open requests', 'prevent_duplicate_requests.js', 'before', 50, True, False, ''),
        ('Set priority and assignment', 'set_priority_and_assignment.js', 'before', 100, True, True,
         'current.isNewRecord() || current.impact.changes() || current.urgency.changes() || current.category.changes()'),
        ('Notify requester on close', 'notify_on_close.js', 'async', 100, False, True,
         'current.state.changesTo(3)'),
        ('Set approval required', 'set_approval_required.js', 'before', 200, True, False,
         'current.estimated_cost > 1000'),
        ('Create manager approval', 'create_manager_approval.js', 'after', 100, True, False,
         "current.approval == 'requested'"),
    ]
    for name, fname, when, order, ins, upd, cond in rules:
        upsert('sys_script', f'name={name}^collection={table}', {
            **base, 'name': name, 'collection': table, 'when': when, 'order': str(order),
            'action_insert': str(ins).lower(), 'action_update': str(upd).lower(),
            'advanced': 'true', 'active': 'true', 'condition': cond,
            'script': scoped(read(f'server/business_rules/{fname}'))}, f'Business Rule "{name}"')
    upsert('sys_script', f'name=Apply approval decision^collection=sysapproval_approver^sys_scope={app}', {
        **base, 'name': 'Apply approval decision', 'collection': 'sysapproval_approver',
        'when': 'after', 'order': '100', 'action_insert': 'false', 'action_update': 'true',
        'advanced': 'true', 'active': 'true',
        'condition': f"current.source_table == '{table}' && "
                     "(current.state.changesTo('approved') || current.state.changesTo('rejected'))",
        'script': read('server/business_rules/apply_approval_decision.js')},
        'Business Rule "Apply approval decision" (on Approval table)')

    print('\nEvent and notification')
    upsert('sysevent_register', f'event_name={event}', {
        **base, 'event_name': event, 'suffix': 'request.closed', 'table': table,
        'fired_by': 'Notify requester on close', 'description': 'IT service request closed'},
        f'event {event}')
    upsert('sysevent_email_action', f'name=IT request closed^collection={table}', {
        **base, 'name': 'IT request closed', 'collection': table, 'generation_type': 'event',
        'event_name': event, 'event_parm_1': 'true', 'action_insert': 'false',
        'action_update': 'false', 'active': 'true',
        'subject': 'Your IT request ${number} is complete',
        'message_html': '<p>Hi ${requested_for},</p><p>Your request ${number} '
                        '(${short_description}) has been closed by ${assignment_group}.</p>'
                        '<p>${URI_REF}</p>'}, 'notification "IT request closed"')

    print('\nClient side')
    clients = [
        ('Route on category change', 'onChange', 'category', 'onChange_category.js'),
        ('Validate cost justification', 'onSubmit', '', 'onSubmit_validate_cost.js'),
    ]
    for name, ctype, field, fname in clients:
        upsert('sys_script_client', f'name={name}^table={table}', {
            **base, 'name': name, 'table': table, 'type': ctype, 'field': field,
            'ui_type': '10', 'active': 'true', 'isolate_script': 'true',
            'script': scoped(read(f'client/client_scripts/{fname}'))}, f'Client Script "{name}"')
    policies = [
        ('Require justification for high-cost requests', 'estimated_cost>1000',
         [('justification', 'true', 'true', 'ignore')]),
        ('Lock priority', '', [('priority', 'ignore', 'ignore', 'true')]),
        ('Lock closed requests', 'stateIN3,4',
         [(f, 'ignore', 'ignore', 'true') for f in
          ('category', 'estimated_cost', 'justification', 'impact', 'urgency')]),
    ]
    for desc, cond, actions in policies:
        pol = upsert('sys_ui_policy', f'short_description={desc}^table={table}', {
            **base, 'short_description': desc, 'table': table, 'conditions': cond,
            'on_load': 'true', 'reverse_if_false': 'true', 'active': 'true', 'order': '100'},
            f'UI Policy "{desc}"')
        if pol:
            for field, visible, mandatory, disabled in actions:
                upsert('sys_ui_policy_action', f'ui_policy={pol}^field={field}', {
                    **base, 'ui_policy': pol, 'table': table, 'field': field,
                    'visible': visible, 'mandatory': mandatory, 'disabled': disabled},
                    f'  action {field}')

    print('\nScripted REST API')
    base_uri = f'/api/{scope}/it_service_requests'
    ws = upsert('sys_ws_definition', f'service_id=it_service_requests^namespace={scope}', {
        **base, 'name': 'IT Service Requests', 'service_id': 'it_service_requests',
        'namespace': scope, 'base_uri': base_uri, 'active': 'true',
        'produces': 'application/json', 'consumes': 'application/json'}, 'REST API definition')
    if ws:
        for name, path, fname in [('Open requests by category', '/summary', 'get_open_summary.js'),
                                  ('Request by number', '/request/{number}', 'get_request_by_number.js')]:
            upsert('sys_ws_operation', f'web_service_definition={ws}^name={name}', {
                **base, 'web_service_definition': ws, 'name': name, 'http_method': 'GET',
                'relative_path': path, 'operation_uri': base_uri + path,
                'requires_authentication': 'true', 'active': 'true',
                'produces': 'application/json',
                'operation_script': scoped(read(f'server/scripted_rest/{fname}'))},
                f'GET {path}')

    print('\nApplication menu')
    menu = upsert('sys_app_application', f'title=IT Service Requests^sys_scope={app}', {
        **base, 'title': 'IT Service Requests', 'active': 'true', 'order': '100'}, 'menu')
    if menu:
        for title, link, order in [('Create New', 'NEW', 50), ('All Requests', 'LIST', 100)]:
            upsert('sys_app_module', f'title={title}^application={menu}', {
                **base, 'title': title, 'application': menu, 'name': table,
                'link_type': link, 'order': str(order), 'active': 'true'}, f'module "{title}"')

    print('\nForm layout')
    section = upsert('sys_ui_section', f'name={table}^view=Default view^captionISEMPTY', {
        **base, 'name': table, 'view': 'Default view', 'caption': '', 'title': 'false'},
        'form section (Default view)')
    if section:
        layout = ['number', 'requested_for', 'category', 'short_description', 'state',
                  'impact', 'urgency', 'priority', 'estimated_cost', 'justification',
                  'assignment_group', 'assigned_to', 'description', 'work_notes']
        for pos, element in enumerate(layout):
            upsert('sys_ui_element', f'sys_ui_section={section}^position={pos}', {
                'sys_ui_section': section, 'element': element, 'position': str(pos),
                'type': ''}, f'  {element}')

    print('\nRole')
    role = upsert('sys_user_role', f'name={scope}.agent', {
        **base, 'name': f'{scope}.agent', 'suffix': 'agent',
        'description': 'Works IT service requests'}, f'role {scope}.agent')
    itil = find('sys_user_role', 'name=itil')['sys_id']
    if role:
        upsert('sys_user_role_contains', f'role={role}^contains={itil}',
               {'role': role, 'contains': itil}, '  role contains itil')

    print('\nUI Policy actions and access controls (server-side script)')
    from bg import run_background
    with open(os.path.join(ROOT, 'deploy', 'post_deploy.js'), encoding='utf-8') as f:
        post = (f.read().replace('__SCOPE__', scope).replace('__TABLE__', table)
                .replace('__APP__', app))
    out = run_background(post)
    for line in out.splitlines():
        if line.strip():
            print('  ' + line.strip())
            if 'FAIL' in line or 'MISSING' in line or line.startswith('ERRORS'):
                FAILED.append(line.strip()[:80])

    print(f'\nDone. {len(FAILED)} failed' + (f': {", ".join(FAILED)}' if FAILED else ''))
    sys.exit(1 if FAILED else 0)


if __name__ == '__main__':
    main()
