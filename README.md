![Scriptorium](docs/assets/scriptorium-manuscript.png)

# Scriptorium

[![CI](https://github.com/kicrazom/scriptorium/actions/workflows/ci.yml/badge.svg)](https://github.com/kicrazom/scriptorium/actions/workflows/ci.yml)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](LICENSE)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20582861.svg)](https://doi.org/10.5281/zenodo.20582861)

**An early-stage Claude Code plugin for scientific-workflow rigor — audit, compute, and grade research, offline-first.**

Where generative tools *write*, Scriptorium *scrutinizes*: it recomputes statistics, screens reporting guidelines, audits citation hygiene, grades evidence on a graduated epistemic scale, and runs a confidential, offline manuscript-review path. It pairs a **tested deterministic core** (Python engines whose every number carries a provenance trace) with a **prompt layer** of agents and skills that reason over the rest. It complements generative writing tools; it does not replace them.

> **Honest scope.** As of v1.0.0 the **deterministic-core contract is stable** ([STABILITY.md](STABILITY.md)); the model-driven prompt layer keeps evolving. Which capabilities are tested code vs guided agent workflows is drawn explicitly in [**STATUS.md**](STATUS.md), every limitation is in [**LIMITATIONS.md**](LIMITATIONS.md), and the layered design is in [**ARCHITECTURE.md**](ARCHITECTURE.md) (60-second overview). Read those before relying on it.

## Why this exists

The AI-for-science market is crowded with tools that *generate*. Far fewer help you *check*: recompute a reported p-value, catch a sample size that does not match its claimed power, screen a manuscript against STROBE, or grade a claim's evidence instead of treating it as binary fact. Scriptorium aims at that under-served rigor layer — and keeps the confidential reviewer path offline, because manuscript confidentiality is a professional obligation.

## What it can do today

**Deterministic core (tested engines — numbers carry a provenance trace):**
- Sample-size / power for **two-sample t, paired t, one-sample t, two-proportion, one-way ANOVA, correlation, survival (log-rank events)**, and **linear regression** (Cohen f², noncentral F) designs — each result self-documents its `method` and `assumptions`, and rejects degenerate inputs.
- Statistical sanity checks: assumption tests (Shapiro / Levene), p/CI recomputation with claimed-value mismatch flagging, GRIM mean-consistency, GRIMMER SD-consistency (via `scrutiny`; the known-buggy test 3 is demoted to *indeterminate*, never a false flag), Mann-Whitney, chi-square, Fisher exact.
- Reporting-guideline keyword screen for **STROBE, CONSORT, PRISMA**.
- Structural citation hygiene (orphan references, dangling markers).
- Prompt-injection screen over untrusted documents (`injection_scan`) — flags embedded directives as findings to report, never to obey (heuristic; treat-as-data, per [SECURITY.md](SECURITY.md)).
- Group-sequential boundaries (O'Brien-Fleming via gsDesign).
- Graduated epistemic grading with weakest-link aggregation.
- **Behavioral injection-refusal harness** — goes beyond *detecting* injection to verifying agents actually **refuse** an embedded directive. The core (schemas, verdict logic, untrusted-data prompt framing, redacted report) is deterministic and default-CI; a model-gated run against a real agent + judge backend (pluggable: `claude_cli` / `codex_cli` / `local_vllm`, skip-if-unavailable) sits behind `SCRIPTORIUM_RUN_LLM_JUDGE=1`. See [docs/behavioral-validation.md](docs/behavioral-validation.md).

**Agent-guided workflows (model-reasoned, not engine-backed):**
- Confidential offline manuscript refereeing (`peer-reviewer`).
- Literature retrieval + credibility grading (`research-scout`, `literature-search`).
- Resource-acquisition advice (`librarian`), broad statistical analysis (`statistician`), IMRaD structure audit, PEER paraphrase, URL capture.

See [STATUS.md](STATUS.md) for the precise component-by-component matrix.

## What it cannot do yet

- **Config parser is wired into the Bash-capable components only.** A tested parser (`scripts/lib/profile.py`, runnable as a CLI) now backs config resolution, and the `statistician` agent and `power-sample-size` skill call it. The offline read-only agents (e.g. `peer-reviewer`) still read `profile.md` directly — by design, since they have no `Bash`.
- Semantic citation *support* (does the source actually back the claim) and contradiction-detection against your own notes — planned, not present.
- Cross-runtime behavioral concordance (e.g. `claude_cli` vs `codex_cli` as independent judges) — supported by the harness but not yet run as a standing check; the shipped run is single-runtime (same-family agent + judge), an honest limitation noted in [docs/behavioral-validation.md](docs/behavioral-validation.md).
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

## Testing

The deterministic core is unit- and golden-tested. CI has two jobs: the main matrix runs the
suite on Python 3.10–3.12 with a blocking `ruff` lint (R-dispatch tests skip there); a dedicated
R job installs R + `gsDesign` + `scrutiny`, runs the **full** suite, and enforces coverage.
Coverage is **~86%**, gated at **≥80%** (`fail_under` in `pyproject.toml`) in the R job where
nothing skips; because the engines are tested as subprocesses, coverage uses `patch = subprocess`
so the number reflects their real execution, not just imported modules.

```bash
pip install -e ".[dev]"
pytest -q              # the full suite
pytest --cov -q        # with coverage (enforces the ≥80% gate)
```

Tests live next to what they cover, **not** in a flat `tests/` directory:

| Path | Covers |
|---|---|
| `tests/core/test_power_sample_size.py` | every power design: known-value/recompute assertions, input-validation rejections, deterministic-provenance check |
| `tests/core/test_stat_run.py`, `test_guideline_check.py`, `test_citation_parse.py`, `test_epistemic_grade.py`, `test_grimmer.py`, `test_injection_scan.py`, `test_interim_boundaries.py` | the other engines |
| `tests/lib/test_{json_io,provenance,epistemic,profile}.py` | shared libraries |
| `tests/test_schemas.py` | every example fixture validated against the JSON schemas, plus malformed-input rejection |

The `grimmer` and `interim_boundaries` tests need R (`scrutiny` / `gsDesign`) and skip
automatically when it is absent, so CI stays green on a stock runner.

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
| [power-sample-size](skills/power-sample-size/SKILL.md) | ANALYZE | A-priori power & sample-size + sensitivity table + Methods sentence; engine-backed for the designs listed in [STATUS.md](STATUS.md), agent-guided beyond. |
| [interim-analysis-reviewer](skills/interim-analysis-reviewer/SKILL.md) | REVIEW | Clinical-trial interim-analysis reviewer — DSMB/SAP, alpha-spending, stopping-boundary governance gaps. |

## Privacy & security

The reviewer path is offline by design (no network tools) and, where the host supports it, network-sandboxed — an operational confidentiality boundary, not cryptographic isolation. Read-only retrieval, no manuscript indexing, no paywall bypass. Full model: [PRIVACY.md](PRIVACY.md), [SECURITY.md](SECURITY.md).

## Configuration

Runs with universal defaults and no setup. To personalize (journal scope, knowledge-base path, stats runtime, strict clinical epistemics), create a profile:

```
/scriptorium-init
```

Resolution order, first match wins: `./.scriptorium/profile.md` → `~/.scriptorium/profile.md` → built-in defaults. Field reference: [docs/configuration.md](docs/configuration.md). A shared, tested parser (`scripts/lib/profile.py`) now backs this resolution; routing every agent through it (so the convention is enforced, not just followed) is in progress — see the [roadmap](ROADMAP.md).

## Ethos

Anti-hallucination first — factual claims carry a source trace; numbers, citations, and doses come only from tool responses, never the model; absences are reported, not filled. Evidence is graduated (speculative → working → corroborated → operational → canonical, + contradicted), never binary. No paywall bypass, no piracy, no ToS-violating scraping. The peer-review path never transmits manuscript content.

## Roadmap

Phased toward a stable, validated `1.0.0` — see [ROADMAP.md](ROADMAP.md). Guiding rule: every README promise is labelled **implemented**, **agent-guided**, or **planned**, and every *implemented* feature has a test, an example, and a documented failure mode.

## Pairs with

Whole-manuscript authoring — generating and polishing a complete paper end-to-end — is a separate concern served by a dedicated scientific-writing workflow. Use that for full-manuscript craft; use Scriptorium for the surrounding rigor, review, and lifecycle.

## License & contributing

**Code: [AGPL-3.0](LICENSE)** — free to use, run, and modify, but derivatives and network-served versions must publish their source under the same terms (no closed 1:1 reuse). **Scientific artifacts** (e.g. [`benchmarks/sci-writing-injection/`](benchmarks/sci-writing-injection/) — [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20582861.svg)](https://doi.org/10.5281/zenodo.20582861)) are **CC-BY-NC-4.0**, cited via their Zenodo DOI. Contributions welcome; see [CONTRIBUTING.md](CONTRIBUTING.md) for component conventions and the anti-hallucination principles every component must uphold.

> Relicensing note: releases up to and including v1.0.0 were published under MIT; those versions remain available under MIT. AGPL-3.0 applies going forward.
