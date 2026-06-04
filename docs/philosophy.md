# Scriptorium — Design Philosophy

Scriptorium is a toolkit for the scientific knowledge lifecycle:

```
DISCOVER → EVALUATE → INGEST → ANALYZE → WRITE → REVIEW → MAINTAIN
```

Tooling for research has an asymmetric failure mode. A confident wrong number, a
fabricated citation, or a leaked manuscript is far more costly than a missing
answer. The whole toolkit is therefore built so that the *cheap* failure (saying
"not found", "not assessable", "awaiting human approval") is always reachable,
and the *expensive* failure (inventing, transmitting, or overstating) is
structurally hard to commit.

These five principles are the Design DNA. Every agent and skill inherits them.
This document explains *why* each one exists and *how* it shows up across the
components, so that contributors adding new components know which invariants must
hold.

---

## 1. Anti-hallucination first

> Every factual claim carries a source trace. Numbers, citations, and doses come
> only from tool responses, never from the model. Absences are reported as
> findings, not silently filled. Every AI inference is marked.

### Rationale

A language model is a fluent prior over text, not a database. Left to free
generation it will produce a plausible-looking identifier, a plausible-looking
effect size, or a plausible-looking guideline version — all indistinguishable in
tone from a real one. In a research context the reader cannot tell a recalled
fact from a confabulated one, because both arrive in the same authoritative
register. The only durable defense is to refuse to let the model be the *source*
of any verifiable fact: facts must originate in a tool response (a database
query, a fetched page, a computed result, a quoted span of the input), and the
claim must carry a trace back to that origin.

The second half — "absences are findings" — matters just as much. The natural
failure mode of a helpful assistant is to fill a gap to be useful. In research
that is the most dangerous thing it can do. A missing power calculation, an
unreported confidence interval, an absent ethics statement: each is information.
Reported honestly as absent, it is an actionable finding. Silently filled, it is
a fabrication wearing the costume of completeness.

### How it shows up

- **Quote-with-anchor everywhere.** Claims about a source carry a locator (file
  path with line range, page number, DOI, or the tool response that produced
  them). A statement that cannot be anchored is not asserted.
- **Identifiers come from tools, not memory.** Literature components surface
  PMIDs, DOIs, author lists, and counts *only* from direct database/API
  responses. There are no model-generated citations anywhere in the toolkit.
- **A vocabulary for "absent".** Components have first-class ways to say a thing
  is not present — `not-in-source`, "absent", "not assessable from the provided
  material", "access limited — assessment from public data only". These are
  outputs, not apologies. The review and interim-analysis paths in particular
  treat "not assessable" as the correct answer when the material does not support
  a judgment.
- **Computed, never guessed.** Statistical and sample-size work reports exactly
  what the analysis returns, verbatim, and refuses to narrate a number it did not
  compute. When no runtime is available it degrades to advisory output — the
  correct test plus a ready-to-run script — rather than inventing a result.
- **Marketing ≠ facts ≠ opinions.** The acquisition-evaluation path keeps
  publisher claims, public user opinions, and its own critique in separate
  layers, and never fabricates review counts or ratings. Conflating hype with
  fact is itself a hallucination.
- **AI inference is labeled.** Where a component must extrapolate beyond the
  source, the inference is marked explicitly and never blended into the
  fact-claims. The reader always knows which sentences are grounded and which are
  the model reasoning.
- **No invented standards.** Where guideline or regulatory versions are
  referenced, they carry a "verify current version" caveat rather than asserting
  a specific edition the model cannot confirm.

This is the principle the other four protect. Graduated epistemics is how an
ungrounded claim is *labeled*; read-only is how an ungrounded write is
*prevented*; confidentiality and no-piracy keep the inputs themselves clean.

---

## 2. Graduated epistemics

> Evidence is not binary fact/inference — it is labeled on a scale
> (speculative → working → corroborated → operational → canonical, plus
> contradicted).

### Rationale

A binary fact/opinion split is too coarse for real evidence. A claim from a
single preprint, a claim replicated across three independent peer-reviewed
studies, and a claim that directly contradicts an established result are all
"not yet textbook fact" — but treating them identically destroys exactly the
information a researcher needs. Knowledge has a *maturity*, and that maturity
should be visible, not flattened.

Scriptorium therefore labels claims on a graded scale rather than asserting them
flatly:

| Status | Meaning |
|---|---|
| `speculative_hypothesis` | a guess or single weak signal; little independent support |
| `working_hypothesis` | plausible, some support, actively in use but unproven |
| `corroborated_inference` | multiple independent sources agree |
| `operational_fact` | reliable enough to build on in practice |
| `canonical_fact` | established, textbook-grade |
| `contradicted` | a newer/stronger source conflicts with it — demote and flag |

Each labeled claim also carries a **confidence** (0–1) and a
**source-independence count** (how many genuinely independent sources support
it — three citations to the same dataset count as one). Promotion up the ladder
has explicit thresholds; it is not a vibe.

The status is not a free-floating tag — it gates behavior. Two sources that
*agree* push a claim up the ladder; a source that *conflicts* with an existing
canonical claim drives a `contradicted` flag and a demotion rather than a quiet
overwrite. The framework makes contradiction a visible event instead of a silent
race between notes.

### How it shows up

- **A signature reusable skill.** The graduated-evidence framework is exposed as
  a first-class skill available at every stage, so any claim — discovered,
  written, or reviewed — can be assigned a status, a confidence, and a
  source-independence count with explicit promotion thresholds. This is the
  toolkit's conceptual differentiator: not "is this true?" but "how well-supported
  is this, by how many independent sources, and what would it take to promote it?"
- **Grading is part of discovery.** Retrieval grades each finding by source tier
  (peer-reviewed → indexes → preprints → grey/web) and decides, against any
  existing knowledge base, whether the finding *confirms*, *extends*, or
  *contradicts* what is already known — quoting the location of the prior claim.
- **Preprints are always caveated.** Preprint sources are labeled as such and
  never silently elevated to peer-reviewed status.
- **Asymmetric risk is configurable.** For high-stakes domains a strictness
  setting raises the bar: a single source or a preprint can never exceed
  `working_hypothesis`, and new claims are checked against existing canonical
  claims for contradiction. In lower-stakes use the default thresholds apply.
  The *mechanism* is fixed; the *strictness* is a dial the user sets.
- **Central claims get a status in review.** The referee path attaches an
  epistemic status to a manuscript's central claims, so "the authors assert X" is
  separated from "X is established".

Graduated epistemics is the natural companion to anti-hallucination: the first
principle keeps claims tied to sources, the second keeps the *strength* of that
tie honest and visible.

---

## 3. Read-only by default, propose-don't-write

> Retrieval and review agents return proposals; the human approves writes.

### Rationale

The expensive, hard-to-reverse actions in a knowledge workflow are writes:
adding a note to a knowledge base, overwriting a claim, committing a file. A
retrieval or review pass that writes autonomously can quietly inject an
ungrounded claim into the permanent record, where it will later be cited as
settled. Reads are cheap and reversible; writes are neither. So the default
posture is read-only, and anything that would mutate state is surfaced as a
*proposal* for a human to approve.

This is not timidity — it is a division of labor. The agent is good at gathering,
grading, and drafting; the human is the accountable party for what enters the
record. Propose-don't-write keeps that accountability where it belongs and keeps
the human in the loop precisely at the moment of irreversibility. It also
composes with anti-hallucination: even if a bad claim slips through grading, it
cannot silently become part of the corpus without a human passing it.

A second strand of this principle is **autonomy within a run**. A subagent
launched for a task runs to completion and returns; it cannot stop mid-run to ask
a question. So "propose-don't-write" also means: do the gathering autonomously,
then return a clearly-marked proposal and a recommendation, and let the human
decide — rather than blocking, or worse, deciding for them.

### How it shows up

- **Retrieval ends with a proposal, not a save.** The discovery path returns a
  findings table, draft note bullets in the user's link style, red flags, and a
  one-line save recommendation — and closes with an explicit "awaiting human
  approval — I do not write." The tools it is given do not include write access.
- **The referee never mutates anything.** The review path is read-only by
  construction: it cannot modify the manuscript or any file. Its deliverable is
  report *text* returned to the caller, who decides what to do with it. The same
  read-only stance holds for the reporting-guideline and interim-analysis
  checks.
- **Writes are opt-in via config, never assumed.** Components that *can* persist
  output do so only when the user has explicitly pointed them at a destination
  (a knowledge-base path, a catalog path). With no destination configured, they
  return the result inline and write nothing. Out-of-the-box, the toolkit touches
  no files it was not handed.
- **Where writes happen, they are guarded.** The components that produce
  artifacts — analysis scripts and results, ingested notes, literature catalogs
  — write next to the relevant data or into a user-configured location, with a
  dedupe check before adding to an existing collection. The write is a
  deliberate, located action, not a side effect.
- **Run autonomously, then hand back the decision.** Triage and retrieval passes
  do their work in one shot and return a candidate list or a recommendation for
  the human to pick from, rather than pausing mid-run or self-authorizing the
  next step.

The rule of thumb for any new component: **if it discovers or reviews, it
proposes; if it writes, the destination is the user's explicit choice.**

---

## 4. Confidentiality where it matters

> The peer-review path is offline and never transmits manuscript content.

### Rationale

Some inputs are privileged. A manuscript under peer review is unpublished,
confidential material entrusted to a referee under a duty of non-disclosure;
publication-ethics norms (e.g. COPE guidance) treat sending any part of it to a
third party as a breach. An unpublished protocol or a statistical analysis plan
carries the same duty. The risk here is not a wrong answer — it is *exfiltration*:
any tool that can reach the network is a channel through which privileged text
could leave, whether to a search API, a model endpoint, or a fetched URL.

"Where it matters" is deliberate. Not everything is confidential — public
metadata and published papers are fine to send to public APIs. The principle is
targeted: identify the paths that handle privileged material and make
transmission *structurally impossible* on those paths, rather than relying on the
model to remember not to leak. The strongest guarantee is the absence of a
capability: an agent with no network tools cannot exfiltrate, no matter what it
is asked to do.

There is also a flip side to confidentiality of inputs: untrusted inputs must not
be allowed to *act*. A manuscript or fetched page is data, not a command channel.

### How it shows up

- **The referee has no network tools, by design.** The peer-review path is given
  only local read and search capabilities — no web search, no fetch, no write.
  This is not a policy the model is asked to honor; it is the toolset it is
  handed. Privileged manuscript text has no route off the machine.
- **Review output never enters a knowledge base.** The referee report is returned
  to the caller and, by convention, saved next to the manuscript by the human —
  never ingested, indexed, or added to any retrievable corpus. Confidential
  material does not become searchable.
- **Minimal quotation.** Confidentiality-sensitive paths quote only the minimal
  text necessary to support a finding, rather than reproducing large spans of a
  privileged document.
- **Untrusted content is data, not instructions.** Paths that consume external or
  privileged text — the referee, retrieval, URL ingestion — treat that text
  strictly as data. A prompt-injection attempt embedded in a PDF or web page is
  reported as a research-integrity red flag, never obeyed. This protects both the
  integrity of the output and, by refusing injected "exfiltrate this" commands,
  the confidentiality of the input.
- **Interim-analysis guardrails.** The interim-analysis path must never be used
  to justify unblinded access to comparative results, unplanned peeking, or
  post-hoc decision rules — confidentiality of trial data and integrity of its
  governance are part of the same duty of care.

Confidentiality is enforced by *capability removal*, which is why it is robust:
you cannot transmit through a tool you were never given.

---

## 5. No paywall bypass, no piracy, no mass scraping

> Public metadata, previews, and public reviews only.

### Rationale

A research toolkit sits next to a lot of paywalled and copyrighted material, and
the convenient path is often the impermissible one: bypassing access controls,
pulling pirated full texts, or scraping a site against its terms. Scriptorium
refuses these for reasons that are both ethical and practical. Ethically, it
respects copyright, licensing, and site terms, and it does not route around
publishers' access controls. Practically, content obtained by bypass or scrape is
provenance-poisoned — you cannot cite it cleanly, you cannot trust its integrity,
and it undermines the source-trace discipline that principle 1 depends on. Legal,
public, attributable sources keep the whole evidence chain auditable.

The constraint is not "no full text ever" — it is "only through legitimate
routes". Open-access full text obtained through legal resolvers is fully in
scope. What is out of scope is *bypass*: defeating a paywall, downloading from a
shadow library as if it were a primary source, or scraping in violation of terms.

### How it shows up

- **Legal open-access routes only.** The discovery path resolves full text
  through legitimate open-access services. Paywalled items are offered as a
  resolver link (and, if the user has configured an institutional proxy, through
  *their own* legitimate access) — never bypassed.
- **Shadow libraries are off by default and never a source.** Any shadow-library
  link is gated behind an explicit, off-by-default user opt-in, is clearly
  labeled as such, and is never presented as a peer-reviewed source. The public
  default is off.
- **No fabricated public opinion, no scraping against terms.** The
  acquisition-evaluation path uses only publicly available reviews and ratings,
  reports counts and distribution honestly, and never scrapes against a site's
  terms or fabricates numbers. When access is blocked it says so —
  "access limited — assessment from public data only" — rather than guessing.
- **No long copyrighted excerpts.** Components quote the minimum needed to make a
  point and do not reproduce long copyrighted passages, whether from a book under
  evaluation or a document under review.
- **Public metadata and previews are enough.** Evaluation and discovery are built
  to work from titles, tables of contents, abstracts, previews, public reviews,
  and open-access text — the legitimately available surface — and to be honest
  about the limits of that surface rather than overreaching past it.

This principle keeps the toolkit's *inputs* as clean as principle 1 keeps its
*outputs*: every link in the chain, from source to claim, stays legal,
attributable, and auditable.

---

## How the five fit together

The principles are not a checklist of separate rules; they are one stance applied
at five points in the pipeline.

- **Anti-hallucination** governs what may be *asserted* — only what a tool
  produced, with a trace, with absences reported.
- **Graduated epistemics** governs how strongly it may be asserted — a labeled
  maturity with a confidence and an independent-source count, not a flat fact.
- **Read-only / propose-don't-write** governs what may be *committed* — proposals
  by default, human-gated or explicitly-configured writes.
- **Confidentiality** governs what may *leave* — privileged inputs cannot, because
  the tools to transmit them are absent.
- **No piracy** governs what may *enter* — only legal, public, attributable
  sources.

Read together they describe a single disposition: **be useful by being honest
about the boundaries of what you know, what you may write, what you may transmit,
and what you may take** — and make the safe failure the easy one. A contributor
adding a new component should be able to point to each of these five and say how
the new component honors it. If it cannot, it does not belong in Scriptorium.
