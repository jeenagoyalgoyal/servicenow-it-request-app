/**
 * Business Rule: Create manager approval
 * Table:   IT Service Request
 * When:    after   Insert: true   Update: false
 * Order:   100
 * Advanced: true
 * Condition: current.approval == 'requested'
 *
 * Adds an approval record for the requester's manager. The manager sees it
 * under "My Approvals" and can approve or reject it there.
 */
(function executeRule(current, previous /* null when async */) {

    var approval = new GlideRecord('sysapproval_approver');
    approval.initialize();
    approval.setValue('approver', current.requested_for.manager);
    approval.setValue('sysapproval', current.getUniqueValue());
    approval.setValue('source_table', current.getTableName());
    approval.setValue('document_id', current.getUniqueValue());
    approval.setValue('state', 'requested');
    approval.insert();

})(current, previous);
