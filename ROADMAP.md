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

## v0.4.1 — Core hardening (released, partial)
- ✅ **GRIMMER** (SD granularity consistency) — via R-dispatch to the reference `scrutiny`;
  the known-buggy test 3 (scrutiny #80) is demoted to indeterminate, never a false flag.
- ✅ Input validation for the power engine; golden fixtures for all seven designs; blocking CI lint.
- ⏳ Regression-power approximation — still planned.
- ⏳ Route agents/skills through `scripts/lib/profile.py` (enforce the config contract, not just
  follow the convention) — still planned.

## v0.5.0 — Agent validation
- Prompt-injection fixtures; hallucinated-citation detection examples.
- Sample peer-review reports; reporting-guideline fixture set.
- Each fixed bug becomes a regression fixture.

## v1.0.0 — Stable public release
- Documented, stable engine I/O contracts (JSON schemas).
- Coverage reporting; reproducibility notes.
- Full component documentation; deprecation policy.

## Principle
Every README promise carries one of three labels — **implemented**, **agent-guided**, or
**planned**. Every *implemented* feature has a test, an example, and a documented failure mode.
