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
| `kb/` provider | engine | yes | ✅ | `folder`, `obsidian` implemented; `rag`, `cag` are stubs |
| `guard/egress_guard` | engine | yes | ✅ | defense-in-depth offline enforcement + honest status |

¹ `interim_boundaries` tests require R + gsDesign; they skip automatically where R is absent
(e.g. on the default CI runner), and run locally.

### `power_sample_size` — design family coverage

| Design (`test`) | Status |
|---|---|
| `two_sample_t` | implemented ✅ |
| `paired_t` | implemented ✅ |
| `two_proportions` | implemented ✅ |
| `one_way_anova` | implemented ✅ |
| `one_sample_t`, `correlation`, survival (log-rank events), regression power | planned (v0.4.0) — currently **agent-guided** in the `power-sample-size` skill via statsmodels/formula fallback |

## Prompt layer (agents & skills)

| Component | Type | Backed | Notes |
|---|---|---|---|
| `peer-reviewer` | agent | no (delegates) | usable; confidential, offline, read-only; flags rechecks for the statistician to run |
| `research-scout` | agent | web/tool | usable; read-only, returns proposals, never writes |
| `librarian` | agent | web/tool | usable; acquisition advisor, anti-hype verdict |
| `statistician` | agent | partial | usable; calls the tested engines above for the operations they cover, degrades to advisory + runnable script otherwise |
| `power-sample-size` | skill | partial | engine-backed for the four families above; other designs agent-guided |
| `reporting-guideline-check` | skill | partial | rich prose review; a deterministic keyword screen exists for STROBE/CONSORT/PRISMA |
| `epistemic-status` | skill | yes | backed by `lib/epistemic` |
| `interim-analysis-reviewer` | skill | no | reviews prespecification; *computing* boundaries is the statistician's engine |
| `field-note-from-url` | skill | no | agent-guided capture with provenance frontmatter |
| `manuscript-imrad` | skill | no | agent-guided structure audit (read-only) |
| `peer-paraphrase` | skill | no | agent-guided PEER-framework paraphrase |

## Configuration

| Item | Status |
|---|---|
| `profile.md` resolution (project → user → defaults) | documented convention; **no shared parser yet** |
| `scripts/lib/profile.py` (tested parser) | planned (v0.4.0) |

See [ROADMAP.md](ROADMAP.md) for what each tier unlocks and [LIMITATIONS.md](LIMITATIONS.md)
for what this tool does not do.
