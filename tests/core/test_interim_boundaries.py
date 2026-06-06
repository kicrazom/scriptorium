# tests/core/test_interim_boundaries.py
import json
import shutil
import subprocess
import sys
import pytest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENGINE = ROOT / "scripts" / "core" / "interim_boundaries.py"

pytestmark = pytest.mark.skipif(shutil.which("Rscript") is None, reason="Rscript not available")


def run_engine(payload):
    proc = subprocess.run(
        [sys.executable, str(ENGINE)],
        input=json.dumps(payload), capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def test_obrien_fleming_two_look():
    out = run_engine({"k": 2, "alpha": 0.025, "test_type": "one_sided", "sfu": "OF"})
    assert out["status"] == "ok"
    bounds = out["data"]["upper_bounds"]
    assert len(bounds) == 2
    # O'Brien-Fleming: first look stricter than the final; final ~1.98.
    assert bounds[0] > bounds[1]
    assert 1.9 < bounds[1] < 2.05
    assert out["data"]["finding"]["status"] == "operational_fact"
