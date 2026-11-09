# Access Controls (ACLs)

The app creates the role `x_<scope>.agent`. Make it contain the `itil` role.

| Operation | Name | Roles | Script |
|---|---|---|---|
| read | `x_<scope>_it_service_request` | `x_<scope>.agent` | — |
| read | `x_<scope>_it_service_request` | (none) | Requester can read own records (below) |
| create | `x_<scope>_it_service_request` | (none; any logged-in user) | — |
| write | `x_<scope>_it_service_request` | `x_<scope>.agent` | — |
| write | `x_<scope>_it_service_request.priority` | `admin` | Only admins can override priority by hand |
| delete | `x_<scope>_it_service_request` | `admin` | — |

## Requester read script
```javascript
answer = (current.getValue('requested_for') == gs.getUserID()) ||
         (current.getValue('opened_by') == gs.getUserID());
```
