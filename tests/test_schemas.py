"""The JSON schemas in schemas/ are a tested contract, not decoration: the committed
example fixtures must validate against them, and malformed requests must be rejected.
"""
import json
from pathlib import Path

import pytest

jsonschema = pytest.importorskip("jsonschema")
from referencing import Registry, Resource  # noqa: E402
from jsonschema import Draft202012Validator  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"
EXAMPLES = ROOT / "examples" / "power-sample-size"


def _registry():
    resources = [
        (s.name, Resource.from_contents(json.loads(s.read_text())))
        for s in SCHEMAS.glob("*.json")
    ]
    return Registry().with_resources(resources)


def _validator(schema_name):
    schema = json.loads((SCHEMAS / schema_name).read_text())
    return Draft202012Validator(schema, registry=_registry())


def test_all_schemas_are_valid_json():
    for s in SCHEMAS.glob("*.json"):
        json.loads(s.read_text())  # raises on malformed JSON


@pytest.mark.parametrize("stem", [
    "two_sample_t", "paired_t", "one_sample_t", "two_proportions",
    "one_way_anova", "correlation", "survival_logrank_events", "linear_regression",
])
def test_example_inputs_match_request_schema(stem):
    inp = json.loads((EXAMPLES / f"{stem}_input.json").read_text())
    _validator("power_request.schema.json").validate(inp)


@pytest.mark.parametrize("stem", [
    "two_sample_t", "paired_t", "one_sample_t", "two_proportions",
    "one_way_anova", "correlation", "survival_logrank_events", "linear_regression",
])
def test_example_outputs_match_response_schema(stem):
    out = json.loads((EXAMPLES / f"{stem}_output.json").read_text())
    _validator("power_response.schema.json").validate(out)


def test_request_schema_rejects_missing_required_field():
    # two_proportions requires p1 and p2
    with pytest.raises(jsonschema.ValidationError):
        _validator("power_request.schema.json").validate({"test": "two_proportions"})


def test_finding_schema_rejects_unknown_status():
    bad = {"claim": "x", "status": "made_up", "confidence": 1.0,
           "source": "s", "source_independence": 1}
    with pytest.raises(jsonschema.ValidationError):
        _validator("finding.schema.json").validate(bad)
