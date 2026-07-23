# Maintain and clean the account

Use this playbook for profile adjustments, pinning or unpinning content,
auditing old public content, and deleting a specific post or reply.

## Start from live reality

Read the current public profile and relevant company context. Capture the live
starting value of any profile field that may need to be restored during a
temporary test. Decide whether a change fixes a current mismatch; do not edit
the profile just to exercise a control.

For identity-wide repositioning, also use the bootstrap-or-reposition
playbook. This playbook owns the precise maintenance action and verification.

## Pin or unpin deliberately

Open the candidate post and current profile before changing the pin. Confirm
the candidate is owned by the current account and still represents the
company. After the action, reopen the public profile and verify the intended
post is pinned—or that no post is pinned when unpinning was the goal.

## Delete precisely

Deletion is a supported operation, including cleanup of old verification or
test content. Before opening the delete confirmation, verify all of these from
live X:

- the current authenticated handle;
- the exact post/reply URL;
- author, text, timestamp, and conversation context;
- the concrete reason this content should no longer exist.

Do not make bulk deletion the default way to reposition an account. Do not
delete from an old company-memory description without reopening the live
object.

When a Goal explicitly requires bulk cleanup, treat it as a bounded destructive
operation of its own. Establish the live count and content classes once, save a
recoverable current-state baseline, and collect compact canonical targets rather
than repeatedly snapshotting the timeline. Delete in batches, re-check identity
between batches, and stop before the next mutation if the operator cancels.
Revisit Posts and Replies after lazy loading settles; a top-of-profile sample is
not proof that the history is empty.

After confirming deletion, reopen the canonical URL and the public profile.
The target must be absent from both relevant views; a closed menu or success
toast alone does not prove deletion.

## Restore temporary test changes

The current development task may explicitly authorize temporary live changes.
When it does, restore profile fields and delete temporary posts/replies before
the same test run ends, then verify the restored public state. Do not leave a
cleanup promise for the next wake.

Keep real improvements that the Goal and live evidence justify. In company
state, distinguish durable account facts and next actions from disposable test
steps; do not append a maintenance log.
