---
name: department-messaging
description: Send a plain collaboration message from one Department to another through Hub.
---

# Department messaging

```bash
python3 -m orchestration.control_client send_department_message \
  --json '{"to":"builder","subject":"short subject","body":"complete context"}' \
  --request-id 'message-<stable-purpose-id>'
```

The logical message contains only message ID, time, from, to, subject, and body.
`from` is bound by the harness; never submit it. There is no `kind`, reply ID,
or related Goal field—put necessary context in subject/body. A message does not
create a Goal or change an Objective, and the CEO is not copied.
