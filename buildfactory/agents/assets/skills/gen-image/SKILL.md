---
name: gen-image
description: >-
  Generate or edit standalone imagery with provisioned image models. Use for
  illustrations, photos, backdrops, and visual series; route text-led layouts
  to design-asset.
---

# gen-image — prompt + invoke image models

Two layers: a vendored PROMPT-craft skill (smixs) that turns intent into a
model-ready prompt, and a thin INVOCATION wrapper that actually produces the
file. Keep them separate in your head: bad results are usually a prompt-layer
problem, not a tool problem.

## When me, when a sibling

- Illustration, backdrop, hero visual, photo-style shot, character/product
  series → **me**.
- Any asset that carries typography (titles, lists, quotes, CJK text of any
  size) → **design-asset**. Image models mangle small and CJK text; the HTML
  route renders it perfectly. When a canvas needs a generated backdrop:
  generate it here, then hand the file back to design-asset for the text layer.
- Judging/refining a generated image → **visual-iterate** (give it the prompt
  AND the preserve-list so revisions re-anchor what must not drift).
- Never AI-generate a product UI screenshot — models hallucinate UI. Use a
  real screenshot at 2x via design-asset instead.

## Prompt layer (vendored smixs skill — follow its reading order)

Open `references/smixs-image/upstream-SKILL.md` and obey its mandatory reading order:
`models.md` → the ONE model file you picked → `golden-rules.md` → task-shaped
modules (text-rendering / editing / characters / multi-panel / patterns/…).
Its `patterns/ui-social.md` and `patterns/poster-illustration.md` map 1:1 to
our social-asset work. Inside vendored reference subtrees, upstream mentions
of `SKILL.md` mean `references/smixs-image/upstream-SKILL.md` or
`references/codex/upstream-SKILL.md` here.

Host adaptations:

- **Executor reality**: our wrapper calls the OpenAI image API (and Codex,
  which is also gpt-image under the hood). So by default write **GPT Image
  syntax** (5-slot template from `gpt-image.md`). Use `nano-banana.md` syntax
  only if a Gemini image tool is actually provisioned in your environment —
  check before writing NB-specific prompts, don't assume.
- **Language note**: smixs files mix English and Russian. The Russian
  passages are normative content, not noise — read them as-is (you read
  Russian natively; no translation step needed).
- smixs "Output format" (Model/Quality/Size header + prompt block) stays —
  produce it, then feed the prompt text to the wrapper yourself.

## Invocation layer (`scripts/generate_image.py`)

```
python3 scripts/generate_image.py --prompt "<prompt>" --out output/hero.png \
    [--size 1080x1440] [--model gpt-image-1-mini] [--quality low] \
    [--ref prev.png] [--timeout 300]
```

- **Primary path = OpenAI API** (`OPENAI_API_KEY`). Default model
  `gpt-image-1-mini`, quality `low` — the scouting tier.
- **Side path = Codex CLI** (ChatGPT subscription): set
  `GEN_IMAGE_VIA_CODEX=1`. Best-effort only — it is slower (1-2 min/image),
  burns shared subscription quota at 3-5x a normal turn, and falls back to
  the API path automatically on failure. Do not build anything that only
  works when the codex path is up.
- Arbitrary `--size` is fine (nearest API size + exact post-resize). No
  transparent backgrounds from gpt-image-2; chroma-key in design-asset if
  needed.
- `--ref` (reference image for consistency/edits) currently works on the
  codex path only; on the API path carry consistency through the prompt's
  preserve-list instead.
- Neither path is seeded/reproducible. Keep the prompt + output pairs you
  liked; the prompt is the only reproducibility you get.

## Cost & iteration discipline

- **Scout cheap, finalize expensive**: explore variants at
  `gpt-image-1-mini` `low` (≈$0.005/img, 2026-07 — prices/models rot, recheck
  before quoting); regenerate ONLY the chosen direction at `gpt-image-2`
  `medium`/`high`. `high` is for text-bearing or detail-critical finals where
  a retry costs more than the quality bump.
- **One change per iteration** + restate the preserve-list every round
  (golden rule; the single biggest drift killer). Editing beats re-rolling.
- During canvas iteration, prefer changing the HTML layer (design-asset) over
  regenerating the backdrop — regeneration is the slowest, least stable move
  in the loop.
- Quota courtesy on the codex path: batch work goes through the API path;
  don't loop-regenerate on subscription quota.

## Suppressed defaults (the reflexes that produce mush)

- No adjective soup: "stunning, epic, masterpiece, 8K" actively hurts
  gpt-image results. Concrete nouns, materials, hex colors, named
  compositions.
- Positive framing only: "empty street at dawn", not "no cars no people".
- Text inside an image: quote it exactly ("EXACT TEXT: …"), keep it 3-5
  words, and if it matters — reconsider: text belongs to design-asset.
- 40-80 words is the sweet spot; a 200-word prompt loses focus.

## Reference map

| File | When |
|---|---|
| `references/smixs-image/upstream-SKILL.md` | always — entry point, mandatory reading order |
| `references/smixs-image/references/models.md` · `gpt-image.md` · `golden-rules.md` | every prompt |
| `references/smixs-image/references/patterns/ui-social.md` · `poster-illustration.md` | social formats, posters |
| `references/smixs-image/references/…` (editing/characters/multi-panel/text-rendering/…) | task-shaped, per smixs routing |
| `references/codex/cli-reference.md` · `prompting-guide.md` · `upstream-SKILL.md` | debugging the codex side path (flags, output paths, size quirks); its 5-slot guide + front-50-words rule also apply to the API path |
| `scripts/generate_image.py` | the executor — run `--help` for flags |
