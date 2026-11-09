/**
 * Business Rule: Notify requester on close
 * Table:   IT Service Request
 * When:    async   Update: true
 * Advanced: true
 * Condition: current.state.changesTo(3)   // 3 = Closed Complete
 *
 * Fires an event; the notification in config/notification.md sends the email.
 * Register the event first: System Policy > Events > Registry
 *   Event name: x_scope.request.closed   Table: IT Service Request
 */
(function executeRule(current, previous /* null when async */) {

    gs.eventQueue(
        'x_scope.request.closed',          // replace x_scope with your app scope
        current,
        current.getValue('requested_for'), // parm1: recipient
        current.getValue('number')         // parm2: request number
    );

})(current, previous);
