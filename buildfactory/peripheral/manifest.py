"""Peripheral adapter registry (design §4 / AC2).

Add a new external source = create `peripheral/adapters/<name>.py` (exposing
`SOURCE` + `to_ime`) and add ONE line here. Nothing else in the codebase changes.
"""

# Email is intentionally absent: the domain-level mail-router persists it in a
# Company journal, then Company Hub projects it to CEO.  Accepting /ingest/email
# here would bypass Company isolation, durable peek, and the CEO cursor.
ADAPTERS = ["webhook"]
