---
name: de-ai-ify
description: >-
  Remove AI-writing tells. Use on finalized public-facing English or Chinese
  copy before it is sent or baked into an asset.
---

# De-AI-ify: strip the AI smell

Your default writing carries AI tells, not because it is *bad* but because "the
most statistically likely phrasing" is exactly what a reader now recognizes as
machine-written. Good content still reads as AI unless you actively strip it.

It works off **concrete tells with before/after rewrites**, not "sound more
human" (which an LLM cannot act on). The catalogs live under `references/` (EN)
and `zh/` (ZH); route by the draft's language and apply the loop.

## When to run it

Run it the moment a piece of copy is decided, on any text that will reach the
public: a post, thread, caption, ad, email, landing copy, or the words that go
into a poster, image, or video. Always run it while the wording is still editable
text, before it is baked into a downstream asset or sent.

In a compose chain it runs on the text before any asset is built from it:
`social/copywriting (draft) → de-ai-ify (this) → visual-asset → use-accounts`.

## Get the voice first

Read the company's brand voice and positioning from `/company` (via the
`company-state` skill) and match it. If none is defined yet, keep the default
human voice each catalog describes (EN: `references/en-humanizer.md`,
"PERSONALITY AND SOUL"; ZH: the 过度消毒反制 / 毛边 rules inside `zh/`).

## Route by language

Chinese AI-smell is not translated English AI-smell: full-width punctuation,
顿号, 英式句法残留, over-translated terms. Pick by the draft's language.

- **English** → `references/en-humanizer.md` (33 patterns, each with before/after)
  plus `references/en-ai-writing-detection.md` (weak→strong "use instead" tables).
- **Chinese** → `zh/upstream-SKILL.md`, a self-contained vendored skill with its own
  control layer (语体矩阵 decides which rules fire per register; 冲突仲裁顺序 §1-6;
  过度消毒反制) driving `zh/references/` (patterns, punctuation, syntax, whitelists,
  brand-voice, platform-patterns). Follow it as-is for Chinese drafts. Within
  the vendored `zh/` subtree, upstream mentions of `SKILL.md` mean
  `zh/upstream-SKILL.md` here.

## The loop

1. **Audit.** Answer in one line: *"what makes this obviously AI-generated?"*
   Name the actual tells, looking for a **cluster**, not one stray hit.
2. **Rewrite, don't gut.** Replace tells with natural phrasing and cover
   everything the original covered (five paragraphs in, five out). Prefer plain
   `is/are/has`, specific detail over inflation, varied sentence length.
3. **Dashes (the strongest single tell).** Strip every em/en dash (`—`/`–`) you
   can replace losslessly with a period, comma, colon, or parentheses. Keep one
   only if it carries a real rhetorical function you would defend (the 逐处自查问
   both catalogs use). Chinese: fix full-width punctuation per
   `zh/references/punctuation.md`.
4. **Deliver** the cleaned text (optionally a one-line "still-AI" note).

## Guard: do not over-de-AI

Stripping tells can strip the human. **A clean but soulless draft is just as
obviously machine-made.** Before finalizing, check the false-positive lists to
keep real voice:

- English → `references/en-humanizer.md`, "DETECTION GUIDANCE / What NOT to flag"
  and "Signs of human writing".
- Chinese → `zh/references/whitelists.md` (keep MCP / NBA / 霉霉 / Niacinamide
  as-is; over-translating them reads *more* AI, not less).

Register matters: skip patterns that do not apply to marketing/social copy (EN
#2 notability, #6 challenges, #21 knowledge-cutoff); 中文由 `zh/` 的语体矩阵按语体
放行公文/学术的庄重表达。Keep specific detail, mixed feelings, real opinions, and
uneven rhythm.
