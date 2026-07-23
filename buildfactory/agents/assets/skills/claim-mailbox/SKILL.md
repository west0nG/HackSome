---
name: claim-mailbox
description: Claim or list permanent Company foundagent.net addresses. CEO-only; use when the Company needs a durable identity for signups, replies, or verification.
---

# Claim a Company email identity

Email addresses belong to the Company, not to a Department or person. Only the
CEO can claim one. Every Company has exactly five lifelong slots across the
`foundagent.net` domain, and every localpart is globally unique.

## Always list first

Before spending a slot, inspect the Company's existing identities:

```bash
python3 -m orchestration.control_client list_company_mailboxes \
  --json '{}' --request-id 'mailbox-list-<purpose>'
```

Reuse a suitable address for third-party accounts and verification. A signup
is not a reason to create a service-specific alias: the account will outlive
the immediate task.

## Claim only for a durable identity

```bash
python3 -m orchestration.control_client claim_company_mailbox \
  --json '{"name":"maya","label":"external account identity"}' \
  --request-id 'mailbox-claim-maya'
```

The payload never includes a Company id. Company Hub supplies the caller's
Company from trusted configuration.

Choose a short, human-credible, reusable name. Lowercase letters, digits, `.`,
`_`, and internal `-` are accepted; `+` aliases and reserved operational names
are rejected.

## The claim is permanent

- The fixed limit is five addresses per Company.
- There is no release, rename, or transfer operation.
- Repeating the same claim for this Company is safe and does not consume a
  second slot.
- A name already claimed by another Company cannot be taken.

Incoming mail is persisted in the Company's private mail journal and normally
wakes the CEO. Department and Worker can inspect that same Company mail through
the controlled `peek_company_email` method; no runtime reads the registry or
mail journal directly.
