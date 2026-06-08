# Engine I/O schemas

JSON Schema (draft 2020-12) contracts for the deterministic engines. They turn "it returns
some JSON" into a checked contract.

| Schema | Describes |
|---|---|
| `envelope.schema.json` | the uniform `ok`/`error` + graded `finding` contract every engine conforms to (v1.0.0 stable) |
| `finding.schema.json` | the graded finding every engine emits |
| `power_request.schema.json` | input to `scripts/core/power_sample_size.py` (per-`test` required fields) |
| `power_response.schema.json` | bespoke response contract for `power_sample_size` (references `finding`) |
| `stat_run_response.schema.json` | bespoke response for `scripts/core/stat_run.py` (op-dispatched: grim / recompute / assumptions / …) |
| `guideline_check_response.schema.json` | bespoke response for `scripts/core/guideline_check.py` |
| `citation_parse_response.schema.json` | bespoke response for `scripts/core/citation_parse.py` |
| `injection_scan_response.schema.json` | bespoke response for `scripts/core/injection_scan.py` |
| `grimmer_response.schema.json` | bespoke response for `scripts/core/grimmer.py` |
| `interim_boundaries_response.schema.json` | bespoke response for `scripts/core/interim_boundaries.py` |
| `epistemic_grade_response.schema.json` | bespoke response for `scripts/core/epistemic_grade.py` |
| `profile.schema.json` | the YAML block of `profile.md` (parsed by `scripts/lib/profile.py`) |

These are **enforced**, not decorative: `tests/test_schemas.py` validates the committed
[`examples/`](../examples) fixtures against the power + finding + profile schemas, and
`tests/test_engine_schemas.py` validates a committed representative output per engine
(`tests/fixtures/envelopes/`) against its bespoke per-engine response schema — plus a
negative control per engine proving the schema actually rejects malformed output. Validation
runs in CI.

Scope note: every L0 engine now carries both the shared envelope contract and a bespoke
per-engine response schema. Runtime enforcement *inside* the engines (an engine validating
its own output before returning) remains planned — see [../ROADMAP.md](../ROADMAP.md).
