/**
 * Business Rule: Set approval required
 * Table:   IT Service Request
 * When:    before   Insert: true   Update: false
 * Order:   200
 * Advanced: true
 * Condition: current.estimated_cost > 1000
 *
 * Requests over $1,000 need the requester's manager to approve.
 * If the requester has no manager, the request is approved and a work note
 * says why, so it isn't stuck waiting.
 */
(function executeRule(current, previous /* null when async */) {

    var manager = current.requested_for.manager;
    if (manager.nil()) {
        current.approval = 'approved';
        current.work_notes = 'No manager on file for the requester. Auto-approved for Service Desk review.';
    } else {
        current.approval = 'requested';
        current.state = -5; // Pending
    }

})(current, previous);
