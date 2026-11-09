# IT Service Request App (ServiceNow)

A scoped ServiceNow application where employees request IT help (hardware, software, access, network). It works out the priority automatically, routes each request to the right support team, blocks duplicates, and asks the requester's manager for approval when the cost is over $1,000.

Deployed and tested on a ServiceNow **Brazil** Personal Developer Instance. The deploy and test scripts (Python, REST API and Playwright) are in `deploy/`.

## Features

| Feature | ServiceNow piece | File |
|---|---|---|
| Custom request table extending **Task**, `ITREQ` numbering | Table, fields, choices | `config/table_and_fields.md` |
| Priority from an impact × urgency matrix | Business Rule + Script Include | `server/business_rules/set_priority_and_assignment.js` |
| Routing to Hardware / Software / Service Desk / Network groups | Script Include (GlideRecord) | `server/script_includes/RequestUtils.js` |
| Blocks a second open request in the same category | Business Rule (`setAbortAction`) | `server/business_rules/prevent_duplicate_requests.js` |
| Requested for defaults to the submitter | Business Rule | `server/business_rules/default_requested_for.js` |
| Manager approval for requests over $1,000 (approve → Work in Progress, reject → Closed Incomplete, no manager → auto-approved) | 3 Business Rules + Approval table (`sysapproval_approver`) | `server/business_rules/*approval*.js` |
| Event and email notification when a request closes | Business Rule + event + notification | `server/business_rules/notify_on_close.js`, `config/notification.md` |
| Assignment group fills in as soon as the category changes | Client Script + **GlideAjax** | `client/client_scripts/onChange_category.js` |
| Justification required over $1,000; priority read-only; closed requests locked | UI Policies + onSubmit Client Script | `config/ui_policies.md`, `client/client_scripts/onSubmit_validate_cost.js` |
| Request data as JSON for other systems | Scripted REST API (2 GET endpoints) | `server/scripted_rest/*.js` |
| Agent role and access controls | Role + ACLs | `config/acls.md` |

## Deploy and test

Needs Python 3, `pip install playwright` and Google Chrome.

1. Create `~/.servicenow_pdi` with 3 lines: instance URL, admin user, password (`chmod 600`). It's read by the scripts and never committed.
2. Deploy (safe to re-run; each record is updated in place):
   ```
   python3 deploy/deploy.py
   ```
3. Run the tests:
   ```
   python3 deploy/smoke_test.py     # 20 REST checks: rules, approvals, event, REST API
   python3 deploy/browser_test.py   # 9 browser checks: GlideAjax, UI Policies, onSubmit
   ```

Latest run (Nov 9, 2026, Brazil PDI): **20/20** REST checks and **9/9** browser checks passed. Both test scripts delete the records they create.

### What the tests check
- **Rules:** priority for 3 impact/urgency combinations, routing for 3 categories, re-routing when the category changes, duplicate blocking, `ITREQ` numbering.
- **Approvals:** a request over $1,000 waits for approval; the approval goes to the requester's manager; approve → Work in Progress; reject → Closed Incomplete; no manager → auto-approved; under $1,000 → no approval.
- **Event:** closing a request fires `request.closed` with the requester and the number.
- **REST API:** `GET /request/{number}` (200 and 404 cases) and `GET /summary`.
- **Form (browser):** all fields shown; GlideAjax fills the group and shows a message; priority is read-only; justification becomes mandatory over $1,000; submit is blocked without it and works with it.

## Notes from building it
- GlideAjax calls go through the global AJAX processor, so the client-callable Script Include must be accessible from **all application scopes**. It also needs an `execute` ACL of type `client_callable_script_include` named after the Script Include. Without these, the form gets "HTTP Processor class not found".
- `GlideAggregate.addActiveQuery()` isn't allowed in scoped apps; use `addQuery('active', true)`.
- Script default values (`javascript:gs.getUserID()`) are blocked on dictionary entries created through REST, so the default is set in a before-insert Business Rule.
- UI Policy actions and ACLs can't be fully created through the REST Table API, so `deploy/post_deploy.js` creates them as admin in Scripts - Background.

## Project structure
```
servicenow-it-request-app/
├── server/
│   ├── script_includes/RequestUtils.js
│   ├── business_rules/          # 7 rules: defaults, duplicates, priority/routing, approvals, close event
│   └── scripted_rest/           # GET /summary, GET /request/{number}
├── client/client_scripts/       # onChange (GlideAjax), onSubmit validation
├── config/                      # table, UI policies, ACLs, notification
└── deploy/                      # deploy.py, post_deploy.js, smoke_test.py, browser_test.py
```

## Author
Jeena Goyal · [GitHub](https://github.com/jeenagoyalgoyal) · [LinkedIn](https://www.linkedin.com/in/jeena-goyal-b372a2284/)
