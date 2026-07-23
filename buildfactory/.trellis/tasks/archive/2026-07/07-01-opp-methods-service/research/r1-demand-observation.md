# R1 — Demand-Observation Core (Sales Safari / 30×500)

**Strand:** R1 = how a headless CEO finds a REAL, already-existing *paid* pain in a market
(instead of inventing an info-product idea) for the **info-product** business form.
**Anchor source:** Amy Hoy & Alex Hillman — "Sales Safari" / 30×500 (net-ethnography:
*study a market, not ideas*).
**Date:** 2026-07-02
**Primary/near-primary sources fetched:** stackingthebricks.com (Amy Hoy essays),
leanb2bbook.com (Alex Hillman interview transcript), solvingproduct.com (Etienne
Garbugli's Sales Safari write-up), joelhooks.com (7-steps + painstorming),
failory.com (Hoy/Hillman info-products interview), wisp.blog (Sales Safari mega-guide).
Full URLs in the sources table at the bottom.

> Executor reminder: the CEO is a headless autonomous LLM. Its only two research
> substitutes are (1) **dispatch a research Goal** to the `researcher` department —
> literally `python3 -m orchestration.messaging send --to researcher --intent "<question>"`
> — and (2) **LLM-native production** (it can itself scan/author text). Every method
> below is written as a thing the agent actually *runs*, not a thing it "understands."

---

## KEPT METHOD 1 — Watering-hole enumeration (find where the market already talks, and gate on readability)

**OPERATION**
- Research-Goal template the CEO sends:
  `--intent "Enumerate the 8-12 highest-activity online 'watering holes' where [MARKET] gathers and talks candidly WITH EACH OTHER (not to vendors) about their work/problems. Use these search patterns: '[MARKET] forum', '[MARKET] subreddit', '[MARKET] Discord/Slack community', '[MARKET] mailing list', '[MARKET] Facebook group', '[MARKET] Stack Exchange', '[MARKET] user group'. For EACH return: name, URL, rough activity level, and whether posts are PUBLICLY READABLE without login. Rank by activity."`
- **Observable signal in findings:** count of watering holes that are BOTH active AND publicly readable.
- **Decision rule (hard gate):** if `< 2` active + publicly-readable watering holes → this market is *unobservable to a headless agent* → **DROP the market, pick another.** Do not proceed on faith.

**PHILOSOPHY BACKING** — watering holes are the raw material; observation only works where the market speaks freely.
> "online locations where your prospects gather and have natural conversations amongst themselves, free from sales agendas" (wisp.blog, restating Hoy/Hillman); "places where prospects gather for pleasure or for work" (Garbugli, solvingproduct.com).

**HUMAN→AGENT SUBSTITUTION** — Human founder already lives in a niche and knows its forums; a headless agent knows none, has no network, and *can only read*. Substitute = dispatch a researcher to enumerate, and add a readability gate a human never needs.

**THREE-TESTS VERDICT** — PASS (a) system-specific: agent has no personal habitat, must locate readable sources first; (b) suppresses the LLM default of imagining an audience it cannot actually observe. The readability gate is the non-trivial (c) part.

---

## KEPT METHOD 2 — Painstorming harvest at scale (collect VERBATIM quotes, forbid summarizing)

**OPERATION**
- Research-Goal template:
  `--intent "In [watering hole URLs from Method 1], collect 40-60 VERBATIM quotes where members express a problem, frustration, question, complaint, or manual workaround about [TOPIC]. Return EACH as: exact quoted text + source URL + date. Do NOT summarize, paraphrase, or cluster — I need the raw words. Prioritize (a) posts asking for help and (b) posts venting/complaining."`
- **Observable signal:** a list of raw quotes, each with URL — NOT a prose summary.
- **Decision rule / threshold:** target ~40-60 quotes (the agent's scale-substitute for the human "30-50 hours"). If the researcher returns a summary or `< 30` verbatim quotes → **re-dispatch** insisting on raw quotes. The corpus, not a conclusion, is the deliverable.

**PHILOSOPHY BACKING** — the signal lives in people's exact words; pain = facts + feelings + actions taken from "words written by actual people."
> "spending as much as 30 to 50 hours *listening for the nouns*" (Garbugli); "the answers come from how people behave, even (especially) when you're not in room asking questions" (Amy Hoy, validation-is-backwards). Painstorming = pain has three facets, "facts… feelings… actions… all three… coming from words written by actual people" (joelhooks, basic-painstorming).

**HUMAN→AGENT SUBSTITUTION** — Human lurks 30-50 hrs and absorbs pain by immersion; agent cannot immerse, so it commissions a *verbatim corpus* at scale and reasons over it. The "forbid summarizing" clause is essential: it stops the pipeline from collapsing into a premature idea.

**THREE-TESTS VERDICT** — PASS all three. (a) fits dispatch-a-Goal; (b) counters the LLM's rush to a tidy summary/idea; (c) the "raw quotes, no paraphrase, ~40-60 count" is a non-trivial constraint directly opposed to the LLM's default to compress.

---

## KEPT METHOD 3 — Trigger-word + question scan (LLM-native lexical pass to locate acute pain)

**OPERATION**
- After the corpus returns, the agent itself (LLM-native, no dispatch) scans every quote for:
  - **Trigger/relief lexicon:** `finally`, `I hate`, `I wish`, `annoying`, `frustrating`, `relief`, `easier`, `faster`, `less`, `more`, plus snark/zingers.
  - **Questions:** any quote containing `?`, `how do I`, `how do you`, `is there a way`.
- Tag each hit. **Decision rule:** treat a quote as a pain-candidate only if it carries a trigger word OR is a help-seeking question; a neutral statement is not pain.

**PHILOSOPHY BACKING** — a question is pain made visible; specific emotion words mark where it hurts.
> trigger words "easier", "faster", "less", "more", "relief", "finally" (Garbugli / joelhooks); "a question is a great first indicator of pain in your audience… questions are easy to spot once you start doing Sales Safari" (Amy Hoy, year-of-hustle); "Think about how much something needs to hurt in order for you to go on the internet, to a room full of strangers and ask for help" (Alex Hillman, leanb2bbook).

**HUMAN→AGENT SUBSTITUTION** — Human feels which posts "sting"; agent replaces intuition with an explicit token scan — which is a genuine LLM *strength* (fast lexical/semantic pattern-match over a text corpus).

**THREE-TESTS VERDICT** — PASS (b)+(c): the specific lexicon and the "question = pain" heuristic are non-obvious rules the LLM would not adopt unprompted (it would otherwise weight eloquent statements over terse questions).

---

## KEPT METHOD 4 — Pattern-across-people gate (recurrence, not one juicy post)

**OPERATION**
- **Decision rule:** a pain qualifies as a *market* signal only if it "shows up a bunch on its own" — i.e. independently voiced by `≥ 5` DISTINCT authors, ideally across `≥ 2` watering holes. Rank surviving pains by `(# distinct authors × emotional intensity)`. Discard one-off complaints no matter how vivid.

**PHILOSOPHY BACKING** — you observe the whole landscape and keep what recurs; you do NOT lock onto one pain and hunt for confirmations.
> "Instead you observe the entire landscape and you go, what's showing up here a bunch on its own." / "It's not about finding one pain and locking onto that, and then finding every example of that pain." / "collect wide swaths of information, look for emergent patterns and then refine." (all Alex Hillman, leanb2bbook).

**HUMAN→AGENT SUBSTITUTION** — Human notices repetition through weeks of exposure; agent counts distinct-author recurrence over the harvested corpus (near-deterministic).

**THREE-TESTS VERDICT** — PASS (b) directly: this is the antidote to the LLM's single worst failure mode here — fixating on and rationalizing its FIRST idea. The distinct-author threshold is the non-trivial (c).

---

## KEPT METHOD 5 — "What do they already PAY for?" (the money signal that turns pain into *paid* pain)

**OPERATION**
- Research-Goal template:
  `--intent "For [MARKET] + [pain from Method 4], find hard evidence of what people ALREADY SPEND money OR serious time on to deal with it: existing paid products, courses, ebooks, paid newsletters, templates, tools, consultants, subscriptions, or elaborate manual workarounds. For each: name, price, and quotes of people buying/recommending/complaining about it. I want proof that money is already changing hands around this pain."`
- **Observable signal:** named paid alternatives WITH prices + quotes of real purchase/recommendation, OR evidence of heavy repeated manual effort (a time-cost proxy).
- **Decision rule (the key gate):** keep the opportunity ONLY if there is evidence of existing spend (a paid alternative that sells, OR a costly time-workaround people endure). If a pain is real but *nobody pays for anything adjacent* → **DROP it** (pain without demonstrated willingness-to-pay is a hobby, not a business).

**PHILOSOPHY BACKING** — buying is a value equation, and demand is proven by money already in motion (need ∩ want ∩ **buy**).
> "buying on value is a pretty straightforward equation. I have a problem. This problem is costing my business money." (Alex Hillman, leanb2bbook). Amy Hoy frames the target as the intersection of *need, want, and buy* — and warns that treating non-payers as customers ("they've got no skin in the game") yields "worthless data" (validation-is-backwards). Painstorming explicitly asks **"What do they buy?"** (joelhooks).

**HUMAN→AGENT SUBSTITUTION** — Human knows from peers what the tribe pays for; agent dispatches a researcher to surface existing paid alternatives + prices, and treats *presence of competitors* as GOOD news.

**THREE-TESTS VERDICT** — PASS all three. (a) dispatch-a-Goal fit; (b) INVERTS the LLM's instinct that "no competitors = white space = great" — here, no existing spend = red flag; (c) strongly non-trivial: existing paid alternatives are a *buy* signal, not a threat.

---

## KEPT METHOD 6 — "Incomplete / hated existing solution" = the demand wedge (boundary hand-off to the product-definition strand)

**OPERATION**
- From Method 5's findings, scan for the pattern: *"people already pay for X, but complain it's [too broad / too expensive / out of date / too advanced for beginners / missing Y]."*
- **Decision rule:** the strongest info-product wedge = the packaged knowledge that resolves that *specific stated complaint* about the paid thing (narrower / cheaper / more focused / more current). If existing paid solutions are universally loved and complete → weaker wedge, deprioritize this pain.

**PHILOSOPHY BACKING** — dissatisfaction with what's already bought is the opening.
> "Existing solutions they perceive as incomplete or ineffective" signal market opportunity (wisp.blog, restating Sales Safari); "collect wide swaths of information, look for emergent patterns and then refine" (Alex Hillman).

**HUMAN→AGENT SUBSTITUTION** — Human intuits the gap; agent cross-references pain-quotes (Methods 3-4) against paid-alternative complaints (Method 5).

**THREE-TESTS VERDICT** — PASS (c): converting a complaint-about-a-competitor into a product wedge is a non-trivial cross-reference the LLM would skip. NOTE: this is the *boundary* of R1 — it observes demand-shape but hands the actual product spec/scope to the product-definition strand. Kept here only as the demand-side output.

---

## DROP LIST (pure virtues / out-of-scope — the LLM already has these or they don't transfer)

- **"Brainstorm many product ideas widely."** This IS the default we are suppressing. DROP.
- **"Think from first principles / consider the market."** Generic; the LLM has it. DROP.
- **"Understand / empathize with your customer deeply."** Vague, not executable. DROP.
- **"Spend 30-50 hours immersing yourself in a forum."** Does not transfer to a headless agent with no personal immersion. REPLACED by Methods 2+3 (commission a verbatim corpus at scale, then scan it). DROP as a literal instruction; keep only as the *rationale* for corpus size.
- **"Ebomb the watering holes / write content / build an audience / grow a list."** That is audience-building & marketing — a DIFFERENT strand. OUT OF SCOPE for R1. DROP here.
- **"Interview ~5 people and ask what they'd pay for."** Amy Hoy explicitly calls this backwards ("throwing spaghetti against a wall"; interviewees "too friendly, too supportive… worthless data"); also a human-only op. DROP — replaced by observing what they *already pay for* (Method 5).

---

## Signatures / Sources

| # | Source | Author / role | Type | URL | Notes / license |
|---|--------|---------------|------|-----|-----------------|
| 1 | Validation is backwards | Amy Hoy | PRIMARY essay | https://stackingthebricks.com/validation-is-backwards/ | © Stacking the Bricks; quoted for research (fair use) |
| 2 | Year of Hustle — Marketing Content / eBombs | Amy Hoy | PRIMARY (free course lesson) | https://stackingthebricks.com/year-of-hustle/marketing-content-ebombs/ | © STB; quoted for research |
| 3 | Alex Hillman on Sales Safari (interview transcript) | Alex Hillman | Near-primary transcript | https://leanb2bbook.com/blog/alex-hillman-sales-safari/ | © Lean B2B; quoted for research |
| 4 | How to Find New Product Opportunities with a Sales Safari | Etienne Garbugli | Near-primary write-up of Hoy/Hillman | https://solvingproduct.com/sales-safari/ | © author; quoted for research |
| 5 | 7 Steps to 30×500 | Joel Hooks | Secondary summary | https://joelhooks.com/7-steps-of-30x500/ | © author; quoted for research |
| 6 | Basic 30×500 Painstorming | Joel Hooks | Secondary (painstorming) | https://joelhooks.com/basic-painstorming | © author; quoted for research |
| 7 | Sales Safari Mastery Mega-Guide | wisp CMS blog | Secondary synthesis | https://www.wisp.blog/blog/sales-safari-mastery-the-mega-guide-to-mind-read-your-audience-and-creating-wildly-successful-content-bombs | © wisp; quoted for research |
| 8 | 10 Years into Selling Info Products to Creative People | Hoy/Hillman interview | Near-primary (info-products) | https://www.failory.com/interview/stacking-the-bricks | © Failory; quoted for research |
| 9 | 30×500 Academy | Amy Hoy / Alex Hillman | PRIMARY (program page) | https://30x500.com/academy/ | © STB; reference |

**Verbatim quotes are excerpts used for internal research/methodology extraction (fair use); none of these sources is open-licensed. Do not redistribute source text verbatim in shipped product.**
