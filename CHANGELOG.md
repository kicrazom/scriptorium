# Changelog

All notable changes to scriptorium are documented here. Format loosely follows
[Keep a Changelog](https://keepachangelog.com/); versioning is [SemVer](https://semver.org/).

## [0.2.0] — 2026-06-06

**Repositioning:** Scriptorium becomes the **Sovereign + Rigor** layer above scientific
writing — it audits / verifies / computes / grades rather than generates, complementing (not
replacing) generative tools. Two pillars (offline-first + deterministic rigor) with a
graduated epistemic-status spine on every output. Layered architecture (Approach A):
deterministic L0 core, pluggable L1 KB-provider, thin model-agnostic L2 orchestration,
orthogonal L3 mode-guard.

### Added
- L0 deterministic core: `scripts/lib/` (json_io, provenance, epistemic spine) and engines
  `epistemic_grade`, `power_sample_size`, `stat_run` (assumptions / recompute / GRIM),
  `guideline_check` (STROBE), `citation_parse` (structural hygiene), `interim_boundaries`
  (gsDesign R-dispatch) — each a JSON-contract CLI with golden tests.
- L1 KB-provider: pluggable `query()` contract, `folder` + `obsidian` adapters, `rag`/`cag`
  stubs, guard-integrated `kb/query.py`.
- L3 mode-guard: defense-in-depth egress control (mode declaration, import audit, honest
  process sandbox) with truthful `status()` disclosure — never claims isolation it cannot make.
- `scripts/run_tests.sh` pre-push quality gate (44 tests + structure validators + guard status).

### Changed
- L2 migration to single-source-of-truth engines: `power-sample-size` and `statistician` now
  call the tested L0 engines (provenance-traced) instead of ad-hoc inline computation;
  `peer-reviewer` flags machine-checkable inconsistencies (GRIM / p-recompute / power-sanity)
  for offline recheck by the statistician, preserving manuscript confidentiality.
- Reviewer-path agents (`peer-reviewer`, reporting/interim review skills) remain `Read/Grep/Glob`
  only — capability-removal kept intact as the Sovereign moat; engines are concentrated in the
  Bash-capable `statistician`.

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
