# Research: gen-image provenance/attribution audit

- **Query**: Complete per-item inventory of non-execution provenance/attribution content in `agents/assets/skills/gen-image/` (entire tree), with closure analysis and byte-exact verification of vendored subtrees.
- **Scope**: internal (full-tree read) + external (upstream byte-exact verification via raw.githubusercontent.com)
- **Date**: 2026-07-10
- **Method**: every `.md` file read in full (no grep-only judgment); closure traced from entry `SKILL.md` through all conditional routes; all 29 vendored files curl-fetched from upstream `main` and byte-compared with `cmp`; git history checked for post-vendor edits.

---

## 1. Byte-exact verification results (decides everything downstream)

**All 29 vendored files are VERIFIED-EXACT** against upstream `main` as of 2026-07-10:

| Upstream | Pinned at | Files verified | Result |
|---|---|---|---|
| `smixs/visual-skills` → `image/` | `5090502` (2026-07-01) | SKILL.md + 15 reference modules + 7 patterns + LICENSE = 24 | all byte-exact (`cmp`) |
| `JunSeo99/claude-skill-codex-imagegen` | `c3cdb9e` (2026-05-16) | SKILL.md, cli-reference.md, prompting-guide.md, SECURITY.md, LICENSE = 5 | all byte-exact (`cmp`) |

Both upstream HEADs predate the 2026-07-03 fetch recorded in ATTRIBUTION.md, so fetch-time state == current upstream state == local state. Git history confirms zero post-vendor edits: the entire skill landed in one commit (`c9477c7`) and was never touched again.

**Consequence**: every provenance item found inside `references/` is **upstream's own content, not host-added**. None of it can be edited in place without breaking ATTRIBUTION.md's byte-exact/verbatim claim (PRD R5 / AC4). All 35 `Source concept` HTML comments in `patterns/*.md` are upstream-authored. The only freely editable provenance lives in the host layer: `SKILL.md`, `ATTRIBUTION.md`, `scripts/generate_image.py`.

---

## 2. Execution-closure map

Entry point: `gen-image/SKILL.md`.

| File | Closure | Route |
|---|---|---|
| `SKILL.md` | IN-CLOSURE | entry |
| `references/smixs-image/SKILL.md` | IN-CLOSURE (always) | host reference map: "always — entry point, mandatory reading order" |
| `smixs .../models.md`, `golden-rules.md` | IN-CLOSURE (always) | smixs mandatory reading order steps 1, 3 |
| `smixs .../gpt-image.md` / `nano-banana.md` | IN-CLOSURE (always, one of two) | step 2 — exactly one model file per prompt |
| `smixs .../text-rendering.md`, `editing.md`, `characters.md`, `slides.md`, `storyboards.md`, `structural.md`, `dimensional.md`, `vision-decomposer.md`, `multi-panel.md` | IN-CLOSURE (conditional) | step 4 task-shaped routing |
| `smixs .../patterns/*.md` (7 files) | IN-CLOSURE (conditional) | step 4 vertical routing; `ui-social.md` + `poster-illustration.md` explicitly flagged by host SKILL.md as mapping 1:1 to social-asset work — high-traffic |
| `smixs .../creative-direction.md`, `prompt-framework.md` | IN-CLOSURE (conditional) | steps 5-6 |
| `references/codex/SKILL.md`, `cli-reference.md`, `prompting-guide.md` | IN-CLOSURE (conditional) | host reference map: "debugging the codex side path"; NOTE host also says "its 5-slot guide + front-50-words rule also apply to the API path" — so `prompting-guide.md` can be pulled into ordinary API-path work, not only debugging |
| `references/codex/SECURITY.md` | IN-CLOSURE (conditional, 2nd degree) | codex/SKILL.md says "See SECURITY.md in the repo" (3 occurrences); the vendored copy resolves locally |
| `scripts/generate_image.py` | IN-CLOSURE (executed; `--help` read per host reference map) | invocation layer |
| `ATTRIBUTION.md` | **BYPASS** | referenced by nothing in the tree (grep-verified) |
| `references/smixs-image/LICENSE`, `references/codex/LICENSE` | **BYPASS** | never routed |

So the ONLY bypass files today are ATTRIBUTION.md and the two LICENSE files. Every upstream provenance item below sits in agent-readable execution closure.

---

## 3. Summary table

| # | File | Items | Category | Closure | Byte-exact status |
|---|---|---|---|---|---|
| H1-H3 | `SKILL.md` (host) | 3 provenance mentions | C1 | IN-CLOSURE | host-authored — free to edit |
| H4-H5 | `SKILL.md` (host) | 2 functional rules with adaptation-history wording | C3 (keep, reword) | IN-CLOSURE | host-authored |
| A1-A5 | `ATTRIBUTION.md` | 5 blocks | C2 | BYPASS | host-authored |
| L1-L2 | 2x `LICENSE` (MIT) | 2 files | C2 | BYPASS | VERIFIED-EXACT — never touch |
| S1 | `smixs .../patterns/*.md` (7 files) | **35 `<!-- Source concept: ... -->` comments** | C1-in-nature, byte-exact constrained | IN-CLOSURE (conditional) | VERIFIED-EXACT (upstream content) |
| S2 | `smixs .../SKILL.md:23` | 1 upstream self-history sentence | C3 (upstream rhetoric, no action) | IN-CLOSURE (always) | VERIFIED-EXACT |
| X1-X2 | `codex/prompting-guide.md:3,30` | 2 upstream source attributions (fal.ai / OpenAI Cookbook) | C1-in-nature, byte-exact constrained | IN-CLOSURE (conditional, incl. API path) | VERIFIED-EXACT |
| X3 | `codex/cli-reference.md:5` | version-baseline note | C3 (functional) | IN-CLOSURE (conditional) | VERIFIED-EXACT |
| X4 | `codex/cli-reference.md:149` | upstream "open an issue on this skill's repo" CTA | C2-in-nature, byte-exact constrained — **behavior risk** | IN-CLOSURE (conditional) | VERIFIED-EXACT |
| X5 | `codex/SKILL.md:187` | dangling `assets/hero.png` marketing pointer | C1-in-nature, byte-exact constrained | IN-CLOSURE (conditional) | VERIFIED-EXACT |
| X6 | `codex/SKILL.md:40,139,143` | "See SECURITY.md in the repo" routing | C3 (functional security routing) | IN-CLOSURE (conditional) | VERIFIED-EXACT |
| X7-X8 | `codex/SECURITY.md:1-4,59-63` | upstream contact + supply-chain notes | C2-in-nature, byte-exact constrained | IN-CLOSURE (2nd-degree conditional) | VERIFIED-EXACT |
| — | `scripts/generate_image.py` | 0 items — docstring purely functional; provenance already externalized to ATTRIBUTION.md | — | IN-CLOSURE | host-authored |
| — | 15 smixs reference modules (non-pattern) | 0 provenance items | — | IN-CLOSURE | VERIFIED-EXACT |

Totals: **C1 host-editable: 3** | **C1/C2-in-nature but byte-exact constrained (upstream): 40** (35 Source-concept + X1, X2, X4, X5, X7/X8 counted as 2) | **C2 bypass (already correct): 7** (A1-A5 + 2 LICENSE) | **C3 keep-in-execution: 5** (H4, H5, S2, X3, X6).

---

## 4. Per-item detail

### 4.1 Host layer — freely editable (this is where migration actually happens)

**H1 — `SKILL.md:8-9`** — C1, IN-CLOSURE
> "Two layers: a vendored PROMPT-craft skill (smixs) that turns intent into a model-ready prompt, and a thin INVOCATION wrapper..."

The two-layer mental model ("bad results are usually a prompt-layer problem, not a tool problem") is functional and must survive (R4). The words "vendored" and "(smixs)" are provenance. Destination: rewrite sentence without attribution; upstream identity already lives in ATTRIBUTION.md.

**H2 — `SKILL.md:26`** — C1, IN-CLOSURE
> "## Prompt layer (vendored smixs skill — follow its reading order)"

"vendored smixs skill" is provenance; "follow its reading order" is functional. Destination: reword heading (e.g. keep only the follow-its-reading-order instruction). Note: the directory name `references/smixs-image/` itself carries the upstream name and appears in mandatory routing (SKILL.md:28, 100-104). Whether to rename the directory is a design decision — renaming would break the "vendored verbatim tree" claim's path column in ATTRIBUTION.md but not the file bytes.

**H3 — `SKILL.md:34`** — C1 (framing), IN-CLOSURE
> "Host adaptations:"

The heading frames the following three bullets as adaptation-vs-upstream history. The bullets themselves (H4, H5, and the executor-reality rule at lines 36-40) are pure behavior rules. Destination: drop the historical framing; if the adaptation narrative is worth keeping, it belongs in MAINTENANCE.md (per PRD R2). ATTRIBUTION.md already records most of it.

**H4 — `SKILL.md:41-43`** — C3 KEEP (functional runtime input constraint)
> "Language note: smixs files mix English and Russian. The Russian passages are normative content, not noise — read them as-is..."

The executing agent genuinely needs this: ~10 vendored files are heavily Russian (`models.md`, `gpt-image.md`, `nano-banana.md`, `golden-rules.md`, `prompt-framework.md`, `slides.md`, `editing.md`, `text-rendering.md` headers, etc.). Without this rule an agent may treat Russian text as noise. This is exactly PRD's "upstream format is a runtime input constraint" carve-out. Keep; may reword to drop the "smixs" name ("some reference files mix English and Russian").

**H5 — `SKILL.md:44-45`** — C3 KEEP (reword)
> "smixs 'Output format' (Model/Quality/Size header + prompt block) stays — produce it, then feed the prompt text to the wrapper yourself."

"stays" implies a decision-vs-upstream narrative; the actual rule (produce the header block, then feed the prompt to the wrapper) is load-bearing product behavior. Rewrite as a plain instruction per R4 (mixed sentence → pure behavior rule + migrate the historical residue).

### 4.2 ATTRIBUTION.md — BYPASS, C2, must be preserved (already in the right place)

**A1 — `ATTRIBUTION.md:3-6`** — C2. The byte-exact/verbatim claim, fetch date (2026-07-03 @ main), and sync policy ("Sync = re-fetch, never hand-edit"). This is the constraint anchor for the whole vendored tree. Keep.

**A2 — `ATTRIBUTION.md:10`** — C2. smixs row: upstream repo/path, MIT, vendor scope (NOT vendored: `video/`, `image.skill`, `assets/hero.webp`), plus the language-note **design-phase history** ("The design-phase plan said 'translate Russian passages into a host appendix' — dropped after inspection..."). The design-history sub-part is maintenance narrative — candidate for MAINTENANCE.md if the task adopts the ATTRIBUTION/MAINTENANCE split, but it must not be lost.

**A3 — `ATTRIBUTION.md:11`** — C2. codex row: upstream repo, MIT, vendor scope, and the functional conflict rule "Upstream pins codex 0.130.0-era flags; our wrapper was e2e-verified against codex-cli 0.142.5 — treat cli-reference.md as debugging aid, wrapper behavior wins on conflict." Note: the conflict rule is duplicated (correctly) in the host SKILL.md reference map row for codex — the execution side already has what it needs.

**A4 — `ATTRIBUTION.md:12`** — C2, with a traceability gap. Script provenance: "informed by: research doc §4.5 pseudocode, JunSeo99's salvage/anti-fallback patterns, and a local codex-cli 0.142.5 e2e (2026-07-02/03)". **Gap**: "research doc §4.5" has no resolvable path (the originating task's research file is not identified). If R2's "traceable before and after migration" is taken seriously, this pointer should be made resolvable or explicitly marked unresolvable.

**A5 — `ATTRIBUTION.md:14-22`** — C2 → MAINTENANCE-flavored. Verification status block (codex e2e passed, fallback verified, API path untested due to missing OPENAI_API_KEY, "see task prd AC4" — another non-resolvable pointer). Candidate for MAINTENANCE.md under the PRD's split.

### 4.3 Vendored smixs tree — all VERIFIED-EXACT upstream content

**S1 — the 35 `Source concept` HTML comments** — C1-in-nature, byte-exact constrained, IN-CLOSURE (conditional)

Every pattern file carries one comment per pattern, always in the form `<!-- Source concept: <generic design concept the pattern encodes> -->`. All are **upstream's own content** (byte-exact verified) — NOT host-added. They describe methodology origin ("Audubon-style naturalist ... illustration", "character model sheet ... for 3D modelers and animators"), not executable rules. Full list:

| File | Lines | Verbatim excerpts (abbreviated) |
|---|---|---|
| `patterns/character-design.md` | 11, 31, 60, 88, 122 | "character model sheet / turnaround sheet for 3D modelers and animators"; "character expression/emotion reference sheet for animation or visual novel production"; "character costume/skin variant sheet..."; "chibi/super-deformed vinyl collectible figurine..."; "anime/game character reference sheet with stats, items, and palette swatches" |
| `patterns/ecommerce.md` | 11, 31, 53, 82, 102 | "miniature/tilt-shift product advertising with construction-worker scale play"; "luxury perfume/cosmetics dark-marble studio photography..."; "9-panel television commercial storyboard grid..."; "frozen-motion ingredient explosion..."; "inflatable surrealism — product packaging rendered as squeezed/puffy/distorted soft objects" |
| `patterns/fashion-editorial.md` | 11, 35, 60, 81, 95 | "fashion campaign triptych collage — hero + detail + movement panels"; "2x2 fashion portrait grid — same model, four setups"; "streetwear poster with model integrated into oversized typographic layout"; "retro roller skating / sportswear campaign with analog film aesthetic"; "futuristic sportswear editorial with organic 3D blob/sphere shapes" |
| `patterns/food-beverage.md` | 11, 43, 67, 104, 118 | "luxury chocolate brand campaign with variant moods and tactile surfaces"; "fashion-meets-beverage campaign board..."; "hyper-realistic food poster with controlled composition slots"; "Audubon-style naturalist botanical/food specimen illustration with cross-section"; "hand-drawn illustrated food map of a city..." |
| `patterns/portrait-cinema.md` | 11, 31, 51, 71, 85 | "golden hour backlit street portrait with lens flare..."; "convenience store / bodega neon portrait..."; "monochrome profile portrait with digital glitch artifacts..."; "Japanese negative film aesthetic — overexposed, muted tones, rooftop setting"; "surreal underwater portrait with translucent fish..." |
| `patterns/poster-illustration.md` | 12, 42, 67, 90, 111 | "time-split composition — same city view, two eras side by side"; "3-panel fitness/boxing campaign collage..."; "smartphone product launch hero in monochromatic lavender..."; "bold emerald fashion poster with oversized type..."; "peacock botanical vintage symmetrical art print..." |
| `patterns/ui-social.md` | 11, 31, 57, 83, 118 | "Instagram Story ad with glassmorphism elements..."; "square social media post with brand color palette..."; "App Store marketing screenshot with iPhone device frame..."; "analytics dashboard UI mockup with charts, cards, and navigation"; "personal color analysis / seasonal color palette board..." |

**Constraint**: PRD R5 forbids editing these in place while claiming byte-exact. Proposed destination — design decision required (PRD next-session entry point #3): either (a) keep canonical vendored originals as bypass artifacts and materialize a comment-stripped execution layer that the smixs routing actually loads, or (b) rename the claim (stop asserting byte-exact in ATTRIBUTION.md) and strip in place. Option (a) preserves the "Sync = re-fetch, never hand-edit" maintenance model; option (b) destroys it. Either way the comments themselves must remain retrievable (R2 — no silent deletion), which option (a) satisfies automatically and option (b) satisfies via the ATTRIBUTION/MAINTENANCE ledger.

**S2 — `smixs-image/SKILL.md:23`** — C3 (upstream rhetoric, no action), IN-CLOSURE (always)
> "Past attempts to write prompts directly from this skill body produced lazy, generic results."

Upstream's own self-history, functioning as motivation for the mandatory reading order. Not host provenance; behaviorally useful emphasis. Byte-exact constrained anyway. Recommend: no action.

**15 non-pattern smixs modules** (`models.md`, `golden-rules.md`, `gpt-image.md`, `nano-banana.md`, `text-rendering.md`, `editing.md`, `characters.md`, `creative-direction.md`, `dimensional.md`, `multi-panel.md`, `prompt-framework.md`, `slides.md`, `storyboards.md`, `structural.md`, `vision-decomposer.md`): read in full — **zero provenance/attribution items**. (`gpt-image.md:17` quotes "The fifth slot is where most mediocre prompts fail silently." without naming a source in-file; `vision-decomposer.md:13-21` names methodology authorities — Bruce Block, Itten, Arnheim, Mascelli, Zheleznyakov — but these are functional prompt-engineering vocabulary the agent applies, i.e. product behavior, not skill provenance. C3, no action.)

### 4.4 Vendored codex tree — all VERIFIED-EXACT upstream content

**X1 — `codex/prompting-guide.md:3`** — C1-in-nature, byte-exact constrained, IN-CLOSURE (conditional, including API-path route)
> "Content based on fal.ai, OpenAI Cookbook, and direct verification."

Upstream's own source attribution. Because host SKILL.md:104 says the codex 5-slot guide "also appl[ies] to the API path", this file is closer to normal execution than pure debugging. Handling follows the same design decision as S1.

**X2 — `codex/prompting-guide.md:30-32`** — C1-in-nature, byte-exact constrained, IN-CLOSURE (conditional)
> '> "The fifth slot is where most mediocre prompts fail silently." — fal.ai'

Visible quote attribution to fal.ai. Same handling as X1.

**X3 — `codex/cli-reference.md:5`** — C3 KEEP, IN-CLOSURE (conditional)
> "This skill was validated against `codex-cli 0.130.0` ... treat the version stamp here as the last known-good baseline, not a permanent guarantee."

Functional version baseline for debugging the side path. Host layer already overrides ("wrapper behavior wins on conflict"). Keep.

**X4 — `codex/cli-reference.md:149`** — C2-in-nature, byte-exact constrained, IN-CLOSURE (conditional) — **flagged risk**
> "Open an issue on this skill's repo with the new behavior so the docs can be updated."

Upstream maintenance CTA that, read literally by an executing agent during codex-version troubleshooting, instructs an external action against a third-party GitHub repo. Given the first-longrun finding that unsanctioned external PRs were the top incident class, this is the single most behavior-relevant provenance item in scope. A sanitized execution layer should exclude this line; the canonical vendored original keeps it.

**X5 — `codex/SKILL.md:187`** — C1-in-nature, byte-exact constrained, IN-CLOSURE (conditional)
> "[`assets/hero.png`](assets/hero.png) — sample 1600×900 image produced via this skill"

Dangling pointer: `assets/` was deliberately not vendored (ATTRIBUTION.md row 2). Upstream marketing reference, useless at runtime.

**X6 — `codex/SKILL.md:40, 139, 143`** — C3 (functional security routing), byte-exact constrained
> "See `SECURITY.md` in the repo for the threat model."

"in the repo" refers to the upstream repo, but the vendored sibling copy resolves the reference locally. The Mode A/Mode B trust-boundary content it routes to is genuinely functional. Keep.

**X7 — `codex/SECURITY.md:1-4`** — C2-in-nature, byte-exact constrained, IN-CLOSURE (2nd-degree conditional)
> "## Reporting a vulnerability — Open a GitHub issue or email jun@indexfinger.org."

Upstream maintainer contact. Same external-action flavor as X4 (weaker — it's about upstream's vulns). Sanitized-layer candidate for exclusion; must survive in the canonical copy.

**X8 — `codex/SECURITY.md:59-63`** — C2-in-nature, byte-exact constrained, IN-CLOSURE (2nd-degree conditional)
> "This repo ships a prebuilt `dist/codex-imagegen.skill` zip... install via Option A or Option C in the README..."

Upstream supply-chain/install notes referencing files (`dist/`, README) that were not vendored. Irrelevant to host runtime; upstream maintenance info.

### 4.5 `scripts/generate_image.py` — clean

Docstring (lines 1-28) and inline comments (e.g. the load-bearing anti-fallback comment at lines 135-136) are purely functional. Its provenance ("informed by research doc §4.5, JunSeo99's salvage patterns") was correctly externalized into ATTRIBUTION.md at authoring time. **Zero migration items — this file is the model for the desired end state.** (Stray artifact: `scripts/__pycache__/generate_image.cpython-313.pyc` is checked into the tree; not provenance, noted for hygiene only.)

### 4.6 LICENSE files — C2, BYPASS, untouchable

- `references/smixs-image/LICENSE` — MIT, Copyright (c) 2026 smixs. Byte-exact vs upstream **repo-root** LICENSE (upstream has no `image/LICENSE`; vendoring placed the root license inside the subtree — correct practice).
- `references/codex/LICENSE` — MIT, Copyright (c) 2026 JunSeo99. Byte-exact vs upstream root LICENSE.

MIT requires the copyright + permission notice be included in copies — both satisfied. Any sanitized-execution-layer design must keep these files materialized alongside whatever copy of the MIT-covered text ships to agents.

---

## 5. ATTRIBUTION.md cross-check (does it cover everything found?)

Covered correctly:
- Both external sources (smixs, JunSeo99) with repo paths, licenses, vendor scope, fetch date, sync policy. No unattributed external source was found anywhere in the tree.
- Script inspiration chain.
- The byte-exact claim itself — now independently VERIFIED-EXACT for all 29 files.

Gaps / notes:
1. **"research doc §4.5"** (A4) and **"task prd AC4"** (A5) are non-resolvable pointers — no path, no task id. Minor R2-traceability gap.
2. ATTRIBUTION.md does not mention that the vendored files carry **upstream-embedded provenance** (35 Source-concept comments, fal.ai/OpenAI-Cookbook lines). Not a legal gap (MIT covers the text as published), but this task's design should record the decision about them here or in MAINTENANCE.md.
3. Second-order sources (fal.ai, OpenAI Cookbook — the sources upstream's author used) are not listed. Informational only; no license obligation flows from them to us.
4. ATTRIBUTION.md is genuinely BYPASS today — nothing in execution text references it. Already compliant with R2's "normal execution must not require reading it".

---

## 6. Caveats / additional findings

- **codex/SKILL.md has broken internal links** in the vendored layout: it links `references/prompting-guide.md` and `references/cli-reference.md` (lines 44, 53, 185-186), but the vendored tree flattened upstream's `skill/references/` so those files are siblings of SKILL.md, not under a `references/` subdir. An agent following the literal link path will miss. Not provenance — but if a sanitized execution layer is built, it is the natural place to also fix these paths (the canonical byte-exact copy cannot be fixed in place).
- **The smixs directory name itself** (`references/smixs-image/`) leaks the upstream author name into routing text (host SKILL.md reference map, 6 mentions). Whether names-in-paths count as "agent-visible provenance" is a scope question for the design; file bytes are unaffected by a rename, but ATTRIBUTION.md's path column and the host SKILL.md routing would need synchronized updates.
- **Russian-language content is normative and pervasive** (~10 of 23 smixs md files). Any automated comment-stripping/sanitizing pipeline must be encoding-safe for Cyrillic and must not touch prose.
- Everything inside `references/` should be treated as a single class: upstream byte-exact, hands-off, migration happens by layer separation not by editing. The host layer (SKILL.md 3 items + ATTRIBUTION.md restructuring) is small and mechanical by comparison.
