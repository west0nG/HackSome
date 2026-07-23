# Research: provenance/attribution audit — mine-customer-voice + visual-iterate

- **Query**: per-item inventory of non-execution provenance/attribution content in `agents/assets/skills/mine-customer-voice/` and `agents/assets/skills/visual-iterate/`, with execution-closure classification and upstream verbatim verification
- **Scope**: internal (files) + external (upstream verification via raw.githubusercontent.com)
- **Date**: 2026-07-10

Categories: **C1** = pure provenance, migrate out of execution text · **C2** = legal/maintenance info, preserve in bypass file (never silently deleted) · **C3** = functional source rule, must STAY in execution text.

---

## Summary Table

| ID | File : lines | Excerpt (abridged) | Category | Closure | Proposed destination | Verbatim/license constraint |
|---|---|---|---|---|---|---|
| MCV-1 | `mine-customer-voice/SKILL.md:13-14` | "(vendored, see `ATTRIBUTION.md`)" | C1 (mixed sentence) | IN-CLOSURE | Delete parenthetical; already covered by ATTRIBUTION.md | None (host text) |
| MCV-2 | `mine-customer-voice/SKILL.md:67` | "The vendored files keep their upstream conventions; map them like this:" | C1 phrasing on a C3 section | IN-CLOSURE | Rephrase neutrally; keep mapping rules | None (host text) |
| MCV-3 | `mine-customer-voice/SKILL.md:69-70` | "that is upstream's name for company context, so read `/company` instead" | C3 rule + C1 phrasing | IN-CLOSURE | Keep rule; optionally neutralize "upstream's name" | None (host text) |
| MCV-4 | `mine-customer-voice/SKILL.md:71-75` | "those paths are upstream's install layout, and the template is already here" | C3 rule + C1 phrasing | IN-CLOSURE | Keep rule; optionally neutralize wording | None (host text) |
| MCV-5 | `mine-customer-voice/SKILL.md:80-82` | "Links into upstream's `tools/integrations/` directory … are not vendored; … skip those links" | C3 rule + C1 phrasing | IN-CLOSURE | Keep skip-rule; optionally neutralize "not vendored" | None (host text) |
| MCV-6 | `mine-customer-voice/SKILL.md:89-93` | "## Sources — Vendored (MIT); see `ATTRIBUTION.md`. Upstream lives untouched under `references/`; this file is the only adaptation layer … Sync by re-copying upstream, not editing it." | C1 + C2 (sync policy) | IN-CLOSURE | Delete whole section; every claim already in ATTRIBUTION.md (policy ¶ + sync section) | None (host text) |
| MCV-7 | `mine-customer-voice/ATTRIBUTION.md` (whole, 47 lines) | vendor table, host-adaptation list, upstream-sync procedure | C2 | BYPASS (but pointed at from SKILL.md:14,91) | Keep as canonical; remove SKILL.md pointers. Mixes attribution + maintenance — PRD default would split sync/adaptation into MAINTENANCE.md, merging also allowed | Records the "vendored verbatim" claim |
| MCV-8 | `mine-customer-voice/vendor/LICENSE.coreyhaines-marketingskills` | MIT © 2025 Corey Haines | C2 | BYPASS | Keep untouched (MIT requires notice retention) | VERIFIED-EXACT |
| MCV-9 | `references/{customer-research,source-guides,listening,listening-sources-template}.md` (upstream-layout mentions, see detail) | e.g. `listening.md:280` "Working inside the marketingskills repo: cp skills/social/…" | Upstream-owned layout noise (NOT host provenance) | IN-CLOSURE | Leave in place OR apply R5 canonical-original + execution-layer split; do NOT edit in place | Vendored-verbatim claim forbids in-place edits |
| MCV-10 | `references/customer-research.md:4-5` | frontmatter `metadata: version: 2.0.0` | Upstream version stamp | IN-CLOSURE | Same as MCV-9 | Same as MCV-9 |
| VI-1 | `visual-iterate/SKILL.md:21` | "run the vendored validator" | C1 (one word) | IN-CLOSURE | Drop "vendored"; sentence stays | None (host text) |
| VI-2 | `visual-iterate/SKILL.md:46` | "(from guizang's control layer)" | C1 | IN-CLOSURE | Delete parenthetical; thresholds stay (C3); origin already in ATTRIBUTION.md bullet 4 | None (host text) |
| VI-3 | `visual-iterate/SKILL.md:104-108` | "Rubric sources (rewritten, not copied): OneRedOak … gstack … anthropics canvas-design … guizang (AGPL, user-approved exception) … Anthropic pptx *pattern* … Details in ATTRIBUTION.md." | C1 | IN-CLOSURE | Delete whole paragraph; ATTRIBUTION.md:12-27 is a strict superset | None (host text); AGPL-exception wording must survive in ATTRIBUTION.md |
| VI-4 | `visual-iterate/ATTRIBUTION.md` (whole, 31 lines) | vendor table w/ AGPL user-approved exception, host-synthesized source list, verification-status history | C2 | BYPASS (pointed at from SKILL.md:108) | Keep as canonical; remove SKILL.md pointer. Verification-status ¶ (L29-31) is maintenance history — MAINTENANCE.md candidate, merging allowed | Records "byte-exact" claim; AGPL exception is legal-critical (R5) |
| VI-5 | `visual-iterate/references/guizang/LICENSE` | AGPL-3.0 full text | C2 | BYPASS | Keep untouched | VERIFIED-EXACT |
| VI-6 | `references/guizang/qa-checklist.md:16,78,97` | refs to `style-system.md`, `references/image-overlay.md` (exist only in design-asset's guizang dir) | Upstream-owned cross-refs (NOT provenance) | IN-CLOSURE (conditional) | Leave; byte-exact claim forbids in-place edit | Byte-exact claim |
| VI-7 | `references/guizang/validate-social-deck.mjs:7-8` | header: "rules codified in SKILL.md / qa-checklist.md / components.md" (upstream's docs) | Upstream-owned comment (NOT provenance) | IN-CLOSURE (staged+executed) | Leave; byte-exact | Byte-exact claim |

C3 anchors (must NOT be touched; product behavior, not skill provenance):

| ID | File : lines | Rule |
|---|---|---|
| C3-a | `mine-customer-voice/SKILL.md:43-48` | mined library = verbatim quotes tied to direction/segment |
| C3-b | `references/customer-research.md:74,77,89,141-148` | capture exact quotes, not paraphrases; Source field = platform + thread URL + date |
| C3-c | `references/source-guides.md:354` | running doc columns Source / Date / Quote / Tags / Notes |
| C3-d | `visual-iterate/references/guizang/qa-checklist.md:93` | web-fetched image source URL recorded in `assets/SOURCES.md`; Flickr CC author name preserved on opt-in |
| C3-e | `mine-customer-voice/SKILL.md:69-87` mapping rules | upstream path/format conventions ARE runtime input constraints (PRD R4); the rules stay even if wording is neutralized |
| C3-f | `visual-iterate/SKILL.md` "guizang" as routing vocabulary (L21, L100-101, L77) | names the style system shared with design-asset; functional routing term, renaming out of scope |

---

## Execution-closure map

### mine-customer-voice (entry: SKILL.md)

| File | Closure | How reached |
|---|---|---|
| `SKILL.md` | IN-CLOSURE | entry point |
| `references/customer-research.md` | IN-CLOSURE | SKILL.md:25 ("the frame") |
| `references/source-guides.md` | IN-CLOSURE | SKILL.md:30; also customer-research.md:120 |
| `references/listening.md` | IN-CLOSURE | SKILL.md:35 |
| `references/listening-sources-template.md` | IN-CLOSURE | SKILL.md:35-36,48; listening.md:272 |
| `ATTRIBUTION.md` | BYPASS by role, but SKILL.md:14 and :91 say "see ATTRIBUTION.md" — a conditional pull-in that violates PRD R2 (execution text must not direct agents to bypass files). Pointer removal is part of MCV-1/MCV-6. | — |
| `vendor/LICENSE.coreyhaines-marketingskills` | BYPASS | only referenced from ATTRIBUTION.md |

### visual-iterate (entry: SKILL.md)

| File | Closure | How reached |
|---|---|---|
| `SKILL.md` | IN-CLOSURE | entry point |
| `references/guizang/validate-social-deck.mjs` | IN-CLOSURE | SKILL.md:21-24 — staged and executed every guizang-routed round |
| `references/guizang/qa-checklist.md` | IN-CLOSURE (conditional) | SKILL.md reference map:101 — "validator green but the render still smells" |
| `ATTRIBUTION.md` | BYPASS by role, but SKILL.md:108 says "Details in ATTRIBUTION.md." — pointer removal is part of VI-3 | — |
| `references/guizang/LICENSE` | BYPASS | never directed; "rides along" per ATTRIBUTION.md |

---

## Per-item detail

### MCV-1 — SKILL.md:13-14

> "The collection playbooks live under `references/` (vendored, see `ATTRIBUTION.md`)."

Mixed sentence (PRD R4 case). Behavioral half — "the collection playbooks live under `references/`" — stays. The parenthetical is pure provenance plus a pointer into a bypass file. ATTRIBUTION.md already states vendored status, licenses, and upstream coordinates. **Migration loses nothing.**

### MCV-2 through MCV-5 — SKILL.md "Reading the catalogs" (:65-87)

The section is the skill's adaptation layer and is overwhelmingly **C3**: it translates upstream file conventions into this environment (`.agents/product-marketing.md` → `/company`; `.agents/listening-sources.md` → `/company` source-list doc; skip upstream copy commands; browser-tool mapping; skip broken `tools/integrations/` links; Related-Skills handoff remap). PRD R4 explicitly protects "上游格式确实构成运行时输入约束" rules — these are exactly that: the agent reads the vendored files at runtime and needs the translation.

What is C1 here is only the *framing vocabulary*: "vendored files", "upstream's name for", "upstream's install layout", "upstream's `tools/integrations/` directory … are not vendored". A rewrite that says "the catalog files use these conventions" / "that path means `/company` here" preserves identical behavior with zero provenance. Note: some mention of "these files come from elsewhere and use foreign paths" arguably helps the agent trust the mapping; design decision is whether to keep a single neutral sentence ("the catalog files use their own path conventions") — behavior-equivalent either way.

### MCV-6 — SKILL.md:89-93 "## Sources" (flagship)

> "Vendored (MIT); see `ATTRIBUTION.md`. Upstream lives untouched under `references/`; this file is the only adaptation layer (library and voice into `/company`, source mapping). Sync by re-copying upstream, not editing it."

- "Vendored (MIT); see ATTRIBUTION.md" — C1, duplicated by ATTRIBUTION.md table (MIT © 2025 Corey Haines) and `vendor/LICENSE.…`.
- "Upstream lives untouched … only adaptation layer" — C1, duplicated by ATTRIBUTION.md:3-7 ("reference material is vendored verbatim. The only original file is `SKILL.md`").
- "Sync by re-copying upstream, not editing it" — C2 maintenance, duplicated by ATTRIBUTION.md "Upstream sync" section (:42-47, "Do not hand-edit vendored files").

Whole section can be deleted from SKILL.md with a diff→bypass mapping note; no content is unique.

### MCV-7 — ATTRIBUTION.md (bypass, keep)

Structure: vendor policy statement (:2-7), 4-row upstream table with repo/paths/version/license/fetch-date/commit (:9-14), license-file pointer + evals-not-vendored note (:16-17), "What our SKILL.md adds" host-adaptation list (:19-40), "Upstream sync" procedure (:42-47).

Observations for design:
- It already serves as the merged ATTRIBUTION+MAINTENANCE file. PRD R2 default separates them; R2 also allows merging when a bypass file exists ("优先合并，不能产生多个互相冲突的来源真相源").
- The "Upstream layout overrides" bullet (:35-40) is the maintenance-side mirror of SKILL.md's "Reading the catalogs" — after any SKILL.md rewording, this bullet's cross-description should be re-checked for drift (it names specific SKILL.md section titles).
- Cross-check vs findings: complete. All four vendored files, the license file, and every host adaptation found in SKILL.md are represented. **No gaps.**

### MCV-8 — vendor/LICENSE.coreyhaines-marketingskills

MIT text, © 2025 Corey Haines. Byte-identical to upstream `LICENSE` at pinned commit (see verification). MIT's notice-retention condition means this file must ship wherever substantial portions of the vendored files ship. Keep untouched; already bypass.

### MCV-9 / MCV-10 — upstream-owned in-closure content in vendored references

All four `references/*.md` are **upstream's own text** (verified byte-exact). They contain no "adapted from"-style skill provenance. What they do contain is upstream *environment/layout* residue that an executing agent sees:

- `customer-research.md:3` description mentions upstream skills `copywriting`, `cro`; `:15` `.agents/product-marketing.md` / `.claude/product-marketing.md` / legacy filename; `:260-273` "Related Skills" table of 9 non-installed skills. All overridden by SKILL.md:69-70 and :83-87.
- `customer-research.md:4-5` frontmatter `metadata: version: 2.0.0` — upstream release stamp (also cited in ATTRIBUTION.md as "v2.0.0").
- `source-guides.md:336` "See [tools/integrations/sparktoro.md](../../../tools/integrations/sparktoro.md)" — broken relative link into upstream repo; overridden by SKILL.md:80-82.
- `listening.md:268-283` "Setting Up the Source List" — `.agents/listening-sources.md`, three `cp` commands for upstream install layouts; **`:280` is the only in-closure occurrence of the upstream repo name ("Working inside the marketingskills repo")**. Overridden by SKILL.md:71-75.
- `listening.md:171-205` and `listening-sources-template.md:30,34,94,117-124` assume a "dev-browser (MCP, already in the global setup)" environment — overridden by SKILL.md:76-79.
- `listening-sources-template.md:3` "Copy this file to `.agents/listening-sources.md`" — overridden by SKILL.md:71-75.

None of this is C1 host provenance. Constraint: ATTRIBUTION.md claims these files are "vendored verbatim" — **any in-place edit drops that claim** (PRD R5 / AC4). If the design wants agents to stop seeing this residue, the only compliant options are (a) leave as-is behind the adaptation layer (current state, works), or (b) canonical-original + separate execution layer per R5.

### VI-1 — visual-iterate/SKILL.md:21

> "guizang-routed cards/decks: run the vendored validator."

Functional sentence; only the word "vendored" is provenance. "guizang-routed" is functional routing vocabulary (C3-f). Fix: "run the validator".

### VI-2 — visual-iterate/SKILL.md:46

> "Overflow gets the graded response (from guizang's control layer): **1-40px** … **160px+** …"

The graded thresholds are C3 (product behavior, mirrored in qa-checklist.md's "Overflow Correction Ladder"). The parenthetical "(from guizang's control layer)" is C1; its content already lives in ATTRIBUTION.md:22-23 ("Overflow-repair grading (1-40/40-90/90-160/160+px) … guizang upstream SKILL.md control layer").

### VI-3 — visual-iterate/SKILL.md:104-108 "Rubric sources" (flagship)

> "Rubric sources (rewritten, not copied): OneRedOak design-review triage + problems-over-prescriptions (MIT), gstack design-review thresholds & PASS/FAIL protocol (MIT), anthropics canvas-design hard checks + no-additions-on-revision (Apache-2.0), guizang thresholds & overflow grading (AGPL, user-approved exception), Anthropic pptx fresh-eyes *pattern* (pattern only — its text is proprietary and none is reproduced here). Details in ATTRIBUTION.md."

Pure C1. Item-by-item comparison against ATTRIBUTION.md:12-27 shows ATTRIBUTION covers all five sources in strictly more detail (adds © 2026 Garry Tan, "~85% NOT taken" scoping, "restated as facts/thresholds", pptx-license reasoning). **Deleting the paragraph from SKILL.md loses nothing**, provided ATTRIBUTION.md is preserved (the AGPL "user-approved exception" and the pptx "no text reproduced" statements are the legally load-bearing sentences — R5).

### VI-4 — visual-iterate/ATTRIBUTION.md (bypass, keep)

Structure: byte-exact claim + fetch date (:3-4), 3-row vendored table with the **AGPL-3.0 dual-license + user-approved exception 2026-07-02, internal use only, "revisit before any external distribution of this repo"** (:8), host-synthesized 5-source list (:12-27), verification-status note (:29-31, e2e run 2026-07-03).

Observations:
- The AGPL exception row is user-approved legal state (matches memory: guizang AGPL 解禁 for internal use). Must never be weakened (R5).
- Table row 1's Notes column also carries a functional fact ("bare-imports `playwright`, so the host documents staging it into `$PLAYWRIGHT_DIR`") — the functional copy correctly lives in SKILL.md:22-24; the ATTRIBUTION copy is descriptive, no conflict.
- Verification-status paragraph (:29-31) is maintenance history (MAINTENANCE.md candidate under the PRD split; merging allowed).
- **Gap**: unlike mine-customer-voice (commit `2815104` pinned), the guizang fetch is pinned only as "`main` @ 2026-07-03" with no commit hash — the byte-exact claim is re-checkable only while upstream main doesn't move (it hadn't as of 2026-07-10, see verification). Factual gap affecting reproducibility of the claim, relevant to AC4.
- Cross-check vs findings: consistent with SKILL.md:104-108 (superset). No missing sources found in either file. **No gaps besides the commit pin.**

### VI-6 / VI-7 — upstream-owned in-closure content in guizang files

- `qa-checklist.md:16` "(see Anti-pattern C in `style-system.md`)", `:78` "(see `style-system.md` \"Style Identity Test\")", `:97` "See `references/image-overlay.md`" — these files are NOT in visual-iterate; they exist in `design-asset/references/guizang/` (checked: `/Users/weston/dev/BuildFactory/agents/assets/skills/design-asset/references/guizang/{style-system.md,image-overlay.md}`). Upstream cross-refs, byte-exact constraint, not provenance. SKILL.md:77-78 already routes the identity tests to design-asset's style-system.md.
- `validate-social-deck.mjs:7-8` header comment: "Checks each `<section class=\"poster …\">` … against the rules codified in SKILL.md / qa-checklist.md / components.md" — refers to upstream guizang's own SKILL.md and components.md, not host files. Byte-exact; no other provenance markers in the script (grep hits on "mit" were `bottomGapLimit` false positives).
- HTML comments: **none** in any file of either skill (`grep '<!--'` returned zero matches).

---

## Upstream verification (Bash curl + diff, 2026-07-10)

### mine-customer-voice — claimed: verbatim from `coreyhaines31/marketingskills` @ commit `2815104` (fetched 2026-07-02)

| Vendored file | Claimed upstream path | Result |
|---|---|---|
| `references/customer-research.md` | `skills/customer-research/SKILL.md` | **VERIFIED-EXACT** |
| `references/source-guides.md` | `skills/customer-research/references/source-guides.md` | **VERIFIED-EXACT** |
| `references/listening.md` | `skills/social/references/listening.md` | **VERIFIED-EXACT** |
| `references/listening-sources-template.md` | `skills/social/references/listening-sources-template.md` | **VERIFIED-EXACT** |
| `vendor/LICENSE.coreyhaines-marketingskills` | `LICENSE` | **VERIFIED-EXACT** |

Method: `curl raw.githubusercontent.com/coreyhaines31/marketingskills/2815104/<path>` then `diff` — all identical, including the rename `SKILL.md` → `customer-research.md` documented in ATTRIBUTION.md:44-45.

### visual-iterate — claimed: byte-exact from `op7418/guizang-social-card-skill` @ `main` (fetched 2026-07-03, no commit pin)

| Vendored file | Claimed upstream path | Result |
|---|---|---|
| `references/guizang/validate-social-deck.mjs` | repo root `validate-social-deck.mjs` | **VERIFIED-EXACT** (cmp byte-identical) |
| `references/guizang/qa-checklist.md` | `references/qa-checklist.md` | **VERIFIED-EXACT** (cmp byte-identical) |
| `references/guizang/LICENSE` | `LICENSE` (AGPL-3.0) | **VERIFIED-EXACT** (cmp byte-identical) |

Method: `curl raw.githubusercontent.com/op7418/guizang-social-card-skill/main/<path>` then `cmp`. Caveat: verified against *today's* main (upstream has not moved since fetch); no commit hash exists in ATTRIBUTION.md to make this reproducible if upstream moves.

**Consequence for the migration design**: every vendored file is upstream's own text and is protected by an explicit verbatim/byte-exact claim → **cannot be edited in place** (AC4). Conversely, **all C1 items needing migration live exclusively in the two host-original SKILL.md files and are freely editable** — the migration for these two skills never touches a verbatim-constrained file.

---

## Caveats / Not Found

- No HTML provenance comments exist in either skill (unlike create-role/decide-direction/find-opportunity/when-idle); all provenance here is visible prose.
- `visual-iterate/SKILL.md:12-13` "(doer ≠ judge — same separation this company enforces between workers and verifiers)" is internal design rationale, not external provenance; not inventoried as C1.
- Whether the neutral rewrite of "Reading the catalogs" should keep one sentence acknowledging foreign path conventions (for agent trust in the mapping) is a design decision, not an audit finding.
- Out of scope but adjacent: `design-asset/references/guizang/` holds the sibling vendored guizang set (style-system.md, image-overlay.md, etc.) that qa-checklist.md cross-references; its audit belongs to whoever covers design-asset.
