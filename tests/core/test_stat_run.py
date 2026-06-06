# tests/core/test_stat_run.py
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENGINE = ROOT / "scripts" / "core" / "stat_run.py"


def run_engine(payload):
    proc = subprocess.run(
        [sys.executable, str(ENGINE)],
        input=json.dumps(payload), capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def test_check_assumptions_flags_nonnormal():
    # Strongly non-normal group (one extreme outlier) vs a spread group.
    payload = {
        "op": "check_assumptions",
        "groups": [[1, 1, 1, 1, 1, 1, 1, 1, 2, 100], [2, 3, 4, 5, 6, 7, 8, 9, 10, 11]],
        "claimed_test": "two_sample_t",
    }
    out = run_engine(payload)
    assert out["status"] == "ok"
    assert out["data"]["assumptions"]["normality"]["violated"] is True
    assert out["data"]["recommended_alternative"] == "mann_whitney"
    assert out["data"]["finding"]["status"] == "operational_fact"
    assert out["data"]["finding"]["source"].startswith("scripts/core/stat_run.py#run=")


def test_unknown_op_is_error():
    proc = subprocess.run(
        [sys.executable, str(ENGINE)],
        input=json.dumps({"op": "divine"}), capture_output=True, text=True,
    )
    assert json.loads(proc.stdout)["status"] == "error"
