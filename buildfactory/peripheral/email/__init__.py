"""Domain-level inbound email package.

Cloudflare Email Routing writes raw MIME to the R2 spool.  The singleton
``poller`` module resolves a permanent Company claim and writes that Company's
private mail journal.  It does not call Peripheral HTTP ingress or route to an
Agent; Company Hub later notifies CEO and serves controlled read-only peeks.
"""
