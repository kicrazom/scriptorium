# Changelog

All notable changes to scriptorium are documented here. Format loosely follows
[Keep a Changelog](https://keepachangelog.com/); versioning is [SemVer](https://semver.org/).

## [Unreleased] — v0.2.0 (in progress)

### Added
- L0 deterministic core foundation: `scripts/lib/` (json_io, provenance, epistemic spine)
  and first engines `core/epistemic_grade.py`, `core/power_sample_size.py`, with golden tests.
- `scripts/run_tests.sh` pre-push quality gate.
- L0 engines: `stat_run` (assumptions, recompute, GRIM), `guideline_check` (STROBE),
  `citation_parse` (structural hygiene), `interim_boundaries` (gsDesign R-dispatch).
- L1 KB-provider: pluggable `query()` contract, `folder` + `obsidian` adapters, `rag`/`cag`
  stubs, guard-integrated `kb/query.py`.
- L3 mode-guard: defense-in-depth egress control (mode declaration, import audit, honest
  process sandbox) with truthful `status()` disclosure.

## [0.1.0] — 2026-06-04

### Added
- **4 agents:** `peer-reviewer` (confidential, offline manuscript referee), `librarian`
  (resource acquisition advisor), `research-scout` (literature retrieval + epistemic
  grading), `statistician` (classical + Bayesian analysis).
- **8 skills:** `literature-search`, `reporting-guideline-check`, `epistemic-status`,
  `field-note-from-url`, `manuscript-imrad`, `peer-paraphrase` (PEER framework),
  `power-sample-size`, `interim-analysis-reviewer`.
- **Config-driven universality** via `profile.md` (resolution order: `./.scriptorium/` →
  `~/.scriptorium/` → universal defaults).
- `/scriptorium-init` command; `plugin.json` + `marketplace.json`; MIT license.
- Validation scripts (JSON, frontmatter, structure) and worked examples per agent.
