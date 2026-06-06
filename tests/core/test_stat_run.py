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


import scipy.stats as _sps  # for inline reference


def test_recompute_ttest_matches_scipy_and_flags_mismatch():
    a = [5.1, 4.9, 5.0, 5.2, 4.8]
    b = [6.0, 5.9, 6.1, 5.8, 6.2]
    payload = {"op": "recompute_ttest", "groups": [a, b], "equal_var": True, "claimed_p": 0.9}
    out = run_engine(payload)
    assert out["status"] == "ok"
    ref = _sps.ttest_ind(a, b, equal_var=True)
    assert abs(out["data"]["p"] - float(ref.pvalue)) < 1e-9
    assert out["data"]["p_matches_claim"] is False  # true p ~1e-4, claim 0.9
    assert out["data"]["finding"]["confidence"] == 1.0


def test_recompute_ttest_without_claim_returns_null_match():
    out = run_engine({"op": "recompute_ttest", "groups": [[1, 2, 3], [4, 5, 6]], "equal_var": True})
    assert out["data"]["p_matches_claim"] is None


def test_grim_detects_impossible_mean():
    out = run_engine({"op": "grim", "mean": 3.45, "n": 10, "decimals": 2})
    assert out["status"] == "ok"
    assert out["data"]["consistent"] is False


def test_grim_accepts_possible_mean():
    # 34/10 = 3.4 exactly reachable
    out = run_engine({"op": "grim", "mean": 3.4, "n": 10, "decimals": 1})
    assert out["data"]["consistent"] is True
