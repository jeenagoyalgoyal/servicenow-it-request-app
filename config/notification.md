# Notification: Request Closed

1. **Register the event:** System Policy > Events > Registry
   - Event name: `x_<scope>.request.closed` · Table: IT Service Request
2. **Notification:** System Notification > Email > Notifications > New
   - Table: IT Service Request
   - When to send: **Event is fired**, Event name: `x_<scope>.request.closed`
   - Who will receive: **Event parm 1 contains recipient** = true
   - Subject: `Your IT request ${number} is complete`
   - Message:
     ```
     Hi ${requested_for},

     Your request ${number} (${short_description}) has been closed by ${assignment_group}.

     ${URI_REF}
     ```
