/**
 * Script Include: RequestUtils
 * Client callable: true (needed for GlideAjax)
 * Accessible from: All application scopes (GlideAjax requests come in through
 *   the global AJAX processor, so "This application scope only" returns
 *   "HTTP Processor class not found")
 * Needs an execute ACL of type client_callable_script_include named RequestUtils
 *
 * Shared logic for the IT Service Request app:
 *  - priority from the impact x urgency matrix
 *  - assignment group routing by category (GlideRecord)
 *  - duplicate open-request check
 *  - GlideAjax entry point used by the onChange client script
 */
var RequestUtils = Class.create();
RequestUtils.prototype = Object.extendsObject(global.AbstractAjaxProcessor, {

    // Replace with your table name, e.g. 'x_1234567_it_service_request'
    TABLE: 'x_scope_it_service_request',

    // Key is "impact-urgency" (1 = High, 2 = Medium, 3 = Low). Value is priority 1 (Critical) to 5 (Planning).
    PRIORITY_MATRIX: {
        '1-1': 1, '1-2': 2, '1-3': 3,
        '2-1': 2, '2-2': 3, '2-3': 4,
        '3-1': 3, '3-2': 4, '3-3': 5
    },

    // Category -> assignment group name (these groups exist in PDI demo data)
    CATEGORY_GROUPS: {
        hardware: 'Hardware',
        software: 'Software',
        access: 'Service Desk',
        network: 'Network'
    },

    /**
     * @param {string} impact  '1' | '2' | '3'
     * @param {string} urgency '1' | '2' | '3'
     * @returns {number} priority 1-5 (defaults to 5 for unknown input)
     */
    calculatePriority: function (impact, urgency) {
        var key = (impact || '3') + '-' + (urgency || '3');
        return this.PRIORITY_MATRIX.hasOwnProperty(key) ? this.PRIORITY_MATRIX[key] : 5;
    },

    /**
     * @param {string} category choice value, e.g. 'hardware'
     * @returns {string} sys_id of the active group, or '' if none
     */
    getAssignmentGroup: function (category) {
        var groupName = this.CATEGORY_GROUPS[category];
        if (!groupName) {
            return '';
        }
        var group = new GlideRecord('sys_user_group');
        group.addQuery('name', groupName);
        group.addActiveQuery();
        group.setLimit(1);
        group.query();
        return group.next() ? group.getUniqueValue() : '';
    },

    /**
     * True if the user already has an active request in this category.
     * @param {string} userId    sys_id of requested_for
     * @param {string} category  choice value
     * @param {string} excludeId sys_id to skip (the record being saved)
     */
    hasOpenRequest: function (userId, category, excludeId) {
        if (!userId || !category) {
            return false;
        }
        var req = new GlideRecord(this.TABLE);
        req.addActiveQuery();
        req.addQuery('requested_for', userId);
        req.addQuery('category', category);
        if (excludeId) {
            req.addQuery('sys_id', '!=', excludeId);
        }
        req.setLimit(1);
        req.query();
        return req.hasNext();
    },

    /**
     * GlideAjax: returns the group for a category as JSON.
     * Params: sysparm_category
     * Returns: {"sys_id": "...", "name": "..."}
     */
    getGroupForCategory: function () {
        var category = this.getParameter('sysparm_category');
        var result = { sys_id: '', name: '' };
        var groupId = this.getAssignmentGroup(category);
        if (groupId) {
            var group = new GlideRecord('sys_user_group');
            if (group.get(groupId)) {
                result.sys_id = groupId;
                result.name = group.getValue('name');
            }
        }
        return JSON.stringify(result);
    },

    type: 'RequestUtils'
});
