# Roadmap

Semantic versioning. Nothing ships to a higher tier until the lower one is real (tests,
examples, honest docs). `1.0.0` is gated on a stable, documented, validated API — not on
feature count.

## v0.2.0 — Layered foundation ✅ (released)
- Deterministic L0 core: epistemic spine, power (two-sample t), stat sanity
  (assumptions / recompute / GRIM), reporting-guideline screen (STROBE), citation hygiene,
  group-sequential boundaries (gsDesign R-dispatch).
- Pluggable KB-provider (folder / obsidian; rag / cag stubs).
- Mode-guard: defense-in-depth offline reviewer path with honest status disclosure.
- 44 tests (golden + contract + behavior).

## v0.3.0 — Credibility release ✅ (released)
- **Docs:** honest README (implemented / agent-guided / planned labels), STATUS matrix,
  LIMITATIONS, PRIVACY, SECURITY, this roadmap.
- **CI:** GitHub Actions, Python 3.10–3.12, pytest.
- **Examples:** input → output fixtures for the power engine.
- **Engine expansion:** power families `paired_t`, `two_proportions`, `one_way_anova`;
  tests `mann_whitney`, `chi_square`, `fisher`; reporting guidelines CONSORT + PRISMA.

## v0.4.0 — Statistics core expansion ✅ (released)
- Power: `one_sample_t`, `correlation`, `survival_logrank_events` (Schoenfeld events).
- Shared, tested config parser `scripts/lib/profile.py` (resolve → load → merge → warn).
- JSON Schema I/O contracts (`schemas/`), enforced against the example fixtures in CI.

## v0.4.1 — Core hardening ✅ (released)
- **GRIMMER** (SD granularity consistency) — via R-dispatch to the reference `scrutiny`;
  the known-buggy test 3 (scrutiny #80) is demoted to indeterminate, never a false flag.
- Input validation for the power engine; golden fixtures for all designs; blocking CI lint.

## v0.4.2 — Regression power + config wiring ✅ (released)
- `linear_regression` power (Cohen f², noncentral F; validated vs Cohen/G*Power) — eight design families.
- `scripts/lib/profile.py` CLI; Bash-capable components (`statistician`, `power-sample-size`)
  now resolve config through the tested parser.

## v0.5.0 — Agent validation, deterministic core ✅ (released)
- ✅ `injection_scan` engine + adversarial fixture corpus + tests (prompt-injection screen).
- ✅ Structural fake-citation detection (already covered by `citation_parse`).
- ⏳ LLM-judged behavioural harness (does an agent *refuse* an embedded directive?), sample
  peer-review reports, reporting-guideline behavioural fixtures — model-output, no golden
  answer; needs an LLM-judge harness. Tracked honestly, not claimed as tested.
- ⏳ Each fixed bug becomes a regression fixture (ongoing convention).

## v1.0.0 — Stable public release ✅ (released)
- Uniform engine envelope contract (all 9 engines) + JSON schemas + STABILITY.md (SemVer + deprecation policy).
- Coverage measured honestly (subprocess) + gated; two CI jobs (matrix + R).
- `epistemic_grade` conformed to the envelope contract.

## Post-1.0 (1.x — additive, contract-preserving)
- LLM-judged behavioural harness for the prompt layer (agent refusing injection; sample reviews).
- More power families (regression variants), more `stat_run` ops, more guidelines.
- Per-engine bespoke schemas (beyond the shared envelope), semantic citation-support,
  contradiction-detection vs the vault.

## Principle
Every README promise carries one of three labels — **implemented**, **agent-guided**, or
**planned**. Every *implemented* feature has a test, an example, and a documented failure mode.
