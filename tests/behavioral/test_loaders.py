"""Loaders resolve a case fixture and the agent's prompt from disk — deterministic, default CI.
These feed the model-gated runner but are themselves model-free.
"""
from pathlib import Path

from scripts.behavioral.run_behavior_case import load_agent_prompt, load_case

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "behavioral" / "fixtures"


def test_load_case_parses_yaml_fixture():
    case = load_case(FIXTURES / "injection_refusal_peer_reviewer.yaml")
    assert case["id"] == "peer_reviewer_refuses_injection_001"
    assert case["agent"] == "peer-reviewer"
    assert "required_scores" in case["judge"]


def test_load_agent_prompt_reads_agent_definition():
    prompt = load_agent_prompt("peer-reviewer", ROOT / "agents")
    assert isinstance(prompt, str)
    assert len(prompt) > 100          # a real agent definition, not empty


def test_every_case_references_an_existing_document_and_agent():
    # Deterministic guard: no case may point at a missing untrusted document or absent agent.
    cases = sorted(FIXTURES.glob("*.yaml"))
    assert cases
    for path in cases:
        case = load_case(path)
        doc = ROOT / case["untrusted_document_path"]
        assert doc.is_file(), f"{path.name}: missing document {case['untrusted_document_path']}"
        agent = ROOT / "agents" / f"{case['agent']}.md"
        assert agent.is_file(), f"{path.name}: missing agent {case['agent']}"
