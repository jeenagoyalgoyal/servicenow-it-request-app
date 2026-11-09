/**
 * Business Rule: Default requested for
 * Table:   IT Service Request
 * When:    before   Insert: true   Update: false
 * Order:   10 (runs before the duplicate check)
 * Advanced: true
 *
 * If no one is chosen, the request is for the person submitting it.
 * (Done here instead of a dictionary default, because the platform blocks
 * script default values on fields created through the REST API.)
 */
(function executeRule(current, previous /* null when async */) {

    if (current.requested_for.nil()) {
        current.requested_for = gs.getUserID();
    }

})(current, previous);
