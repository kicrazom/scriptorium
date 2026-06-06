# Engine I/O schemas

JSON Schema (draft 2020-12) contracts for the deterministic engines. They turn "it returns
some JSON" into a checked contract.

| Schema | Describes |
|---|---|
| `power_request.schema.json` | input to `scripts/core/power_sample_size.py` (per-`test` required fields) |
| `power_response.schema.json` | the engine's `ok`/`error` envelope (references `finding`) |
| `finding.schema.json` | the graded finding every engine emits |
| `profile.schema.json` | the YAML block of `profile.md` (parsed by `scripts/lib/profile.py`) |

These are **enforced**, not decorative: `tests/test_schemas.py` validates the committed
[`examples/`](../examples) fixtures against them and checks that malformed requests are
rejected. Validation runs in CI.

Scope note: schemas currently cover the `power_sample_size` engine, the shared finding, and
the profile. Schemas for the other engines (`stat_run`, `guideline_check`, etc.) and runtime
enforcement inside the engines are planned — see [../ROADMAP.md](../ROADMAP.md).
