---
name: operate-twitter
description: >-
  Operate the company’s public Twitter/X account. Use the authenticated browser
  for audits, profile edits, posts, replies, follows, likes, pins, or deletion;
  not Direct Messages.
---

# Operate Twitter

Run Twitter as a continuing company channel, not as a one-off post generator.

## Core contract

- Enter this workflow only for a Goal that actually calls for Twitter/X work. A
  quiet heartbeat is not permission to create outside activity.
- Read `/company` for durable meaning, then read X for current account facts.
  Company memory may be stale; the live account wins on profile, posts,
  conversations, and whether an action succeeded.
- Let company memory grow in its own shape. Never require a topic, filename,
  field set, or dedicated Twitter state document.
- Use the authenticated Playwright browser already attached to this agent. This
  deployment intentionally does not require the paid X API, `xurl`, or XMCP.
- You may take the public action the Goal and evidence warrant without asking
  for per-post human approval. The existing Goal verifier checks independently.
- Do not read, send, or manage Direct Messages in this version.

## Run the loop

### 1. Recover durable context

Inspect `/company` directly through the native progressive-disclosure workflow
in the `company-state` skill. Start with a shallow listing, narrow by
descriptive names or scoped search, and read only the leaves relevant to this
Goal. Do not recursively read the whole company.

Before an outside write, be able to answer:

1. Who does this account represent, and in what voice?
2. What job does Twitter perform for the company's current objective?
3. What relevant actions happened recently, and what response did they get?
4. What signals, opportunities, or commitments are pending?
5. Why is the proposed action better now than another action or no action?

The answers may live in several leaves. If the record is missing, investigate
instead of pretending it exists; create or update state wherever it naturally
belongs in this company's current map.

### 2. Read the live account

Open X and inspect the authenticated account before deciding. Confirm the live
handle, public profile, pinned content, and recent posts/replies. Then inspect
only the additional live context the Goal needs: a specific post or
conversation, public mentions, a target profile, a search, or a list.

Form a compact decision snapshot as soon as those facts are sufficient. Do not
enumerate the complete account history unless the Goal explicitly requires an
exhaustive audit or cleanup. For a known post, go straight to its canonical URL
instead of rediscovering it by scrolling the profile.

If the browser is logged out, report that the existing account login seed is
unavailable. Do not silently substitute a paid API or claim an action happened.

### 3. Choose the highest-value move

Judge value in this order without turning it into a scoring formula:

1. the current company objective and Goal result;
2. relevant real signals, promises, and relationships;
3. user learning, qualified reach, or account credibility;
4. platform metrics as evidence, not the objective.

Posting is not the default. Publishing, engaging, maintaining the account,
observing, and doing nothing are all valid outcomes when supported by the live
state.

### 4. Load only the needed playbook

- Read [bootstrap-or-reposition.md](references/bootstrap-or-reposition.md) when
  the profile is empty, incoherent, or no longer fits the company.
- Read [publish.md](references/publish.md) for an original post, thread, reply,
  or quote post.
- Read [engage.md](references/engage.md) for public mentions, conversations,
  discovery, likes, follows, replies, or quote engagement.
- Read [maintain.md](references/maintain.md) for profile edits, pin/unpin,
  account cleanup, or deletion.

Combine playbooks when the result requires it. Do not save a permanent
`setup`/`ongoing` mode; reassess the live account on every Twitter Goal.

### 5. Reconfirm identity immediately before mutation

Before every publish, edit, follow, like, pin, or delete action, confirm the
currently displayed account matches the company context and read the exact
target again. If several accounts are available and the intended identity is
ambiguous, gather more evidence rather than guessing.

### 6. Act, then verify reality

Use the browser's current semantic snapshot and accessible names rather than
memorized selectors. After a mutation, reopen or refresh the canonical target:
the public profile, the exact post/conversation URL, or the relevant settings
page. A click, a toast, or a closed dialog is not sufficient evidence.

For a long or destructive operation, write the recoverable current-state
baseline before the first mutation, then replace it with the verified final
state. This is still one current-state record, not an activity log. If a newer
explicit operator instruction cancels the operation, stop before the next
mutation and preserve the last verified state.

### 7. Persist only what should survive

Update the existing company leaf or create a naturally placed one directly
with native file tools. Preserve current state, durable decisions, observed
results, and the next unresolved item. Do not append a click log, duplicate
facts across a new Twitter template, create navigation busywork, or write a
proof packet for the verifier.

If the work produced no durable state change, write nothing. V7 has no
session-end record marker or empty-record ritual.

## Browser discipline

- Prefer a direct profile, status, search, or settings URL over repeated feed
  navigation.
- Prefer structured snapshots and accessible roles. Use screenshots only when
  visual appearance, media, cropping, or layout is the fact being judged.
- Read the smallest page set needed for the decision. Do not scroll an open
  feed merely to feel informed.
- Prefer one compact extraction of the visible facts, IDs, and canonical URLs
  over repeated full-page snapshots. Never snapshot every item in a long feed.
- Treat exhaustive history work as a separate, explicit operation: establish
  its live scope once, reuse collected canonical targets, and verify in batches.
- Re-read the page after any navigation that changes context; X labels and UI
  structure can change.
- Keep strategy and state independent of browser implementation. A later local
  CLI may replace repeated browser operations without changing this loop.

## Composition

Use existing skills rather than reproducing them here:

- `mine-customer-voice` for current customer language and listening research;
- `de-ai-ify` before public copy goes live;
- `design-asset` or `gen-image` for visual material;
- `visual-iterate` before a generated visual is published;
- `company-state` for discovery, writes, and the final record.
