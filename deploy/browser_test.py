#!/usr/bin/env python3
"""Browser tests for the client side (Client Scripts, GlideAjax, UI Policies, form layout).

Usage:  python3 deploy/browser_test.py          (add --headed to watch)
Logs in with ~/.servicenow_pdi, opens a new IT Service Request form and checks:
  - the new fields are on the form
  - choosing a category fills the assignment group through GlideAjax
  - priority is read-only
  - cost over $1,000 makes justification mandatory (UI Policy)
  - submit is blocked without justification (onSubmit Client Script)
  - submit works once justification is filled in
The test request is deleted at the end.
"""
import sys

from playwright.sync_api import sync_playwright

from sn import PASSWORD, URL, USER, api, find

RESULTS = []


def check(name, ok, detail=''):
    RESULTS.append(bool(ok))
    print(f'  {"PASS" if ok else "FAIL"}  {name}' + (f'  ({detail})' if detail and not ok else ''))


def main():
    vendor = find('sys_properties', 'name=glide.appcreator.company.code', 'value')['value']
    table = f'x_{vendor}_itreq_service_request'
    hardware = find('sys_user_group', 'name=Hardware')['sys_id']
    abel = find('sys_user', 'user_name=abel.tuter')['sys_id']
    created = None

    from sn import get_records
    for row in get_records(table, 'short_descriptionSTARTSWITH[browser]'):
        api('DELETE', f'/api/now/table/{table}/{row["sys_id"]}')
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='chrome', headless='--headed' not in sys.argv)
        page = browser.new_page()
        page.set_default_timeout(30000)
        try:
            page.goto(f'{URL}/login.do')
            page.fill('#user_name', USER)
            page.fill('#user_password', PASSWORD)
            page.click('#sysverb_login')
            page.wait_for_load_state('networkidle')

            page.goto(f'{URL}/{table}.do?sys_id=-1')
            page.wait_for_function('typeof g_form !== "undefined" && g_form.getTableName && g_form.getTableName()')
            check('login and open new request form', True)

            fields = page.evaluate('''() => ["requested_for","category","estimated_cost",
                "justification","priority","assignment_group"].filter(f => !g_form.hasField(f))''')
            check('form shows all app fields', fields == [], f'missing: {fields}')

            page.locator(f'[id="{table}.category"]').select_option('hardware')
            page.wait_for_function(f'g_form.getValue("assignment_group") === "{hardware}"')
            group = page.evaluate('g_form.getValue("assignment_group")')
            check('category change fills assignment group via GlideAjax', group == hardware, group)
            msg = page.evaluate('''() => [...document.querySelectorAll(".fieldmsg")]
                .map(e => e.textContent).join(" ")''')
            check('shows "Routed to Hardware" message', 'Routed to Hardware' in msg, msg)

            readonly = page.evaluate('''() => { const c = g_form.getControl("priority");
                return !!(c && (c.disabled || c.readOnly || c.getAttribute("readonly") !== null)); }''')
            check('priority is read-only (UI Policy)', readonly)

            mandatory_before = page.evaluate('g_form.isMandatory("justification")')
            cost = page.locator(f'[id="{table}.estimated_cost"]')
            cost.fill('1500')
            cost.press('Tab')
            page.wait_for_function('g_form.isMandatory("justification") === true')
            check('justification becomes mandatory when cost > $1,000',
                  not mandatory_before and page.evaluate('g_form.isMandatory("justification")'))

            page.evaluate(f'g_form.setValue("requested_for", "{abel}", "Abel Tuter")')
            page.evaluate('g_form.setValue("short_description", "[browser] New laptop")')
            # Turn off only the mandatory flag so the onSubmit script itself is tested.
            page.evaluate('g_form.setMandatory("justification", false)')
            page.click('#sysverb_insert')
            page.wait_for_timeout(2500)
            still_new = page.evaluate('g_form.isNewRecord()')
            msg = page.evaluate('''() => [...document.querySelectorAll(".fieldmsg")]
                .map(e => e.textContent).join(" ")''')
            check('submit blocked without justification (onSubmit script)',
                  still_new and 'justification is required' in msg.lower(), msg)

            page.locator(f'[id="{table}.justification"]').fill('Replacement for failed laptop')
            with page.expect_navigation():
                page.click('#sysverb_insert')
            row = find(table, 'short_description=[browser] New laptop',
                       'sys_id,number,assignment_group,priority')
            created = row and row['sys_id']
            check('submit succeeds with justification and saves the record', bool(row), str(row))
            if row:
                check('saved record is routed to Hardware', row['assignment_group'] == hardware,
                      row['assignment_group'])
        except Exception as e:  # report the failure instead of a stack trace
            check('browser run', False, f'{type(e).__name__}: {str(e)[:300]}')
            page.screenshot(path='/tmp/sn_browser_failure.png', full_page=True)
            print('  screenshot: /tmp/sn_browser_failure.png')
        finally:
            browser.close()
            if created:
                api('DELETE', f'/api/now/table/{table}/{created}')
                print('\nCleaned up 1 test request.')

    print(f'\n{sum(RESULTS)}/{len(RESULTS)} checks passed')
    sys.exit(0 if RESULTS and all(RESULTS) else 1)


if __name__ == '__main__':
    main()
