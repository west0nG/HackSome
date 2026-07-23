# Useful Idea E2E Benchmark

## Benchmark prompts

These are two separate benchmark inputs and must never be concatenated:

1. `PAWN`
2. `发行二周目——带着 AI，重打一遍米哈游游戏的全球发行`

Their tracked, hash-bound source files live in `fixtures/manifest.json`.
The current valid run reads only `fixtures/mihoyo-global-release.md`; `PAWN`
remains a separate future run with its own challenge, state, artifacts, and
report.

## Run ledger

| Run | Result | Learning |
|---|---|---|
| `pawn-mihoyo-e2e-01` | Cancelled; non-resumable | Invalid benchmark because two independent prompts were concatenated. |
| `mihoyo-global-release-e2e-01` | Failed at S1 | Codex structured output rejected JSON Schema `uniqueItems`; the retry was non-actionable. |
| `mihoyo-global-release-e2e-02` | Paused at early S9 | First valid full-fanout benchmark of the Mihoyo prompt; policy 1 and the first policy-2 calibration both exposed the same value-substitution false pass. |

## Runtime defects found and fixed

### Codex schema subset

- Removed `uniqueItems` from wire schemas.
- Kept alias and completion-path uniqueness as controller validation.
- Added runner preflight for known unsupported schema keywords.
- Added local Draft 2020-12 schema validation before spawn and local instance
  validation for the returned last message.
- Invalid request/schema/unsupported-parameter/context-length errors are now
  non-retryable.

### Runtime context isolation

- Added `--disable plugins`.
- Added `skills.include_instructions=false`.
- Kept project instruction injection disabled.
- Added a fail-closed preflight for non-empty global `AGENTS.override.md` or
  `AGENTS.md` in the effective `CODEX_HOME`; the active machine's file is empty,
  so the current run was not contaminated.
- Added a fail-closed preflight for saved legacy Codex configurations that omit
  any mandatory feature disable, config override, or isolation control.
- S0 input fell from 14,517 tokens in the earlier run to 8,015 tokens in the
  isolated run.

### Transient reconnect handling

A Codex attempt can emit a temporary reconnect `error` and later finish with
`turn.completed`. The completed turn is now authoritative, avoiding a duplicate
runner-level session resume.

### S3 input/output contract collision

The first verifier correctly derived non-empty `recheck_evidence_ids`, but the
controller incorrectly bound that output to the empty input list. The fixed
contract is:

- `routing.assigned_recheck_evidence_ids`: blind verifier input scope;
- artifact `recheck_evidence_ids`: verifier output decision.

Prepared staged artifacts are hash-journaled. If canonical publication is
missing after an interruption, resume now revalidates and promotes the staged
bytes without another Codex call. This recovered 20 real S3 outputs.

### True but out-of-domain Problems

S1 treated every named actor as a potential user, including participants and
judges. The participant branch produced real Problems about hackathon pitch
decks, team formation, and submission deadlines, none of which belongs to the
game-global-publishing challenge domain.

S5 T1 now reads `DiscoveryView` and requires direct challenge-domain relevance.
This is a Problem relevance check, not a Sponsor technology or submission
compliance gate.

### S1 target-user eligibility

The next prompt revision treats `DiscoveryView.explicit_audiences` and every
named group as research leads, not mandatory outputs. A group must have an
independent relationship to the challenge theme or problem domains; mention as
a participant, judge, organizer, Sponsor, submission/Q&A actor, or public-data
source is insufficient. This remains a prompt contract rather than a brittle
controller keyword filter.

### S5 evidence-context narrowing

The live S5 implementation repeated every Research and Verification file for an
Audience in every Problem gate. Across the 86 Problems, the full input averaged
8.42 evidence documents while the Problem body actually cited 5.10. Keeping
the complete cited files but excluding uncited same-Audience files retained
about 68% of the evidence bytes.

The next controller revision derives the exact subset from canonical paths and
local Evidence ids in the Problem's `Evidence` and `Counterevidence and
Uncertainty` sections. It validates Audience ownership, Research/Verification
pairing, canonical verifier-001 citation, and verifier-002 coverage when the
first verifier requested a blind recheck. The same subset is used by primary
and blind Gateways and carried into downstream Idea stages. It does not reduce
candidate counts or excerpt source documents.

### Completed S5 checkpoint replay

The paused run had already completed S5 before the stricter body-citation
contract was introduced. Five historical passed Problems are artifact-valid
but fail the newer parser. Reinterpreting them on resume would have silently
reduced 68 passed Problems to 63 and orphaned 25 existing S6 tasks.

Completed S5 is now replayed from integrity-bound Gateway tasks and the exact
historical evidence packet each Gateway received. Every Problem must still have
one terminal primary pass or a fully validated, ledger-bound S5 elimination.
A blind confirmation that returns `pass` is disagreement, not acceptance.
Against the real checkpoint, replay restored exactly 68 passes and 18
eliminations, with all 68 existing S6 Problem branches still attached.

### Early product-invalid screen

The live S6 sample exposed Ideas whose advertised value depended on an
uncontrolled official or community response. Waiting until after competitor
research to reject those branches multiplies avoidable work.

Topology v2 therefore gives every S6 Draft an independent early S9
`draft_screen` before S7. It checks only felt value, a complete real User Flow,
causal delivery, and fidelity to the passed Problem. Only `invalid` stops the
branch; `pass` and `repairable` continue unchanged, and the later full S9 keeps
its complete repair budget. Similarity is never a failure. The review binds the
exact S6 revision and SHA-256 so later S8 edits cannot rewrite what it reviewed.

### Bounded preparation for large fan-out

Starting 708 draft screens exposed a controller bottleneck before any model
limit: every coroutine copied context and rewrote a growing 9.6 MB `state.json`
before it reached the runner semaphore. The parent process stayed near 100% CPU
while all four spawned Codex sessions were starved of stdout handling.

Artifact-task preparation now acquires the same persisted Codex concurrency
slot before copying context or mutating state, and holds it only for that
concrete stage task. All candidates remain queued, the early-screen barrier is
unchanged, and later stages can still interleave; the fix adds no candidate cap.

### Draft-screen false passes

The first policy returned 25 passes before the run was paused. A deterministic
read-only audit of the first 16 found 13 defensible passes and three material
false passes:

- two Ideas delivered only a feedback ticket/community report while the passed
  player Problem remained unresolved until an uncontrolled third party acted;
- one Idea named internal story/voice manifests and client quest-state mutation
  as its mechanism without establishing that the player-facing product owned
  those inputs or permissions.

The reviews were adversarial in form but treated the Idea's own mechanism claims
as evidence. They also treated productizing an observed workaround as sufficient
Problem fidelity. The run was stopped before spending hundreds of additional
sessions on this policy. Historical reviews remain immutable; the replacement
policy uses a new versioned draft-screen task/path and blind context.

Draft-screen policy 2 first made the review prove the product's causal value path
instead of accepting the Idea's own mechanism claims as evidence. It separates
artifact production from Problem-aligned user value, checks control over every
critical input/action, rejects value that depends on an uncontrolled third
party, and reserves `repairable` for one local defect that leaves the core
product unchanged. It does not import the benchmark's public-data compliance
rule, compare Ideas, require direction diversity, or cap the fan-out.

The interrupted run was explicitly moved to policy 2: all 25 completed policy-1
reviews remained immutable history, only the 683 incomplete policy-1 tasks were
cancelled, and independent policy-2 tasks/sessions used the same hash-bound S6
revisions. No policy-1 review entered policy-2 context or counted as the current
decision.

The controlled policy-2 resume confirmed that the preparation fix held exactly
four active tasks and did not pre-register the remaining fan-out. The run was
stopped again after eight completed policy-2 reviews because the first known
ticket/report false pass still returned `pass`. The review repeated the new
causal-control rules but then redefined the product's value as cheaper feedback
preparation, using a workaround and consequence to replace the passed Problem's
primary blocked state: the player still could not trust or understand the game
text. The next policy must make that comparison mechanical: derive the primary
blocked state from the Problem section, derive the product's immediate user
state change before any uncontrolled third party acts, and reject a branch when
those outcomes do not materially match. Historical policy-2 reviews remain
immutable and are not valid current-policy decisions.

Policy 3 adds that missing comparison as an explicit closure test. It derives
the target user's original blocked judgment/action from the passed Problem,
reads only the Idea's declared Trigger, primary output, and felt-value moment,
then asks whether the immediate output still advances that same state if no
uncontrolled third party ever reads or acts. Workarounds, optional fields,
secondary audiences, and reviewer-invented uses cannot rescue a changed value
loop. A partial solution can still pass when it directly advances the same
native outcome. New runs persist policy 3 and write `draft-screen-003.md`;
policies 1 and 2 remain supported historical formats.

A seven-Idea policy-3 calibration then separated the product and feasibility
boundaries more cleanly:

- one report-only Idea became `invalid` because its triggering player knew no
  more about the text after receiving the primary output;
- a stronger correction package stayed `pass` because its declared primary
  output included direct comparison, uncertainty, and temporary explanation,
  so keeping it is consistent with the eliminate-only policy;
- the player-side Idea that silently assumed internal manifests and client
  state mutation became `invalid` because neither the target user nor that
  product plausibly controlled the core authority;
- two account-migration Ideas stayed `pass` at S9 because they explicitly
  described a first-party miHoYo product. The user value and flow are real if
  the first party owns the account/server capability. Whether a hackathon team
  can build and demo them from public data belongs to S10 feasibility, not this
  product-validity screen;
- the risk-list Idea moved from `repairable` to `pass`, but both statuses retain
  it unchanged, so that judgment difference does not affect candidate count.

This calibration is deliberately conservative: S9 eliminates only a clearly
broken product/value loop. It does not force every reviewer to match a golden
label when multiple defensible product judgments exist.

The full policy-3 resume was sampled through 27 completed screens, then paused
again. Outcomes were 13 `pass` and 14 `invalid`, so the gate was no longer a
rubber stamp. The remaining bottleneck was context size, not candidate count:
those 27 screens consumed about 5.19 million input tokens (4.15 million cached)
and 119 thousand output tokens. The mean input was about 192 thousand tokens
per Idea because every early screen repeatedly received the full Gateway,
Research, and Verification packet. At the observed mean duration, 708 screens
would require roughly 136 million input tokens and 4.2 hours at four-way
concurrency before any survivor entered S7.

The next runtime revision therefore keeps all 708 candidates but replaces the
early screen's repeated evidence corpus with a deterministic, hash-bound product
view containing only the passed Problem's native user state/consequences and the
S6 Idea's declared user, trigger, primary flow, mechanism, minimum features, and
failure assumptions. Later full S9 still receives competition/evidence context.
Because 27 immutable policy-3 artifacts already exist, this compact context must
use a new policy/task/path identity rather than silently changing policy 3.

## Product-quality observations so far

### Audience expansion

S1 produced nine broad audiences. Useful branches included players, global
publishing practitioners, localization practitioners, and game organizations.
Meta or weak branches included participants, judges, vague "related business
people," and community members inferred from the fact that community data is
publicly searchable.

For a future fresh run, S1 should distinguish target users from challenge
actors, evaluators, participants, and evidence sources. Mention in the prompt is
not sufficient direct relevance.

### Evidence verification

S2 produced 27 research documents. S3 produced 27 first reviews and 23 blind
second reviews: 85% of first reviews requested another verifier. The second
reviews materially narrowed overclaims, but `partially_supported` currently
triggers the expensive path too often.

At the end of S3, recorded usage was approximately:

- 11.3 million input tokens;
- 6.3 million cached input tokens;
- 303 thousand output tokens.

The dominant cause is repeated web reopening and source-by-source verification,
not the four-task concurrency limit itself.

### Problem synthesis

The first two player-focused S4 writers each retained six Problems. The
documents were concrete and evidence-linked, but this confirms that dynamic
quality-gated fan-out can grow quickly. Similar good outputs must not be removed
merely to meet a quota; downstream absolute gates and runtime accounting still
need to make the growth visible.

S4 eventually produced 86 Problems across nine Audiences, with a dynamic
0-to-6 output range per writer. S5 classified the first revision of those
Problems as:

- 58 direct passes;
- 17 rejection candidates;
- 11 candidates needing one targeted evidence retry.

All 17 rejections were independently confirmed, producing no overturned
decision. The duplicate Gateway added auditability in this sample but no
observed correction benefit. Of the 11 evidence retries, ten revised Problems
passed a fresh Gateway; one still needed evidence after the only retry and was
eliminated. S5 therefore ended with 68 passed Problems and 18 eliminations.

The first inspected double rejection was correctly nuanced: the evidence
proved that hackathon participants struggle with team formation, GitHub,
deployment, and judging, but both Gateways failed only T1 because that real
Problem is outside game global publishing. They did not pretend the Problem was
false.

One inspected evidence retry also worked as intended. A player-content-backlog
Problem moved from a mostly single-discussion claim to multiple independently
verified first-hand sources, a narrower joint condition (continuous updates,
limited events, and backlog), and explicit counterevidence before passing.

### Idea fan-out

S6 expanded the 68 passed Problems into 340 independent Generator tasks (five
per Problem). The completed fan-out produced 708 Ideas. The dynamic output
distribution was 41 Generators with one Idea, 230 with two, and 69 with three.
No Generator abstained, which shows that allowing an empty result is not yet
equivalent to model self-restraint.

The first complete player Problem cluster contained 13 Ideas but only four
material routes. Eleven had a direct end-to-end value flow. Two structured
report/ticket generators failed an absolute product test: the player still had
to wait for an uncontrolled official or community response before receiving
the promised explanation or ability to continue playing. Similarity was not
the reason for failure.

The first complete publishing-practitioner cluster contained nine Ideas and
three material routes: a language-commitment/conflict ledger, a language-upgrade
decision and handoff package, and a public-feedback evidence miner. All nine
had a direct decision-user flow, but five largely repeated the ledger route.
Several also inherited a shared unverified premise: they required private
Steam-region, wishlist, or UTM data despite the benchmark's public-data-only
constraint. Parallel agreement therefore cannot be treated as evidence that a
shared assumption is valid.

A deterministic 20-Idea sample across the four Audience groups represented at
that point found:

- 18/20 with concretely felt value;
- 17/20 with a complete causal product flow, one partial flow, and two broken
  flows that required official account-database or cross-server write access;
- 19/20 faithful to the passed Problem;
- only 7/20 strictly compatible with public data, one locally repairable, and
  12/20 dependent on private localization assets, platform analytics, TMS,
  contracts, or internal backends.

The dominant weakness is therefore not random ideation. It is failure to
separate “a real product for this user” from “a product this hackathon team can
demonstrate under the public-data constraint.” The early S9 screen should catch
uncontrolled permissions that break causal delivery. Whether S8/S10 correctly
replace or reject private-data dependencies remains an explicit benchmark
question; this observation does not justify deduplication or a fixed candidate
cap.

Final recorded S6 usage was approximately 80.27 million input tokens, including
63.36 million cached input tokens, plus 2.09 million output tokens. Forty-two
tasks recorded two attempts and 298 recorded one. One inspected branch showed
that an interrupted deterministic format correction could reset its retry
budget on resume; this identified a required durable retry-counter fix. The
correction count, prior validation error, session id, and attempt usage are now
persisted before another correction is allowed, for both JSON and Markdown
tasks. Recorded S5 usage was approximately 22.8 million input tokens. The
benchmark confirms that
candidate parallelism is valuable, while evidence routing and earlier absolute
product gates are necessary to keep multiplicative work from carrying obviously
broken Ideas into competitor research.

## Remaining benchmark checks

- Resume the full policy-3 fan-out after the seven-Idea calibration.
- Confirm S10 rejects or materially scope-reduces first-party-only Ideas that a
  hackathon team cannot build and demonstrate with public data.
- Finish `mihoyo-global-release-e2e-02` through S11.
- Check whether S8 removes private-data assumptions under the public-data-only
  rule.
- Check whether S9 rejects the player report/ticket Ideas for failing to close
  the user's value loop.
- Inspect Red Team decisions, feasibility decisions, later eliminations, and
  final report quality.
- Run deterministic validation on the completed run.
- Run `PAWN` separately.
