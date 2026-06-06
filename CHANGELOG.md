# Changelog

All notable changes to scriptorium are documented here. Format loosely follows
[Keep a Changelog](https://keepachangelog.com/); versioning is [SemVer](https://semver.org/).

## [1.0.0] — 2026-06-06 — Stable deterministic-core contract

First stable release. The deterministic core's contract is now frozen under SemVer (see
[STABILITY.md](STABILITY.md)); the model-driven prompt layer continues to evolve.

### Added
- **Uniform engine envelope contract** — every one of the nine L0 engines returns
  `{status, data{finding}, …}` on success / `{status:error, message}` on failure. Specified by
  `schemas/envelope.schema.json` and verified for all engines in `tests/test_envelope_contract.py`
  (one committed output fixture per engine under `tests/fixtures/envelopes/`).
- **STABILITY.md** — the SemVer contract: what is frozen (engine invocation, envelope, finding,
  power/profile schemas, provenance) vs what may still evolve (additive coverage, prompt wording,
  the experimental LLM-judge harness) + a deprecation policy.

### Changed
- `epistemic_grade` now also emits a `finding` (its aggregate re-expressed as a graded finding),
  so it conforms to the uniform envelope contract like every other engine.

### Stable surface
9 deterministic engines (power: 8 designs; stat_run: 6 ops; guideline_check: STROBE/CONSORT/PRISMA;
citation_parse; epistemic_grade; interim_boundaries/gsDesign; grimmer/scrutiny; injection_scan),
pluggable KB-provider, mode-guard, tested config parser. 105 tests, two CI jobs (matrix 3.10–3.12
+ R-engines), coverage ~86% gated ≥80%, blocking ruff.

## [0.5.2] — 2026-06-06 — Coverage, R-CI, architecture doc

### Added
- **Coverage measurement + gate** — `pytest-cov` with `patch = subprocess` (the engines run as
  subprocesses, so this captures their real execution, not just imported modules). Real coverage
  **~86%**, CI-enforced at **≥80%** (`fail_under` in `pyproject.toml`). Naive `--cov` would have
  reported a misleading 23% — fixed by measuring subprocesses honestly.
- **`ci-r.yml`** — a dedicated CI job that installs R + `gsDesign` + `scrutiny` and actually runs
  the R-dispatch engine tests (`grimmer`, `interim_boundaries`), which skip on the stock runner.
- **`ARCHITECTURE.md`** — layered-design diagram + request flow + policy boundaries (60-second
  overview), linked from the README honest-scope note.

### Changed
- README: "small deterministic core" → "tested deterministic core" (nine engines — "small" was
  misleading); added coverage details to the Testing section.

## [0.5.1] — 2026-06-06 — Doc consistency + test discoverability

### Fixed
- STATUS.md prompt-layer row said `power-sample-size` is "engine-backed for the four families
  above" — stale since the engine grew to eight designs. Now points to the full design table.

### Added
- A **Testing** section in the README documenting the test layout. The engine known-value,
  input-validation, and deterministic-provenance tests already existed in
  `tests/core/test_power_sample_size.py` (and the other engines in `tests/core/` / `tests/lib/`);
  this makes them discoverable to readers who expect a flat `tests/` directory.

## [0.5.0] — 2026-06-06 — Agent validation (deterministic core)

### Added
- **`injection_scan` engine** — a deterministic prompt-injection screen over untrusted
  documents, operationalising the SECURITY.md threat model (*untrusted documents are data, not
  instructions*). Curated, imperative-injection-specific patterns; hits are findings to report,
  never directives to obey. It is a **heuristic screen** — `working_hypothesis` findings, never
  a confident safe/malicious verdict.
- **Adversarial fixture corpus** (`tests/fixtures/adversarial/`): an injection manuscript and a
  clean control, with `tests/core/test_injection_scan.py` asserting the injection is flagged and
  the clean control passes (no false positives).
- `tests/fixtures/adversarial/README.md` documenting, honestly, what is deterministically tested
  (injection_scan, structural fake-citation via `citation_parse`) vs what remains a manual /
  LLM-judged behavioural harness (whether an agent *refuses* an embedded directive) — tracked as
  future work, not claimed as tested.

### Notes
- `peer-reviewer` already treats prompt-injection text as a research-integrity red flag at the
  prompt level (it has no `Bash`); the engine serves the Bash-capable orchestration layer.

## [0.4.2] — 2026-06-06 — Regression power + config wiring

### Added
- **`linear_regression` power** — total N for a fixed-model multiple regression via Cohen's f²
  and the noncentral F (iterated), matching Cohen's tables and G*Power. Brings the engine to
  eight design families, all with golden fixtures validated against the schemas.
- **Config parser CLI** — `python scripts/lib/profile.py` prints the merged profile as JSON.
  The Bash-capable components (`statistician` agent, `power-sample-size` skill) now resolve
  config by calling the tested parser instead of hand-parsing `profile.md`.

### Changed
- README / STATUS reconciled: regression is now implemented (not agent-guided); the config
  parser is wired into the Bash-capable components (offline read-only agents still read the
  file directly, by design).

## [0.4.1] — 2026-06-06 — Core hardening

Theme: tighten what already exists — validation, complete evidence, stricter CI.

### Added
- **GRIMMER engine** (`scripts/core/grimmer.py`) — SD granularity consistency via R-dispatch
  to the reference `scrutiny` package. scrutiny has a known bug (issue #80) where GRIMMER
  "test 3" can false-positive; a test-3-only failure is therefore **demoted to an indeterminate
  finding** (working_hypothesis), never a confident inconsistency. GRIM and tests 1–2 are sound.
- **Input validation** in `power_sample_size` — rejects out-of-range or degenerate inputs
  (`r = 0`, `hazard_ratio = 1`, `p1 = p2`, alpha/power outside (0,1), etc.) with a clear error
  instead of dividing by zero.
- **Golden fixtures for all seven power designs** (input + output); `tests/test_schemas.py`
  now validates every one against the JSON schemas.

### Changed
- **CI lint is now blocking** — removed the advisory `ruff … || true`; added a `[tool.ruff]`
  config (line length, deliberate test-only ignores). The tree is ruff-clean.
- README: replaced the stale "engine-backed for four designs" wording with a pointer to the
  live design table in STATUS.md.

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
