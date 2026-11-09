# Table and Fields

**Table:** IT Service Request (`x_<scope>_it_service_request`)
**Extends:** Task. It inherits number, state, impact, urgency, priority, assignment_group, assigned_to, short_description, opened_at and approval.
**Number prefix:** `ITREQ` (for example ITREQ0001001)
**Create module:** yes (the app menu gets "IT Service Requests")

## New fields

| Label | Column name | Type | Notes |
|---|---|---|---|
| Requested for | `requested_for` | Reference (sys_user) | Mandatory. Default: `javascript:gs.getUserID()` |
| Category | `category` | Choice | Mandatory. Choices below |
| Estimated cost | `estimated_cost` | Integer | Dollars. Default 0 |
| Justification | `justification` | String (1000) | Required when estimated cost is over 1000 |

## Category choices

| Label | Value |
|---|---|
| Hardware | `hardware` |
| Software | `software` |
| Access | `access` |
| Network | `network` |

## Form layout
Number, Requested for, Category, Short description, Impact, Urgency, Priority (read-only), Estimated cost, Justification, Assignment group, Assigned to, State.

Make **Priority** read-only on the form (Form Designer, or a UI Policy action) because the Business Rule sets it.
