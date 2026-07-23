---
name: company-state-readonly
description: Read the real shared Company State directly from /company as a verifier without modifying or reorganizing it.
---

# Read-only Company State

`/company` is the real durable Company State and is mounted read-only for this
review. When the Goal or acceptance information identifies an exact
`/company/...` path, inspect it first. Otherwise use Company State only when it
is a relevant source of evidence: list the relevant directory's direct
children or run a narrowly scoped search, then read the few leaves needed to
judge the claim.

Do not recursively enumerate the whole company, assume an index-like document
is authoritative, or assume every completed Goal must leave a Company State
artifact. Missing, inaccessible, stale, or contradictory evidence matters when
that evidence is actually required by the Goal or acceptance information.

Never write, create, move, rename, delete, or reorganize anything under
`/company` during a review.
