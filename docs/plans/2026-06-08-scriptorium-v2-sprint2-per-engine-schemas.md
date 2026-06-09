# Sprint 2 — Per-Engine Bespoke Schemas Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give each of the 7 remaining L0 engines its own JSON Schema that validates the *engine-specific* `data` payload (not just the shared `finding`), enforced by a committed-fixture test — bringing every engine up to the contract rigor `power_sample_size` already has.

**Architecture:** Today every engine conforms to the shared `schemas/envelope.schema.json` (which only pins `status` + `data.finding`). `power_sample_size` additionally has a bespoke `schemas/power_response.schema.json` pinning its own fields. This sprint adds the same bespoke layer for the other 7 engines (`stat_run`, `guideline_check`, `citation_parse`, `injection_scan`, `grimmer`, `interim_boundaries`, `epistemic_grade`). Each bespoke schema reuses the envelope boilerplate (`status`/`message`/`data` + the `allOf` ok/error conditional), `$ref`s `finding.schema.json`, and pins the engine's own `data` fields. A new auto-discovering test (`tests/test_engine_schemas.py`) validates the already-committed `tests/fixtures/envelopes/<engine>.out.json` representative output against its schema, plus a per-engine negative control.

**Tech Stack:** Python 3.10–3.12, `jsonschema` + `referencing` (Draft 2020-12), pytest, ruff (BLOCKING in CI). R engines (`grimmer`, `interim_boundaries`) need no R at *schema-test* time — they validate the committed JSON fixture, not a live run.

---

## Design decisions (read before starting)

1. **Naming:** `schemas/<engine_stem>_response.schema.json`, where `<engine_stem>` is the engine filename without `.py` (e.g. `stat_run_response.schema.json`). This matches the existing `power_response.schema.json` convention.
2. **Boilerplate is identical across all 7** — copy the envelope wrapper verbatim; only `title`, `description`, `$id`, and `data.required` + `data.properties` change.
3. **`$ref` to finding:** every `data` requires `finding` via `{"$ref": "finding.schema.json"}`. The test registry resolves cross-file `$ref` exactly as `test_schemas.py` already does.
4. **Stable-shape engines** (`guideline_check`, `citation_parse`, `injection_scan`, `grimmer`, `interim_boundaries`, `epistemic_grade`) pin all their `data` fields as `required` + typed, with `additionalProperties: false` on `data` is **NOT** used — keep `additionalProperties` default (true) so provenance-internal additions don't break the contract; rigor comes from `required` + types.
5. **`stat_run` is op-dispatched** (`grim`, `check_assumptions`, `recompute_ttest`, `mann_whitney`, `chi_square`, `fisher`) → different `data` fields per op. Its schema requires ONLY `finding`, types the known optional fields when present, and leaves `additionalProperties` true. This is honest: the invariant is "a graded finding + typed-if-present numerics", not a fixed field set.
6. **Fixtures:** reuse the existing `tests/fixtures/envelopes/<engine>.out.json` (real engine outputs, already committed) as the positive case. No new positive fixtures needed. Negative controls live inline in the test.
7. **Out of scope (do NOT touch):** engine source code, agent prompts, the shared `envelope.schema.json`, `power_response.schema.json`. This sprint is schema + test + docs only.

---

## File Structure

- Create: `schemas/stat_run_response.schema.json`
- Create: `schemas/guideline_check_response.schema.json`
- Create: `schemas/citation_parse_response.schema.json`
- Create: `schemas/injection_scan_response.schema.json`
- Create: `schemas/grimmer_response.schema.json`
- Create: `schemas/interim_boundaries_response.schema.json`
- Create: `schemas/epistemic_grade_response.schema.json`
- Create: `tests/test_engine_schemas.py`
- Modify: `schemas/README.md` (document the new per-engine schemas)
- Modify: `STATUS.md`, `ROADMAP.md`, `CHANGELOG.md` (reconcile: per-engine schemas planned→implemented)

---

## Task 1: Test harness + first bespoke schema (`stat_run`)

**Files:**
- Create: `tests/test_engine_schemas.py`
- Create: `schemas/stat_run_response.schema.json`
- Reuses: `tests/fixtures/envelopes/stat_run.out.json` (already committed)

- [ ] **Step 1: Write the failing test harness**

Create `tests/test_engine_schemas.py`:

```python
"""Per-engine bespoke schemas (Sprint 2): each engine's committed representative output
validates against schemas/<engine>_response.schema.json, and a per-engine negative control
is rejected. Auto-discovers every *_response.schema.json so adding a schema extends coverage.
"""
import json
from pathlib import Path

import pytest

jsonschema = pytest.importorskip("jsonschema")
from referencing import Registry, Resource  # noqa: E402
from jsonschema import Draft202012Validator  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"
ENVELOPES = ROOT / "tests" / "fixtures" / "envelopes"

# schema stem (without _response) -> envelope fixture stem
FIXTURE_ALIAS = {"power": "power_sample_size"}

# Engines whose bespoke schema is delivered by THIS sprint (power already had one).
SPRINT2_ENGINES = [
    "stat_run", "guideline_check", "citation_parse", "injection_scan",
    "grimmer", "interim_boundaries", "epistemic_grade",
]


def _registry():
    resources = [
        (s.name, Resource.from_contents(json.loads(s.read_text())))
        for s in SCHEMAS.glob("*.json")
    ]
    return Registry().with_resources(resources)


def _validator(schema_name):
    schema = json.loads((SCHEMAS / schema_name).read_text())
    return Draft202012Validator(schema, registry=_registry())


def _fixture_for(engine):
    return ENVELOPES / f"{FIXTURE_ALIAS.get(engine, engine)}.out.json"


@pytest.mark.parametrize("engine", SPRINT2_ENGINES)
def test_each_sprint2_engine_has_a_response_schema(engine):
    assert (SCHEMAS / f"{engine}_response.schema.json").exists(), \
        f"missing schemas/{engine}_response.schema.json"


@pytest.mark.parametrize("engine", SPRINT2_ENGINES)
def test_engine_fixture_validates_against_bespoke_schema(engine):
    out = json.loads(_fixture_for(engine).read_text())
    _validator(f"{engine}_response.schema.json").validate(out)


# Per-engine negative controls: a minimally-mutated payload that MUST be rejected.
NEGATIVE_CONTROLS = {
    "stat_run": {"status": "ok", "data": {"n": "ten",  # n must be integer
                 "finding": {"claim": "x", "status": "operational_fact",
                             "confidence": 1.0, "source": "s", "source_independence": 1}}},
}


@pytest.mark.parametrize("engine", sorted(NEGATIVE_CONTROLS))
def test_negative_control_is_rejected(engine):
    with pytest.raises(jsonschema.ValidationError):
        _validator(f"{engine}_response.schema.json").validate(NEGATIVE_CONTROLS[engine])
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd ~/code/scriptorium && . .venv/bin/activate && pytest tests/test_engine_schemas.py -q`
Expected: FAIL — `test_each_sprint2_engine_has_a_response_schema` errors for all 7 (schemas absent), and the validator tests error on missing schema file.

- [ ] **Step 3: Create `schemas/stat_run_response.schema.json`**

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://github.com/kicrazom/scriptorium/schemas/stat_run_response.schema.json",
  "title": "StatRunResponse",
  "description": "Envelope returned by scripts/core/stat_run.py. Op-dispatched (grim, check_assumptions, recompute_ttest, mann_whitney, chi_square, fisher) so data fields vary by op; only finding is invariant. Known fields are typed when present.",
  "type": "object",
  "required": ["status"],
  "properties": {
    "status": {"type": "string", "enum": ["ok", "error"]},
    "message": {"type": "string", "description": "Present when status == error."},
    "data": {
      "type": "object",
      "required": ["finding"],
      "properties": {
        "consistent": {"type": "boolean"},
        "mean": {"type": "number"},
        "n": {"type": "integer"},
        "nearest_consistent": {"type": "array", "items": {"type": "number"}},
        "t": {"type": "number"},
        "df": {"type": "number"},
        "p": {"type": "number"},
        "ci95": {"type": "array", "items": {"type": "number"}, "minItems": 2, "maxItems": 2},
        "assumptions": {"type": "object"},
        "recommended_alternative": {"type": "string"},
        "finding": {"$ref": "finding.schema.json"}
      },
      "description": "grim: {consistent, mean, n, nearest_consistent}; recompute_ttest: {t, df, p, ci95}; check_assumptions: {assumptions, recommended_alternative}. All optional, typed when present."
    }
  },
  "allOf": [
    {"if": {"properties": {"status": {"const": "ok"}}}, "then": {"required": ["data"]}},
    {"if": {"properties": {"status": {"const": "error"}}}, "then": {"required": ["message"]}}
  ]
}
```

- [ ] **Step 4: Run the stat_run-relevant tests to verify pass**

Run: `cd ~/code/scriptorium && . .venv/bin/activate && pytest tests/test_engine_schemas.py -q -k stat_run`
Expected: 3 PASS (schema-exists, fixture-validates, negative-control-rejected for stat_run). The other 6 engines still FAIL — expected, delivered in later tasks.

- [ ] **Step 5: Commit**

```bash
cd ~/code/scriptorium
git add tests/test_engine_schemas.py schemas/stat_run_response.schema.json
git commit -m "test(schemas): per-engine schema harness + bespoke stat_run_response schema"
```

---

## Task 2: `guideline_check` bespoke schema

**Files:**
- Create: `schemas/guideline_check_response.schema.json`
- Reuses: `tests/fixtures/envelopes/guideline_check.out.json`

- [ ] **Step 1: Add a negative control to `tests/test_engine_schemas.py`**

In `NEGATIVE_CONTROLS`, add this entry (a `missing` item lacking required `id`/`item` keys → reject):

```python
    "guideline_check": {"status": "ok", "data": {
        "guideline": "strobe", "present": ["1a"],
        "missing": [{"oops": "no id"}],  # each missing item requires id + item
        "finding": {"claim": "x", "status": "working_hypothesis",
                    "confidence": 0.6, "source": "s", "source_independence": 1}}},
```

- [ ] **Step 2: Run to verify the new cases fail**

Run: `pytest tests/test_engine_schemas.py -q -k guideline_check`
Expected: FAIL — schema-exists + fixture-validates error (schema absent); negative-control errors (schema absent).

- [ ] **Step 3: Create `schemas/guideline_check_response.schema.json`**

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://github.com/kicrazom/scriptorium/schemas/guideline_check_response.schema.json",
  "title": "GuidelineCheckResponse",
  "description": "Envelope returned by scripts/core/guideline_check.py: keyword gap-screen of a manuscript against a reporting checklist (STROBE/CONSORT/PRISMA).",
  "type": "object",
  "required": ["status"],
  "properties": {
    "status": {"type": "string", "enum": ["ok", "error"]},
    "message": {"type": "string", "description": "Present when status == error."},
    "data": {
      "type": "object",
      "required": ["guideline", "present", "missing", "finding"],
      "properties": {
        "guideline": {"type": "string"},
        "present": {"type": "array", "items": {"type": "string"}},
        "missing": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["id", "item"],
            "properties": {"id": {"type": "string"}, "item": {"type": "string"}}
          }
        },
        "finding": {"$ref": "finding.schema.json"}
      }
    }
  },
  "allOf": [
    {"if": {"properties": {"status": {"const": "ok"}}}, "then": {"required": ["data"]}},
    {"if": {"properties": {"status": {"const": "error"}}}, "then": {"required": ["message"]}}
  ]
}
```

- [ ] **Step 4: Run to verify pass**

Run: `pytest tests/test_engine_schemas.py -q -k guideline_check`
Expected: 3 PASS.

- [ ] **Step 5: Commit**

```bash
cd ~/code/scriptorium
git add tests/test_engine_schemas.py schemas/guideline_check_response.schema.json
git commit -m "test(schemas): bespoke guideline_check_response schema + negative control"
```

---

## Task 3: `citation_parse` bespoke schema

**Files:**
- Create: `schemas/citation_parse_response.schema.json`
- Reuses: `tests/fixtures/envelopes/citation_parse.out.json`

- [ ] **Step 1: Add negative control**

In `NEGATIVE_CONTROLS` add (`n_references` as string → reject):

```python
    "citation_parse": {"status": "ok", "data": {
        "cited_markers": [1, 3], "n_references": "three",  # must be integer
        "orphan_references": [2], "dangling_citations": [],
        "finding": {"claim": "x", "status": "operational_fact",
                    "confidence": 1.0, "source": "s", "source_independence": 1}}},
```

- [ ] **Step 2: Run to verify fail**

Run: `pytest tests/test_engine_schemas.py -q -k citation_parse`
Expected: FAIL (schema absent).

- [ ] **Step 3: Create `schemas/citation_parse_response.schema.json`**

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://github.com/kicrazom/scriptorium/schemas/citation_parse_response.schema.json",
  "title": "CitationParseResponse",
  "description": "Envelope returned by scripts/core/citation_parse.py: structural citation hygiene (orphan references + dangling in-text markers). NOT semantic support (that is Sprint 3).",
  "type": "object",
  "required": ["status"],
  "properties": {
    "status": {"type": "string", "enum": ["ok", "error"]},
    "message": {"type": "string", "description": "Present when status == error."},
    "data": {
      "type": "object",
      "required": ["cited_markers", "n_references", "orphan_references", "dangling_citations", "finding"],
      "properties": {
        "cited_markers": {"type": "array", "items": {"type": "integer"}},
        "n_references": {"type": "integer", "minimum": 0},
        "orphan_references": {"type": "array", "items": {"type": "integer"}},
        "dangling_citations": {"type": "array", "items": {"type": "integer"}},
        "finding": {"$ref": "finding.schema.json"}
      }
    }
  },
  "allOf": [
    {"if": {"properties": {"status": {"const": "ok"}}}, "then": {"required": ["data"]}},
    {"if": {"properties": {"status": {"const": "error"}}}, "then": {"required": ["message"]}}
  ]
}
```

- [ ] **Step 4: Run to verify pass**

Run: `pytest tests/test_engine_schemas.py -q -k citation_parse`
Expected: 3 PASS.

- [ ] **Step 5: Commit**

```bash
cd ~/code/scriptorium
git add tests/test_engine_schemas.py schemas/citation_parse_response.schema.json
git commit -m "test(schemas): bespoke citation_parse_response schema + negative control"
```

---

## Task 4: `injection_scan` bespoke schema

**Files:**
- Create: `schemas/injection_scan_response.schema.json`
- Reuses: `tests/fixtures/envelopes/injection_scan.out.json`

- [ ] **Step 1: Add negative control**

In `NEGATIVE_CONTROLS` add (an injection item missing required `line` → reject):

```python
    "injection_scan": {"status": "ok", "data": {
        "injections": [{"pattern": "ignore-previous", "snippet": "..."}],  # missing line
        "finding": {"claim": "x", "status": "working_hypothesis",
                    "confidence": 0.6, "source": "s", "source_independence": 1}}},
```

- [ ] **Step 2: Run to verify fail**

Run: `pytest tests/test_engine_schemas.py -q -k injection_scan`
Expected: FAIL (schema absent).

- [ ] **Step 3: Create `schemas/injection_scan_response.schema.json`**

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://github.com/kicrazom/scriptorium/schemas/injection_scan_response.schema.json",
  "title": "InjectionScanResponse",
  "description": "Envelope returned by scripts/core/injection_scan.py: deterministic prompt-injection pattern scan over an untrusted document. Heuristic — absence of a hit is never proof the document is safe.",
  "type": "object",
  "required": ["status"],
  "properties": {
    "status": {"type": "string", "enum": ["ok", "error"]},
    "message": {"type": "string", "description": "Present when status == error."},
    "data": {
      "type": "object",
      "required": ["injections", "finding"],
      "properties": {
        "injections": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["pattern", "line", "snippet"],
            "properties": {
              "pattern": {"type": "string"},
              "line": {"type": "integer", "minimum": 1},
              "snippet": {"type": "string"}
            }
          }
        },
        "finding": {"$ref": "finding.schema.json"}
      }
    }
  },
  "allOf": [
    {"if": {"properties": {"status": {"const": "ok"}}}, "then": {"required": ["data"]}},
    {"if": {"properties": {"status": {"const": "error"}}}, "then": {"required": ["message"]}}
  ]
}
```

- [ ] **Step 4: Run to verify pass**

Run: `pytest tests/test_engine_schemas.py -q -k injection_scan`
Expected: 3 PASS.

- [ ] **Step 5: Commit**

```bash
cd ~/code/scriptorium
git add tests/test_engine_schemas.py schemas/injection_scan_response.schema.json
git commit -m "test(schemas): bespoke injection_scan_response schema + negative control"
```

---

## Task 5: `grimmer` bespoke schema

**Files:**
- Create: `schemas/grimmer_response.schema.json`
- Reuses: `tests/fixtures/envelopes/grimmer.out.json`

- [ ] **Step 1: Add negative control**

In `NEGATIVE_CONTROLS` add (`consistent` as string → reject):

```python
    "grimmer": {"status": "ok", "data": {
        "consistent": "yes", "reliable": True, "reason": "Passed all",  # consistent must be boolean
        "finding": {"claim": "x", "status": "operational_fact",
                    "confidence": 1.0, "source": "s", "source_independence": 1}}},
```

- [ ] **Step 2: Run to verify fail**

Run: `pytest tests/test_engine_schemas.py -q -k grimmer`
Expected: FAIL (schema absent).

- [ ] **Step 3: Create `schemas/grimmer_response.schema.json`**

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://github.com/kicrazom/scriptorium/schemas/grimmer_response.schema.json",
  "title": "GrimmerResponse",
  "description": "Envelope returned by scripts/core/grimmer.py: GRIM + GRIMMER granularity consistency via R scrutiny. GRIMMER test 3 is demoted to indeterminate (known scrutiny issue #80); finding status reflects that.",
  "type": "object",
  "required": ["status"],
  "properties": {
    "status": {"type": "string", "enum": ["ok", "error"]},
    "message": {"type": "string", "description": "Present when status == error."},
    "data": {
      "type": "object",
      "required": ["consistent", "reliable", "reason", "finding"],
      "properties": {
        "consistent": {"type": "boolean"},
        "reliable": {"type": "boolean"},
        "reason": {"type": "string"},
        "finding": {"$ref": "finding.schema.json"}
      }
    }
  },
  "allOf": [
    {"if": {"properties": {"status": {"const": "ok"}}}, "then": {"required": ["data"]}},
    {"if": {"properties": {"status": {"const": "error"}}}, "then": {"required": ["message"]}}
  ]
}
```

- [ ] **Step 4: Run to verify pass**

Run: `pytest tests/test_engine_schemas.py -q -k grimmer`
Expected: 3 PASS.

- [ ] **Step 5: Commit**

```bash
cd ~/code/scriptorium
git add tests/test_engine_schemas.py schemas/grimmer_response.schema.json
git commit -m "test(schemas): bespoke grimmer_response schema + negative control"
```

---

## Task 6: `interim_boundaries` bespoke schema

**Files:**
- Create: `schemas/interim_boundaries_response.schema.json`
- Reuses: `tests/fixtures/envelopes/interim_boundaries.out.json`

- [ ] **Step 1: Add negative control**

In `NEGATIVE_CONTROLS` add (`k` as string → reject):

```python
    "interim_boundaries": {"status": "ok", "data": {
        "k": "two", "upper_bounds": [2.96, 1.97], "sfu": "OF",  # k must be integer
        "finding": {"claim": "x", "status": "operational_fact",
                    "confidence": 1.0, "source": "s", "source_independence": 1}}},
```

- [ ] **Step 2: Run to verify fail**

Run: `pytest tests/test_engine_schemas.py -q -k interim_boundaries`
Expected: FAIL (schema absent).

- [ ] **Step 3: Create `schemas/interim_boundaries_response.schema.json`**

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://github.com/kicrazom/scriptorium/schemas/interim_boundaries_response.schema.json",
  "title": "InterimBoundariesResponse",
  "description": "Envelope returned by scripts/core/interim_boundaries.py: group-sequential efficacy boundaries via R gsDesign (O'Brien-Fleming / Pocock spending).",
  "type": "object",
  "required": ["status"],
  "properties": {
    "status": {"type": "string", "enum": ["ok", "error"]},
    "message": {"type": "string", "description": "Present when status == error."},
    "data": {
      "type": "object",
      "required": ["k", "upper_bounds", "sfu", "finding"],
      "properties": {
        "k": {"type": "integer", "minimum": 1},
        "upper_bounds": {"type": "array", "items": {"type": "number"}, "minItems": 1},
        "sfu": {"type": "string"},
        "finding": {"$ref": "finding.schema.json"}
      }
    }
  },
  "allOf": [
    {"if": {"properties": {"status": {"const": "ok"}}}, "then": {"required": ["data"]}},
    {"if": {"properties": {"status": {"const": "error"}}}, "then": {"required": ["message"]}}
  ]
}
```

- [ ] **Step 4: Run to verify pass**

Run: `pytest tests/test_engine_schemas.py -q -k interim_boundaries`
Expected: 3 PASS.

- [ ] **Step 5: Commit**

```bash
cd ~/code/scriptorium
git add tests/test_engine_schemas.py schemas/interim_boundaries_response.schema.json
git commit -m "test(schemas): bespoke interim_boundaries_response schema + negative control"
```

---

## Task 7: `epistemic_grade` bespoke schema

**Files:**
- Create: `schemas/epistemic_grade_response.schema.json`
- Reuses: `tests/fixtures/envelopes/epistemic_grade.out.json`

- [ ] **Step 1: Add negative control**

In `NEGATIVE_CONTROLS` add (`overall_status` not in the epistemic enum → reject):

```python
    "epistemic_grade": {"status": "ok", "data": {
        "overall_status": "made_up", "overall_confidence": 0.6, "n_findings": 2,  # bad enum
        "finding": {"claim": "x", "status": "working_hypothesis",
                    "confidence": 0.6, "source": "s", "source_independence": 2}}},
```

- [ ] **Step 2: Run to verify fail**

Run: `pytest tests/test_engine_schemas.py -q -k epistemic_grade`
Expected: FAIL (schema absent).

- [ ] **Step 3: Create `schemas/epistemic_grade_response.schema.json`**

Note: `overall_status` reuses the same enum as `finding.status`; spelled out here (a `$ref` into a sub-property of finding.schema.json is awkward, so inline the enum — single source of truth remains finding.schema.json, this is a deliberate mirror documented in the description).

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://github.com/kicrazom/scriptorium/schemas/epistemic_grade_response.schema.json",
  "title": "EpistemicGradeResponse",
  "description": "Envelope returned by scripts/core/epistemic_grade.py: weakest-link aggregation of multiple findings. overall_status mirrors the finding.status enum (deliberate inline copy).",
  "type": "object",
  "required": ["status"],
  "properties": {
    "status": {"type": "string", "enum": ["ok", "error"]},
    "message": {"type": "string", "description": "Present when status == error."},
    "data": {
      "type": "object",
      "required": ["overall_status", "overall_confidence", "n_findings", "finding"],
      "properties": {
        "overall_status": {
          "type": "string",
          "enum": [
            "contradicted", "speculative_hypothesis", "working_hypothesis",
            "corroborated_inference", "operational_fact", "canonical_fact"
          ]
        },
        "overall_confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "n_findings": {"type": "integer", "minimum": 0},
        "finding": {"$ref": "finding.schema.json"}
      }
    }
  },
  "allOf": [
    {"if": {"properties": {"status": {"const": "ok"}}}, "then": {"required": ["data"]}},
    {"if": {"properties": {"status": {"const": "error"}}}, "then": {"required": ["message"]}}
  ]
}
```

- [ ] **Step 4: Run the FULL engine-schema suite**

Run: `pytest tests/test_engine_schemas.py -q`
Expected: all PASS — 7×(schema-exists) + 7×(fixture-validates) + 7×(negative-control) = 21 passed.

- [ ] **Step 5: Run the WHOLE gate (no regressions)**

Run: `cd ~/code/scriptorium && . .venv/bin/activate && ./scripts/run_tests.sh`
Expected: full suite green (prior count + 21 new), ruff clean. Note coverage gate lives in CI-R (needs R); local `run_tests.sh` green is the pre-push bar per repo convention.

- [ ] **Step 6: Commit**

```bash
cd ~/code/scriptorium
git add tests/test_engine_schemas.py schemas/epistemic_grade_response.schema.json
git commit -m "test(schemas): bespoke epistemic_grade_response schema — all 9 engines now schema-pinned"
```

---

## Task 8: Docs reconcile + release

**Files:**
- Modify: `schemas/README.md`
- Modify: `STATUS.md`
- Modify: `ROADMAP.md:57`
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Read the four docs to find exact lines**

Run: `cd ~/code/scriptorium && sed -n '1,60p' schemas/README.md && grep -n "schema\|envelope\|Per-engine" STATUS.md ROADMAP.md CHANGELOG.md`
Expected: locate the schema inventory in `schemas/README.md`, the per-engine roadmap bullet (`ROADMAP.md:57`), the STATUS schema row, and the CHANGELOG `Unreleased` block.

- [ ] **Step 2: Update `schemas/README.md`**

Add the 7 new schemas to the inventory list, each one line: `<engine>_response.schema.json — bespoke response contract for scripts/core/<engine>.py`. State that every L0 engine now has both the shared envelope and a bespoke per-engine response schema, tested by `tests/test_engine_schemas.py`.

- [ ] **Step 3: Update `STATUS.md`**

Move "per-engine bespoke schemas" from planned → implemented. Per repo rule (implemented = test + example + failure-mode): cite `tests/test_engine_schemas.py` (21 cases incl. per-engine negative controls) as the test, the committed envelope fixtures as examples, and the negative controls as the failure-mode.

- [ ] **Step 4: Update `ROADMAP.md` and `CHANGELOG.md`**

Remove/strike the "per-engine bespoke schemas" item from the roadmap (`ROADMAP.md:57`); add a `CHANGELOG.md` entry under a new `## [1.2.0]` heading: "Added: bespoke per-engine response schemas for all 7 remaining L0 engines (stat_run, guideline_check, citation_parse, injection_scan, grimmer, interim_boundaries, epistemic_grade) + auto-discovering schema-contract test."

- [ ] **Step 5: Commit docs**

```bash
cd ~/code/scriptorium
git add schemas/README.md STATUS.md ROADMAP.md CHANGELOG.md
git commit -m "docs: reconcile per-engine schemas planned->implemented; CHANGELOG 1.2.0"
```

- [ ] **Step 6: Push and verify CI green on the pushed HEAD**

```bash
cd ~/code/scriptorium
git push origin main
gh run list --limit 2
```
Expected: both `CI` and `CI (R engines)` complete + success on the pushed commit SHA. Poll until both green BEFORE tagging.

- [ ] **Step 7: Release decision (HUMAN-GATED — stop here, present to Łukasz)**

Do NOT tag autonomously. Present: this is additive, contract-tightening, no behavior change → SemVer **minor** `v1.2.0`. On Łukasz's OK:

```bash
cd ~/code/scriptorium
git tag v1.2.0
git push origin v1.2.0
gh release create v1.2.0 --title "v1.2.0 — Per-engine bespoke schemas" --notes "All 9 L0 engines now carry a bespoke per-engine response schema (data-payload contract) on top of the shared envelope, enforced by tests/test_engine_schemas.py."
```

---

## Self-Review

**Spec coverage:** ROADMAP item "Per-engine bespoke schemas (beyond the shared envelope)" → Tasks 1–7 deliver a schema per remaining engine; Task 8 reconciles docs + release. The other ROADMAP-57 items (semantic citation-support, contradiction-detection) are explicitly out of scope (Sprint 3/4). ✓

**Placeholder scan:** every schema is given as complete JSON; every test edit shows the literal code; every command has expected output. No TBD/TODO. ✓

**Type consistency:** `finding` always via `{"$ref": "finding.schema.json"}`; `overall_status`/finding `status` enums match the 6 values in `finding.schema.json`; fixture alias map handles power's stem≠fixture mismatch; engine stems match `scripts/core/<engine>.py` and `tests/fixtures/envelopes/<engine>.out.json`. The `NEGATIVE_CONTROLS` dict is appended incrementally (Tasks 1–7) and `test_negative_control_is_rejected` auto-parametrizes over its keys — no list to keep in sync. ✓
