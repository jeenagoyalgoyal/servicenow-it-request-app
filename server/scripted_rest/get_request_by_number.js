/**
 * Scripted REST API: IT Service Requests
 * Resource: GET /request/{number}
 * Full path: /api/<your_scope>/it_service_requests/request/{number}
 * Requires authentication: true
 *
 * Returns one request as JSON. Gives 404 if not found and 403 if the
 * caller isn't allowed to read it (the table ACLs are respected).
 */
(function process(/*RESTAPIRequest*/ request, /*RESTAPIResponse*/ response) {

    var TABLE = 'x_scope_it_service_request'; // replace with your table name
    var number = request.pathParams.number;

    var req = new GlideRecord(TABLE);
    if (!req.get('number', number)) {
        response.setError(new sn_ws_err.NotFoundError('No request found with number ' + number));
        return;
    }

    if (!req.canRead()) {
        var forbidden = new sn_ws_err.ServiceError();
        forbidden.setStatus(403);
        forbidden.setMessage('You do not have access to this request.');
        response.setError(forbidden);
        return;
    }

    response.setStatus(200);
    response.setBody({
        number: req.getValue('number'),
        short_description: req.getValue('short_description'),
        category: req.getValue('category'),
        priority: req.getDisplayValue('priority'),
        state: req.getDisplayValue('state'),
        requested_for: req.getDisplayValue('requested_for'),
        assignment_group: req.getDisplayValue('assignment_group'),
        estimated_cost: parseInt(req.getValue('estimated_cost'), 10) || 0,
        opened_at: req.getValue('opened_at')
    });

})(request, response);
