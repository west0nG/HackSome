---
name: send-email
description: Send external email from a Company foundagent.net address through Hub. Available to Department and Worker; use for replies, follow-ups, or notifications.
---

# Send Company email

Department and Worker may both send. For ordinary external execution, a
Department should usually create a Goal and let its Worker do the operation.
That is workflow guidance, not a permission restriction: if direct handling is
the sensible action in the current wake, the Department may send itself.

## 1. Select an existing Company identity

```bash
python3 -m orchestration.control_client list_company_mailboxes \
  --json '{}' --request-id 'mailbox-list-before-send-<purpose>'
```

Use one of the returned localparts. Do not invent an address and do not access
the global registry directly.

## 2. Send through Company Hub

```bash
python3 -m orchestration.control_client send_company_email \
  --json '{"mailbox":"maya","to":"person@example.com","subject":"Subject","text":"Plain-text body"}' \
  --request-id 'email-send-<stable-logical-id>'
```

Optional payload fields are `html` and `from_name`. `mailbox` is the localpart,
not a full address. The Hub binds the Company and actor outside the payload and
rejects addresses belonging to another Company.

Keep the same request id only when retrying the exact same logical email. It is
also the provider idempotency key. Never reuse it for changed recipients,
subject, or body.

## Shared quota and failure behavior

- Company: 30 reservations per rolling 24 hours.
- Each Company address: 15 reservations per rolling 24 hours.
- Reservation happens before the provider call, so a failed send still costs
  one slot and is not refunded.
- Do not blind-retry a provider failure. Read the error, correct the cause, and
  decide whether a genuinely new send is warranted.

Email is external and public. Internal Company coordination uses Department
messaging, not email. Protect domain reputation: avoid indiscriminate cold
outreach, write for the actual recipient, and treat every send as the Company's
voice.
