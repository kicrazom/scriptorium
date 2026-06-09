# Implementation status

Scriptorium has two layers: a **deterministic core** (Python engines + libraries, unit- and
golden-tested) and a **prompt layer** (agents and skills, defined as instructions for the
model). This page says exactly what is which, so you never have to guess whether a capability
is tested code or a guided workflow.

Legend — **Type:** `engine`/`lib` = deterministic code · `agent`/`skill` = prompt-defined.
**Backed:** is the capability executed by a tested engine, or reasoned by the model?

## Deterministic core (tested code)

| Component | Type | Backed | Tests | Notes |
|---|---|---|---|---|
| `lib/epistemic` | lib | yes | ✅ | status ladder, weakest-link aggregation, finding schema |
| `lib/json_io` | lib | yes | ✅ | request parse + ok/error envelope |
| `lib/provenance` | lib | yes | ✅ | engine/KB source traces, seed-stable run ids |
| `core/epistemic_grade` | engine | yes | ✅ | aggregate findings → graded result |
| `core/power_sample_size` | engine | yes | ✅ | **see family table below** |
| `core/stat_run` | engine | yes | ✅ | `check_assumptions`, `recompute_ttest`, `grim`, `mann_whitney`, `chi_square`, `fisher` |
| `core/guideline_check` | engine | yes | ✅ | keyword-gap screen: STROBE, CONSORT, PRISMA |
| `core/citation_parse` | engine | yes | ✅ | structural hygiene: orphan refs, dangling markers |
| `core/interim_boundaries` | engine | yes | ✅¹ | group-sequential O'Brien-Fleming via gsDesign (R) |
| `core/grimmer` | engine | yes | ✅¹ | SD granularity consistency via `scrutiny` (R); demotes the known-buggy test 3 (scrutiny #80) to indeterminate |
| `core/injection_scan` | engine | yes | ✅ | heuristic prompt-injection screen over untrusted docs; 15 curated patterns (ignore/role-reassign/reveal-prompt + append-verbatim, citation-laundering, command/data exfil, base64-obfuscated); hits are findings to report, never directives to obey |
| `kb/` provider | engine | yes | ✅ | `folder`, `obsidian` implemented; `rag`, `cag` are stubs |
| `guard/egress_guard` | engine | yes | ✅ | defense-in-depth offline enforcement + honest status |

¹ `interim_boundaries` (R + gsDesign) and `grimmer` (R + scrutiny) tests skip automatically
where R / the package is absent (e.g. on the default CI runner), and run locally.

### `power_sample_size` — design family coverage

| Design (`test`) | Status |
|---|---|
| `two_sample_t` | implemented ✅ |
| `paired_t` | implemented ✅ |
| `one_sample_t` | implemented ✅ |
| `two_proportions` | implemented ✅ |
| `one_way_anova` | implemented ✅ |
| `correlation` | implemented ✅ (Fisher z, closed form) |
| `survival_logrank_events` | implemented ✅ (Schoenfeld; returns required **events**) |
| `linear_regression` | implemented ✅ (Cohen f², noncentral F; validated vs Cohen/G*Power) |

## Prompt layer (agents & skills)

| Component | Type | Backed | Notes |
|---|---|---|---|
| `peer-reviewer` | agent | no (delegates) | usable; confidential, offline, read-only; flags rechecks for the statistician to run; **injection-refusal behaviourally tested** (see below) |
| `research-scout` | agent | web/tool | usable; read-only, returns proposals, never writes; **injection-refusal behaviourally tested** |
| `librarian` | agent | web/tool | usable; acquisition advisor, anti-hype verdict; **injection-refusal behaviourally tested** |
| `statistician` | agent | partial | usable; calls the tested engines above for the operations they cover, degrades to advisory + runnable script otherwise |
| `power-sample-size` | skill | partial | engine-backed for the eight designs in the table above; other designs agent-guided |
| `reporting-guideline-check` | skill | partial | rich prose review; a deterministic keyword screen exists for STROBE/CONSORT/PRISMA |
| `epistemic-status` | skill | yes | backed by `lib/epistemic` |
| `interim-analysis-reviewer` | skill | no | reviews prespecification; *computing* boundaries is the statistician's engine |
| `field-note-from-url` | skill | no | agent-guided capture with provenance frontmatter |
| `manuscript-imrad` | skill | no | agent-guided structure audit (read-only) |
| `peer-paraphrase` | skill | no | agent-guided PEER-framework paraphrase |

## Configuration

| Item | Status |
|---|---|
| `scripts/lib/profile.py` (tested parser + CLI: resolve → load yaml-block → merge defaults → warn unknown) | implemented ✅ |
| Bash-capable components routed through the parser (`statistician`, `power-sample-size`) | done ✅ — they call the parser CLI |
| offline read-only agents routed through the parser | not applicable — no `Bash`; they read `profile.md` directly by design |
| `schemas/` (JSON Schema I/O contracts: envelope, finding, power request/response, profile) | implemented ✅, enforced in `tests/test_schemas.py` |
| uniform engine envelope contract (every engine → `ok`/`error` + graded `finding`) | implemented ✅, verified for all 9 engines in `tests/test_envelope_contract.py` (v1.0.0 stable contract) |
| per-engine bespoke response schemas (each engine's `data` payload pinned, not just the shared envelope) | implemented ✅, enforced in `tests/test_engine_schemas.py` (representative fixture + negative control per engine; v1.2.0) |

## Behavioral validation (prompt layer)

`injection_scan` (L0) *detects* injection patterns deterministically; detection is not refusal.
A two-layer harness tests whether an agent actually **refuses** an embedded directive:

| Component | Type | Backed | Notes |
|---|---|---|---|
| verdict / prompt-assembly / judgement-parsing / report-redaction / backend availability | lib | yes | ✅ deterministic, default CI (`tests/behavioral/`, 37 tests); 7 cases / 4 agents / 5 attack classes |
| `behavior_case` + `behavior_judgement` schemas | contract | yes | ✅ enforced against committed fixtures |
| model-gated harness (real agent + judge backend) | harness | model-judged | optional `llm_judge` mark; runs only with `SCRIPTORIUM_RUN_LLM_JUDGE=1` |

Backends are pluggable and skip-if-unavailable (R-engine convention): `claude_cli` (verified),
`codex_cli` (provisional argv), `local_vllm` (scaffolded, skip-if-unavailable, not yet validated
against a live model). The final verdict is recomputed from the
judge's scores, so a judge contradicting its own scores is overridden. Details:
[docs/behavioral-validation.md](docs/behavioral-validation.md).

See [ROADMAP.md](ROADMAP.md) for what each tier unlocks and [LIMITATIONS.md](LIMITATIONS.md)
for what this tool does not do.
