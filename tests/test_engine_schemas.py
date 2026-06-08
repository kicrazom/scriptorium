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
# power already has a bespoke schema (power_response.schema.json) validated by
# tests/test_schemas.py; the alias is reserved so this harness can fold in power
# coverage later without renaming any fixtures.
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
    path = SCHEMAS / schema_name
    assert path.exists(), f"{schema_name} not yet delivered (Sprint 2 in progress)"
    schema = json.loads(path.read_text())
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
# Every engine in SPRINT2_ENGINES gains one entry here as its task lands;
# by sprint end all 7 are covered.
NEGATIVE_CONTROLS = {
    "stat_run": {"status": "ok", "data": {"n": "ten",  # n must be integer
                 "finding": {"claim": "x", "status": "operational_fact",
                             "confidence": 1.0, "source": "s", "source_independence": 1}}},
    "guideline_check": {"status": "ok", "data": {
        "guideline": "strobe", "present": ["1a"],
        "missing": [{"oops": "no id"}],  # each missing item requires id + item
        "finding": {"claim": "x", "status": "working_hypothesis",
                    "confidence": 0.6, "source": "s", "source_independence": 1}}},
    "citation_parse": {"status": "ok", "data": {
        "cited_markers": [1, 3], "n_references": "three",  # must be integer
        "orphan_references": [2], "dangling_citations": [],
        "finding": {"claim": "x", "status": "operational_fact",
                    "confidence": 1.0, "source": "s", "source_independence": 1}}},
    "injection_scan": {"status": "ok", "data": {
        "injections": [{"pattern": "ignore-previous", "snippet": "..."}],  # missing line
        "finding": {"claim": "x", "status": "working_hypothesis",
                    "confidence": 0.6, "source": "s", "source_independence": 1}}},
    "grimmer": {"status": "ok", "data": {
        "consistent": "yes", "reliable": True, "reason": "Passed all",  # consistent must be boolean
        "finding": {"claim": "x", "status": "operational_fact",
                    "confidence": 1.0, "source": "s", "source_independence": 1}}},
}


@pytest.mark.parametrize("engine", sorted(NEGATIVE_CONTROLS))
def test_negative_control_is_rejected(engine):
    with pytest.raises(jsonschema.ValidationError):
        _validator(f"{engine}_response.schema.json").validate(NEGATIVE_CONTROLS[engine])
