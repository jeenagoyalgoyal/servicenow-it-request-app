/**
 * Business Rule: Prevent duplicate open requests
 * Table:   IT Service Request
 * When:    before   Insert: true   Update: false
 * Order:   50 (runs before the priority/assignment rule)
 * Advanced: true
 *
 * Stops a user from opening a second active request in the same category.
 */
(function executeRule(current, previous /* null when async */) {

    var utils = new RequestUtils();
    var duplicate = utils.hasOpenRequest(
        current.getValue('requested_for'),
        current.getValue('category'),
        current.getUniqueValue()
    );

    if (duplicate) {
        gs.addErrorMessage(gs.getMessage(
            'An open {0} request already exists for this user. Please update that request instead.',
            [current.getDisplayValue('category')]
        ));
        current.setAbortAction(true);
    }

})(current, previous);
