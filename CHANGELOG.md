# Changelog

All notable changes to scriptorium are documented here. Format loosely follows
[Keep a Changelog](https://keepachangelog.com/); versioning is [SemVer](https://semver.org/).

## [0.4.0] — 2026-06-06 — Statistics core expansion

### Added
- **Power/sample-size families:** `one_sample_t`, `correlation` (Fisher z, closed form),
  `survival_logrank_events` (Schoenfeld; returns required events). The engine now covers
  seven designs, each self-documenting its `method` and `assumptions`.
- **Config parser** `scripts/lib/profile.py` — resolves `profile.md` (project → user →
  defaults), extracts the YAML block, merges over universal defaults, and warns on unknown
  sections instead of crashing. Tested behaviorally.
- **JSON Schema I/O contracts** (`schemas/`: power request/response, finding, profile),
  enforced against the committed example fixtures in `tests/test_schemas.py`.
- **Examples:** `correlation` input/output fixture (validated against the schemas).

### Deferred
- **GRIMMER** moved to v0.4.1 — deferred until it can be ported from and validated against a
  reference implementation (`scrutiny` / `rsprite2`). Shipping an unverified statistic would
  defeat the tool's purpose.
- Regression-power approximation, and routing agents through the new parser → v0.4.1.

## [0.3.0] — 2026-06-06 — Credibility release

Theme: *less manifesto, more evidence.* Claims are now drawn precisely against the
implementation, with CI proving the test suite and examples showing real input → output.

### Added
- **Engine expansion.** Power/sample-size families `paired_t`, `two_proportions` (Cohen's h),
  `one_way_anova`; statistical tests `mann_whitney`, `chi_square`, `fisher`; reporting
  guidelines CONSORT (2010) and PRISMA (2020) alongside STROBE.
- **Self-documenting power output.** Each result now carries `method` (the exact routine) and
  `assumptions` (alpha, power, alternative, effect input) next to the provenance trace.
- **CI.** GitHub Actions, Python 3.10–3.12, pytest (54 tests) + advisory ruff.
- **Examples.** `examples/power-sample-size/` — verified, reproducible input/output fixtures.
- **Honest docs.** `STATUS.md` (deterministic-core vs prompt-layer matrix), `LIMITATIONS.md`,
  `PRIVACY.md`, `SECURITY.md`, `ROADMAP.md`; README rewritten with explicit *what it can do
  today* / *what it cannot do yet* and implemented / agent-guided / planned labels.

### Changed
- README no longer over-claims: "every number from a tested engine" is now scoped to the
  designs the engine actually backs, with the rest labelled agent-guided.

### Deferred
- GRIMMER (SD granularity consistency) — needs a careful, separately-tested algorithm (v0.4.0).
- Shared config parser `scripts/lib/profile.py` and engine JSON schemas (v0.4.0).

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
