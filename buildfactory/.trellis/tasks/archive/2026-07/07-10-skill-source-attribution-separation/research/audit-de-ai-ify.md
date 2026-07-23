# Research: de-ai-ify provenance/attribution audit

- **Query**: Per-item inventory of every piece of NON-EXECUTION provenance/attribution content in `agents/assets/skills/de-ai-ify/` (host SKILL.md, references/en-*, zh/ vendored skill, vendor/LICENSE.*, ATTRIBUTION.md); execution-closure classification; verbatim verification vs upstream; migration destinations under the vendored-intact constraint.
- **Scope**: internal (full-tree read) + external (upstream raw.githubusercontent.com diff)
- **Date**: 2026-07-10
- **Files in scope**: 14 .md + 3 LICENSE files, ~3,882 lines total. All read in full.

---

## 1. Summary table

| File | Provenance items | Categories | Closure | Verbatim status |
|---|---|---|---|---|
| `SKILL.md` (host, 80 ln) | **2** (H1 `## Sources` section L75-79; H2 "vendored" adjective L40) | C1 (+C2 duplicated in ATTRIBUTION) | IN-CLOSURE (entry, always read) | HOST-ORIGINAL (editable) |
| `ATTRIBUTION.md` (39 ln) | 1 (A1: whole file) | C2 | BYPASS (only pointed at from H1) | HOST-ORIGINAL (editable) |
| `references/en-humanizer.md` (622 ln) | 3 (E1 frontmatter L1-20; E2 L24; E3 `## Reference` L618-623) | C2 (E1) / C1-nature frozen (E2, E3) | IN-CLOSURE (EN route, required) | **VERIFIED-EXACT** vs `blader/humanizer` `main` `SKILL.md` |
| `references/en-ai-writing-detection.md` (200 ln) | 1 (D1 `Sources:` line L5) | C1-nature frozen | IN-CLOSURE (EN route, required) | **VERIFIED-EXACT** vs `coreyhaines31/marketingskills` `main` |
| `zh/SKILL.md` (923 ln) | 3 provenance (Z1 frontmatter L1-18; Z2 L858; Z3 `## 参考来源` L920-922) + 5 functional-source (Z4-Z8, C3) | C2 (Z1) / C1-nature frozen (Z2, Z3) / C3 | IN-CLOSURE (ZH route, required, "follow as-is") | **VERIFIED-EXACT** vs `LifelongLazyLearner/qu-ai-wei` `main` |
| `zh/references/patterns.md` (985 ln) | 3 (P1 L302; P2 L961-972; P3 L985) | C1-nature frozen | IN-CLOSURE (ZH step 2, required) | **VERIFIED-EXACT** |
| `zh/references/platform-patterns.md` (265 ln) | 1 (PP1 L28) + F3 (C3 word-list calibration) | C1-nature frozen / C3 | IN-CLOSURE (conditional: H-group registers) | **VERIFIED-EXACT** |
| `zh/references/sources.md` (55 ln) | 1 (S1: whole file = upstream's own provenance file) | C2 (with C3 subsections L21-32, L44-48) | CONDITIONAL IN-CLOSURE (linked from zh/SKILL.md L293 CCL path, L830 #49, L922) | **VERIFIED-EXACT** |
| `zh/references/punctuation.md` (117 ln) | 0 pure provenance (PU1 evidence-base L5 = C3) | C3 | IN-CLOSURE (conditional) | **VERIFIED-EXACT** |
| `zh/references/whitelists.md` (133 ln) | 0 (header self-ref only, F8) | C3 | IN-CLOSURE (conditional: §5 whitelist checks) | **VERIFIED-EXACT** |
| `zh/references/brand-voice.md` (189 ln) | 0 (header self-ref only, F8) | C3 | IN-CLOSURE (conditional: brand register) | **VERIFIED-EXACT** |
| `zh/references/syntax.md` (59 ln) | 0 (header self-ref only, F8) | C3 | IN-CLOSURE (conditional) | **VERIFIED-EXACT** |
| `zh/references/examples.md` (83 ln) | 0 (header self-ref only, F8) | C3 | IN-CLOSURE (conditional) | **VERIFIED-EXACT** |
| `zh/references/reference-models.md` (70 ln) | 0 (header self-ref only, F8) | C3 | IN-CLOSURE (conditional) | **VERIFIED-EXACT** |
| `vendor/LICENSE.blader-humanizer` | 1 (V1) | C2 | BYPASS | **VERIFIED-EXACT** vs upstream `LICENSE` |
| `vendor/LICENSE.coreyhaines-marketingskills` | 1 (V2) | C2 | BYPASS | **VERIFIED-EXACT** vs upstream `LICENSE` |
| `vendor/LICENSE.qu-ai-wei` | 1 (V3) | C2 | BYPASS | **VERIFIED-EXACT** vs upstream `LICENSE` |

**HTML comments: none anywhere in the tree** (grep `<!--` = 0 hits).

Category legend: C1 = pure provenance, should migrate out of execution text; C2 = legal/maintenance info that must be preserved in a bypass file; C3 = functional source rule that must STAY.
"C1-nature frozen" = content that would be C1 if host-authored, but lives inside a byte-exact vendored file and **cannot be edited without breaking the vendored-intact claim** (R5/AC4).

---

## 2. Verbatim verification (method + results)

Method: `curl` raw files from `raw.githubusercontent.com` (`main` branch, 2026-07-10) and `diff` against the local tree.

| Local file | Upstream file | Result |
|---|---|---|
| `references/en-humanizer.md` | `blader/humanizer` → `SKILL.md` (v2.8.2) | byte-identical |
| `references/en-ai-writing-detection.md` | `coreyhaines31/marketingskills` → `skills/seo-audit/references/ai-writing-detection.md` | byte-identical |
| `zh/SKILL.md` | `LifelongLazyLearner/qu-ai-wei` → `SKILL.md` (v0.8.2) | byte-identical |
| `zh/references/*.md` (all 9) | `qu-ai-wei` → `references/*.md` | byte-identical, 9/9 |
| `vendor/LICENSE.*` (all 3) | each repo's `LICENSE` | byte-identical, 3/3 |

**Every vendored byte is VERIFIED-EXACT (16/16 files).** Consequence: **all provenance text inside `references/en-*` and `zh/**` is upstream's own** — it can only be handled by (a) registering it as an allowed vendored exception in the AC6 scanner, or (b) the "provenance-free execution layer generated from the vendored canon" approach the PRD R5 anticipates. It cannot be migrated by editing those files.

Caveat: ATTRIBUTION.md pins only "2026-07-01, `main`" — **no commit SHA**. Today's match means upstream has not moved (or moved and returned) since fetch; future verbatim verification is against a moving target until a SHA/checksum is recorded. There is also **no CI test enforcing byte-exactness** — `test_de_ai_ify_integrity.py` only checks link resolution.

---

## 3. Execution-closure map

Entry point: host `SKILL.md` (always loaded on invocation).

- **EN route** (host L38-39, L65-66): `references/en-humanizer.md` + `references/en-ai-writing-detection.md` — both REQUIRED reads.
- **ZH route** (host L40-43, L55-56, L67): `zh/SKILL.md` REQUIRED ("Follow it as-is"). zh/SKILL.md then directs:
  - `zh/references/patterns.md` — step-2 rule detail ("完整定义...见", decision tree "命中后读对应 reference 核对") → effectively always read on any ZH rewrite.
  - `zh/references/platform-patterns.md` — when H-group registers activate (自媒体/文学/流行语/B站); also linked from patterns.md H-group index.
  - `zh/references/whitelists.md` — arbitration §5 hard exception + 中英混排 section; host SKILL.md also cites it directly (L67).
  - `zh/references/punctuation.md` — 标点 second layer; host SKILL.md also cites it directly (L56).
  - `zh/references/brand-voice.md` — brand-ad register or brand-vs-自媒体 ambiguity.
  - `zh/references/syntax.md` — 语序 full diagnosis.
  - `zh/references/examples.md` — worked example for output format.
  - `zh/references/reference-models.md` — self-audit contrast anchors.
  - `zh/references/sources.md` — **conditional**: upstream's own header says "第零步/第一步不读此文件…按需读取", but zh/SKILL.md L293 sends the agent here as a *runtime verification path* (CCL corpus check when a rewrite is uncertain), and L830 (#49 word-list calibration) + L922 (bibliography) also link it. So it is reachable in normal execution, low probability.
- **BYPASS** (nothing in the execution text instructs reading them): `ATTRIBUTION.md` (only *mentioned* in host L77 "see `ATTRIBUTION.md`" — a pointer inside the Sources section, itself slated for migration), `vendor/LICENSE.*` (only pointed at from ATTRIBUTION.md L15).

Net: **every .md except ATTRIBUTION.md is in (at least conditional) execution closure.** The only host-editable in-closure text is host `SKILL.md`.

---

## 4. Per-item detail

### 4.1 Host-editable items (real migration targets)

**H1 — host `SKILL.md` L75-79, `## Sources` section** — IN-CLOSURE — **C1** (content is C2 but fully duplicated in the bypass file)
> "## Sources / Vendored (MIT); see `ATTRIBUTION.md`. Upstream lives untouched under `references/` and `zh/`; this file is the only adaptation layer (language routing, voice-from-`/company`, marketing register). Sync by re-copying upstream, not editing it."

- Contains: vendored/license note, ATTRIBUTION pointer, host-adaptation summary, upstream-sync policy. None of it is needed at runtime.
- Duplication check (safe-to-delete audit): "Vendored (MIT)" = ATTRIBUTION table L9-13; "see ATTRIBUTION.md" = self; "Upstream lives untouched" = ATTRIBUTION L4-6 + L22; "only adaptation layer (language routing, voice-from-/company, marketing register)" = ATTRIBUTION L24-31 verbatim coverage; "Sync by re-copying upstream, not editing it" = ATTRIBUTION L33-38. **Zero unique information** → the section can be deleted outright with a diff note mapping it to ATTRIBUTION.md (satisfies R2 traceability / AC8).
- Proposed destination: delete from SKILL.md; canonical copy stays in `ATTRIBUTION.md` (merge, don't create a second truth source). The sync-policy sentences arguably belong in a `MAINTENANCE.md` per R2's default mapping — but ATTRIBUTION.md already holds them ("Upstream sync" section), and R2 says prefer merging into the existing bypass file.
- Constraint: none (host file). Integrity test: deleting the section removes the inline `` `ATTRIBUTION.md` `` mention — the test only *checks* mentions that exist, so removal is safe. Do NOT relocate ATTRIBUTION.md out of the skill dir while the mention remains, or the test fails (host-SKILL inline-code mentions are resolved).

**H2 — host `SKILL.md` L40-41, "vendored" adjective inside the ZH routing rule** — IN-CLOSURE — **C1 (one word) inside a C3 sentence**
> "**Chinese** → `zh/SKILL.md`, a self-contained **vendored** skill with its own control layer (语体矩阵 … 冲突仲裁顺序 §1-6; 过度消毒反制) driving `zh/references/` … Follow it as-is for Chinese drafts."

- The sentence is a functional routing rule (R4: must survive). "vendored" is the only provenance token; rewrite as "a self-contained skill with its own control layer" (pure behavior). The vendored fact is already in ATTRIBUTION.md L20-22.
- Constraint: none (host file). No link changes.

**A1 — `ATTRIBUTION.md` L1-39 (whole file)** — BYPASS — **C2**
- The designated bypass file: vendor policy statement, source table (3 repos, licenses, fetch dates), structure notes, "What our SKILL.md adds", "Upstream sync" instructions incl. known-divergence watch item (dash-removal default).
- Action: keep; it is the merge target for H1/H2. Must never be silently deleted (R2). Note it mixes attribution (R2's ATTRIBUTION role) with maintenance/sync content (R2's MAINTENANCE role) — design must either accept the mix or split, but must not fork into two conflicting truth sources.

**V1/V2/V3 — `vendor/LICENSE.blader-humanizer`, `vendor/LICENSE.coreyhaines-marketingskills`, `vendor/LICENSE.qu-ai-wei`** — BYPASS — **C2**
- Full MIT texts: © 2025 Siqi Chen, © 2025 Corey Haines, © 2026 @LifelongLazyLearner. All byte-identical to upstream `LICENSE` files.
- Action: keep verbatim (R5). MIT requires the copyright + permission notice to accompany copies — these files are the compliance mechanism; they must keep materializing with the skill.

### 4.2 Upstream-frozen in-closure provenance (cannot edit; needs a design decision: scanner-allowlist registration vs shadow execution layer)

**E1 — `references/en-humanizer.md` L1-20, YAML frontmatter** — IN-CLOSURE (EN) — **C2, frozen**
> `name: humanizer` / `version: 2.8.2` / description "…Based on Wikipedia's comprehensive 'Signs of AI writing' guide…" / `license: MIT` / `compatibility: any-agent` / `allowed-tools: … AskUserQuestion`

- Upstream identity + license declaration + methodology origin, plus upstream harness metadata (`allowed-tools` incl. `AskUserQuestion`) that does not match host runtime (host explicitly overrides the AskUserQuestion voice path via `/company`). An executing agent sees all of it.

**E2 — `references/en-humanizer.md` L24** — IN-CLOSURE (EN) — **C1-nature, frozen**
> "This guide is based on Wikipedia's 'Signs of AI writing' page, maintained by WikiProject AI Cleanup."

**E3 — `references/en-humanizer.md` L618-623, `## Reference` section** — IN-CLOSURE (EN) — **C1/C2-nature, frozen**
> "This skill is based on [Wikipedia:Signs of AI writing](…), maintained by WikiProject AI Cleanup. The patterns documented there come from observations of thousands of instances… Key insight from Wikipedia: 'LLMs use statistical algorithms to guess what should come next…'"

- Note the closing quote doubles as a compact statement of the skill's core theory; a shadow execution layer could keep the quote and drop the sourcing sentence, but the vendored original cannot be touched.

**D1 — `references/en-ai-writing-detection.md` L5** — IN-CLOSURE (EN) — **C1-nature, frozen**
> "Sources: Grammarly (2025), Microsoft 365 Life Hacks (2025), GPTHuman (2025), Walter Writes (2025), Textero (2025), Plagiarism Today (2025), Rolling Stone (2025), MDPI Blog (2025)"

- Pure research-source list, zero execution value. Single line near the top of a required EN read.

**Z1 — `zh/SKILL.md` L1-18, YAML frontmatter** — IN-CLOSURE (ZH) — **C2, frozen**
> `name: qu-ai-wei` / `version: 0.8.2` / `license: MIT` / `compatibility: cursor claude-code codex opencode kiro factory slate hermes` / `allowed-tools: … AskUserQuestion`

- Upstream identity/license/harness metadata. Also note the description defines `/qu-ai-wei` slash-command triggers that don't exist in host runtime (functional noise, not provenance).

**Z2 — `zh/SKILL.md` L858** — IN-CLOSURE (ZH, rule-count overview) — **C1-nature, frozen**
> "I 幻觉与格式残留 (#45-48):4 条 — 受中文维基《AI生成文的特徵》启发"

**Z3 — `zh/SKILL.md` L920-922, `## 参考来源` section** — IN-CLOSURE (ZH, end of required file) — **C1/C2-nature, frozen**
> "叶圣陶「写话」主张(1924/1934)/ Wikipedia: Signs of AI writing / 吕叔湘《现代汉语八百词》 / 朱德熙《语法讲义》 / 国标 GB/T 15834-2011 / yage.ai《写作中的 AI 味是哪儿来的》 / 《咬文嚼字》年度榜单及刷新机制 —— 全部见 [references/sources.md](references/sources.md)。"

- Bibliography section with a markdown link to `references/sources.md` that the integrity test resolves — the link (and therefore sources.md's presence in the materialized tree) is load-bearing.

**P1 — `zh/references/patterns.md` L302** — IN-CLOSURE (ZH) — **C1-nature, frozen**
> "也覆盖伪洞察枢纽（humanizer #27 中文版）：…"

- Cross-skill methodology origin ("Chinese version of humanizer #27") embedded in rule #19's definition.

**P2 — `zh/references/patterns.md` L961-972, `## 故意不收录的规则` closing note** — IN-CLOSURE (ZH) — **C1-nature, frozen (mixed with C3)**
> L972: "这些都是英文去 AI 腔工具会覆盖、但中文语境用不上的类别，不是'继承自'哪个工具 —— 而是独立评估后选择不纳入。"

- The list itself (Title Case / curly quotes / copula avoidance … not applicable to Chinese) is functional scope-definition (C3); the closing design-history sentence about inheritance/independent evaluation is provenance.

**P3 — `zh/references/patterns.md` L985** — IN-CLOSURE (ZH) — **C1-nature, frozen**
> "I 幻觉与格式残留(#45-48):4 条 — 受中文维基《AI生成文的特徵》启发" (same note as Z2, duplicated in the reference file's count overview)

**PP1 — `zh/references/platform-patterns.md` L28** — IN-CLOSURE (conditional, H-group) — **C1-nature, frozen**
> "格言公式（humanizer #32 中文版）：把论点包装成可转发金句…"

**S1 — `zh/references/sources.md` L1-55 (whole file)** — CONDITIONAL IN-CLOSURE — **C2, frozen (contains C3 subsections)**
- Upstream's own dedicated provenance/philosophy file: 叶圣陶 philosophy roots (L5-9), Wikipedia EN/ZH signs-of-AI-writing credits (L11-13), grammar authorities 吕叔湘/朱德熙 (L15-19), honest-declaration that rules were NOT corpus-verified (L23), CCL/BCC corpus how-to (L21-32), GB/T 15834-2011 punctuation standard note (L34-37), yage.ai article credit for #39-#42 (L39-41), 《咬文嚼字》annual refresh mechanism + 2024/2025 lists (L43-48), community-contribution invitation (L52).
- Mixed nature: **L21-32 (CCL corpus usage) and L44-48 (flow-word lists) are functional at runtime** — zh/SKILL.md L293 explicitly routes uncertain rewrites here, and #49's word vintage matters for judgment. The rest is pure provenance.
- Upstream itself already designed it as a mostly-bypass file ("SKILL.md 在第零步/第一步不读此文件…按需读取" L3). It cannot be removed: 3 links from zh/SKILL.md would go dead (integrity test) and vendored-intact would break.
- L48 mentions upstream-repo files not vendored here (`.cursorrules`, `WARP.md`, `README.md`) — plain text, not links, so the integrity test does not check them; no action possible (frozen).

### 4.3 Functional source rules that must STAY (C3) — registered here so the AC6 scanner can allowlist them

- **F1 — host `SKILL.md` routing/pointer mesh** (L13-14, L29-31, L38-43, L52-56, L65-67, L70-72): all `references/en-*.md`, `zh/SKILL.md`, `zh/references/punctuation.md`, `zh/references/whitelists.md` pointers, the EN pattern numbers (#2/#6/#21) and ZH mechanism names (语体矩阵/冲突仲裁顺序/过度消毒反制/逐处自查问). These reference upstream *format/content as runtime input* — R4 explicitly protects them.
- **F2 — `zh/SKILL.md` L293**: CCL corpus (corpus.pku.edu.cn) reverse-verification instruction + pointer to sources.md「现代汉语经验基线」— a runtime tool, not provenance.
- **F3 — `zh/references/platform-patterns.md` L172-179**: 《咬文嚼字》-calibrated word-half-life tables incl. "2026-04 刷新" vintage note — the authority and vintage are part of the judgment rule (#49).
- **F4 — `zh/references/punctuation.md` L5, L16, L27, L48, L109-117**: 三联/南方周末/财新 observation baselines — cited as diagnostic evidence inside the rules themselves.
- **F5 — `zh/SKILL.md` L414-427, L473-481**: GB/T 15834-2011, W3C CLREQ, sparanoid self-description, pangu.js/pangu.py pointers, "ChatGPT hyphen"/Sam Altman/cross-model dash observations — all evidence and boundary definitions for the spacing/dash rules.
- **F6 — Tim Cook letter examples**: `zh/SKILL.md` L650, `zh/references/patterns.md` L538/L559-565 — attributed worked examples (product behavior), not skill provenance.
- **F7 — `zh/SKILL.md` L642**: "QWEN 在集成测试中出现的…捏造细节" — upstream development-history flavored, but functions as the concrete counter-example defining the "AI 假装成一个真实但不存在的人" failure class. Frozen anyway.
- **F8 — headers of all 9 `zh/references/*.md`**: "本文件是 qu-ai-wei 的 X reference。SKILL.md 在…时读取本文件" — upstream self-identification + read-routing. The read-routing half is functional; the `qu-ai-wei` name is upstream identity (frozen). Consistent pattern across brand-voice/examples/patterns/platform-patterns/punctuation/reference-models/sources/syntax/whitelists.
- **F9 — `references/en-humanizer.md` L556**: "Edits made before November 30, 2022. ChatGPT's public launch…" — a detection heuristic, not provenance.

---

## 5. ATTRIBUTION.md coverage cross-check

Verified claims:
- "the reference material is vendored **verbatim**" — **VERIFIED** (16/16 byte-identical).
- `zh/` "vendored **intact**" — **VERIFIED** (SKILL.md + all 9 references byte-identical; internal cross-links all resolve).
- License attributions match upstream LICENSE files exactly (names, years).
- Source table paths/repos/versions are accurate (en-humanizer carries `version: 2.8.2`, zh carries `version: 0.8.2`, matching the table).

Gaps / imprecision (record only, no recommendation):
1. **No commit SHA or checksum** — fetch pinned only as "2026-07-01, `main`"; verbatim claims are re-verifiable today but not tamper-evident over time; no test enforces byte-exactness.
2. "The only original file is `SKILL.md`" (L6) — strictly, `ATTRIBUTION.md` itself and the `vendor/LICENSE.*` copies are also host-placed artifacts (the license *texts* are upstream verbatim).
3. ATTRIBUTION does not restate upstream's second-order sources (Wikipedia is mentioned for humanizer; Grammarly-et-al for en-ai-writing-detection and 叶圣陶/yage.ai/咬文嚼字 for qu-ai-wei live only inside the vendored files/sources.md). Arguably correct layering; noted for completeness.
4. No statement of how the *host* handles upstream frontmatter mismatches (e.g., upstream `allowed-tools: AskUserQuestion` vs host's `/company` voice override is described, but the frontmatter itself still ships to the agent).

---

## 6. Integrity-test interactions (`agent/tests/test_de_ai_ify_integrity.py`)

What the test does: materializes growth's loadout via `resident_loadout.materialize_for`, walks the materialized `de-ai-ify` tree, and asserts every markdown link `](x.md)` in **every** .md resolves, plus every inline-code `` `x.md` `` mention in the **host SKILL.md only**. URLs/anchors/non-.md are skipped. It does NOT check byte-exactness.

Migration risk flags:
1. **`zh/references/sources.md` cannot be dropped or relocated** — zh/SKILL.md links it at L293, L830, L922 (checked in all files). Dropping the "provenance file" breaks the test AND vendored-intact.
2. **Host inline mentions are checked**: currently `references/en-humanizer.md`, `references/en-ai-writing-detection.md`, `zh/SKILL.md`, `zh/references/punctuation.md`, `zh/references/whitelists.md`, `ATTRIBUTION.md`. Deleting the H1 Sources section removes the `ATTRIBUTION.md` mention → safe (fewer refs). Relocating/renaming ATTRIBUTION.md while the mention survives → test fails. Adding a `MAINTENANCE.md` and mentioning it in host SKILL.md is safe only if the file materializes (copytree copies the whole dir, so yes) — but note R2 forbids execution text from requiring bypass reads, so a new mention should not be added to SKILL.md at all.
3. **Any shadow/execution-layer scheme must keep the vendored tree link-closed**: renaming vendored files or splitting zh/ breaks internal links (patterns↔platform-patterns, reference-models→brand-voice, examples→brand-voice, SKILL→all 9) and the vendored-intact claim simultaneously.
4. Vendored files' inline-code .md mentions are deliberately NOT checked (test comment L69-71), so upstream prose like sources.md's `WARP.md / README.md` (files that don't exist here) does not fail — do not "fix" that.
5. `vendor/LICENSE.*` are not .md → invisible to this test; their continued materialization is only guaranteed by copytree, nothing asserts it. If AC6/R6 adds a bypass-file materialization check, LICENSE files are currently untested surface.

---

## 7. Counts

- **C1 host-editable (actionable migrations): 2** — H1 (SKILL.md L75-79), H2 (SKILL.md L40 "vendored"). Both migrate into the existing `ATTRIBUTION.md` (already fully duplicated there; deletion + diff-mapping suffices).
- **C1-nature but frozen in vendored files: 9** — E2, E3, D1 (EN route, always read on EN drafts); Z2, Z3, P1, P2, P3 (ZH route); PP1 (H-group conditional). Cannot be edited (AC4); need scanner allowlisting or the R5 shadow-layer design.
- **C2 (preserve in bypass): 7** — A1, V1, V2, V3 (host-side, already bypass); E1, Z1 (frozen frontmatter, in-closure); S1 (frozen, conditional in-closure).
- **C3 (functional, must stay): F1-F9** across host SKILL.md, zh/SKILL.md, patterns/platform-patterns/punctuation/whitelists/brand-voice/reference-models/examples/syntax.

## Caveats / Not found

- No HTML provenance comments exist in this skill (unlike create-role/decide-direction/find-opportunity/when-idle) — the de-ai-ify problem is (a) a visible host Sources section and (b) upstream-owned provenance inside byte-exact vendored files. The second class is the PRD's hardest case (R5) and de-ai-ify is likely its main exemplar.
- Verbatim verification is against upstream `main` on 2026-07-10; without a pinned SHA I cannot prove upstream hasn't force-moved since the 2026-07-01 fetch — but a byte-identical match across 16 files makes divergence effectively ruled out.
- I did not verify materialization behavior beyond reading the test (did not run pytest); the copytree claim comes from the PRD's Confirmed Facts and the test's use of `resident_loadout.materialize_for`.
