---
name: visual-iterate
description: >-
  Validate and iteratively refine rendered visual assets before delivery or
  publication. Use after design-asset or gen-image produces an image.
---

# visual-iterate — the loop that earns "done"

A first render is a draft. This skill closes the loop: script gates → visual
review → minimal fix → re-render. The two iron laws: **cheap deterministic
checks run before any judgment call**, and **the author never grades their own
work** (doer ≠ judge — same separation this company enforces between workers
and verifiers).

## Loop state machine (fixed order, every round)

1. **RENDER** — the PNG(s) from design-asset's `render_asset.mjs` or
   gen-image's wrapper. You judge pixels, never HTML source: font fallbacks,
   real contrast, and kerning exist only in the render.
2. **SCRIPT GATES** (deterministic, non-negotiable, run FIRST):
   - guizang-routed cards/decks: run the vendored validator. It bare-imports
     playwright, so stage it next to a node_modules that has it:
     ```
     cp references/guizang/validate-social-deck.mjs "$PLAYWRIGHT_DIR/" &&
     node "$PLAYWRIGHT_DIR/validate-social-deck.mjs" <task-dir|page.html> [--style=swiss|editorial]
     ```
     Rules R1-R9: overflow, footer collision, Swiss bold-display ban,
     min font floor, 4-band density (≥75% fill), display-title caps, browser
     figure-margin drift, visual bounds/bottom whitespace, title-to-content
     gap. Exit 1 = FAIL: fix before any review round. WARN is advisory — read
     it. (A directory target expects `index.html` inside.)
   - every asset, minimum: exact pixel size matches the platform spec, file
     is a real PNG/JPEG, filename follows the output naming convention.
   - Do not skip gates because the render "looks obviously fine" — density
     drift and figure-margin drift are precisely the invisible failures.
3. **REVIEW (doer ≠ judge)** — hand the render to a reviewer that did NOT
   design it: spawn a fresh-context subagent and give it ONLY (a) the PNG(s),
   (b) one line of goal + target platform, (c) the rubric below, verbatim.
   Withhold your design rationale — a reviewer that knows why you did it
   will excuse it. No subagent mechanism available → degraded mode: step
   through the rubric in writing against the PNG, one verdict per item,
   before any self-pass.
4. **MINIMAL FIX** — one finding per edit, surgical `Edit` on the HTML, never
   a file rewrite. Fixing means refining what exists: adding new elements or
   decoration in a fix round is the classic failure (suppress it). Overflow
   gets the graded response (from guizang's control layer): **1-40px**
   nudge/tighten spacing · **40-90px** local compaction · **90-160px**
   compress title/copy · **160px+** change the layout recipe — then re-check
   bottom whitespace didn't swing the other way. Generated-image issues:
   prefer fixing the HTML layer; if you must regenerate, one change + restate
   the full preserve-list (gen-image discipline; regeneration is the slowest,
   least stable move).
5. **RE-RENDER** → back to 2. Keep lineage as `{name}_{n}.html`; record each
   round (findings → action) so a later session can resume the thread.

## Reviewer rubric (pass verbatim to the reviewer)

Output contract: first line `PASS` or `FAIL` — it MUST be `FAIL` if any
[Blocker] or [High] finding exists (a "PASS with a High" is a contradiction;
this was an observed reviewer drift). Then findings, each tagged
**[Blocker] / [High] / [Medium] / [Nit]**. State problems, not prescriptions —
describe what is wrong and its impact, name the pixel region as evidence;
do not dictate the fix. Blocker/High without located evidence doesn't count.

- **360px thumbnail test**: at feed-thumbnail size, is the ONE idea of this
  asset still readable? A cover that fails this fails the asset.
- **Contrast**: body text vs background ≥ 4.5:1; display-size type may pass
  at 3:1. Estimate honestly; borderline = [High].
- **Hierarchy**: exactly one primary focal point; title/subtitle/meta clearly
  stepped; no two elements fighting for first glance.
- **Alignment & spacing**: one grid, spacing steps from one scale; no
  orphaned near-misses (2-3px off reads as sloppy, not intentional).
- **Overflow/clipping/collision**: nothing touches the canvas edge
  unintentionally, nothing overlaps the footer band, no cut glyphs.
- **AI-slop set** (any hit = [High]): purple-blue gradients, three-circle
  icon-grid layouts, everything-centered, uniform bubble radii, emoji as
  design elements, left-color-bar cards, generic hero copy.
- **System identity**: does it pass the declared style system's identity
  test (for guizang work: style-system.md's Swiss/Editorial tests)? Tokens
  actually used, or ad-hoc values snuck in?
- **Platform fit**: exact canvas size, safe areas respected, text inside
  margins.

## Termination (numbers, not vibes)

- **Round cap: 3** per asset (a 4th only if round 3 fixed a [Blocker]).
  Codex-generated backdrops make rounds slow (1-2 min each) — all the more
  reason to fix in HTML.
- **PASS =** all script gates green AND reviewer reports no [Blocker]/[High].
  [Medium]/[Nit] get fixed only if a round is happening anyway.
- **Same finding survives 2 fix attempts** → stop patching that spot: change
  the layout recipe or escalate with the round log. Grinding the same fix is
  how decks die.
- **Regression rule**: a round that introduces a new [Blocker] gets reverted
  to the previous lineage version; take the other fix path instead.

## Reference map

| File | When |
|---|---|
| `references/guizang/validate-social-deck.mjs` | every guizang-routed round, before review |
| `references/guizang/qa-checklist.md` | validator green but the render still smells — the full manual list |

Rubric sources (rewritten, not copied): OneRedOak design-review triage +
problems-over-prescriptions (MIT), gstack design-review thresholds & PASS/FAIL
protocol (MIT), anthropics canvas-design hard checks + no-additions-on-revision
(Apache-2.0), guizang thresholds & overflow grading (AGPL, user-approved
exception), Anthropic pptx fresh-eyes *pattern* (pattern only — its text is
proprietary and none is reproduced here). Details in ATTRIBUTION.md.
