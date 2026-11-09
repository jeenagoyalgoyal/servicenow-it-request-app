#!/usr/bin/env python3
"""End-to-end checks against a deployed instance, using REST only.

Usage:  python3 deploy/smoke_test.py
Creates test requests, checks the Business Rules, event and Scripted REST API,
then deletes the test requests.
"""
import sys
import time

from sn import api, find, get_records

RESULTS = []


def check(name, ok, detail=''):
    RESULTS.append(ok)
    print(f'  {"PASS" if ok else "FAIL"}  {name}' + (f'  ({detail})' if detail and not ok else ''))


def main():
    vendor = find('sys_properties', 'name=glide.appcreator.company.code', 'value')['value']
    scope = f'x_{vendor}_itreq'
    table = f'{scope}_service_request'
    groups = {g['name']: g['sys_id'] for g in
              get_records('sys_user_group', 'nameINHardware,Software,Service Desk,Network', 'name,sys_id')}
    abel = find('sys_user', 'user_name=abel.tuter')['sys_id']
    beth = find('sys_user', 'user_name=beth.anglin')['sys_id']
    created = []
    fields = 'sys_id,number,priority,assignment_group,state,category'

    def insert(body):
        status, data = api('POST', f'/api/now/table/{table}', body,
                           params={'sysparm_fields': fields, 'sysparm_exclude_reference_link': 'true'})
        if status == 201:
            created.append(data['result']['sys_id'])
        return status, data

    def patch(sys_id, body):
        return api('PATCH', f'/api/now/table/{table}/{sys_id}', body,
                   params={'sysparm_fields': fields, 'sysparm_exclude_reference_link': 'true'})

    # Clear leftovers from an earlier run so the duplicate rule doesn't block us.
    for row in get_records(table, f'requested_forIN{abel},{beth}^short_descriptionSTARTSWITH[smoke]'):
        api('DELETE', f'/api/now/table/{table}/{row["sys_id"]}')

    try:
        print('Business Rules')
        status, data = insert({'requested_for': abel, 'category': 'hardware', 'impact': '1',
                               'urgency': '1', 'short_description': '[smoke] Laptop not booting'})
        check('insert request', status == 201, f'HTTP {status} {str(data)[:200]}')
        if status != 201:
            return
        a = data['result']
        check('number uses ITREQ prefix', a['number'].startswith('ITREQ'), a['number'])
        check('priority 1 for high impact + high urgency', a['priority'] == '1', a['priority'])
        check('routed to Hardware group', a['assignment_group'] == groups['Hardware'],
              a['assignment_group'])

        status, data = insert({'requested_for': abel, 'category': 'hardware', 'impact': '3',
                               'urgency': '3', 'short_description': '[smoke] Second hardware request'})
        check('duplicate open request is blocked', status != 201, f'HTTP {status}')

        status, data = insert({'requested_for': beth, 'category': 'software', 'impact': '2',
                               'urgency': '3', 'short_description': '[smoke] Install Visio'})
        c = data.get('result', {}) if status == 201 else {}
        check('priority 4 for medium impact + low urgency', c.get('priority') == '4', c.get('priority'))
        check('routed to Software group', c.get('assignment_group') == groups['Software'],
              c.get('assignment_group'))

        status, data = patch(a['sys_id'], {'category': 'network', 'impact': '3', 'urgency': '3'})
        u = data.get('result', {})
        check('re-routed to Network when category changes',
              u.get('assignment_group') == groups['Network'], u.get('assignment_group'))
        check('priority recalculated to 5 on update', u.get('priority') == '5', u.get('priority'))

        print('\nEvent on close')
        patch(a['sys_id'], {'state': '3'})
        event = None
        for _ in range(12):
            time.sleep(5)
            event = find('sysevent', f'name={scope}.request.closed^instance={a["sys_id"]}',
                         'sys_id,parm1,parm2,state')
            if event:
                break
        check('request.closed event fired with requester and number',
              bool(event) and event['parm1'] == abel and event['parm2'] == a['number'], str(event))

        print('\nScripted REST API')
        base = f'/api/{scope}/it_service_requests'
        status, data = api('GET', f'{base}/request/{c.get("number", "")}')
        body = data.get('result', {}) if isinstance(data, dict) else {}
        check('GET /request/{number} returns the request', status == 200 and
              body.get('number') == c.get('number'), f'HTTP {status} {str(data)[:200]}')
        check('response includes assignment group name', body.get('assignment_group') == 'Software',
              body.get('assignment_group'))
        status, data = api('GET', f'{base}/request/ITREQ9999999')
        check('GET unknown number returns 404', status == 404, f'HTTP {status}')
        status, data = api('GET', f'{base}/summary')
        cats = {r['category']: r['open'] for r in data.get('result', {}).get('open_by_category', [])} \
            if status == 200 else {}
        check('GET /summary counts open requests by category', status == 200 and
              cats.get('software', 0) >= 1, f'HTTP {status} {str(data)[:200]}')

        print('\nManager approval (requests over $1,000)')
        users = get_records('sys_user', 'active=true^managerISNOTEMPTY^manager.active=true^user_nameISNOTEMPTY',
                            'sys_id,user_name,manager', limit=3)
        no_mgr = get_records('sys_user', 'active=true^managerISEMPTY^user_nameISNOTEMPTY^user_name!=admin',
                             'sys_id,user_name', limit=1)
        for u in users[:2] + no_mgr:
            for row in get_records(table, f'requested_for={u["sys_id"]}^active=true'):
                api('DELETE', f'/api/now/table/{table}/{row["sys_id"]}')

        def approval_for(req_id):
            return find('sysapproval_approver', f'document_id={req_id}', 'sys_id,approver,state')

        status, data = insert({'requested_for': users[0]['sys_id'], 'category': 'hardware',
                               'estimated_cost': '1500', 'justification': 'New laptop',
                               'short_description': '[smoke] Laptop over $1,000'})
        r1 = data.get('result', {}) if status == 201 else {}
        full = find(table, f'sys_id={r1.get("sys_id")}', 'approval,state') or {}
        check('request over $1,000 waits for approval', full.get('approval') == 'requested'
              and full.get('state') == '-5', str(full))
        ap = approval_for(r1.get('sys_id'))
        check("approval created for the requester's manager",
              bool(ap) and ap['approver'] == users[0]['manager'], str(ap))
        if ap:
            api('PATCH', f'/api/now/table/sysapproval_approver/{ap["sys_id"]}', {'state': 'approved'})
            time.sleep(2)
            full = find(table, f'sys_id={r1["sys_id"]}', 'approval,state') or {}
            check('approving moves request to Work in Progress',
                  full.get('approval') == 'approved' and full.get('state') == '2', str(full))

        status, data = insert({'requested_for': users[1]['sys_id'], 'category': 'software',
                               'estimated_cost': '2500', 'justification': 'Design licence',
                               'short_description': '[smoke] Licence over $1,000'})
        r2 = data.get('result', {}) if status == 201 else {}
        ap = approval_for(r2.get('sys_id'))
        if ap:
            api('PATCH', f'/api/now/table/sysapproval_approver/{ap["sys_id"]}', {'state': 'rejected'})
            time.sleep(2)
        full = find(table, f'sys_id={r2.get("sys_id")}', 'approval,state,active') or {}
        check('rejecting closes request as Closed Incomplete',
              bool(ap) and full.get('approval') == 'rejected' and full.get('state') == '4', str(full))

        if no_mgr:
            status, data = insert({'requested_for': no_mgr[0]['sys_id'], 'category': 'access',
                                   'estimated_cost': '1200', 'justification': 'Admin tool access',
                                   'short_description': '[smoke] No manager on file'})
            r3 = data.get('result', {}) if status == 201 else {}
            full = find(table, f'sys_id={r3.get("sys_id")}', 'approval') or {}
            check('no manager on file -> auto-approved, no approval record',
                  full.get('approval') == 'approved' and not approval_for(r3.get('sys_id')), str(full))

        status, data = insert({'requested_for': users[0]['sys_id'], 'category': 'network',
                               'estimated_cost': '200', 'short_description': '[smoke] Cheap cable'})
        r4 = data.get('result', {}) if status == 201 else {}
        check('request under $1,000 needs no approval', bool(r4) and not approval_for(r4.get('sys_id')))
    finally:
        for sys_id in created:
            for ap in get_records('sysapproval_approver', f'document_id={sys_id}'):
                api('DELETE', f'/api/now/table/sysapproval_approver/{ap["sys_id"]}')
            api('DELETE', f'/api/now/table/{table}/{sys_id}')
        print(f'\nCleaned up {len(created)} test request(s).')

    passed = sum(RESULTS)
    print(f'\n{passed}/{len(RESULTS)} checks passed')
    sys.exit(0 if RESULTS and all(RESULTS) else 1)


if __name__ == '__main__':
    main()
