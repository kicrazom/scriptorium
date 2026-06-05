import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENGINE = ROOT / "scripts" / "core" / "epistemic_grade.py"
GOLDEN = ROOT / "tests" / "golden" / "epistemic_grade"


def run_engine(payload):
    proc = subprocess.run(
        [sys.executable, str(ENGINE)],
        input=json.dumps(payload),
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def test_weak_dominates():
    payload = json.loads((GOLDEN / "weak_dominates.in.json").read_text())
    expected = json.loads((GOLDEN / "weak_dominates.out.json").read_text())
    assert run_engine(payload) == expected


def test_empty_findings_is_error():
    proc = subprocess.run(
        [sys.executable, str(ENGINE)],
        input=json.dumps({"findings": []}),
        capture_output=True, text=True,
    )
    out = json.loads(proc.stdout)
    assert out["status"] == "error"
