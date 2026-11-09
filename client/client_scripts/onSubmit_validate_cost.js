/**
 * Client Script: Validate cost justification
 * Table: IT Service Request   UI Type: All
 * Type:  onSubmit
 *
 * Blocks submit when the estimated cost is over $1,000 and there's no
 * justification. (The UI Policy also makes the field mandatory; this script
 * covers lists and forms where the policy doesn't run.)
 */
function onSubmit() {
    var COST_LIMIT = 1000;
    var cost = parseInt(g_form.getValue('estimated_cost'), 10) || 0;
    var justification = (g_form.getValue('justification') || '').trim();

    g_form.hideFieldMsg('justification', true);

    if (cost > COST_LIMIT && justification === '') {
        g_form.showFieldMsg('justification',
            'A justification is required for requests over $' + COST_LIMIT + '.', 'error');
        return false;
    }
    return true;
}
