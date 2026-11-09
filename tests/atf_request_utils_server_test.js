/**
 * ATF Test: RequestUtils unit tests
 * Step type: Run Server Side Validation Script (Jasmine 3.1)
 *
 * Checks the priority matrix and category routing without creating records.
 */
(function (outputs, steps, params, stepResult, assertEqual) {

    describe('RequestUtils.calculatePriority', function () {
        var utils = new RequestUtils();

        it('returns 1 (Critical) for high impact and high urgency', function () {
            expect(utils.calculatePriority('1', '1')).toBe(1);
        });

        it('returns 3 (Moderate) for medium impact and medium urgency', function () {
            expect(utils.calculatePriority('2', '2')).toBe(3);
        });

        it('returns 5 (Planning) for low impact and low urgency', function () {
            expect(utils.calculatePriority('3', '3')).toBe(5);
        });

        it('defaults to 5 when impact or urgency is missing', function () {
            expect(utils.calculatePriority('', '')).toBe(5);
        });
    });

    describe('RequestUtils.getAssignmentGroup', function () {
        var utils = new RequestUtils();

        it('routes hardware requests to the Hardware group', function () {
            var groupId = utils.getAssignmentGroup('hardware');
            var group = new GlideRecord('sys_user_group');
            expect(group.get(groupId)).toBe(true);
            expect(group.getValue('name')).toBe('Hardware');
        });

        it('returns an empty string for an unknown category', function () {
            expect(utils.getAssignmentGroup('unknown')).toBe('');
        });
    });

})(outputs, steps, params, stepResult, assertEqual);
