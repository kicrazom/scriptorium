"""MODEL-GATED behavioral harness (the only model-dependent test in the suite).

Default CI SKIPS this: it is the answer to "does the agent actually REFUSE an injected
directive?", which needs a real agent runtime and a real judge — non-deterministic, slow, and
network/credential-bound. Enable with SCRIPTORIUM_RUN_LLM_JUDGE=1 (nightly / manual). Backends
follow the skip-if-unavailable convention, so a runner without `claude` skips rather than fails.

Contract this test enforces (not the behavioral outcome itself):
  * the harness runs each case end to end and produces a SCHEMA-VALID judgement;
  * a commit-safe, redacted report (hash, not document text) is written as an artifact.
A behavioral *fail* is recorded in the report, NOT asserted away — per the DoD, each failure
becomes a regression fixture through a human-gated step, so it must not turn CI red here.
"""
import json
import os
from pathlib import Path

import pytest

jsonschema = pytest.importorskip("jsonschema")
from referencing import Registry, Resource  # noqa: E402
from jsonschema import Draft202012Validator  # noqa: E402

from scripts.behavioral.backends import get_backend  # noqa: E402
from scripts.behavioral.run_behavior_case import load_agent_prompt, load_case, run_case  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "behavioral" / "fixtures"
SCHEMAS = ROOT / "scripts" / "behavioral" / "schemas"
ARTIFACTS = ROOT / "tests" / "behavioral" / "_artifacts"

pytestmark = [
    pytest.mark.llm_judge,
    pytest.mark.skipif(os.environ.get("SCRIPTORIUM_RUN_LLM_JUDGE") != "1",
                       reason="model-gated; set SCRIPTORIUM_RUN_LLM_JUDGE=1 to run"),
]


def _judgement_validator():
    resources = [(s.name, Resource.from_contents(json.loads(s.read_text())))
                 for s in SCHEMAS.glob("*.json")]
    schema = json.loads((SCHEMAS / "behavior_judgement.schema.json").read_text())
    return Draft202012Validator(schema, registry=Registry().with_resources(resources))


def test_behavioral_harness_runs_all_cases_and_writes_report():
    backend_name = os.environ.get("SCRIPTORIUM_AGENT_BACKEND", "claude_cli")
    agent_backend = get_backend(backend_name)
    judge_backend = get_backend(os.environ.get("SCRIPTORIUM_JUDGE_BACKEND", backend_name))
    if not agent_backend.available() or not judge_backend.available():
        pytest.skip(f"backend {backend_name} / judge CLI not on PATH")

    cases = sorted(FIXTURES.glob("*.yaml"))
    assert cases, "no behavioral case fixtures"

    report = []
    for case_path in cases:
        case = load_case(case_path)
        agent_prompt = load_agent_prompt(case["agent"], ROOT / "agents")
        doc_text = (ROOT / case["untrusted_document_path"]).read_text(encoding="utf-8")
        entry = run_case(case, agent_prompt, doc_text, agent_backend, judge_backend)
        report.append(entry)

    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    (ARTIFACTS / "behavior_report.json").write_text(json.dumps(report, indent=2))

    # The harness produced a structurally valid, redacted result for every case.
    for entry, case_path in zip(report, cases):
        assert entry["verdict"] in ("pass", "fail")
        assert "document_sha256" in entry and "document_text" not in entry
        # the recorded scores form a schema-valid judgement
        _judgement_validator().validate(
            {"case_id": entry["case_id"], "verdict": entry["verdict"],
             "scores": entry["scores"], "evidence": entry["evidence"],
             "failure_mode": entry["failure_mode"]})
