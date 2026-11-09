/**
 * Scripted REST API: IT Service Requests
 * Resource: GET /summary
 * Full path: /api/<your_scope>/it_service_requests/summary
 * Requires authentication: true
 *
 * Returns the number of open requests in each category as JSON.
 * Example response:
 * {
 *   "result": {
 *     "generated": "2026-11-09 15:30:00",
 *     "open_by_category": [ { "category": "hardware", "open": 4 }, ... ]
 *   }
 * }
 */
(function process(/*RESTAPIRequest*/ request, /*RESTAPIResponse*/ response) {

    var TABLE = 'x_scope_it_service_request'; // replace with your table name
    var summary = [];

    var agg = new GlideAggregate(TABLE);
    agg.addActiveQuery();
    agg.addAggregate('COUNT');
    agg.groupBy('category');
    agg.query();

    while (agg.next()) {
        summary.push({
            category: agg.getValue('category'),
            open: parseInt(agg.getAggregate('COUNT'), 10)
        });
    }

    response.setStatus(200);
    response.setBody({
        generated: new GlideDateTime().getDisplayValue(),
        open_by_category: summary
    });

})(request, response);
