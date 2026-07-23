---
name: mine-customer-voice
description: >-
  Mine customer language from reviews, forums, and comments into /company. Use
  before writing for a new segment or when its language and brand-voice
  evidence is thin.
---

# Mine customer voice

Copy written from default knowledge comes out as the statistical average of
all marketing text, and readers scroll past it. Copy that lands repeats how
customers themselves describe the problem, in their words. Those words are
not in the model; they are in Reddit threads, reviews, and comment sections
right now, and collecting them is a step of the work, not an optimization.
The collection playbooks live under `references/` (vendored, see
`ATTRIBUTION.md`).

## When to run it

Run it before drafting copy for a direction or segment that has no
customer-language document in `/company` yet, and when entering a new
segment. If a library exists but drafting keeps reaching for generic
phrasing, the library is thin: collect more.

## What to collect, and where

- `references/customer-research.md`: the frame. Two modes (squeeze material
  the company already has: support logs, interviews, reviews; or go find it
  in the wild), an extraction checklist (jobs to be done, pains, switching
  triggers, and the language used), and a synthesis template that ranks
  themes by frequency times intensity, each with verbatim quotes.
- `references/source-guides.md`: per-source tactics. Reddit search operators,
  subreddit lists by category, and which post types carry signal; review-site
  mining (read 3-star reviews first, they are the most honest; 1-star for
  failure modes; 5-star for praise language worth reusing); Hacker News,
  Product Hunt, YouTube comments, LinkedIn.
- `references/listening.md` plus `listening-sources-template.md`: the
  programmatic pipes. curl recipes for the Reddit, Hacker News, and Bluesky
  public APIs, RSS recipes for blogs and channels, and a scoring rubric for
  triaging what comes back.

## The deliverable is company state

Write what you mine into `/company` (via the `company-state` skill) as a
customer-language library: verbatim quotes grouped by theme, ranked, tied to
the direction or segment they came from. Where it lives and how it is
organized is your call; research the existing `/company` layout first and
grow the taxonomy as directions multiply. The persistent source list that
`listening.md` keeps is also a `/company` document: seed it from
`references/listening-sources-template.md`, prune sources that never yield.

## Deriving the brand voice

Defining and maintaining the company's voice is your job. When `/company`
has no voice yet, derive one from the mined customer language plus the
company's positioning, and record it to `/company` (location is your call).
Write copy against it afterwards; when good drafts keep fighting the voice
document, the document is wrong, update it.

## Using the library when writing

Draft from the verbatims: open with the problem in the customer's own words,
reuse their vocabulary for features and outcomes, and take proof-point
phrasing from their praise language. Run `de-ai-ify` on the result before it
ships.

## Reading the catalogs

The vendored files keep their upstream conventions; map them like this:

- `customer-research.md` opens by reading `.agents/product-marketing.md`:
  that is upstream's name for company context, so read `/company` instead.
- Wherever `listening.md` or the template says the source list lives at
  `.agents/listening-sources.md` (or `.claude/listening-sources.md`), that
  means your `/company` source-list document. Skip its "Setting Up the
  Source List" copy commands: those paths are upstream's install layout, and
  the template is already here at `references/listening-sources-template.md`.
- `listening.md` reaches LinkedIn and X through a browser tool it assumes is
  installed. Use whatever browser tool your environment mounts; with none
  available, the scriptable sources (Reddit, Hacker News, Bluesky, RSS)
  carry the collection loop on their own.
- Links into upstream's `tools/integrations/` directory (such as the
  SparkToro pointer in `source-guides.md`) are not vendored; the inline
  guidance around them is complete, so skip those links.
- The "Related Skills" handoff table in `customer-research.md` points at
  skills that are not installed; the handoff that matters, writing copy
  informed by the research, is whatever drafting the goal asked for,
  followed by `de-ai-ify`. Its persona-generation section is optional; the
  language library is the deliverable.

## Sources

Vendored (MIT); see `ATTRIBUTION.md`. Upstream lives untouched under
`references/`; this file is the only adaptation layer (library and voice into
`/company`, source mapping). Sync by re-copying upstream, not editing it.
