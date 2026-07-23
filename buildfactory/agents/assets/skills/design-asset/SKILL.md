---
name: design-asset
description: >-
  Build text-led static visual assets in HTML/CSS and render them to PNG. Use
  for social cards, covers, carousels, and typography-heavy graphics; not
  standalone imagery.
---

# design-asset — HTML/CSS static visual assets

You produce publication-quality static images by writing HTML/CSS on a fixed-size
canvas and rendering it to PNG. This path is deterministic, revisable, and reliable
for text — image-generation models are not (small/CJK text comes out mangled).

## When me, when a sibling

- Text or layout carries the asset (title cards, checklists, comparisons, covers,
  carousels) → **me**.
- A photorealistic/illustrative picture IS the asset, or a canvas needs an
  illustration/backdrop → **gen-image**; then continue here, layering type and
  components over the generated image (`background-image` or absolutely-positioned
  `<img>` under the text layer).
- Before delivering anything → hand the HTML + PNG to **visual-iterate** for the
  check-revise loop. Do not self-approve in the same breath you designed.

## Workflow (order is the discipline: intent → tokens → layout → pixels)

1. **Read `/company` first**: positioning, brand voice, current campaign. Brand
   constraints beat every default below. No voice recorded yet → that is a
   mine-customer-voice / charter matter, not a reason to invent a one-off style.
2. **Fix the canvas** from the platform table below. One deck = one aspect ratio.
3. **Commit to ONE style system** (routing below). Never mix systems inside a
   deck — mixing reads as noise, not richness.
4. **Layout before pixels**: sketch the page as an ASCII wireframe or a one-line
   content plan per page (what is the ONE idea of this page?). Only then write CSS.
5. **Write the token sheet first** (`:root` custom properties) per
   `references/superdesign/token-checklist.md` — name the theme, note what you
   referenced. Components consume only tokens; no ad-hoc hex sprinkled in
   rules. Reconciling the two token vocabularies: guizang variables
   (`--paper/--ink/--grey-N/--accent`) are the WORKING tokens the recipes
   consume; declare the checklist's shadcn names as aliases of them. Where a
   style bans a checklist item (Swiss: no shadows, no radius), declare it as
   `none`/`0` with a comment — an omission must be a visible decision.
   Fonts: declare full fallback chains ending in a system CJK face
   (`"Noto Sans SC", "PingFang SC", sans-serif`); the skill vendors no font
   files, so cross-OS drift is real — treat exotic single-font stacks as
   unavailable.
6. **Build the HTML**: one canvas element per page, fixed px size,
   `overflow: hidden`. Deck pages live in one file, one canvas each.
   For guizang-routed work, START FROM the vendored seed templates
   `references/guizang/assets/template-swiss-card.html` /
   `template-editorial-card.html` — every guizang doc ("the seed template
   ships…", typed classes like `.h-statement`/`.t-cat`/`.card-fill`) assumes
   them. Copy the template next to your work file; don't rebuild the classes
   from prose. guizang markup uses `<section class="poster xhs">` — add
   `canvas` alongside (`class="canvas poster xhs"`) so the render selector
   matches.
7. **Render**: `node scripts/render_asset.mjs page.html output/xhs-01-cover.png
   --selector .canvas --width 1080 --height 1440` (multi-match auto-numbers).
   The script waits for `networkidle` + `document.fonts.ready` and exports at
   2x. If it exits 2, run the bootstrap command it prints. Web root = the
   HTML's own directory: `assets/` and fonts must sit NEXT TO the HTML file,
   not next to the script.
8. **Hand to visual-iterate.** Iterate on the HTML (surgical edits), re-render;
   keep lineage as `{name}_{n}.html` when forking versions. If visual-iterate
   is not materialized in this environment, the minimum bar before delivering:
   run the style system's identity test, LOOK at the rendered PNG yourself,
   and check the guizang hard gates (overflow, footer collision, density,
   360px-thumbnail readability).

## Canvas specs (values: guizang platform-specs — third-party production values
as of 2026-07, NOT re-verified against official platform docs; recheck if a
platform rejects an upload; full safe-areas/naming/cover-structure rules in
`references/guizang/platform-specs.md`)

| Target | Size | Ratio | Notes |
|---|---|---|---|
| Xiaohongshu card/deck | 1080×1440 | 3:4 | side margin 72-96px, top 72-112, bottom 80-120; 1 cover + 4-8 pages; PNG |
| WeChat cover pair | 2100×900 + 1080×1080 | 21:9 + 1:1 | always generate as a pair in one HTML; square gets a 4-10-char short title, not the full headline. WeChat's listed ratio is 2.35:1 (≈2115×900) — ~1% wider than 21:9, so keep nothing meaningful within ~10px of the left/right edges (crop tolerance) |
| og-image | 1200×630 | 1.91:1 | keep title inside center ~1000px |
| X/Twitter card | 1200×675 | 16:9 | |

## Style routing (pick ONE, by content type)

- **Chinese social cards/decks (xiaohongshu, WeChat)** → guizang system:
  `references/guizang/style-system.md` (Editorial Magazine×E-ink vs Swiss
  International — run its identity tests), palettes ONLY from
  `references/guizang/theme-presets.md` (no custom hex — the whitelist is the
  taste floor), page layouts from `references/guizang/layout-recipes.md`
  (M01-M16 Editorial / S01-S06 Swiss), reusable blocks from
  `references/guizang/components.md`, backgrounds from
  `references/guizang/background-systems.md`. Arbitrations where guizang docs
  conflict or trap (learned by blind test):
  - Cover-title size: components.md's validated CJK size bands WIN over
    style-system.md's generic 84-128px range. Before committing a display
    size, compute line width (chars × size + tracking) against the content
    column; shrink until it fits — do not eyeball.
  - S01 "full accent background" branch: all card components and grey tokens
    assume a paper background. Take the paper variant unless you are
    deliberately hand-building inverse components.
  - Density rules (content fill ≥75% canvas height, no whitespace band >15%)
    apply to BOTH Editorial and Swiss — the validator checks them regardless.
  - The one-issue-element-per-poster rule: a `.chrome-min` top row IS the
    issue element; a bare `.t-cat` category label is not. Top label + bottom
    points-strip on a cover is legal; two chrome rows is not.
  - A single standalone card is a valid deliverable — platform-specs' "1
    cover + 4-8 pages" is the recommended deck shape, not a minimum.
- **Western/English or non-card formats (og-image, banners, quote cards)** →
  `references/jiji262/design-styles.md` (10 named design languages with full
  font stacks/grids/avoid-lists; use its Advisor mode to propose 2-3 directions)
  + hard thresholds from `references/jiji262/design-principles.md`.
- **Need a fast coherent palette+font pairing** → pick one of the 10 specs in
  `references/theme-factory/themes/` and apply it yourself. Upstream flow asks
  the user to choose; you choose autonomously: match theme mood to content
  (e.g. tech-innovation for product/launch, golden-hour for lifestyle) and
  record which one you picked and why.
- **Always, before any of the above**: read
  `references/anthropic-frontend-design/upstream-SKILL.md` once per session — it is the
  base discipline (bold aesthetic commitment, 4-6 token color system, motion
  restraint, self-critique pass against the brief). Within that vendored
  subtree, upstream mentions of `SKILL.md` mean
  `references/anthropic-frontend-design/upstream-SKILL.md` here.

## Suppressed defaults (these are the mistakes you make when unguided)

- No Bootstrap/Tailwind default blue as brand color. No purple-blue gradients,
  no three-circle-icon feature grids, no uniformly rounded cards, no emoji as
  design elements, no left-color-bar cards — the recognizable AI-slop set.
- No Inter/Roboto/system-ui by reflex. Choose from the style system's stack or
  jiji262's curated lists; a deliberate serif or mono is usually stronger.
- Figure-ground contrast for isolated assets: light component → dark/tinted
  backdrop, dark component → light backdrop. Never same-value on same-value.
- Web-app vocabulary does not apply: no hover states, no responsive breakpoints,
  no a11y focus rings. The canvas is print. Design like a poster, not a page.
- If you load CDN Tailwind alongside component CSS, guard overridden properties
  with `!important` (cascade collisions are silent). Prefer no CDN at all:
  hand-write the CSS; the render server serves local files only.
- One idea per page. If a page needs a paragraph of explanation, split it.

## Hard rules (deterministic, checkable)

- Fixed canvas: exact px width/height, `overflow: hidden`, footer pinned with
  `margin-top: auto` in a flex column — never `position: absolute` over
  growing content.
- No text overflow, no edge-touch, no footer collision. Measure overflow before
  fixing: 1-40px nudge, 40-90px local compaction, 90-160px compress title/copy,
  160px+ change recipe (grading from guizang; visual-iterate enforces it).
- Originals into `assets/` (next to the HTML — the render server's web root);
  `object-fit: contain` for UI screenshots/dense text, `cover` only when
  cropping is safe (placement rules in platform-specs).
- Output naming (matches upstream docs and validator): `output/xhs-01-cover.png`,
  `output/xhs-02-<topic>.png`, `output/wechat-21x9-cover.png`,
  `output/wechat-1x1-cover.png`.

## Reference map (read on demand, one hop)

| File | When |
|---|---|
| `references/anthropic-frontend-design/upstream-SKILL.md` | always once — base aesthetics discipline |
| `references/guizang/style-system.md` · `theme-presets.md` · `layout-recipes.md` · `components.md` · `background-systems.md` · `platform-specs.md` | Chinese social cards/decks |
| `references/guizang/assets/template-swiss-card.html` · `template-editorial-card.html` | seed templates — the starting markup for guizang work (carry all typed classes) |
| `references/guizang/assets/magazine-bg-webgl.js` | Editorial atmosphere layer (background-systems assumes it) |
| `references/guizang/image-overlay.md` | required gate for layout M16 / anti-pattern D (image-led covers) |
| `references/guizang/upstream-SKILL.md` | upstream control layer — consult when a guizang reference cites a rule you can't find |
| `references/jiji262/design-styles.md` · `design-principles.md` | Western/English assets, style proposals, numeric thresholds |
| `references/theme-factory/themes/*.md` | quick palette+font pairing |
| `references/superdesign/token-checklist.md` | every asset — token sheet checklist |

Upstream files cited by guizang docs but NOT vendored (live-photo-production,
screenshot-treatment, qa-checklist, title-shortener, map-component, portrait-fill,
category-cookbook, content-planning, production-workflow): those citations are
INERT wherever they appear in the vendored sub-documents — Live Photo and
analytics workflows are deferred capabilities; qa-checklist ships with
visual-iterate. Also inert: platform-specs' "Final Response Media" section
("In Codex desktop…") — upstream product residue, does not apply here.
