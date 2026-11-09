/**
 * Business Rule: Apply approval decision
 * Table:   Approval (sysapproval_approver)
 * When:    after   Update: true
 * Order:   100
 * Advanced: true
 * Condition: current.source_table == '<your IT Service Request table>' &&
 *            (current.state.changesTo('approved') || current.state.changesTo('rejected'))
 *
 * Copies the manager's decision back to the request:
 *   approved -> Work in Progress
 *   rejected -> Closed Incomplete
 */
(function executeRule(current, previous /* null when async */) {

    var req = new GlideRecord(current.getValue('source_table'));
    if (!req.get(current.getValue('document_id'))) {
        return;
    }

    var approver = current.getDisplayValue('approver');
    if (current.getValue('state') == 'approved') {
        req.approval = 'approved';
        req.state = 2; // Work in Progress
        req.work_notes = 'Approved by ' + approver + '.';
    } else {
        req.approval = 'rejected';
        req.state = 4; // Closed Incomplete
        req.work_notes = 'Rejected by ' + approver + '.';
    }
    req.update();

})(current, previous);
