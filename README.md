# IT Service Request App (ServiceNow)

A scoped ServiceNow application that lets employees request IT help (hardware, software, access, network). The app works out the priority automatically, sends each request to the right support team, and asks the requester's manager for approval when the cost is over $1,000.

Built on a ServiceNow Personal Developer Instance (PDI) with JavaScript (server and client side), GlideRecord, GlideAjax, Flow Designer, a Scripted REST API and the Automated Test Framework (ATF).

## Features

| Feature | ServiceNow piece | File |
|---|---|---|
| Custom request table (extends **Task**) | Table, fields, choices | `config/table_and_fields.md` |
| Priority from impact × urgency matrix | Business Rule + Script Include | `server/business_rules/set_priority_and_assignment.js` |
| Routing to Hardware / Software / Service Desk / Network groups | Script Include (GlideRecord) | `server/script_includes/RequestUtils.js` |
| Block duplicate open requests | Business Rule (`setAbortAction`) | `server/business_rules/prevent_duplicate_requests.js` |
| Email the requester when closed | Business Rule + event + notification | `server/business_rules/notify_on_close.js` |
| Live assignment group when category changes | Client Script + GlideAjax | `client/client_scripts/onChange_category.js` |
| Justification required for requests over $1,000 | Client Script (onSubmit) + UI Policy | `client/client_scripts/onSubmit_validate_cost.js`, `config/ui_policies.md` |
| Manager approval for requests over $1,000 | Flow Designer | `config/flow_designer_approval.md` |
| Request data as JSON for other systems | Scripted REST API | `server/scripted_rest/*.js` |
| Role-based access | ACLs | `config/acls.md` |
| Automated tests | ATF (server-side Jasmine + form tests) | `tests/` |

## Project structure

```
servicenow-it-request-app/
├── README.md
├── config/                  # table, UI policies, flow, ACLs, notification (setup steps)
├── server/
│   ├── script_includes/     # RequestUtils (GlideRecord + GlideAjax processor)
│   ├── business_rules/      # priority/assignment, duplicates, close notification
│   └── scripted_rest/       # GET summary, GET by number
├── client/client_scripts/   # onChange (GlideAjax), onSubmit validation
└── tests/                   # ATF test definitions
```

## Setup on a Personal Developer Instance

1. Get a free instance at https://developer.servicenow.com (Sign in, then **Request Instance**).
2. Open **App Engine Studio** or **ServiceNow Studio** and create a scoped app named **IT Service Request**. ServiceNow gives it a scope like `x_<your_prefix>_it_service`. Note it down.
3. Create the table and fields in `config/table_and_fields.md`.
4. Create the Script Include `RequestUtils` and tick **Client callable**. Paste in `server/script_includes/RequestUtils.js`.
5. Create the three Business Rules in `server/business_rules/`. Each file's header lists the **When / Order / Condition** settings.
6. Create the two Client Scripts in `client/client_scripts/`. In `onChange_category.js`, replace `x_scope` with your app scope.
7. Set up the UI Policy, the Flow, the ACLs and the notification using the files in `config/`.
8. Create the Scripted REST API in `server/scripted_rest/`.
9. Create the ATF tests in `tests/` and run them.
10. **Optional:** link the app to this GitHub repo (Studio, then **Source Control**, then **Link to Source Control**) so the full app XML is versioned here.

The demo data on a new PDI already includes the **Hardware**, **Software**, **Service Desk** and **Network** groups that the routing uses.

## Testing

- `tests/atf_request_utils_server_test.js` checks the priority matrix and group routing (Jasmine, run with the ATF step "Run Server Side Validation Script").
- `tests/atf_form_tests.md` covers form tests: auto priority, auto routing, duplicate blocking, and the over-$1,000 justification rule.

## Author

Jeena Goyal · [GitHub](https://github.com/jeenagoyalgoyal) · [LinkedIn](https://www.linkedin.com/in/jeena-goyal-b372a2284/)
