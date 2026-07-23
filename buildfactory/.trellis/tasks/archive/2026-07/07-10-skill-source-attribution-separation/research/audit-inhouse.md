# Research: In-house skills provenance audit (14 non-vendored skills)

- **Query**: Per-item inventory of all non-execution provenance content in `agents/assets/skills/` in-house skills: find-opportunity, decide-direction, create-role, when-idle, check-email, claim-mailbox, company-state, deploy-site, provision-ga4, receive-goal, review-objective, review-role, send-goal, set-objective
- **Scope**: internal
- **Date**: 2026-07-10
- **Method**: Every `.md` in all 14 skills read in full (19 files, ~1,600 lines); cross-checked with keyword grep (`<!--`, distilled, adapted, inspired, provenance, gstack, CAMEL, research/, Source, upstream, Apache, MIT, attribution); execution-closure traced from each SKILL.md; referenced research paths resolved against `.trellis/tasks/` + archive; when-idle checked against git history.

## Summary table

| Skill | Provenance items | Categories | Closure of affected files | Needs new ATTRIBUTION.md? |
|---|---|---|---|---|
| find-opportunity | 5 HTML comments (FO-1, IP-1, KDP-1, ETSY-1, GUM-1) + 1 borderline visible sentence (IP-2) | C1 (+C2 license/history sub-parts) | ALL IN-CLOSURE | **YES** |
| decide-direction | 2 HTML comments (DD-1, DC-1) | C1 (+C2) | ALL IN-CLOSURE (DC-1 also enters the reviewer subagent's prompt) | **YES** |
| create-role | 1 HTML comment (CR-1) + 1 visible MIXED sentence (CR-2, R4 rewrite) | C1 (+C2); CR-2 mixed C3+C1 | IN-CLOSURE | **YES** |
| when-idle | 0 today — the HTML comment the PRD names was already removed in the 07-10 rewrite (see §When-idle note) | — | IN-CLOSURE | No (optional MAINTENANCE.md, see note) |
| check-email | 0 | — | IN-CLOSURE | No |
| claim-mailbox | 0 | — | IN-CLOSURE | No |
| company-state | 0 | — | IN-CLOSURE | No |
| deploy-site | 0 (2 internal-evidence sentences reviewed, classified C3 stay) | — | IN-CLOSURE | No |
| provision-ga4 | 0 | — | IN-CLOSURE | No |
| receive-goal | 0 | — | IN-CLOSURE | No |
| review-objective | 0 | — | IN-CLOSURE | No |
| review-role | 0 | — | IN-CLOSURE | No |
| send-goal | 0 | — | IN-CLOSURE | No |
| set-objective | 0 | — | IN-CLOSURE | No |

**Totals**: 8 HTML provenance comments (all C1 with embedded C2 sub-parts), 1 visible mixed behavior+provenance sentence requiring R4 rewrite (create-role L95), 1 borderline visible sentence (IP-2), 0 existing ATTRIBUTION.md files, 3 skills needing a new ATTRIBUTION.md. All provenance items sit in files that ARE read during normal execution — there is no BYPASS file anywhere in these 14 skills today.

## Execution-closure map

- `find-opportunity/SKILL.md` (entry) → L46-50 conditionally directs the agent to `references/finding-info-product-opportunities.md` (info-product form) → its Platforms table (L97-101) directs to exactly one of `references/platform-gumroad.md` / `platform-amazon-kdp.md` / `platform-etsy.md`. **All 4 references IN-CLOSURE** (conditional but on the normal execution path).
- `decide-direction/SKILL.md` (entry) → `references/direction-critic.md` is read either by the spawned reviewer subagent (L50-54, the prompt tells it to read the brief) or by the agent itself in degraded mode (L66-67). **IN-CLOSURE, and additionally lands in a second agent's context** — the "fresh eyes" reviewer sees the provenance comment too.
- `create-role/SKILL.md` — no `references/`; points at runtime paths (`/opt/foundagent-orch/charters/`, live yamls) which are out of scope. **IN-CLOSURE** (single file).
- The other 11 skills are single-file SKILL.md with no reference reads. All IN-CLOSURE by definition (entry files).
- Materialization is `shutil.copytree` (per PRD confirmed facts) — HTML comments are NOT stripped; an agent Reading the file sees them.

## Per-item detail

### FO-1 — find-opportunity/SKILL.md L67-70 (end-of-file HTML comment)

> `<!-- General discipline distilled from PG "How to Get Startup Ideas" and gstack office-hours / ETHOS (Garry Tan / YC, MIT): get real signal, don't fabricate; narrow and deliverable over grand. Form-specific opportunity-finding methods are deferred to dedicated research tasks (see 07-01-ceo-monetization). This skill feeds decide-direction. -->`

- **Category**: C1 (methodology provenance: PG essay, gstack/Garry Tan/YC) with C2 sub-parts (the `MIT` license token for gstack; the deferral/roadmap note).
- **Closure**: IN-CLOSURE (entry file).
- **Behavior-change check (R4)**: removing the whole comment changes NO behavior — every behavioral fragment is duplicated in the visible body:
  - "get real signal, don't fabricate" → L11-16 ("Don't invent one out of thin air") and L34-38 ("Get real signal before you imagine anything").
  - "narrow and deliverable over grand" → L64-65 ("Aim small and real ... not a grand vision").
  - "Form-specific methods deferred" → L49-50 ("The other forms don't have a written method yet").
  - "This skill feeds decide-direction" → L58 ("Hand each candidate you like to `decide-direction`").
- **Proposed destination**: new `find-opportunity/ATTRIBUTION.md` (sources + gstack MIT license note); the deferral/roadmap sentence is maintenance history → same file or MAINTENANCE.md per design.
- **Notes**: the pointer `07-01-ceo-monetization` is **dangling** — that task was deleted 07-03 and is not in archive. Nearest real artifacts: `.trellis/tasks/archive/2026-07/07-01-ceo-find-idea/research/idea-generation-methods.md` (origin research for this skill) and `.trellis/tasks/archive/2026-07/07-01-opp-methods-service/` (the "dedicated research task" that actually happened). ATTRIBUTION.md must record the corrected pointers so nothing is silently lost.

### IP-1 — find-opportunity/references/finding-info-product-opportunities.md L114-122 (end-of-file HTML comment)

> `<!-- Method distilled and re-calibrated for a headless autonomous agent from public methods, cited as idea sources (see this task's research/ for per-clause provenance): Amy Hoy & Alex Hillman (Sales Safari / 30×500) — study a market, listen for the nouns, what do they already pay for; Nathan Barry (Authority), Ramit Sethi (Zero to Launch), Justin Welsh — sell before you build ...; Pieter Levels — charging money validates; Daniel Vassallo — treat ideas like cattle, not pets; Indie Hackers — the truest validation is the exchange of money. Human moves that don't transfer (personal immersion, an owned audience, surveys) are replaced by dispatched research Goals + reading money-already-moved. This file feeds decide-direction. -->`

- **Category**: C1 (seven external methodology sources + per-clause research pointer) with a C2 sub-part (the adaptation-history sentence "Human moves that don't transfer ... are replaced by ...").
- **Closure**: IN-CLOSURE (read whenever the info-product form is picked).
- **Behavior-change check (R4)**: safe to remove whole comment.
  - "This file feeds decide-direction" → duplicated at step 7, L87-89.
  - The adaptation sentence describes design history, not a rule the agent executes; the operational consequences (dispatch research Goals, judge by money-moved) are the visible body of steps 1-5.
- **Proposed destination**: `find-opportunity/ATTRIBUTION.md` (all seven sources); adaptation-history sentence → ATTRIBUTION/MAINTENANCE.
- **Notes**: "this task's research/" resolves to `.trellis/tasks/archive/2026-07/07-01-opp-methods-service/research/` (contains `r1-demand-observation.md`, `r2-selection-validation.md`, `r3-willingness-to-pay.md`, plus the three platform files). Record the resolved path in ATTRIBUTION.md — the relative phrase is unresolvable at runtime.

### IP-2 — find-opportunity/references/finding-info-product-opportunities.md L38-40 (visible sentence, BORDERLINE)

> "(This is your stand-in for a human spending days immersed in a community.)"

- **Category**: borderline C3/C1. Functionally it explains why the raw verbatim corpus matters (it substitutes human immersion — hence "insist on raw quotes, not a summary"); provenance-wise it is a visible trace of the Sales-Safari adaptation.
- **Closure**: IN-CLOSURE.
- **Behavior-change check (R4)**: the enforceable rules of step 2 (collect verbatim quotes with source URLs; reject summaries) stand alone without this sentence, so removal would not change executable rules — but the sentence does carry motivational calibration for how strictly to police the corpus.
- **Proposed destination**: design decision — either keep as-is (functional framing) or rewrite to a pure behavior justification without the human-method framing, moving the adaptation trace to ATTRIBUTION.md. Flagged, not prescribed.

### KDP-1 — find-opportunity/references/platform-amazon-kdp.md L93-99 (end-of-file HTML comment)

> `<!-- KDP-specific method, cited as idea sources (per-clause provenance in this task's research/amazon-kdp.md): Kindlepreneur/Dave Chesson (keyword three-way intersection, autocomplete + a-z, BSR-to-sales, category rankability, 7 slots / 10 categories), Low Content Profits & Publishing.com (low-content niches, beatable-gap read), KDP Help (70% royalty band). Numbers are order-of-magnitude; prefer category BSR over overall. Specializes steps 4–5 of finding-info-product-opportunities.md; generation only — hand candidates to decide-direction. -->`

- **Category**: C1 (sources + research pointer) with MIXED behavior fragments inside the comment (see below).
- **Closure**: IN-CLOSURE (read when KDP is picked).
- **Behavior-change check (R4)**: the two behavior fragments inside the comment are each duplicated in visible text, so the comment can be removed whole with no rewrite:
  - "Numbers are order-of-magnitude" → L41 ("BSR as a sales proxy (order-of-magnitude)") + parent file "A note on the numbers" L108-112.
  - "prefer category BSR over overall" → L45 ("Always weigh **category BSR, not just overall**").
  - "Specializes steps 4-5" → L3-4. "generation only — hand candidates to decide-direction" → parent step 7 L87-89.
- **Proposed destination**: `find-opportunity/ATTRIBUTION.md`.
- **Notes**: research pointer resolves to `.trellis/tasks/archive/2026-07/07-01-opp-methods-service/research/amazon-kdp.md`.

### KDP-2 — find-opportunity/references/platform-amazon-kdp.md L90 (visible sentence, C3 STAY)

> "**Publisher Rocket / Chrome BSR plugins** — paid GUIs you can't drive; keep their *thinking* (demand/competition/rankability), get the data via the research Goals above."

- **Category**: C3 — functional trap rule (tells the agent not to attempt paid GUI tools and how to substitute). Names external tools as runtime obstacles, not as citations. Must STAY.
- **Notes**: register in the R6 allowlist of functional source mentions so the regression scan doesn't flag it.

### ETSY-1 — find-opportunity/references/platform-etsy.md L83-89 (end-of-file HTML comment)

> `<!-- Etsy-specific method, cited as idea sources (per-clause provenance in this task's research/etsy.md): Etsy Seller Handbook (query matching + listing quality score), eRank & EverBee (search/competition/difficulty, <50-reviews new best-seller), Printful (low-competition steps, too-low / saturated thresholds), growingyourcraft/mydesigns (2026 AI-flood, hyper-specificity), BetterListing (long-tail + 13 tags + recency). Numbers are order-of-magnitude. Specializes steps 4–5 ...; generation only — hand candidates to decide-direction. -->`

- **Category**: C1 (five source groups + research pointer) with duplicated behavior fragments.
- **Closure**: IN-CLOSURE (read when Etsy is picked).
- **Behavior-change check (R4)**: safe to remove whole. "Numbers are order-of-magnitude" → parent L108-112 + L81 ("directional (~80% accurate), not exact"); "Specializes steps 4-5" → L3; "generation only" → parent step 7.
- **Proposed destination**: `find-opportunity/ATTRIBUTION.md`.
- **Notes**: research pointer resolves to `.trellis/tasks/archive/2026-07/07-01-opp-methods-service/research/etsy.md`. The BODY mentions of eRank/EverBee (L24, L31, L81) are C3 functional — they are the data sources the researcher is told to query — and must stay; only the citation comment migrates. Register in R6 allowlist.

### GUM-1 — find-opportunity/references/platform-gumroad.md L75-80 (end-of-file HTML comment)

> `<!-- Gumroad-specific method, cited as idea sources (per-clause provenance in this task's research/gumroad.md): Indie Hackers (zero organic discovery / catch-22), gumtrends.com & profitable.app (sales estimates, % mixed reviews, listing-count inflation), Leandro Calado "I Analyzed 36 Hot Products on Gumroad" (opportunity score / established-businesses warning). Numbers are order-of-magnitude. Specializes steps 4–5 ...; generation only — hand candidates to decide-direction. -->`

- **Category**: C1 (three source groups + research pointer) with duplicated behavior fragments.
- **Closure**: IN-CLOSURE (read when Gumroad is picked).
- **Behavior-change check (R4)**: safe to remove whole. "Numbers are order-of-magnitude" → L73 ("treat any specific % or price ceiling as 'about'") + parent L108-112; "Specializes"/"generation only" duplicated as above.
- **Proposed destination**: `find-opportunity/ATTRIBUTION.md`.
- **Notes**: research pointer resolves to `.trellis/tasks/archive/2026-07/07-01-opp-methods-service/research/gumroad.md`. BODY mentions of gumtrends.com / profitable.app (L21-22, L37, L44, L48) are C3 functional data sources — stay; register in R6 allowlist.

### DD-1 — decide-direction/SKILL.md L94-97 (end-of-file HTML comment) — PRD mandatory regression exemplar

> `<!-- Judgment framework distilled from gstack (Garry Tan / YC, MIT): office-hours + plan-ceo-review + "How great CEOs think". Re-calibrated from YC-startup rigor to small-company shippability. See references/direction-critic.md and the task's research/ceo-skill-reuse.md for provenance. -->`

- **Category**: C1 (gstack / Garry Tan / YC provenance + research pointer) with C2 sub-parts (MIT license token; re-calibration adaptation history).
- **Closure**: IN-CLOSURE (entry file, read by the CEO on every direction decision).
- **Behavior-change check (R4)**: safe to remove whole. "small-company shippability" is the visible opening thesis (L8-9 "You run a small company, not a billion-dollar startup"). The pointer to direction-critic.md as a provenance source is pure citation (the functional pointer to the brief already exists at L50-54).
- **Proposed destination**: new `decide-direction/ATTRIBUTION.md` (shared with DC-1 — one truth source for the skill).
- **Notes**: "the task's research/ceo-skill-reuse.md" resolves to `.trellis/tasks/archive/2026-07/06-28-role-ceo/research/ceo-skill-reuse.md` — record the absolute archive path; the relative phrase is unresolvable.

### DC-1 — decide-direction/references/direction-critic.md L49-53 (end-of-file HTML comment) — PRD mandatory regression exemplar

> `<!-- Distilled and re-calibrated from gstack (Garry Tan / YC, MIT): office-hours six forcing questions + plan-ceo-review scope modes + anti-sycophancy posture. Re-calibrated from YC-startup rigor down to small-company shippability; inverted from "partner interviews a human founder" to "an autonomous reviewer of a self-proposed direction." See the task's research/ceo-skill-reuse.md for per-clause provenance. -->`

- **Category**: C1 (gstack provenance + per-clause research pointer) with C2 sub-parts (MIT; two adaptation-history sentences).
- **Closure**: IN-CLOSURE — and higher exposure than any other item: this brief is the full prompt-payload of the spawned independent reviewer subagent (decide-direction L50-54), so the provenance comment currently enters a SECOND agent's execution context on every direction review.
- **Behavior-change check (R4)**: safe to remove whole. "small-company shippability" bar is the visible body (L7-9 "You are **not** a billion-dollar VC ..."); the "inverted from partner-interview" history has no executable counterpart and none is needed — the brief's second person framing already embodies it.
- **Proposed destination**: `decide-direction/ATTRIBUTION.md` (merged with DD-1); adaptation history → ATTRIBUTION/MAINTENANCE per design.
- **Notes**: same ceo-skill-reuse.md resolution as DD-1.

### CR-1 — create-role/SKILL.md L153-159 (end-of-file HTML comment) — PRD mandatory regression exemplar

> `<!-- Methodology sources: job-spec-before-persona adapted from CAMEL's task-specifier (camel-ai/camel, Apache-2.0); reuse-before-generate ("a tools shortfall is a loadout change, not a hire") adapted from AG2 CaptainAgent's retrieval-before-generation / "less is better" stance (ag2ai/ag2, Apache-2.0); charter anatomy + three-test self-audit reverse-engineered in-house from the live foundagent charters — see .trellis/tasks/07-06-create-role/research/quality-bar.md §3–§5. -->`

- **Category**: C1 (CAMEL + AG2 methodology provenance, in-house reverse-engineering note, research pointer) with C2 sub-parts (two Apache-2.0 license identifiers — methodology/idea sources, not vendored code, but the license record should be preserved in ATTRIBUTION).
- **Closure**: IN-CLOSURE (entry file).
- **Behavior-change check (R4)**: safe to remove whole. The quoted behavior fragment "a tools shortfall is a loadout change, not a hire" is duplicated verbatim-in-substance in the visible body L29-32 ("A shortfall of **tools** is not — that is a loadout change to an existing role").
- **Proposed destination**: new `create-role/ATTRIBUTION.md`.
- **Notes**: the research path `.trellis/tasks/07-06-create-role/research/quality-bar.md` is **stale** — the task is archived; the live path is `.trellis/tasks/archive/2026-07/07-06-create-role/research/quality-bar.md` (verified to exist). Record the corrected path.

### CR-2 — create-role/SKILL.md L95 (visible MIXED sentence — the one R4 rewrite in scope)

> "the default is to write nothing — no `mcp.json` in the bundle means the provisioner copies the full server set (the 07-06 capability-first stance: give everything, prune later)."

- **Category**: MIXED C3 + C1. The behavior rule (omit mcp.json → full server set; stance: give everything, prune later) is functional and must stay. The parenthetical's "07-06" is an internal decision-history pointer — provenance, per PRD scope ("历史提交或改造缘由").
- **Closure**: IN-CLOSURE.
- **Behavior-change check (R4)**: this is the one sentence in my scope that CANNOT be deleted whole — it must be REWRITTEN as a pure behavior rule (e.g. keep "the capability-first stance: give everything, prune later" without the date-pointer), with the 07-06 decision reference migrated to ATTRIBUTION/MAINTENANCE.
- **Proposed destination**: rewrite in place; migrate the "07-06" decision pointer to `create-role/ATTRIBUTION.md` (or MAINTENANCE.md).
- **Notes**: nearby L91 "(this omission is why verifier.yaml has none)" was reviewed: internal live-system example used as functional calibration → C3 stay, not provenance.

## When-idle note (PRD-named exemplar that no longer exists)

The task brief and PRD name a `when-idle/SKILL.md` HTML comment as a hotspot. **It is not in the current file.** Git history:

- Added in `fccdf37` (07-08-proactive-idle): a comment recording the trigger mechanism (`agents/ceo.yaml idle: proactive`, `agent_loop._render_events`) and the firsttest pattern-①/pattern-⑦ rationale for worker hard-stop and gated direction changes.
- Removed in `35b4bdf` (07-10 when-idle rewrite, `feat(ceo): rewrite when-idle — an empty-ledger idle pass must dispatch`). The removal predates this task; the content survives in git history and in `.trellis/tasks/archive/2026-07/07-08-proactive-idle/`.

Today when-idle contains zero provenance. Its internal incident references ("each of these has actually happened", "A CEO once slept 7 hours") are C3 functional calibration counterexamples (they suppress a known LLM default) — stay. Design decision for the main agent: if R2's no-silent-loss rule is applied retroactively, a `when-idle/MAINTENANCE.md` could restore the removed comment's mechanism/rationale content from git; otherwise nothing to do.

## ATTRIBUTION.md requirements (R2 / AC3) — none of the 14 skills has one today

### 1. find-opportunity/ATTRIBUTION.md (new) must contain

- Paul Graham, "How to Get Startup Ideas" (general discipline).
- gstack office-hours / ETHOS / plan-ceo-review (Garry Tan / YC), MIT license — shared lineage with decide-direction.
- Info-product method sources: Amy Hoy & Alex Hillman (Sales Safari / 30×500); Nathan Barry (Authority); Ramit Sethi (Zero to Launch); Justin Welsh; Pieter Levels; Daniel Vassallo; Indie Hackers.
- KDP sources: Kindlepreneur / Dave Chesson; Low Content Profits; Publishing.com; KDP Help (70% royalty band).
- Etsy sources: Etsy Seller Handbook; eRank; EverBee; Printful; growingyourcraft; mydesigns; BetterListing.
- Gumroad sources: Indie Hackers; gumtrends.com; profitable.app; Leandro Calado, "I Analyzed 36 Hot Products on Gumroad".
- Resolved research paths: `.trellis/tasks/archive/2026-07/07-01-ceo-find-idea/research/idea-generation-methods.md`; `.trellis/tasks/archive/2026-07/07-01-opp-methods-service/research/{r1-demand-observation,r2-selection-validation,r3-willingness-to-pay,amazon-kdp,etsy,gumroad}.md`.
- Note that the `07-01-ceo-monetization` task referenced in the old comment was deleted 07-03 (pointer corrected to the artifacts above).
- Adaptation history: method re-calibrated for a headless autonomous agent; human moves (immersion, owned audience, surveys) replaced by dispatched research Goals + money-already-moved reads.

### 2. decide-direction/ATTRIBUTION.md (new) must contain

- gstack (Garry Tan / YC), MIT license: office-hours six forcing questions; plan-ceo-review scope modes; "How great CEOs think"; anti-sycophancy posture.
- Per-clause provenance path: `.trellis/tasks/archive/2026-07/06-28-role-ceo/research/ceo-skill-reuse.md` (covers both SKILL.md and references/direction-critic.md).
- Adaptation history: re-calibrated from YC-startup rigor to small-company shippability; inverted from "partner interviews a human founder" to "autonomous reviewer of a self-proposed direction".

### 3. create-role/ATTRIBUTION.md (new) must contain

- CAMEL task-specifier (camel-ai/camel, Apache-2.0) — job-spec-before-persona.
- AG2 CaptainAgent (ag2ai/ag2, Apache-2.0) — reuse-before-generate / "less is better".
- In-house: charter anatomy + three-test self-audit reverse-engineered from live foundagent charters; corrected research path `.trellis/tasks/archive/2026-07/07-06-create-role/research/quality-bar.md` §3-§5.
- The 07-06 capability-first loadout decision (from the CR-2 rewrite).

## Reviewed and explicitly EXCLUDED (not provenance — C3 functional or plain system facts)

| File / lines | Text | Why excluded |
|---|---|---|
| check-email L13 | "fetching happens upstream in a deterministic poller" | Architecture fact ("upstream" = mail pipeline, not an upstream repo); tells the agent no IMAP exists. |
| deploy-site L25-26 | "This exact path is proven in production (`glp1.foundagent.net`)" | Internal operational evidence backing a live procedure; C3 stay. |
| deploy-site L35-36 | "This has already happened once in this fleet; do not repeat it" | Internal incident calibration (suppresses a default); C3 stay. |
| when-idle L92-97 | "Traps (each of these has actually happened)" / "A CEO once slept 7 hours" | Internal incident counterexamples; C3 stay. |
| create-role L91 | "(this omission is why verifier.yaml has none)" | Live-system example; functional. |
| platform bodies | eRank / EverBee / gumtrends.com / profitable.app / Amazon autocomplete usages in visible steps | Runtime data sources the researcher is instructed to query — functional source rules (register in R6 allowlist). |
| set-objective L28 | "Inherit the `decide-direction` pragmatism" | Cross-skill functional pointer, not provenance. |
| review-objective / review-role | placeholder-charter references | Live-system calibration baselines; functional. |
| finding-info-product L110-112 | "A note on the numbers" section | Functional rule about reading thresholds; stays (the comment fragments that duplicate it migrate). |

claim-mailbox, company-state, provision-ga4, receive-goal, send-goal: nothing even borderline — fully clean.

## Stale / dangling pointer resolution (must be carried into ATTRIBUTION files)

| Pointer as written | Status | Resolves to |
|---|---|---|
| "see 07-01-ceo-monetization" (FO-1) | DANGLING — task deleted 07-03, not in archive | nearest artifacts: `archive/2026-07/07-01-ceo-find-idea/` + `archive/2026-07/07-01-opp-methods-service/` |
| "this task's research/" (IP-1) | relative, unresolvable at runtime | `.trellis/tasks/archive/2026-07/07-01-opp-methods-service/research/` |
| "this task's research/amazon-kdp.md" (KDP-1) | relative | `.trellis/tasks/archive/2026-07/07-01-opp-methods-service/research/amazon-kdp.md` |
| "this task's research/etsy.md" (ETSY-1) | relative | `...07-01-opp-methods-service/research/etsy.md` |
| "this task's research/gumroad.md" (GUM-1) | relative | `...07-01-opp-methods-service/research/gumroad.md` |
| "the task's research/ceo-skill-reuse.md" (DD-1, DC-1) | relative | `.trellis/tasks/archive/2026-07/06-28-role-ceo/research/ceo-skill-reuse.md` |
| `.trellis/tasks/07-06-create-role/research/quality-bar.md` (CR-1) | STALE — task archived | `.trellis/tasks/archive/2026-07/07-06-create-role/research/quality-bar.md` |

## Caveats / Not Found

- No `Source concept` phrasing (as such) appears anywhere in these 14 skills — that pattern belongs to the vendored-skill scope (de-ai-ify / design-asset / gen-image etc.), outside this audit.
- No visible "this method comes from ..." paragraphs exist in these 14 skills; all pure provenance is HTML-comment-only, plus the two visible borderline/mixed items IP-2 and CR-2.
- Vendored/byte-exact concerns (R5) do not apply to any of these 14 skills — no LICENSE files, no vendored copies here.
- Line numbers are as of commit `5521e74` (2026-07-10 working tree).
