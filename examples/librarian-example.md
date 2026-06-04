# Librarian — worked example (illustrative)

> **⚠️ SYNTHETIC / ILLUSTRATIVE EXAMPLE.** This transcript is fabricated to demonstrate the
> `librarian` agent's output shape and five-layer discipline. The book, author, publisher,
> prices, review counts, and ratings below are **invented** and do **not** describe any real
> resource. Numbers shown here are placeholders for *what a real run's tool responses would
> fill in* — in a live run every number traces to a `WebFetch` / `WebSearch` / `Read`
> result, and "not retrieved" stays "not retrieved". Do not cite anything here as fact.

This shows: a short user request → the agent's structured evaluation (abbreviated). It runs
with **no profile present**, so it uses universal defaults and scores strategic-fit against
the user's stated goal only.

---

## User request

> Is *Designing Resilient Pipelines: Event-Driven Data Systems at Scale* (1st ed.) worth
> buying? Goal: I maintain a mid-size streaming ETL platform and want patterns I can apply,
> not API tutorials. Link: `https://example-press.test/books/resilient-pipelines`

---

## Agent output (abbreviated)

# Evaluation: Designing Resilient Pipelines: Event-Driven Data Systems at Scale

**Verdict:** BUY_ON_DISCOUNT
**Score:** 74/100
**Confidence:** medium
**Time-cost:** 35-55 h (read + work the exercises) — `AI-inferred (estimate)` from ~440 pp
**Money-cost:** 49 USD list (publisher page); bundle/discount likely within ~2 months

> **No `librarian.domains` in profile** — strategic-fit scored against the stated goal only
> ("applicable patterns for a mid-size streaming ETL platform"), not a configured domain set.

## Facts (verified)
- Author: *J. Marek* (fictional), former platform engineer — `verified` (publisher author page).
- Publisher / year / edition: *Example Press*, 2025, 1st ed. — `verified` (publisher page).
- Format / length: print + DRM-free PDF/EPUB, ~440 pp — `verified` (publisher page).
- Companion repo: `example-press/resilient-pipelines-code`, last commit ~3 mo ago, CI green
  — `verified` (public repo page).
- Price: 49 USD list — `verified` (publisher page).
- Errata page exists, 4 entries — `verified`.

## Publisher / marketing claims
- *"Master fault-tolerant streaming in a weekend."* — quoted **as a claim**; the ~440 pp
  length contradicts "a weekend" (flagged below), not restated as fact.
- *"Production-ready patterns for any scale."* — marketing; treated as layer 2, not evidence.

## Public user opinions
- Aggregate review page: **41 ratings, mean 4.2/5** `publicly-available` (read directly).
  Distribution skewed positive (≈70% 4-5★, ≈12% 1-2★).
- Recurring **+**: praised for the backpressure and idempotency chapters; concrete diagrams.
- Recurring **−**: two reviews call the Kafka examples "already dated vs current versions";
  one flags a broken exercise (matches errata entry #3).
- ⚠️ **Contradiction surfaced:** reviews praise depth on delivery semantics but several call
  the observability chapter "thin" — shown, not averaged away.
- Practitioner forum thread (8 comments) `publicly-available`: net positive for fundamentals.

## Agent critique [AI-inferred]
- Teaches **fundamentals** (delivery semantics, backpressure, idempotency, partitioning) over
  transient API surface → ages better than a tutorial; freshness risk concentrated in the
  vendor-specific example chapters.
- Practicality is real but uneven: strong exercises early, lighter project layer late.
- For the stated goal (applicable patterns, not API walkthroughs) the core chapters fit well;
  the observability gap is the main weakness against that goal.

## Strengths
- Fundamentals-first; durable concepts. Maintained, CI-green companion repo. DRM-free.

## Risks / weaknesses
- Vendor example chapters dating; thin observability coverage; "weekend" marketing oversells.

## Scoring
| Criterion | Score | Comment |
|---|---:|---|
| Strategic fit (20) | 15 | Patterns-over-tutorials fit; no profile domains, scored vs stated goal. |
| Content quality (20) | 16 | Strong fundamentals; one thin chapter (observability). |
| Freshness (15) | 9 | 2025/1st ed., but vendor examples flagged as dating. |
| Practicality (15) | 12 | Working repo + exercises; lighter late-book project layer. |
| Author credibility (10) | 8 | Relevant platform-engineering track record (publisher bio). |
| User opinions (10) | 7 | 41 ratings, net positive, specific praise + concrete complaints. |
| ROI time/money (10) | 7 | Worth it at discount; full price not justified vs free docs for vendor parts. |
| **Total** | **74** | Weighted sum. |

## Sources checked
- Official: publisher book page, author page, errata. | Preview/ToC: public table of contents.
- Opinions: aggregate review page (41 ratings), one practitioner forum thread, companion repo.
- Comparators: official vendor streaming docs (free), one established competing title.
- Not reachable: full text (paywalled — assessed from ToC + preview + public reviews only).

## Next step
Wait for a publisher/bundle discount, then buy the DRM-free edition; read the official free
vendor docs for the observability gap. If urgent, `READ_SAMPLE_FIRST` (public ToC + sample
chapter) before paying list price.

---

### Why this is `BUY_ON_DISCOUNT`, not `BUY_NOW`

The score (74) lands in the conditional band, and the **time cost** (35-55 h) plus a thin
observability chapter and dating vendor examples mean full price (49 USD) is not justified
over the free official docs for those parts — but the durable fundamentals make it a clear
buy once discounted. Confidence is **medium** because layers 1-3 were filled from public
data, but the full text was paywalled (assessed from ToC, preview, and public reviews only).

### Note on the five layers

The whole point of the agent: **facts** (price, pages, repo), **marketing claims** ("master
in a weekend"), **public opinions** (41 ratings, the depth-vs-thin contradiction), **agent
critique** (`AI-inferred`), and the **verdict** (money + time cost) are kept strictly
separate and individually labeled — never blended into a single confident-sounding average.
