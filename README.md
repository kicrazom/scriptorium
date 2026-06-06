![Scriptorium](docs/assets/scriptorium-manuscript.png)

# Scriptorium

[![CI](https://github.com/kicrazom/scriptorium/actions/workflows/ci.yml/badge.svg)](https://github.com/kicrazom/scriptorium/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**An early-stage Claude Code plugin for scientific-workflow rigor — audit, compute, and grade research, offline-first.**

Where generative tools *write*, Scriptorium *scrutinizes*: it recomputes statistics, screens reporting guidelines, audits citation hygiene, grades evidence on a graduated epistemic scale, and runs a confidential, offline manuscript-review path. It pairs a small **deterministic core** (tested Python engines whose every number carries a provenance trace) with a **prompt layer** of agents and skills that reason over the rest. It complements generative writing tools; it does not replace them.

> **Honest scope.** This is a young project. Some capabilities are tested code; others are guided agent workflows. The line between them is drawn explicitly in [**STATUS.md**](STATUS.md), and every limitation is listed in [**LIMITATIONS.md**](LIMITATIONS.md). Read those before relying on it.

## Why this exists

The AI-for-science market is crowded with tools that *generate*. Far fewer help you *check*: recompute a reported p-value, catch a sample size that does not match its claimed power, screen a manuscript against STROBE, or grade a claim's evidence instead of treating it as binary fact. Scriptorium aims at that under-served rigor layer — and keeps the confidential reviewer path offline, because manuscript confidentiality is a professional obligation.

## What it can do today

**Deterministic core (tested engines — numbers carry a provenance trace):**
- Sample-size / power for **two-sample t, paired t, two-proportion, and one-way ANOVA** designs.
- Statistical sanity checks: assumption tests (Shapiro / Levene), p/CI recomputation with claimed-value mismatch flagging, GRIM mean-consistency, Mann-Whitney, chi-square, Fisher exact.
- Reporting-guideline keyword screen for **STROBE, CONSORT, PRISMA**.
- Structural citation hygiene (orphan references, dangling markers).
- Group-sequential boundaries (O'Brien-Fleming via gsDesign).
- Graduated epistemic grading with weakest-link aggregation.

**Agent-guided workflows (model-reasoned, not engine-backed):**
- Confidential offline manuscript refereeing (`peer-reviewer`).
- Literature retrieval + credibility grading (`research-scout`, `literature-search`).
- Resource-acquisition advice (`librarian`), broad statistical analysis (`statistician`), IMRaD structure audit, PEER paraphrase, URL capture.

See [STATUS.md](STATUS.md) for the precise component-by-component matrix.

## What it cannot do yet

- Power/sample-size for **one-sample t, correlation, survival (log-rank), and regression** — documented in the skill, but **agent-guided** (statsmodels/formula fallback), not yet a tested engine. Planned for v0.4.0.
- A shared, tested config parser — `profile.md` is currently a documented convention each component follows, not a mechanically enforced contract. Planned for v0.4.0.
- Semantic citation *support* (does the source actually back the claim) and contradiction-detection against your own notes — planned, not present.
- It is **not** a medical decision system and **not** a replacement for expert review. See [LIMITATIONS.md](LIMITATIONS.md).

## Install

```
/plugin marketplace add kicrazom/scriptorium
/plugin install scriptorium@scriptorium
```

## Quickstart

The deterministic engines are plain JSON-in / JSON-out CLIs you can run directly:

```bash
echo '{"test":"two_sample_t","effect_size":0.40,"alpha":0.05,"power":0.80,"ratio":1.0}' \
  | python scripts/core/power_sample_size.py
```

Output (abridged) — note the `finding.source` provenance trace:

```json
{"status":"ok","data":{"n_per_group":100,"n_total":200,
  "finding":{"status":"operational_fact","confidence":1.0,
             "source":"scripts/core/power_sample_size.py#run=..."}}}
```

More input → output fixtures live in [`examples/`](examples/).

## Components

The name evokes the medieval *scriptorium* — the room where manuscripts were written, corrected, and stored. That triad (writer, reviewer, librarian) maps onto the core agents. Status labels (implemented / partial / agent-guided) are in [STATUS.md](STATUS.md).

### Agents

| Agent | Stage | What it does |
|---|---|---|
| [peer-reviewer](agents/peer-reviewer.md) | REVIEW | Confidential, offline manuscript referee — guideline + statistical + IMRaD + integrity rubric, never transmits the manuscript. |
| [librarian](agents/librarian.md) | EVALUATE | Acquisition advisor for books, courses, repos, and bundles — anti-hype verdict separating facts, marketing, public reviews, and ROI. |
| [research-scout](agents/research-scout.md) | DISCOVER | Literature retrieval with tiered-source credibility grading, dedup, and compare-to-knowledge-base — returns a proposal, never writes. |
| [statistician](agents/statistician.md) | ANALYZE | Do-your-own-analysis agent — calls the tested engines for the operations they cover, degrades to advisory + a runnable script otherwise. |

### Skills

| Skill | Stage | What it does |
|---|---|---|
| [literature-search](skills/literature-search/SKILL.md) | DISCOVER | Structured database query → literature note; PMIDs/DOIs from tool responses only, zero invented citations. |
| [reporting-guideline-check](skills/reporting-guideline-check/SKILL.md) | REVIEW | Reporting checklist (STROBE/CONSORT/PRISMA/TRIPOD + extended) → compliance table, gap list, fixes. |
| [epistemic-status](skills/epistemic-status/SKILL.md) | all | Graduated evidence status + confidence + source independence for any claim, with explicit promotion thresholds. |
| [field-note-from-url](skills/field-note-from-url/SKILL.md) | INGEST | URL → structured note with provenance frontmatter; stub pattern for blocked sources. |
| [manuscript-imrad](skills/manuscript-imrad/SKILL.md) | WRITE | Structure-audit a draft against IMRaD; claims-vs-data alignment, explicit Limitations, spin-flagging. |
| [peer-paraphrase](skills/peer-paraphrase/SKILL.md) | WRITE | Academic paraphrasing by the PEER framework (Point → Evidence → Explanation → Repeat). |
| [power-sample-size](skills/power-sample-size/SKILL.md) | ANALYZE | A-priori power & sample-size + sensitivity table + Methods sentence; engine-backed for four designs, agent-guided beyond. |
| [interim-analysis-reviewer](skills/interim-analysis-reviewer/SKILL.md) | REVIEW | Clinical-trial interim-analysis reviewer — DSMB/SAP, alpha-spending, stopping-boundary governance gaps. |

## Privacy & security

The reviewer path is offline by design (no network tools) and, where the host supports it, network-sandboxed — an operational confidentiality boundary, not cryptographic isolation. Read-only retrieval, no manuscript indexing, no paywall bypass. Full model: [PRIVACY.md](PRIVACY.md), [SECURITY.md](SECURITY.md).

## Configuration

Runs with universal defaults and no setup. To personalize (journal scope, knowledge-base path, stats runtime, strict clinical epistemics), create a profile:

```
/scriptorium-init
```

Resolution order, first match wins: `./.scriptorium/profile.md` → `~/.scriptorium/profile.md` → built-in defaults. Field reference: [docs/configuration.md](docs/configuration.md). (A shared, tested parser is on the [roadmap](ROADMAP.md); today each component follows the convention via its prompt.)

## Ethos

Anti-hallucination first — factual claims carry a source trace; numbers, citations, and doses come only from tool responses, never the model; absences are reported, not filled. Evidence is graduated (speculative → working → corroborated → operational → canonical, + contradicted), never binary. No paywall bypass, no piracy, no ToS-violating scraping. The peer-review path never transmits manuscript content.

## Roadmap

Phased toward a stable, validated `1.0.0` — see [ROADMAP.md](ROADMAP.md). Guiding rule: every README promise is labelled **implemented**, **agent-guided**, or **planned**, and every *implemented* feature has a test, an example, and a documented failure mode.

## Pairs with

Whole-manuscript authoring — generating and polishing a complete paper end-to-end — is a separate concern served by a dedicated scientific-writing workflow. Use that for full-manuscript craft; use Scriptorium for the surrounding rigor, review, and lifecycle.

## License & contributing

[MIT](LICENSE) — maximum public reuse. Contributions welcome; see [CONTRIBUTING.md](CONTRIBUTING.md) for component conventions and the anti-hallucination principles every component must uphold.
