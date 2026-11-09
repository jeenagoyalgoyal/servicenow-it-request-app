# Role and Access Controls

Created by `deploy/deploy.py` (role) and `deploy/post_deploy.js` (ACLs).

**Role:** `x_<scope>.agent`. It contains `itil`.

| Type | Operation | Name | Who | Rule |
|---|---|---|---|---|
| record | read | `<table>` | `x_<scope>.agent` | Agents can read all requests |
| record | read | `<table>` | script | Requesters can read their own requests |
| record | create | `<table>` | `snc_internal` | Any logged-in user can create a request |
| record | write | `<table>` | `x_<scope>.agent` | Agents can update requests |
| record | write | `<table>.priority` | `admin` | Only admins can override priority |
| record | delete | `<table>` | `admin` | Only admins can delete requests |
| client_callable_script_include | execute | `RequestUtils` | `snc_internal` | Lets the form call RequestUtils through GlideAjax |

## Requester read script
```javascript
answer = (current.getValue('requested_for') == gs.getUserID()) ||
         (current.getValue('opened_by') == gs.getUserID());
```

The tests run as admin. The GlideAjax ACL is exercised by the browser test; the record ACLs for non-admin users haven't been tested yet.
