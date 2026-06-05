import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENGINE = ROOT / "scripts" / "core" / "power_sample_size.py"
GOLDEN = ROOT / "tests" / "golden" / "power_sample_size"


def run_engine(payload):
    proc = subprocess.run(
        [sys.executable, str(ENGINE)],
        input=json.dumps(payload),
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def test_cohen_medium_effect():
    payload = json.loads((GOLDEN / "cohen_medium.in.json").read_text())
    out = run_engine(payload)
    assert out["status"] == "ok"
    assert out["data"]["n_per_group"] == 64
    assert out["data"]["n_total"] == 128
    assert out["data"]["finding"]["status"] == "operational_fact"
    assert out["data"]["finding"]["confidence"] == 1.0
    assert out["data"]["finding"]["source"].startswith("scripts/core/power_sample_size.py#run=")


def test_unknown_test_is_error():
    proc = subprocess.run(
        [sys.executable, str(ENGINE)],
        input=json.dumps({"test": "telepathy", "effect_size": 0.5}),
        capture_output=True, text=True,
    )
    out = json.loads(proc.stdout)
    assert out["status"] == "error"
