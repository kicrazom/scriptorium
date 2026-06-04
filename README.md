# Scriptorium

**A Claude Code toolkit for the scientific knowledge lifecycle — protect your time, attention, and rigor.**

Scriptorium is a single Claude Code plugin that bundles four agents and eight skills for the full arc of research work: discovering literature, evaluating what's worth reading, ingesting sources with provenance, running classical and Bayesian analysis, drafting in IMRaD, refereeing manuscripts offline, and keeping the whole knowledge base honest. Every component is anti-hallucination-first (claims carry a source trace, numbers come from tool responses, absences are reported as findings), uses graduated epistemics instead of binary fact/inference, and ships with universal defaults so it works out-of-the-box for any user — personalize it later with an optional `profile.md`.

## Install

```
/plugin marketplace add kicrazom/scriptorium
/plugin install scriptorium@scriptorium
```

## Components

The name evokes the medieval *scriptorium* — the room where manuscripts were written, corrected, and stored. That triad (writer, reviewer, librarian) maps onto the core agents.

### Agents

| Agent | Stage | What it does |
|---|---|---|
| [peer-reviewer](agents/peer-reviewer.md) | REVIEW | Confidential, offline manuscript referee — guideline + statistical + IMRaD + integrity rubric, never transmits the manuscript. |
| [librarian](agents/librarian.md) | EVALUATE | Acquisition advisor for books, courses, repos, and bundles — anti-hype verdict separating facts, marketing, public reviews, and ROI. |
| [research-scout](agents/research-scout.md) | DISCOVER | Literature retrieval with tiered-source credibility grading, dedup, and compare-to-knowledge-base — returns a proposal, never writes. |
| [statistician](agents/statistician.md) | ANALYZE | Do-your-own-analysis agent for classical and Bayesian statistics — degrades to advisory + a runnable script when no runtime is present. |

### Skills

| Skill | Stage | What it does |
|---|---|---|
| [literature-search](skills/literature-search/SKILL.md) | DISCOVER | Structured database query → literature note; PMIDs/DOIs from tool responses only, zero invented citations. |
| [reporting-guideline-check](skills/reporting-guideline-check/SKILL.md) | REVIEW | Item-by-item reporting checklist (STROBE/CONSORT/PRISMA/TRIPOD + extended) → compliance table, gap list, fixes. |
| [epistemic-status](skills/epistemic-status/SKILL.md) | all | Assign graduated evidence status + confidence + source independence to any claim, with explicit promotion thresholds. |
| [field-note-from-url](skills/field-note-from-url/SKILL.md) | INGEST | URL (paper/repo/video/blog/docs) → structured note with provenance frontmatter; stub pattern for blocked sources. |
| [manuscript-imrad](skills/manuscript-imrad/SKILL.md) | WRITE | Scaffold + structure-lint a draft against IMRaD; claims-vs-data alignment, explicit Limitations, spin-flagging. |
| [peer-paraphrase](skills/peer-paraphrase/SKILL.md) | WRITE | Academic paraphrasing by the PEER framework (Point → Evidence → Explanation → Repeat), not synonym-swap. |
| [power-sample-size](skills/power-sample-size/SKILL.md) | ANALYZE | A-priori power & sample-size determination + sensitivity table + ready Methods sentence; flags post-hoc power as invalid. |
| [interim-analysis-reviewer](skills/interim-analysis-reviewer/SKILL.md) | REVIEW / ANALYZE | Clinical-trial interim-analysis reviewer — DSMB/SAP, alpha-spending, stopping boundaries, ICH-E9 governance gaps. |

## Lifecycle

```
DISCOVER → EVALUATE → INGEST → ANALYZE → WRITE → REVIEW → MAINTAIN
```

## Configuration

Scriptorium runs with sensible universal defaults and no setup. To personalize (journal scope, knowledge-base path, preferred stats runtime, strict clinical epistemics, etc.), create a profile:

```
/scriptorium-init
```

This copies the documented template to `./.scriptorium/profile.md` (keep it git-ignored — your settings stay yours). Each component resolves its profile at start, reading the **first** that exists:

1. `./.scriptorium/profile.md` — project-local
2. `~/.scriptorium/profile.md` — user-global
3. none → universal defaults

See [docs/configuration.md](docs/configuration.md) for the full field reference.

## Ethos

Anti-hallucination first — every factual claim carries a source trace, and numbers, citations, and doses come only from tool responses, never the model; absences are reported, not filled. Evidence is graduated (speculative → working → corroborated → operational → canonical, + contradicted), never binary fact/inference. No paywall bypass, no piracy, no ToS-violating scraping — public metadata, previews, and public reviews only. The peer-review path is offline and never transmits manuscript content.

## Pairs with

Scriptorium covers paragraph-level (peer-paraphrase) and document-structure (manuscript-imrad) writing. **Whole-manuscript craft** — generating and polishing a complete paper end-to-end — is a separate concern, served by a dedicated scientific-writing workflow. Use that for full-manuscript authoring; use Scriptorium for the surrounding lifecycle.

## License & contributing

[MIT](LICENSE) — maximum public reuse. Contributions welcome; see [CONTRIBUTING.md](CONTRIBUTING.md) for the roster process, component conventions, and the shared anti-hallucination principles every component must uphold.
