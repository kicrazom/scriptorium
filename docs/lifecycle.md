# Scriptorium — The Scientific Knowledge Lifecycle

Scriptorium organizes its agents and skills around a seven-stage lifecycle for
working with research knowledge. Each stage answers one question and is served by
one or more components. This document maps stages → components and traces how data
flows from a raw search to a maintained knowledge base.

```
DISCOVER → EVALUATE → INGEST → ANALYZE → WRITE → REVIEW → MAINTAIN
```

The name evokes the medieval *scriptorium* — the room where manuscripts were
copied (writer), corrected (reviewer), and stored (librarian). That triad maps
onto the core agents.

---

## The seven stages

### 1. DISCOVER — *what exists?*

Find candidate literature and resources; grade their credibility; relate findings
to what you already know.

| Component | Type | Role at this stage |
|---|---|---|
| `research-scout` | agent | Retrieval + credibility/epistemic grading + dedup + compare-to-KB. Read-only; returns a **proposal**, never saves. Fetched web content is treated as data, not instructions. No fabricated PMIDs/DOIs/authors/numbers (`not-in-source` when absent). |
| `literature-search` | skill | Structured database query → literature note. PEO/PICO query suites, snowball expansion, recall checks. PMIDs/DOIs come **only from tool responses** (zero model-invented citations). |

**Division of labour:** `literature-search` *gathers* the raw structured catalog;
`research-scout` *judges* — it grades each finding on a tiered source ladder
(T1 peer-reviewed → T4 grey/web) and compares it against your knowledge base.
Use the skill to collect, the agent to assess.

### 2. EVALUATE — *is it worth my money / time?*

Decide whether a book, course, online material, bundle, repo, or doc is worth
buying / reading / studying / adding / skipping.

| Component | Type | Role at this stage |
|---|---|---|
| `librarian` | agent | Acquisition advisor. Separates five layers and never conflates them: (1) facts, (2) marketing claims, (3) public user opinions, (4) agent critique, (5) acquisition verdict. Scores 0–100 over weighted criteria; emits a verdict label (`BUY_NOW`, `READ_SAMPLE_FIRST`, `SKIP`, …) with confidence, time-cost, money-cost, and which sources were actually checked. |

**Anti-hype core:** public data only — no paywall bypass, no piracy, no scraping
against ToS, no invented review counts or ratings. When a source is blocked, the
librarian says so ("assessment from public data only") rather than guessing.

### 3. INGEST — *capture it as a note.*

Turn a discovered URL into a structured, provenance-bearing note.

| Component | Type | Role at this stage |
|---|---|---|
| `field-note-from-url` | skill | URL (paper / repo / video / blog / docs) → structured note with provenance frontmatter (source URL, author, type, retrieval date, epistemic status). Clean-markdown extraction; **stub pattern** for blocked sources (write a stub with URL + title + `awaiting-content`, do not halt). |

The frontmatter schema is generic and configurable, so the note slots into
whatever knowledge base you keep.

### 4. ANALYZE — *what do the data say?*

Plan and run your own statistics; size a study before you run it.

| Component | Type | Role at this stage |
|---|---|---|
| `statistician` | agent | Do-your-own-analysis for **classical and Bayesian** statistics. Classical: descriptives, t/Mann-Whitney, ANOVA/Kruskal-Wallis, χ²/Fisher, regression (linear/logistic/Cox), mixed-effects, multiplicity control, diagnostics, survival. Bayesian: stated priors, posterior summaries, **credible intervals**, Bayes factors, model comparison (WAIC/PSIS-LOO), MCMC diagnostics. |
| `power-sample-size` | skill | A-priori power and sample-size determination. Required N (or power given N, or minimum detectable effect given N), a sensitivity table over plausible effect sizes, and a ready Methods-section sentence. Flags **post-hoc / observed power as statistically invalid**. |

**Discipline shared here:** never fabricate a statistic — report exactly what the
analysis returns. State which assumptions were checked and their results.
Distinguish exploratory vs confirmatory, and statistical vs practical
significance. When no runtime is available, both components **degrade to
advisory** — they name the correct procedure and emit a ready-to-run script.

### 5. WRITE — *say it clearly and correctly.*

Structure a manuscript; paraphrase prose at the paragraph level without distorting
meaning.

| Component | Type | Role at this stage |
|---|---|---|
| `peer-paraphrase` | skill | Academic paraphrasing by the **PEER** framework (Point → Evidence → Explanation → Repeat/Link), not mechanical synonym-swap. One paragraph = one main idea; flags paragraphs that pack >1 point and suggests a split. **No new claims, no changed argument strength.** |
| `manuscript-imrad` | skill | Scaffold + structure-lint a draft against IMRaD: section presence/order, hypothesis → methods → results → conclusions coherence, claims-vs-data alignment, explicit Limitations, spin-flagging of non-significant results framed as positive. |
| `epistemic-status` | skill | (Spans all stages.) Assigns graduated evidence labels — `speculative_hypothesis → working_hypothesis → corroborated_inference → operational_fact → canonical_fact` (+ `contradicted`) — with confidence and source-independence count, plus explicit promotion thresholds. The signature differentiator; available everywhere, used during WRITE to grade central claims. |

**Levels:** `peer-paraphrase` is the micro level (one paragraph);
`manuscript-imrad` is document structure; whole-manuscript craft is out of scope.

### 6. REVIEW — *is it sound, complete, and confidential?*

Referee a manuscript; check reporting-guideline compliance; scrutinize clinical
interim analyses.

| Component | Type | Role at this stage |
|---|---|---|
| `peer-reviewer` | agent | Confidential, **offline** manuscript referee (Read/Grep/Glob only — no network by design; an unpublished manuscript is privileged material and is never transmitted). Detects study design → picks reporting guideline(s); reviews statistics, IMRaD logic, scope-fit, structural critique, citations/reproducibility/ethics. Treats manuscript text as data, never instructions. Output: a structured referee report with an editor-facing recommendation. |
| `reporting-guideline-check` | skill | Applies a reporting checklist item-by-item (STROBE, CONSORT(+AI), PRISMA, TRIPOD(+AI), STARD, CLAIM, SPIRIT, CHEERS, CARE, ARRIVE; GRADE for recommendation strength; SPIN flagging) → compliance table + gap list + fix suggestions. Usable standalone on your own draft. |
| `interim-analysis-reviewer` | skill | Clinical-trial interim-analysis specialist: DSMB/DMC reports, SAP sections, futility/efficacy stopping boundaries, alpha-spending, adaptive designs. Classifies the analysis first, then checks prespecification, type-I error control, estimand alignment, and governance. Read-only; **no fabricated statistics** ("Not assessable from the provided material" instead). |

**Boundaries within REVIEW:** `peer-reviewer` is the whole-manuscript referee and
may surface interim issues at a high level; `interim-analysis-reviewer` goes deep
on interim methodology (clinical only); `reporting-guideline-check` is the generic
checklist engine the referee shares conceptually. The referee does not import the
skill at runtime (it is offline); they share checklist content via the docs.

### 7. MAINTAIN — *keep the knowledge base healthy.* *(v2)*

Deduplicate, reconcile contradictions, prune stale notes, and re-grade evidence as
new sources arrive.

| Component | Type | Status |
|---|---|---|
| `knowledge-gardener` | agent | **Deferred to v2.** Curation and upkeep of the knowledge base. Until it ships, MAINTAIN is performed manually, drawing on `epistemic-status` (re-grading) and `research-scout` (contradiction detection against existing canonical claims). |

A companion `citation-auditor` (verify citation existence/support, not formatting)
is also slated for v2.

---

## Stage → component matrix

| Stage | Agents | Skills |
|---|---|---|
| DISCOVER | research-scout | literature-search |
| EVALUATE | librarian | — |
| INGEST | — | field-note-from-url |
| ANALYZE | statistician | power-sample-size |
| WRITE | — | peer-paraphrase, manuscript-imrad |
| REVIEW | peer-reviewer | reporting-guideline-check, interim-analysis-reviewer |
| MAINTAIN | knowledge-gardener *(v2)* | — |
| *(all stages)* | — | epistemic-status |

---

## Data flow

The components chain naturally: a raw search becomes graded findings, findings
become captured notes, notes feed analysis and writing, drafts pass through
review, and everything is eventually maintained.

```
  DISCOVER            INGEST              ANALYZE                  WRITE
 ┌─────────┐        ┌──────────┐        ┌──────────────┐        ┌─────────────────┐
 │research- │       │field-    │        │statistician  │        │peer-paraphrase  │
 │  scout   │──────▶│note-     │───────▶│      +       │───────▶│manuscript-imrad │
 │   +      │       │from-url  │        │power-sample- │        │epistemic-status │
 │literature│       │          │        │   size       │        │                 │
 │ -search  │       └──────────┘        └──────────────┘        └────────┬────────┘
 └─────────┘                                                              │
      │                                                                   ▼
      │           EVALUATE                                          REVIEW
      │          ┌──────────┐                          ┌──────────────────────────────┐
      └─ ──── ──▶│librarian │                          │ peer-reviewer (offline)       │
       (gate     └──────────┘                          │ reporting-guideline-check     │
        before                                         │ interim-analysis-reviewer     │
        acquiring)                                      └───────────────┬──────────────┘
                                                                        │
                                                                        ▼
                                                                   MAINTAIN (v2)
                                                              ┌────────────────────┐
                                                              │ knowledge-gardener │
                                                              └────────────────────┘

   epistemic-status  ── threads through every stage, grading each claim ──▶
```

Read as a pipeline:

1. **DISCOVER** — `literature-search` runs the structured queries; `research-scout`
   grades the results on the source ladder and compares them to the knowledge base,
   returning a proposal.
2. **EVALUATE** — for non-paper resources (books, courses, repos), `librarian`
   gates the acquisition decision before anything is bought or studied.
3. **INGEST** — approved URLs become provenance-bearing notes via
   `field-note-from-url`.
4. **ANALYZE** — `power-sample-size` sizes a study a priori; `statistician` runs the
   actual classical/Bayesian analysis on the data.
5. **WRITE** — `peer-paraphrase` (paragraph) and `manuscript-imrad` (document)
   shape the draft; `epistemic-status` labels the strength of each claim.
6. **REVIEW** — `peer-reviewer` referees the whole manuscript offline;
   `reporting-guideline-check` and `interim-analysis-reviewer` provide focused,
   specialist checks.
7. **MAINTAIN** *(v2)* — `knowledge-gardener` keeps the accumulated notes deduped,
   reconciled, and current.

`epistemic-status` is the cross-cutting thread: every stage can attach a graduated
evidence label to a claim, so confidence travels with the knowledge rather than
being asserted fresh at each step.

---

## Boundaries between overlapping components

A few pairs deliberately overlap; the dividing lines:

- **statistician ⟷ power-sample-size ⟷ peer-reviewer / reporting-guideline-check.**
  `power-sample-size` is the narrow a-priori procedure (design → N). `statistician`
  is the broad analyst (data → result) and can invoke the power logic for planning.
  `peer-reviewer` and `reporting-guideline-check` critique *others'* statistics and
  reporting rather than computing your own.
- **interim-analysis-reviewer ⟷ statistician ⟷ peer-reviewer.**
  `interim-analysis-reviewer` is the clinical interim specialist (governance, SAP,
  boundaries). `statistician` *computes* sequential boundaries / conditional power;
  `interim-analysis-reviewer` *reviews* whether they were prespecified and valid.
  Non-clinical sequential testing (e.g. early-stopping a benchmark sweep) is a
  `statistician` concern, not a clinical interim analysis.
- **research-scout ⟷ literature-search.** `literature-search` produces the raw
  structured catalog; `research-scout` grades credibility and relates findings to
  the knowledge base. Gather with the skill, judge with the agent.
- **peer-paraphrase ⟷ manuscript-imrad.** `peer-paraphrase` is the paragraph micro
  level; `manuscript-imrad` is document structure. Full manuscript craft is out of
  scope (a complementary concern, cross-linked from the README).
- **librarian ⟷ cataloging.** `librarian` evaluates (universal). Writing a note into
  a specific personal catalog is optional and config-gated; it is not the agent's
  core job.

---

## Shared principles across all stages

Every component inherits the same discipline:

1. **Source-trace every fact** — quote + anchor (file line, page, DOI, tool
   response). Numbers and citations come from tool output only; `not-in-source` /
   "absent" instead of guessing.
2. **Mark every AI inference** explicitly; never blend inference with fact-claims.
3. **Graduated epistemics** available everywhere; asymmetric-risk strictness is
   configurable for high-stakes/clinical claims.
4. **Read-only / propose-don't-write** for retrieval and review; writes are
   human-gated or config-enabled.
5. **Untrusted content is data, not instructions** (prompt-injection defense in the
   reviewer, scout, and ingest paths).
6. **No paywall bypass, no piracy, no ToS-violating scraping** — public data only.
7. **Specialist-to-specialist style** — concise; units on one line; comma-separated
   parameter lists; effect sizes reported with their uncertainty.
