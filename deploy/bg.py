#!/usr/bin/env python3
"""Run a server-side script on the instance through Scripts - Background (admin only).

Used by deploy.py for the few records the REST Table API can't set correctly.
Usage as a module: run_background(script, scope='global') -> output text
Usage from the shell: python3 deploy/bg.py <file.js> [scope]
"""
import re
import sys

from playwright.sync_api import sync_playwright

from sn import PASSWORD, URL, USER


def run_background(script, scope='global'):
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='chrome', headless=True)
        page = browser.new_page()
        page.set_default_timeout(60000)
        try:
            page.goto(f'{URL}/login.do')
            page.fill('#user_name', USER)
            page.fill('#user_password', PASSWORD)
            page.click('#sysverb_login')
            page.wait_for_load_state('networkidle')
            page.goto(f'{URL}/sys.scripts.do')
            page.wait_for_selector('textarea[name="script"]')
            page.evaluate('(s) => { document.querySelector(\'textarea[name="script"]\').value = s; }', script)
            scope_select = page.locator('select[name="sys_scope"]')
            if scope_select.count():
                scope_select.select_option(label=scope) if scope != 'global' else scope_select.select_option('global')
            with page.expect_navigation():
                page.locator('input[type="submit"][value="Run script"], button:has-text("Run script")').first.click()
            text = page.inner_text('body')
        finally:
            browser.close()
    # Keep only the script output lines ("*** Script: ...")
    lines = [re.sub(r'^.*?\*\*\* Script: ', '', l) for l in text.splitlines() if '*** Script' in l]
    errors = [l for l in text.splitlines() if 'Evaluator' in l or 'Error' in l][:10]
    return '\n'.join(lines + (['ERRORS:'] + errors if errors else []))


if __name__ == '__main__':
    with open(sys.argv[1], encoding='utf-8') as f:
        src = f.read()
    print(run_background(src, sys.argv[2] if len(sys.argv) > 2 else 'global'))
