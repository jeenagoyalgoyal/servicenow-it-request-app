# Flow Designer: High-Cost Request Approval

**Flow name:** IT Request – Manager Approval
**Run as:** System user

## Trigger
- **Created** record on **IT Service Request**
- **Condition:** Estimated cost **greater than** 1000

## Actions
1. **Look Up Record:** User where Sys ID = Trigger → Requested for. Pill: *manager*.
2. **If** Requested for → Manager **is empty**
   - **Update Record:** Approval = Approved, Work notes = "No manager on file. Auto-approved for Service Desk review."
   - **End**
3. **Ask For Approval**
   - Record: Trigger → IT Service Request
   - Approval field: Approval
   - Rules: Approve when **Anyone approves** → Requested for.Manager
   - Due date: 3 days (auto-reject at timeout)
4. **If** Approval state **is** Approved
   - **Update Record:** State = Work in Progress, Work notes = "Approved by manager."
5. **Else**
   - **Update Record:** State = Closed Incomplete, Work notes = "Rejected by manager."
   - **Send Email** to Requested for: "Your request ${number} was not approved."

## Testing the flow
Use **Test** in Flow Designer with a request that has an estimated cost of 1500 and a requester who has a manager (for example *Abel Tuter* in the PDI demo data). Approve it from the requester's manager's approval list and confirm that State changes to Work in Progress.
