# Audit: design-asset — provenance/attribution vs execution text

- **Query**: Per-item inventory of all NON-EXECUTION provenance/attribution content in `agents/assets/skills/design-asset/`; closure tracing; byte-exact verification (R5/AC4).
- **Scope**: internal + upstream verification (network)
- **Date**: 2026-07-10
- **Method**: every `.md` in the tree read in full (semantic pass, not grep-only); execution closure traced from host `SKILL.md`; every vendored file byte-compared against upstream `raw.githubusercontent.com @ main` via `curl` + `cmp`; git history checked for post-vendoring edits.

---

## 1. Summary table

| File | Provenance items | Categories | Closure | Byte-exact status |
|---|---|---|---|---|
| `SKILL.md` (host, 170 ln) | 8 (A1–A8) | C1 ×5 (partial rewrites), C3 ×3 | IN-CLOSURE (entry) | host-original, editable |
| `references/superdesign/token-checklist.md` | 6 (B1–B6) | C1 ×4, C2 ×1 (license blockquote), C3 (checklist body stays) | IN-CLOSURE (**every asset**, workflow step 5) | NOT byte-exact by design (extraction); editable. Quoted prompt string VERIFIED verbatim vs upstream `theme-tool.ts` |
| `references/guizang/style-system.md` | 2 (G1, G2) | C1-in-vendored | IN-CLOSURE (Chinese-social route) | **VERIFIED-EXACT** |
| `references/guizang/theme-presets.md` | 2 (G3, G4) | C1-in-vendored | IN-CLOSURE (Chinese-social route) | **VERIFIED-EXACT** |
| `references/guizang/layout-recipes.md` | 1 (G5) | C1-in-vendored | IN-CLOSURE (Chinese-social route) | **VERIFIED-EXACT** |
| `references/guizang/components.md` | 3 (G6–G8) | C1-in-vendored (upstream changelog + test-evidence paths) | IN-CLOSURE (Chinese-social route) | **VERIFIED-EXACT** |
| `references/guizang/background-systems.md` | 1 (G9) | C1/C3 mixed-in-vendored | IN-CLOSURE (Chinese-social route) | **VERIFIED-EXACT** |
| `references/guizang/platform-specs.md` | 2 (G10, G11) | inert-citation (declared) | IN-CLOSURE (canvas specs + placement) | **VERIFIED-EXACT** |
| `references/guizang/image-overlay.md` | 0 (false positive — see §6) | — | IN-CLOSURE (conditional gate, M16/anti-pattern D) | **VERIFIED-EXACT** |
| `references/guizang/upstream-SKILL.md` | whole-file (G12) + in-file items | C2 (canonical upstream original) + C3 (rules host depends on) | **CONDITIONAL IN-CLOSURE** (escape hatch — see §3) | **VERIFIED-EXACT** |
| `references/guizang/assets/template-*.html` ×2 | 0 (headers are functional usage docs) | — | IN-CLOSURE (copied as seed, step 6) | **VERIFIED-EXACT** ×2 |
| `references/guizang/assets/magazine-bg-webgl.js` | 1 (G13) | C1-in-vendored (header comment) | IN-CLOSURE (loaded by Editorial pages) | **VERIFIED-EXACT** |
| `references/jiji262/design-styles.md` | 1 (J1, upstream residue path) + 1 false positive | inert-citation (NOT declared) | IN-CLOSURE (Western/English route) | **VERIFIED-EXACT** |
| `references/jiji262/design-principles.md` | 0 | — | IN-CLOSURE (Western/English route) | **VERIFIED-EXACT** |
| `references/anthropic-frontend-design/SKILL.md` | 1 (F1, frontmatter license pointer) | C2-in-vendored | IN-CLOSURE (**always, once per session**) | **VERIFIED-EXACT** |
| `references/theme-factory/themes/*.md` ×10 | 0 (2 false positives) | — | IN-CLOSURE (quick-palette route) | **VERIFIED-EXACT** ×10 |
| `scripts/render_asset.mjs` | 1 (D1, header adaptation credit) | C2 (MIT notice) | executed every render; header visible on Read | host adaptation (not verbatim, as declared) |
| `ATTRIBUTION.md` | (bypass truth source) | C2 | BYPASS (but see gap X6) | host-original |
| `references/guizang/LICENSE` (AGPL-3.0, 662 ln) | — | C2, never delete | BYPASS | **VERIFIED-EXACT** |
| `references/guizang/COMMERCIAL_LICENSING.md` (190 ln, zh) | — | C2, never delete (dual-license offer) | BYPASS | **VERIFIED-EXACT** |
| `references/jiji262/LICENSE` (MIT © 2026 jiji262) | — | C2 | BYPASS | **VERIFIED-EXACT** |
| `references/anthropic-frontend-design/LICENSE.txt` (Apache-2.0) | — | C2 | BYPASS | **VERIFIED-EXACT** |
| `references/theme-factory/LICENSE.txt` (Apache-2.0) | — | C2 | BYPASS | **VERIFIED-EXACT** |

Byte-exact verification total: **29/29 files VERIFIED-EXACT** against current upstream `main` (2026-07-10). Git history: every vendored file has exactly one commit (`caf08603`) — zero post-vendoring host edits. ATTRIBUTION's byte-exact claim **holds fully**.

Category counts:
- **C1 editable** (pure provenance in host-editable execution text — migrate/reword): **~11 items** in 2 files (host `SKILL.md`, `token-checklist.md`).
- **C1-in-vendored** (upstream's OWN provenance inside byte-exact files — cannot edit without dropping the claim): **~12 items** in 8 guizang files + webgl js + anthropic frontmatter. Needs the R5 design decision (derived execution layer vs accept-in-place).
- **C2** (legal/maintenance, preserve in bypass): 4 LICENSE files, COMMERCIAL_LICENSING.md, ATTRIBUTION.md, token-checklist license blockquote, render_asset.mjs MIT credit, 2 user-approved exceptions (2026-07-02).
- **C3** (functional source rules that must STAY): inert-citation declarations, escape-hatch routing, canvas-value recheck caveat, token-checklist discipline, upstream product-attribution rules (SOURCES.md / CC credit), all instructional HTML-comment examples.

---

## 2. Byte-exact verification detail (R5 / AC4)

Method: `curl` each upstream raw URL, `cmp -s` against local copy. All commands run 2026-07-10.

| Upstream | Files | Result |
|---|---|---|
| `anthropics/skills` → `skills/frontend-design/` | SKILL.md, LICENSE.txt | VERIFIED-EXACT (2/2) |
| `anthropics/skills` → `skills/theme-factory/` | 10 themes + LICENSE.txt | VERIFIED-EXACT (11/11) |
| `jiji262/claude-design-skill` | design-styles.md, design-principles.md, LICENSE | VERIFIED-EXACT (3/3) |
| `op7418/guizang-social-card-skill` | 7 reference .md, upstream-SKILL.md (=root SKILL.md), 2 template HTML, magazine-bg-webgl.js, LICENSE, COMMERCIAL_LICENSING.md | VERIFIED-EXACT (13/13) |
| `superdesigndev/superdesign` → `src/tools/theme-tool.ts` | token-checklist.md is an EXTRACTION (declared, not byte-exact). The quoted `cssSheetDescription` block and the two params (`theme_name`, `reasoning_reference`) match upstream **verbatim** — extraction claim VERIFIED |
| `frontend-slides` plugin (local install `~/.claude/plugins/marketplaces/frontend-slides/`) | render_asset.mjs adaptation source `scripts/export-pdf.sh` exists; plugin LICENSE = MIT © 2025 Zara Zhang — matches ATTRIBUTION claim |

Consequences for the migration design:
1. **Every in-file provenance line inside guizang/jiji262/anthropic/theme-factory files is upstream's OWN text, not host-added.** Nothing host-added hides inside any byte-exact file. Editing any of them = dropping the byte-exact claim for that file (AC4).
2. The **only editable execution files** in this skill are: host `SKILL.md`, `references/superdesign/token-checklist.md`, `scripts/render_asset.mjs`, `ATTRIBUTION.md`.
3. Since local == current upstream main, "sync = re-fetch" is currently a no-op; any derived no-provenance execution layer would start from an identical base.

### ⚠ New legal fact discovered during verification (X1)

`superdesigndev/superdesign` **now has a root `LICENSE` file** (HTTP 200): *"mostly licensed under AGPLv3; certain files under a separate commercial license, marked `/* @license Enterprise */`"*. `src/tools/theme-tool.ts` carries **no** Enterprise marker → it falls under **AGPL-3.0**. ATTRIBUTION.md's "**No license file** (NOASSERTION — copyright reserved by default)" is **outdated** (either added upstream after the 2026-07-03 fetch, or missed at fetch time). Practical effect: superdesign moves from "no-license exception" to the same AGPL-internal-use posture as guizang (user already approved AGPL internal use 2026-07-02 for guizang). ATTRIBUTION.md must be updated during this task — legal info in the bypass file must be current, not silently wrong.

---

## 3. Execution-closure trace from host SKILL.md

Routing statements in host `SKILL.md` (entry file):

| Target | Routing text (SKILL.md) | Closure verdict |
|---|---|---|
| `references/anthropic-frontend-design/SKILL.md` | L114-117 "**Always**, before any of the above: read … once per session" | IN-CLOSURE, unconditional |
| `references/superdesign/token-checklist.md` | L34-35 workflow step 5 "Write the token sheet first … per `references/superdesign/token-checklist.md`" | IN-CLOSURE, unconditional (every asset) |
| guizang `style-system` / `theme-presets` / `layout-recipes` / `components` / `background-systems` | L82-89 style routing (Chinese social) | IN-CLOSURE, conditional (Chinese cards/decks) |
| guizang `platform-specs.md` | L70-71 "full safe-areas/naming/cover-structure rules in …" | IN-CLOSURE, conditional |
| guizang `image-overlay.md` | L158 "required gate for layout M16 / anti-pattern D" | IN-CLOSURE, conditional |
| guizang `assets/template-*.html` | L47-54 step 6 "START FROM the vendored seed templates" | IN-CLOSURE, conditional (copied into work dir) |
| guizang `assets/magazine-bg-webgl.js` | L157 "Editorial atmosphere layer (background-systems assumes it)"; loaded via `<script>` per background-systems.md | IN-CLOSURE, conditional |
| **guizang `upstream-SKILL.md`** | L159 "upstream control layer — **consult when a guizang reference cites a rule you can't find**" | **CONDITIONAL IN-CLOSURE — escape hatch, NOT a pure bypass archive.** ATTRIBUTION confirms intent: "kept for dependency-closure (control-layer rules like the overflow-repair grading live there)". Note: the overflow grading itself IS restated in host SKILL.md L139-141, but other control-layer rules (e.g. R8/R9 validator semantics, overflow-fix follow-ups, title-gap rules at upstream L324-325) are reachable only through this hatch. |
| jiji262 `design-styles.md` + `design-principles.md` | L105-108 Western/English route | IN-CLOSURE, conditional |
| `theme-factory/themes/*.md` | L109-113 quick palette route | IN-CLOSURE, conditional |
| `scripts/render_asset.mjs` | L55-60 step 7 (executed; header printed usage/bootstrap read when debugging) | executed every render |
| `ATTRIBUTION.md`, 4× LICENSE, `COMMERCIAL_LICENSING.md` | never referenced from SKILL.md | BYPASS |

Answer to the assignment's specific question: **`upstream-SKILL.md` is routed to during execution** (conditionally, as an escape hatch), it is NOT kept only as an inert upstream original. Any design that strips provenance from the normal path must decide what to do with this hatch — the file is 100% upstream text (byte-exact) and contains upstream's own provenance line at L10 plus upstream repo conventions (`local-tests/`, validator invocations, user-interaction flows) that don't match host reality.

One bypass-pointer violation found: `token-checklist.md` L7 tells the executing agent "See ATTRIBUTION.md." — execution text directing at a bypass file (conflicts with R2's "normal execution must not require reading bypass files"). Item B2 below.

---

## 4. Per-item detail — editable execution files

### 4.1 Host `SKILL.md` (agents/assets/skills/design-asset/SKILL.md)

| ID | Lines | Verbatim excerpt (shortened) | Category | Closure | Proposed destination | Constraint |
|---|---|---|---|---|---|---|
| A1 | 47-48 | "START FROM the **vendored** seed templates" | C1 (vocabulary only) | IN | reword ("the seed templates"); vendored-fact already in ATTRIBUTION.md | none |
| A2 | 69-72 | "(values: **guizang platform-specs — third-party production values** as of 2026-07, NOT re-verified against official platform docs; recheck if a platform rejects an upload…)" | C1+C3 mixed | IN | KEEP behavior: "tested-as-of-2026-07; recheck if a platform rejects an upload" (R4 functional caveat). MIGRATE sourcing ("guizang / third-party") — already duplicated in ATTRIBUTION.md host-adaptations bullet 3, so this is a dedupe | R4: don't delete the recheck rule |
| A3 | 89-90 | "Arbitrations where guizang docs conflict or trap (**learned by blind test**):" | C1 (research history) | IN | drop "(learned by blind test)"; keep all arbitration bullets (functional). History already in ATTRIBUTION.md guizang row ("blind usability test caught the missing closure") | none |
| A4 | 110-113 | "**Upstream flow asks the user to choose**; you choose autonomously: match theme mood … and record which one you picked and why." | C1+C3 mixed | IN | KEEP "choose autonomously … record which one and why" (C3). MIGRATE the upstream-comparison clause — already in ATTRIBUTION.md host-adaptations bullet 1 (dedupe) | R4 rewrite, not delete |
| A5 | 146 | "Output naming (**matches upstream docs** and validator):" | C1 partial | IN | reword to "(matches the validator)" — validator interop is C3 (visual-iterate's `validate-social-deck.mjs` expects these names) | none |
| A6 | 155-158 | Reference-map rows for guizang docs/templates/webgl | — (functional routing) | IN | keep | none |
| A7 | 159 | "`references/guizang/upstream-SKILL.md` \| **upstream control layer** — consult when a guizang reference cites a rule you can't find" | C3 (routing) with provenance flavor | IN | design decision: keep hatch (reworded) vs restate remaining control-layer rules and demote upstream-SKILL.md to bypass. Flag for design.md | if hatch removed, the un-restated upstream rules must be re-homed (R4) |
| A8 | 164-170 | "Upstream files cited by guizang docs but NOT **vendored** (live-photo-production, screenshot-treatment, qa-checklist, …): those citations are **INERT** … Also inert: platform-specs' 'Final Response Media' section ('In Codex desktop…') — **upstream product residue**, does not apply here." | **C3 — must stay** (runtime input constraint: the byte-exact guizang docs really do cite these 9 missing files + a Codex-desktop flow; without the inert list an agent chases dead paths) | IN | keep, may reword vocabulary ("vendored/upstream residue" → neutral phrasing); this is exactly PRD R4's "上游格式构成运行时输入约束" case | inert list must track the byte-exact files' citations |

### 4.2 `references/superdesign/token-checklist.md` (host-authored extraction — editable)

| ID | Lines | Verbatim excerpt (shortened) | Category | Closure | Proposed destination | Constraint |
|---|---|---|---|---|---|---|
| B1 | 1 | "# Design-token checklist (**extracted from superdesign**)" | C1 | IN (every asset) | retitle without source | none |
| B2 | 3-7 | "> **Provenance: extracted verbatim from `superdesigndev/superdesign` `src/tools/theme-tool.ts`** (the `cssSheetDescription` prompt string, **lines 20-35**, plus the two forcing-function tool parameters), **fetched 2026-07-03** … Upstream has **NO license file** … vendored under the **user's explicit 2026-07-02 approval** for internal use. **See ATTRIBUTION.md.**" | C1+**C2** | IN | MIGRATE whole blockquote into ATTRIBUTION.md superdesign row. Critical: ATTRIBUTION currently **delegates** detail to this header ("provenance header inside") — the line-range/param detail exists ONLY here; merging must land it in ATTRIBUTION before stripping (R2: no silent loss). Also fixes the bypass-pointer violation ("See ATTRIBUTION.md" in execution text). Update license status per finding X1 (upstream now AGPLv3) | never silently delete: license + user-approval record |
| B3 | 9-11 | "The **upstream** checklist of required variables:" | C1 vocab | IN | reword ("Required variables:"); the code-block checklist itself is C3, byte-preserve it (it's the verbatim upstream quote — maintenance sync anchor) | keep quoted block verbatim or record in ATTRIBUTION that verbatim-ness was dropped |
| B4 | 28-29 | "**Upstream note kept as-is:** 'You can add more relevant ones…'" | C1 wrapper, C3 content | IN | keep the quoted rule; reword wrapper | same as B3 |
| B5 | 31-36 | "Two forcing-function fields **the upstream tool requires** alongside the sheet — keep them as a discipline **even without the tool**: `theme_name` … `reasoning_reference` …" | C1 wrapper, C3 content | IN | keep discipline (host SKILL.md step 5 depends on it: "name the theme, note what you referenced"); reword upstream framing | R4 |
| B6 | 38-43 | "## **Host adaptation notes (not upstream)** — For static single-canvas social assets, `--sidebar-*` and `--chart-1..5` are usually N/A — declare them anyway … omissions are decisions, not accidents." | C1 heading, C3 body | IN | keep body (functional rule host SKILL.md step 5 leans on); neutral heading | R4 |

Note: token-checklist.md is the ONE vendored-family execution file that is legitimately editable (extraction, not byte-exact). If edited, ATTRIBUTION.md's blanket sentence "Everything under `references/` is vendored **verbatim** (byte-exact…)" — already contradicted by its own superdesign row — should be qualified (see gap X3).

### 4.3 `scripts/render_asset.mjs`

| ID | Lines | Verbatim excerpt | Category | Closure | Proposed destination | Constraint |
|---|---|---|---|---|---|---|
| D1 | 2-6 | "// render_asset.mjs — deterministic HTML -> PNG … // **Adapted from frontend-slides scripts/export-pdf.sh (MIT (c) 2025 Zara Zhang)**: same local-HTTP-server + networkidle + document.fonts.ready + per-element screenshot shape, re-cut for arbitrary fixed-size canvases instead of slides." | **C2** (MIT credit + adaptation history) | executed every render; header read when debugging (exit-2 bootstrap instructions L19-23 are functional C3) | Two options: (a) keep the 3-line credit in-file (MIT notice retention is the safest legal posture for a derivative; only ~3 lines of agent-visible noise), or (b) move credit to ATTRIBUTION.md — but ATTRIBUTION currently says "adaptation noted in file header" (delegation), so it must absorb the note first, and the skill ships no MIT license text for this file (gap X5) | MIT: "The above copyright notice … shall be included in all copies or substantial portions of the Software" — do not delete the credit without re-homing it in a file that materializes with the skill (ATTRIBUTION.md does materialize) |

Usage/bootstrap comments (L8-23) and all other comments in the file are functional — keep.

---

## 5. Per-item detail — byte-exact vendored files (upstream-own provenance; CANNOT edit, R5)

All items below are upstream's own text, verified byte-exact. Options per PRD R5: keep canonical original + derive a no-provenance execution layer, or accept in place. None may be edited in-file while the byte-exact claim stands.

| ID | File:lines | Verbatim excerpt (shortened) | Nature | Closure |
|---|---|---|---|---|
| G1 | `guizang/style-system.md:3` | "This skill extracts **Guizang PPT** visual principles for static social images. It does not depend on the original PPT templates." | upstream self-provenance | IN |
| G2 | `guizang/style-system.md:34` | "See `local-tests/demo-showcase/editorial.html` for **source-of-truth**." | upstream repo residue (dead path here) | IN |
| G3 | `guizang/theme-presets.md:7` | "These are **adapted from the Guizang PPT electronic-magazine mode** for static Rednote and WeChat images." | upstream self-provenance | IN |
| G4 | `guizang/theme-presets.md:137` | "These are **adapted from the Guizang PPT Swiss mode**." | upstream self-provenance | IN |
| G5 | `guizang/layout-recipes.md:3` | "These are static social-image recipes **adapted from the Guizang PPT style language**. They are not copied PPT templates." | upstream self-provenance | IN |
| G6 | `guizang/components.md:42` | "> **Restored 2026-05-27.** The previous defaults (900/700/700/sans body/−.01em) made Editorial cards read as heavy infographic banners. … see `local-tests/demo-showcase/editorial.html` for the source-of-truth." | upstream changelog + dead path | IN |
| G7 | `guizang/components.md:78` | "verified empirically in `local-tests/smoke-ai-tools/`" | upstream test-evidence path (dead here) | IN |
| G8 | `guizang/components.md:90` (also 98) | "Verified in `local-tests/demo-smoke-editorial-travel/` …" | upstream test-evidence path (dead here) | IN |
| G9 | `guizang/background-systems.md:3` | "The **original Guizang PPT** electronic-magazine mode uses WebGL fluid, contour, ink, and chromatic atmosphere. Static Rednote/WeChat images **should preserve that feeling**…" | mixed: provenance + functional aesthetic anchor (the "preserve that feeling" half is a real design rule) | IN |
| G10 | `guizang/platform-specs.md:25` | "Use `references/live-photo-production.md` when making `.pvt` packages…" | citation of non-vendored file — **declared inert** by host SKILL.md A8 | IN |
| G11 | `guizang/platform-specs.md:134-142` | "## Final Response Media — In **Codex desktop**, local media can be shown with absolute paths…" | upstream product residue — **declared inert** by host SKILL.md A8 | IN |
| G12 | `guizang/upstream-SKILL.md` (whole file, 336 ln; esp. L10) | "This skill is self-contained. It **borrows visual principles from the Guizang PPT style system**, but it must not edit the original PPT skill…" + full upstream workflow (intake questions to a human user, `local-tests/` conventions, validator calls, category cookbook, web-image sourcing flow L254-293 incl. functional attribution rules: record source URLs in `assets/SOURCES.md`, preserve CC attribution) | canonical upstream original, kept for dependency closure | CONDITIONAL IN (escape hatch, §3) |
| G13 | `guizang/assets/magazine-bg-webgl.js:1-3` | "/* Reusable **Guizang-style** electronic magazine background. Copy or inline into generated HTML. …*/" | upstream header comment (mostly functional, one style-name mention) | IN |
| J1 | `jiji262/design-styles.md:12` | "**Concrete reference:** [../demos/style-gallery/index.html] renders the same one-page intro in all 10 styles…" | upstream residue → dead relative path in host tree; **NOT declared inert** by host SKILL.md (gap X4) | IN |
| F1 | `anthropic-frontend-design/SKILL.md:4` | frontmatter "license: Complete terms in LICENSE.txt" | upstream license pointer inside execution text (points at a bypass file that IS materialized alongside) | IN (always-read file) |

Other guizang doc citations of non-vendored files, all covered by host SKILL.md's inert list (A8): `components.md:179` → `references/screenshot-treatment.md`; `components.md:193` → `references/map-component.md`; `upstream-SKILL.md` cites all nine. No un-declared guizang dead citation found beyond those; the only un-declared dead citation in the whole tree is J1 (jiji262 demo path).

---

## 6. False positives (keyword hits that are NOT provenance — do not migrate)

| File:lines | Content | Why functional |
|---|---|---|
| `jiji262/design-styles.md:187-196` | HTML comment example `<!-- System: Swiss Editorial (Pentagram lineage) … -->` | Instructional pattern: "write a mini system upfront in a comment" is the methodology itself |
| `guizang/style-system.md:133,136` | `<!-- WRONG: … -->` / `<!-- RIGHT: … -->` | Anti-pattern teaching example |
| `guizang/layout-recipes.md:414-420, 425-426, 456-457` | `<!-- subject map (cover hero …) -->`, `<!-- NO MASK — … -->` | Skeleton code demonstrating the mandatory subject-map comment |
| `guizang/image-overlay.md:85-90` | `<!-- subject map (Wukong cover hero): … -->` | Same — the rule REQUIRES agents to write such comments (product behavior) |
| `theme-factory/themes/sunset-boulevard.md:3`, `forest-canopy.md:3` | "inspired by golden hour sunsets / dense forest environments" | Theme mood description, not skill provenance |
| Designer/brand names throughout `jiji262/design-styles.md` (Pentagram, Vignelli, Sagmeister…) and `guizang` (Kinfolk, Cereal, Monocle) | style anchors | Aesthetic reference vocabulary = the content of the skill, not its origin story |
| `guizang/upstream-SKILL.md:254-293` web-image sourcing + attribution flow | record `assets/SOURCES.md`, CC credit, disclose provenance to user | **C3 product behavior** (PRD explicitly excludes: 记录图片 URL、保留 CC 作者名) |

The task brief's expectation of "HTML provenance comments in guizang/*.md and jiji262/design-styles.md" resolves to these false positives — **semantic pass found zero HTML comments that are provenance** in this skill. All HTML comments in scope are instructional examples.

---

## 7. ATTRIBUTION.md cross-check & gaps

ATTRIBUTION.md (23 ln, host-original, BYPASS) covers: all 5 upstream sources with paths/licenses/notes, both user-approved exceptions (guizang AGPL internal-use 2026-07-02; superdesign 2026-07-02), sync policy, host-level adaptations (3 bullets), the blind-test closure lesson, the corrected research claim (upstream ships no `render.mjs`), non-vendored binary note. Coverage is strong. Gaps/actions:

| ID | Gap | Action needed during migration |
|---|---|---|
| X1 | **superdesign license status outdated**: upstream now has root LICENSE = AGPLv3 (dual, `@license Enterprise` commercial markers; `theme-tool.ts` unmarked → AGPLv3). ATTRIBUTION says "No license file (NOASSERTION)" | Update superdesign row; posture converges with guizang's AGPL-internal-use approval, but the record must be corrected, arguably re-confirmed with user |
| X2 | **ATTRIBUTION delegates detail to two execution-file headers**: superdesign row says "provenance header inside"; render_asset.mjs row says "adaptation noted in file header". The extraction line-range (`theme-tool.ts` lines 20-35 + two params) exists ONLY in token-checklist.md L3-7 | Absorb both headers' content into ATTRIBUTION.md BEFORE stripping them (R2 traceability) |
| X3 | Blanket claim "Everything under `references/` is vendored **verbatim** (byte-exact…)" is internally contradicted by the superdesign row (extraction) and will be further off if token-checklist.md is edited | Qualify blanket sentence ("except `references/superdesign/` — extraction") |
| X4 | `jiji262/design-styles.md:12` dead path `../demos/style-gallery/index.html` not in host SKILL.md's inert list | Add to inert declarations (C3) or accept; note in design |
| X5 | No MIT license text ships for `render_asset.mjs`'s upstream (frontend-slides, MIT © 2025 Zara Zhang) — only the pointer in ATTRIBUTION + in-file credit | If in-file credit is stripped, ship the notice via ATTRIBUTION (it materializes with the skill); consider whether MIT notice text itself should be added |
| X6 | `token-checklist.md:7` "See ATTRIBUTION.md." — execution text directs agent at bypass file (R2 violation) | Removed by B2 migration |
| X7 | No `MAINTENANCE.md` exists. Host-adaptation history + sync policy + research-claim corrections currently live in ATTRIBUTION.md | PRD default splits maintenance info to MAINTENANCE.md; since ATTRIBUTION already holds it coherently, design should choose merge-target explicitly (R2: no conflicting dual truth-sources) |

---

## 8. Key design inputs for this skill (summary)

1. **The byte-exact wall is real and currently intact (29/29).** Every provenance line inside `references/` (except superdesign) is upstream-authored. R3-style in-file cleanup is impossible there without violating R5/AC4. The only cleanups possible today: host `SKILL.md` (8 items), `token-checklist.md` (6 items), `render_asset.mjs` header (1 item, MIT-constrained).
2. **`upstream-SKILL.md` is conditionally routed-to** (escape hatch at SKILL.md L159), so a "keep originals as bypass, execute from derived layer" design must either preserve the hatch (agent still sees upstream text incl. its provenance and human-interaction flows) or restate the remaining control-layer rules and close the hatch.
3. **Host SKILL.md's inert-citation block (A8) is functional (C3)** and exists precisely BECAUSE the vendored files are byte-exact and cite files that were not vendored. Any rewording must keep the declarations.
4. **The upstream provenance lines that agents actually see** on the guizang route are 5 short sentences (G1, G3, G4, G5, G9) + one changelog blockquote (G6) + dead `local-tests/` paths (G2, G7, G8) + declared-inert product residue (G10, G11). Impact-wise they are mild; the heaviest agent-visible non-execution text on that route is arguably the whole of `upstream-SKILL.md` when the hatch fires.
5. **Nothing in this skill should be deleted-only**: guizang AGPL + commercial dual-license files, superdesign approval record, MIT credit, and the two user exceptions are all C2 preserve-forever items.
