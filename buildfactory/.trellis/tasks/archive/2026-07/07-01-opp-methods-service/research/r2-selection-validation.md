# R2 — Info-product selection & validation methods (for headless CEO `find-opportunity`)

- **Strand**: R2 = info-product-specific SELECTION (which topic) + VALIDATION (will it SELL before we build it).
- **Query**: Given a market, how does a zero-human autonomous CEO pick the right info-product topic and prove it will sell, using only (1) research Goals to a `researcher` and (2) LLM-native authoring?
- **Anchor sources (real practitioners, primary web pulled)**: Nathan Barry (*Authority* / nathanbarry.com / ConvertKit), Ramit Sethi (*Zero to Launch* / GrowthLab / IWT), Justin Welsh (justinwelsh.me one-person business), Pieter Levels (levels.io / *MAKE*), Daniel Vassallo (Small Bets).
- **Date**: 2026-07-02
- **Executor reminder**: The CEO has NO personal expertise, NO audience, NO human taste. Its only two substitutes are: dispatch a research Goal (`python3 -m orchestration.messaging send --to researcher --intent "<question>"`) and author the product itself. So every "teach what you know / sell to your audience" method is re-translated: the binding constraint moves FROM "can I make it / do I know it" TO **"is there proven PAID demand."** These methods are the selection/validation LAYER on top of the seed pain-mining method (SI1 Sales Safari); they decide WHICH observed pain becomes a real, minimal, sellable info-product.

---

## KEPT METHOD 1 — WTP-first topic pick: only topics where money ALREADY changes hands, with thin/bad supply

**1. OPERATION**
- Research-Goal template (run once a candidate market/pain is on the table):
  `--intent "For the topic '<topic>' aimed at '<specific buyer>': list every EXISTING PAID info-product (course, ebook, paid newsletter, template pack, paid community). For each, report: price, platform, any visible sales/review/subscriber count, publish/last-update date, and the top 3 recurring complaints in reviews/comments. Also report whether buyers are stitching together free scraps because no good paid product exists. Return a table + a one-line verdict on supply quality."`
- Observable signal: ≥1 paid product with evidence of real sales (review count, sales badge, "sold X copies", paid-subscriber count) **AND** supply is thin or low-quality (few products, stale, or complaint-heavy reviews).
- Decision rule / threshold: KEEP a topic only if `paid-demand = TRUE` AND `supply-gap = TRUE`. If products exist but are excellent and saturated → DROP (no gap). If nobody sells anything → treat as UNVALIDATED, not "wide open" (usually means people won't pay). Prefer a proven-paid crowded-but-mediocre market over a novel one with zero paid precedent.

**2. PHILOSOPHY BACKING**
- "all those don't matter if no one is willing to pay you for your skills!" — Ramit Sethi (Forbes/IWT). Barry's topic rule: teach "a skill that other people use to make money" (Authority) — i.e. a topic already tied to money.

**3. HUMAN→AGENT SUBSTITUTION**
- Human: "teach the skill YOU know that people pay for" (Barry/Sacha: "I naturally wrote about user interface design, because that's what I know"). Agent has no such skill. Substitute: research the market for topics where PAID products already exist, then LLM-author a better one. The competence question ("do I know this?") is replaced by proven-demand + author-anything.

**4. THREE-TESTS VERDICT** — PASS (a,b,c).
- (a) system-specific: fully doable via one research Goal + LLM authoring; landable by researcher.
- (b) suppresses LLM default: LLM will propose "an AI-powered course on X" with no check that anyone pays. This forces existing-paid-product evidence first.
- (c) non-trivial tradeoff: prefers a crowded-but-mediocre paid market over a "blue ocean" with zero paid precedent — the opposite of the LLM's instinct to chase novelty.

---

## KEPT METHOD 2 — Demand before creation: detect ALREADY-PAID demand in the wild (translation of "sell before you build")

**1. OPERATION**
- Research-Goal template:
  `--intent "Find hard evidence that people ALREADY PAY money for a product shaped like '<candidate info-product>'. Look for: (a) similar ebooks/guides with visible purchase counts or crowdfunding/pre-order totals; (b) paid newsletters on this topic and their subscriber/price signals; (c) course sales counts on Gumroad/Udemy/Podia; (d) waitlists or pre-order pages that filled; (e) comments like 'take my money' / 'is there a paid version' / 'I'd pay for this'. Return each instance with the money signal (price × approx volume) and a link. Then estimate: how many DISTINCT instances of real payment did you find?"`
- Observable signal: N independent instances of real payment (a purchase, pre-order, paid subscription, or a competitor charging and clearly still in business), not mere interest.
- Decision rule: require **≥3 independent paid-demand instances** before promoting a candidate (mirrors Ramit's "at least three paying customers" bar, applied to observed market payment). Note for the future: once the company owns a channel, the CEO can dispatch a REAL pre-sell / waitlist / "BUY button" test as the strongest signal; at pure selection time it observes the market's demonstrated payment instead.

**2. PHILOSOPHY BACKING**
- "Charging money is also another test. It validates your idea. It shows people value it and are willing to GIVE you money." — Pieter Levels (levels.io). Barry: a landing page + email signups was "enough for me to say… there's enough demand to move forward"; Steve waited for 8,000 subscribers before writing. Welsh presells ~30 days as proof of demand before building.

**3. HUMAN→AGENT SUBSTITUTION**
- Human: pre-sell to their OWN email list / put BUY buttons on their OWN site (Levels' *MAKE*: thousands pre-paid $26.99 for a book that didn't exist yet). Agent has no list and no traffic, so it cannot run its own pre-sale at selection time. Substitute: observe payment that has ALREADY happened in the market (others' pre-orders, sales counts, paid-sub counts). The real pre-sell moves to the execution/growth layer as a later, stronger confirmation.

**4. THREE-TESTS VERDICT** — PASS (a,b,c).
- (a) system-specific: observation-via-Goal is exactly the agent's substitute for an audience.
- (b) suppresses LLM default: LLM would "validate demand" by hand-waving about a large TAM. This defines a countable, money-anchored signal.
- (c) non-trivial: sets a hard ≥3-paid-instances gate and explicitly demotes the agent's own (nonexistent) audience as the validation vehicle.

---

## KEPT METHOD 3 — Interest ≠ demand: count ONLY revealed payment; discount vanity signals

**1. OPERATION**
- Decision rule applied to ALL researcher findings — rank signals, act only on the top tier:
  - TIER-1 (counts as demand): someone paid money (purchase, pre-order, paid subscription); a paid competitor sustained over time; people asking "where's the paid version / take my money."
  - TIER-2 (weak, needs Tier-1 backup): waitlist emails, "I'd buy this" replies, high search volume, big subreddit.
  - TIER-3 (vanity, ignore for GO decision): likes, upvotes, "great idea!", the topic being painful to us.
- Rule: a candidate may NOT be promoted on Tier-2/3 alone. If only Tier-2/3 exists, label `UNVALIDATED` and either dispatch a deeper WTP Goal or drop.
- Optional confirming Goal: `--intent "For '<topic>', separate STATED interest (upvotes, 'I'd buy', high search volume) from REVEALED payment (actual purchases, pre-orders, paid subscribers, paying competitors). Report each bucket separately and flag if the only evidence is stated interest."`

**2. PHILOSOPHY BACKING**
- "It doesn't count as validation until your customers have paid you money." — Nathan Barry. Also: "Don't think that just because something is painful to you, that other people are willing to pay for it." (Barry). Ramit: "Survey buyers versus non-buyers."

**3. HUMAN→AGENT SUBSTITUTION**
- Human founder gets fooled by friends saying "great idea" and does a real pre-sale to disprove it. Agent gets fooled by high-engagement Reddit/HN threads reading as demand. Substitute: an explicit signal-tier rule that makes the researcher separate paid behavior from talk, so the agent doesn't mistake engagement for revenue.

**4. THREE-TESTS VERDICT** — PASS (a,b,c).
- (a) system-specific: directly governs how researcher output is scored.
- (b) suppresses LLM default: the LLM's strongest failure here is treating discussion volume / search volume / "people care about X" as proof it will sell. This is the exact counter.
- (c) non-trivial counter-signal: high interest with zero paid precedent is a RED flag (people talk but won't pay), which the LLM would read as green.

---

## KEPT METHOD 4 — Narrow to ONE burning pain for ONE reachable buyer; ship the smallest thing that fully kills it

**1. OPERATION**
- Research-Goal template:
  `--intent "In the community/market '<X>', identify the SINGLE most acute, most repeated pain (the one people describe with urgency/frustration, not a mild annoyance). Report: who exactly has it (specific role/situation), the exact words they use ('finally', 'I hate when', 'I keep having to…'), how they cope today and what they already pay for, and the ONE concrete outcome they'd pay to reach. Rank the top 3 pains by intensity × frequency × existing spend."`
- Decision rule (candidate definition gate): every candidate MUST name (i) ONE specific buyer, (ii) ONE burning problem in their words, (iii) the ONE outcome, (iv) the SMALLEST text deliverable that fully removes that pain (a 20-page focused guide / one checklist / one template pack — not a "complete course on <broad domain>"). Reject candidates that name a broad audience ("marketers") or a broad topic ("productivity").

**2. PHILOSOPHY BACKING**
- "Most people pick the wrong audience and the wrong product." — Ramit Sethi. Ramit's "burning pain" framing (the pain "antibiotics won't cure"). Welsh's MVP ethos: strip everything non-essential — "none of that is necessary to get started." Barry cites "the shortest possible guide to investing" as a model.

**3. HUMAN→AGENT SUBSTITUTION**
- Human narrows by immersion/taste in a niche they live in. Agent has no lived niche, so it narrows by dispatching a pain-ranking Goal and applying a structural "one buyer + one pain + smallest deliverable" gate on the writeup.

**4. THREE-TESTS VERDICT** — PASS (a,b,c).
- (a) system-specific: pain-ranking Goal + a definition gate the CEO can mechanically check.
- (b) suppresses LLM default: the LLM defaults to broad, ambitious scope ("a comprehensive AI course on productivity"). This forces a single acute pain + minimal deliverable.
- (c) non-trivial: "smallest thing that fully solves ONE pain" beats "more complete/bigger" — counter to the LLM's completeness bias.

---

## KEPT METHOD 5 — Treat candidates like cattle, not pets: emit 2-3 different bets, cap scope, let paid signal pick

**1. OPERATION**
- Decision rule for the candidate SET (feeds the existing find-opportunity "produce 2-3 candidates" seam):
  - Emit **2-3 clearly DIFFERENT** candidates (different buyer or different pain), never one.
  - Each candidate must pass a buildability gate: authorable end-to-end by LLM-native writing, shippable within a small timebox, needing NO large external infra (no video production, no live cohort, no custom software). If a candidate needs heavy non-text machinery → cut scope or drop it.
  - Do NOT rank/kill candidates on the CEO's own taste; hand all surviving candidates to `decide-direction` and let the money-anchored evidence (Methods 1-3) drive GO/DROP. Before generating, check `/company` memory to avoid already-rejected directions.

**2. PHILOSOPHY BACKING**
- "I like to call it treating ideas like cattle, not like pets, so you don't fall in love with your projects." — Daniel Vassallo. Also Vassallo: a small bet is "a very time-boxed effort… rather than an indefinite project," and a selection filter of "Is it something you can bring to market quickly? … on your own?"

**3. HUMAN→AGENT SUBSTITUTION**
- Human runs a portfolio of small bets over months and lets the market pick winners. Agent can't run its own months-long market test at selection time, so the substitute is: generate a small SLATE of cheap, self-buildable candidates and let the downstream money-evidence + `decide-direction` prune — the agent's "portfolio" is the candidate slate, not launched products.

**4. THREE-TESTS VERDICT** — PASS (a,b,c).
- (a) system-specific: matches the 2-3-candidate → decide-direction seam and the token-ROI / low-infra constraint; buildability gate = LLM-native only.
- (b) suppresses LLM default: LLM fixates on its first idea and inflates ambition. This forces multiplicity + scope caps + no self-judging.
- (c) non-trivial: "kill your darlings / don't fall in love / cap the build to what we can ship alone" is a discipline the LLM won't self-impose.

---

## DROP LIST (with why)

- **"Build your own audience first" (Welsh/Barry audience-first)** — DROP as a *selection-time method*: the agent has no audience and building one is a growth/execution-layer concern, not a way to pick a topic. Its useful core is INVERTED into Method 2 (observe the market's already-paid demand instead of your own list).
- **"Teach what YOU know / write about what you know" (Barry, Sacha Greif)** — DROP the literal form: the agent has no personal expertise. Re-translated in Method 1: constraint moves from "do I know it" to "is there proven paid demand," since the agent can author anything.
- **"Move fast / ship / put out even a bad product / iterate" (Welsh "move fast", Levels, Sacha "you'll learn more by putting out a bad book")** — DROP as a pure virtue the LLM already over-indexes on; it needs restraint (Methods 3-5), not more encouragement to ship.
- **"Build in public builds trust / community" (Levels, Welsh)** — DROP for this skill: it's a distribution/trust tactic, not a way to select or validate WHAT to make. Belongs to growth layer.
- **Launch-sequence, pricing, copy, and "$16k in 72 hours" tactics (Barry launch sequence; Welsh pricing lessons)** — OUT OF SCOPE: execution/monetization layer (parent PRD layer ③/④), not opportunity selection.
- **"Survey your existing buyers vs non-buyers" as a literal step (Ramit)** — DROP the literal execution (agent has no buyers yet); its insight (weight payers over talkers) is absorbed into Method 3's signal tiers.

---

## SOURCES TABLE

| # | Source (author) | URL | What was extracted | License / use note |
|---|---|---|---|---|
| 1 | Nathan Barry — *Authority* landing | https://nathanbarry.com/authority/ | topic = "a skill people use to make money"; Steve's 8,000-subscriber landing-page validation | All rights reserved; quoted for research only, cite as idea source, do not reproduce verbatim in shipped skill |
| 2 | Nathan Barry — Barry/Greif $39k ebooks interview | https://nathanbarry.com/nathan-barry-sacha-greif-sold-39k-worth-ebooks/ | "100 email addresses… enough… to move forward"; "wrote about UI design, because that's what I know" | same |
| 3 | Nathan Barry — million-dollar-business / audience (search-surfaced) | https://nathanbarry.com/how-to-build-a-million-dollar-business-from-your-audience-102/ | "It doesn't count as validation until your customers have paid you money"; "just because something is painful to you…" | same |
| 4 | Ramit Sethi — Forbes / IWT advice | https://www.forbes.com/sites/bryancollinseurope/2019/07/02/ramit-sethi-offer-this-advice-for-starting-an-online-business/ | "get at least three paying customers"; "all those don't matter if no one is willing to pay you"; don't jump to building | same |
| 5 | Ramit Sethi — Growth Everywhere interview | https://www.levelingup.com/growth-everywhere-interview/ramit-sethi-i-will-teach-you-to-be-rich/ | "Most people pick the wrong audience and the wrong product"; "Survey buyers versus non-buyers" | same |
| 6 | Ramit Sethi — Zero to Launch challenge page | https://growthlab.com/challenges/launch-your-profitable-online-business/ | "guarantee it's profitable — before you even have a product"; burning-pain framing | same |
| 7 | Justin Welsh — MVP in 27 minutes | https://www.justinwelsh.me/newsletter/build-an-mvp-startup-business-in-27-minutes | "prove an idea before you ever invest a meaningful amount of time"; "6 months… nobody ended up buying"; strip to essentials | same |
| 8 | Justin Welsh — $3.39M course sales / Idea.Audience.Proof.Product | https://www.justinwelsh.me/newsletter/what-ive-learned-from-3-394-480-in-digital-course-sales | Idea→Audience→Proof→Product framing; presell as proof of demand | same |
| 9 | Pieter Levels — bootstrapping talk | https://levels.io/bootstrapping/ | "Charging money… validates your idea"; "put BUY buttons on everything"; *MAKE* pre-orders ($26.99, book didn't exist) | same |
| 10 | Daniel Vassallo — Ship It! #88 (changelog) | https://changelog.com/shipit/88 | "treat ideas like cattle, not like pets"; small bet = time-boxed; "bring to market quickly / on your own" | same |
