"""Small ServiceNow REST helper shared by deploy.py and smoke_test.py.

Credentials come from ~/.servicenow_pdi (line 1: instance URL, line 2: user,
line 3: password). They are never written to the repo or put on the command
line: curl reads them from stdin.
"""
import json
import os
import re
import subprocess
import tempfile
import urllib.parse

CRED_FILE = os.path.expanduser(os.environ.get('SN_CRED_FILE', '~/.servicenow_pdi'))


def _load_creds():
    with open(CRED_FILE, encoding='utf-8') as f:
        lines = [line.strip() for line in f.read().splitlines()]
    match = re.match(r'https?://[^/\s]+', lines[0])
    if not match or len(lines) < 3:
        raise SystemExit(f'{CRED_FILE} must contain: URL, user, password (one per line)')
    return match.group(0), lines[1], lines[2]


URL, USER, PASSWORD = _load_creds()


def _curl_config():
    def esc(s):
        return s.replace('\\', '\\\\').replace('"', '\\"')
    return f'user = "{esc(USER)}:{esc(PASSWORD)}"\n'


def api(method, path, body=None, params=None):
    """Call the instance. Returns (status_code, parsed_json_or_text)."""
    url = URL + path
    if params:
        url += '?' + urllib.parse.urlencode(params)
    args = ['curl', '-s', '-K', '-', '-X', method,
            '-H', 'Accept: application/json',
            '-H', 'Content-Type: application/json',
            '-w', '\n%{http_code}', url]
    tmp = None
    if body is not None:
        tmp = tempfile.NamedTemporaryFile('w', suffix='.json', delete=False, encoding='utf-8')
        json.dump(body, tmp)
        tmp.close()
        args += ['--data-binary', '@' + tmp.name]
    try:
        out = subprocess.run(args, input=_curl_config(), capture_output=True,
                             text=True, timeout=120).stdout
    finally:
        if tmp:
            os.unlink(tmp.name)
    text, _, code = out.rpartition('\n')
    status = int(code) if code.isdigit() else 0
    try:
        data = json.loads(text) if text.strip() else {}
    except ValueError:
        data = text[:500]
    return status, data


def get_records(table, query, fields='sys_id', limit=100):
    status, data = api('GET', f'/api/now/table/{table}', params={
        'sysparm_query': query, 'sysparm_fields': fields,
        'sysparm_limit': limit, 'sysparm_exclude_reference_link': 'true'})
    if status != 200:
        raise RuntimeError(f'GET {table} ({query}) failed: HTTP {status} {str(data)[:300]}')
    return data['result']


def find(table, query, fields='sys_id'):
    rows = get_records(table, query, fields, limit=1)
    return rows[0] if rows else None
