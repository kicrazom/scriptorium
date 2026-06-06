"""GRIMMER engine — R-dispatch to scrutiny. Skips when R/scrutiny are unavailable
(e.g. the default CI runner), like the interim_boundaries test.

The engine is correct-by-construction (it IS scrutiny). These tests verify the wiring and,
crucially, the test-3 DEMOTION: scrutiny issue #80 means GRIMMER test 3 can false-positive, so
a test-3-only failure must come back as an indeterminate finding, never a confident inconsistency.
"""
import json
import shutil
import subprocess
import sys
import pytest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENGINE = ROOT / "scripts" / "core" / "grimmer.py"


def _scrutiny_available():
    if shutil.which("Rscript") is None:
        return False
    p = subprocess.run(
        ["Rscript", "-e", 'quit(status = !requireNamespace("scrutiny", quietly=TRUE))'],
        capture_output=True,
    )
    return p.returncode == 0


pytestmark = pytest.mark.skipif(not _scrutiny_available(), reason="R + scrutiny not available")


def run_engine(payload):
    proc = subprocess.run(
        [sys.executable, str(ENGINE)],
        input=json.dumps(payload), capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def test_consistent_mean_sd_passes():
    out = run_engine({"x": "2.57", "sd": "1.10", "n": 30})
    assert out["status"] == "ok"
    assert out["data"]["consistent"] is True
    assert out["data"]["finding"]["status"] == "operational_fact"


def test_grim_failure_is_reliable_inconsistency():
    out = run_engine({"x": "5.19", "sd": "1.34", "n": 28})
    d = out["data"]
    assert d["consistent"] is False
    assert d["reliable"] is True               # GRIM is sound
    assert d["finding"]["status"] == "operational_fact"


def test_test3_failure_is_demoted_to_indeterminate():
    # scrutiny issue #80: test 3 can false-positive → must NOT be a confident flag.
    out = run_engine({"x": "5.23", "sd": "2.55", "n": 35})
    d = out["data"]
    assert d["consistent"] is False
    assert "test 3" in d["reason"].lower()
    assert d["reliable"] is False
    assert d["finding"]["status"] == "working_hypothesis"   # demoted, not operational_fact
    assert d["finding"]["confidence"] < 1.0
