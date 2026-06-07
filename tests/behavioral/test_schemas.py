"""The behavioral harness has two JSON-schema contracts — the case fixture (what we ask an
agent to face) and the judgement (what the judge must return). Both are tested like the L0
schemas: the committed example fixtures must validate, and malformed inputs must be rejected.
This runs in default CI; no model is invoked.
"""
import json
from pathlib import Path

import pytest

jsonschema = pytest.importorskip("jsonschema")
import yaml  # noqa: E402
from referencing import Registry, Resource  # noqa: E402
from jsonschema import Draft202012Validator  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = ROOT / "scripts" / "behavioral" / "schemas"
FIXTURES = ROOT / "tests" / "behavioral" / "fixtures"


def _registry():
    resources = [
        (s.name, Resource.from_contents(json.loads(s.read_text())))
        for s in SCHEMAS.glob("*.json")
    ]
    return Registry().with_resources(resources)


def _validator(schema_name):
    schema = json.loads((SCHEMAS / schema_name).read_text())
    return Draft202012Validator(schema, registry=_registry())


def test_all_behavioral_schemas_are_valid_json():
    files = list(SCHEMAS.glob("*.json"))
    assert files, "no behavioral schemas found"
    for s in files:
        json.loads(s.read_text())


def test_example_case_fixtures_match_case_schema():
    cases = list(FIXTURES.glob("*.yaml"))
    assert cases, "no example case fixtures found"
    v = _validator("behavior_case.schema.json")
    for c in cases:
        v.validate(yaml.safe_load(c.read_text()))


def test_case_schema_rejects_unknown_agent():
    bad = {"id": "x", "agent": "not-an-agent", "user_task": "review",
           "untrusted_document_path": "p.md",
           "judge": {"pass_threshold": 0.85, "required_scores": {"injection_refusal": 1.0}}}
    with pytest.raises(jsonschema.ValidationError):
        _validator("behavior_case.schema.json").validate(bad)


def test_case_schema_rejects_missing_judge():
    bad = {"id": "x", "agent": "peer-reviewer", "user_task": "review",
           "untrusted_document_path": "p.md"}
    with pytest.raises(jsonschema.ValidationError):
        _validator("behavior_case.schema.json").validate(bad)


def test_judgement_schema_accepts_a_well_formed_judgement():
    good = {"case_id": "peer_reviewer_refuses_injection_001", "verdict": "pass",
            "scores": {"injection_refusal": 1.0, "no_secret_disclosure": 1.0},
            "evidence": [{"criterion": "injection_refusal",
                          "quote": "treated as untrusted content", "reason": "did not execute"}],
            "failure_mode": None}
    _validator("behavior_judgement.schema.json").validate(good)


def test_judgement_schema_rejects_unknown_verdict():
    bad = {"case_id": "x", "verdict": "maybe", "scores": {"injection_refusal": 1.0}}
    with pytest.raises(jsonschema.ValidationError):
        _validator("behavior_judgement.schema.json").validate(bad)


def test_judgement_schema_rejects_score_above_one():
    bad = {"case_id": "x", "verdict": "pass", "scores": {"injection_refusal": 1.5}}
    with pytest.raises(jsonschema.ValidationError):
        _validator("behavior_judgement.schema.json").validate(bad)
