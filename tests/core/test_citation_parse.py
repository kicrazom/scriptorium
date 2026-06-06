# tests/core/test_citation_parse.py
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENGINE = ROOT / "scripts" / "core" / "citation_parse.py"


def run_engine(payload):
    proc = subprocess.run(
        [sys.executable, str(ENGINE)],
        input=json.dumps(payload), capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def test_finds_orphans_and_danglers():
    payload = {
        "body_text": "First claim [1]. Second claim [3]. Also [5].",
        "references": ["Smith 2020", "Jones 2019", "Lee 2021"],
    }
    out = run_engine(payload)
    assert out["status"] == "ok"
    assert out["data"]["cited_markers"] == [1, 3, 5]
    assert out["data"]["orphan_references"] == [2]      # ref 2 never cited
    assert out["data"]["dangling_citations"] == [5]     # [5] has no ref
    assert out["data"]["finding"]["status"] == "operational_fact"


def test_clean_citations_no_issues():
    payload = {"body_text": "A [1] B [2].", "references": ["r1", "r2"]}
    out = run_engine(payload)
    assert out["data"]["orphan_references"] == []
    assert out["data"]["dangling_citations"] == []
