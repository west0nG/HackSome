# Finding an info-product opportunity on Amazon KDP

Read this once you've picked Amazon KDP (Kindle Direct Publishing). It makes steps 4–5
of the main method concrete for KDP. KDP fits things a text author can produce fully:
niche how-to ebooks, and **low-content books** — planners, journals, notebooks,
workbooks — where the buyer fills the pages in.

## The anchor

A good Kindle opportunity sits where three things meet: **demand** (people actually
type it into Amazon), **buy intent** (those searchers buy), and **rankability** (the
competition isn't so entrenched you can't break in). Every read below is a way to see
those three from the outside — not to guess whether a topic "sounds popular."

## Step 4 here — prove people already pay (KDP reads)

First, **don't invent keywords — harvest them from Amazon.** Amazon's search
autocomplete is fossil evidence of what shoppers actually type.
```text
Research question: "On Amazon (main + Kindle Store search bar), type the seed '<seed>' and record every autocomplete
  suggestion. Then append each letter a-z ('<seed> a', '<seed> b', …) and record what each reveals. Return the
  full list of real autocompleted phrases, flag the 3-5+ word long-tail ones, and tag each how-to vs
  low-content (planner/journal/workbook)."
Expected evidence: "A deduplicated list of real Amazon autocomplete phrases, long-tail ones flagged and tagged."
```
Keep only phrases Amazon actually autocompletes; drop phrasings you invented (no
evidence anyone searches them). Favor long-tail — broad terms aren't rankable.

Then, **does the keyword actually sell?** A keyword having searchers ≠ those searchers
buying. Read the Best Seller Rank (BSR) of the top ~10 books for it.
```text
Research question: "On Amazon, search the exact Kindle Store phrase '<keyword>'. For the top ~10 results report each
  book's title, format, price, Best Seller Rank (BOTH overall Kindle Store rank AND the rank in each named
  sub-category), review count, and stars. I need to know whether the books ranking for this keyword are
  actually selling."
Expected evidence: "A table of the top ~10 books with price, overall BSR, category BSR(s), review count, stars; note
  if top results have weak/absent BSR."
```
BSR as a sales proxy (order-of-magnitude): under ~10,000 = strong daily sales; under
~100,000 = consistent movement; above ~500,000 = infrequent.
- **Keep (keyword sells):** top books mostly ≤ ~100,000 BSR, with at least one or two under ~50,000/10,000.
- **Drop (doesn't sell):** top books mostly > ~500,000 BSR — people may search it, but they don't buy.
- Always weigh **category BSR, not just overall** (see rankability below).

## Step 5 here — a beatable gap (KDP reads)

```text
Research question: "For the exact Kindle Store phrase '<keyword>': (1) roughly how many results does Amazon return?
  (2) For the top 5 books report review COUNT, stars, publication/last-updated date, page count/thinness, and
  cover-quality impression. (3) Is the top dominated by one big brand, or beatable indie titles? (4) Scan the
  1-3 star reviews for recurring 'I wish it had…' complaints. Cross-reference the BSR read — I need to know if
  these books SELL but are BEATABLE."
Expected evidence: "Result-count band; top-5 review counts + stars + freshness + thinness; brand-dominance read;
  recurring unmet complaints (or 'none')."
```
- **Keep (proven but beatable):** top books sell (good BSR) **and** are beatable — roughly **50–300 reviews** (proven demand with room to enter), a low result band, or leaders that are outdated/thin/mediocre with recurring complaints.
- **Drop (saturated):** every top-5 book has ~1,000+ reviews — entrenched, no wedge.
- **Drop (unproven):** almost nothing selling / all top BSR weak — not open water, just nobody buying.
- **Rescue by narrowing:** a saturated head term ("coloring book") often has a wide-open long-tail ("bold-line mushroom coloring book for adults") — same royalty, far less competition. Use the autocomplete long-tails from step 4.

## KDP's own lever — category rankability

KDP has a lever a general model won't know: the **same book** needs, say, ~14 sales/day
to hit #1 in one category but ~1,000/day in another. Find a reachable category.
```text
Research question: "For '<keyword/niche>': open the top 3-5 selling books and list the exact Amazon sub-categories
  each is filed under (from the Best Sellers Rank breakdown). For each named sub-category report the BSR of the
  current #1 and #20 book, so we can estimate how few daily sales it takes to reach #1 or top-20. Flag reachable
  categories vs ones owned by mega-sellers."
Expected evidence: "Per top book: its sub-categories; per sub-category: #1 and #20 BSR; a shortlist of reachable
  categories."
```
Keep the topic if at least one sub-category looks reachable (its #1 isn't an
ultra-low-BSR giant). Note for build time: a book gets up to ~10 categories and 7
keyword slots — reserve a slot or two to anchor it into the reachable category, or
Amazon may file it elsewhere.

## Shape and price

- **You can author:** niche how-to non-fiction; low-content planners/journals/notebooks/workbooks (structure + prompts, no manuscript).
- **You can't (drop or reshape):** coloring books, puzzle/activity books, illustrated titles — they need art assets a text author can't produce, even if demand and gap are perfect.
- **Royalty band:** a Kindle ebook earns 70% only when priced **$2.99–$9.99**; outside that it's 35%. Aim inside the band.

## Traps to skip

- **Publisher Rocket / Chrome BSR plugins** — paid GUIs you can't drive; keep their *thinking* (demand/competition/rankability), get the data via the research Goals above.
- "Pick a trending niche" (interest, not proven buying), "zero-competition blue ocean" (usually nobody pays), and TAM sizing — all drop.

<!-- KDP-specific method, cited as idea sources (per-clause provenance in this task's
research/amazon-kdp.md): Kindlepreneur/Dave Chesson (keyword three-way intersection,
autocomplete + a-z, BSR-to-sales, category rankability, 7 slots / 10 categories),
Low Content Profits & Publishing.com (low-content niches, beatable-gap read), KDP Help
(70% royalty band). Numbers are order-of-magnitude; prefer category BSR over overall.
Specializes steps 4–5 of finding-info-product-opportunities.md; generation only — hand
candidates to manage-objectives. -->
