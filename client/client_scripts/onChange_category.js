/**
 * Client Script: Route on category change
 * Table: IT Service Request   UI Type: All
 * Type:  onChange             Field: Category
 *
 * Calls RequestUtils through GlideAjax and fills in the assignment group
 * straight away, so the user sees where the request will go before saving.
 */
function onChange(control, oldValue, newValue, isLoading, isTemplate) {
    if (isLoading || newValue === '') {
        return;
    }

    // In a scoped app use the full API name: '<your_scope>.RequestUtils'
    var ga = new GlideAjax('x_scope.RequestUtils');
    ga.addParam('sysparm_name', 'getGroupForCategory');
    ga.addParam('sysparm_category', newValue);
    ga.getXMLAnswer(function (answer) {
        var group = {};
        try {
            group = JSON.parse(answer || '{}');
        } catch (e) {
            return;
        }
        g_form.hideFieldMsg('assignment_group', true);
        if (group.sys_id) {
            g_form.setValue('assignment_group', group.sys_id, group.name);
            g_form.showFieldMsg('assignment_group',
                'Routed to ' + group.name + ' based on the category.', 'info');
        }
    });
}
