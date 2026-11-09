/**
 * Business Rule: Set priority and assignment
 * Table:   IT Service Request
 * When:    before   Insert: true   Update: true
 * Order:   100
 * Advanced: true
 * Condition: current.isNewRecord() || current.impact.changes() || current.urgency.changes() || current.category.changes()
 *
 * Sets priority from impact x urgency and sends the request to the right
 * assignment group. A group picked by hand is kept unless the category changes.
 */
(function executeRule(current, previous /* null when async */) {

    var utils = new RequestUtils();

    current.priority = utils.calculatePriority(
        current.getValue('impact'),
        current.getValue('urgency')
    );

    if (current.assignment_group.nil() || current.category.changes()) {
        var groupId = utils.getAssignmentGroup(current.getValue('category'));
        if (groupId) {
            current.assignment_group = groupId;
        }
    }

})(current, previous);
