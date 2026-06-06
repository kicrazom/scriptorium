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


def test_paired_t_family():
    payload = {"test": "paired_t", "effect_size": 0.5, "alpha": 0.05, "power": 0.80}
    out = run_engine(payload)
    assert out["status"] == "ok"
    # canonical one-sample/paired n for d=0.5, power .80 ~ 34
    assert 33 <= out["data"]["n_per_group"] <= 35
    assert out["data"]["n_total"] == out["data"]["n_per_group"]  # single group of pairs
    assert out["data"]["finding"]["status"] == "operational_fact"


def test_two_proportions_family():
    payload = {"test": "two_proportions", "p1": 0.5, "p2": 0.3, "alpha": 0.05, "power": 0.80}
    out = run_engine(payload)
    assert out["status"] == "ok"
    # canonical n/group for p1=.5,p2=.3 ~ 93
    assert 85 <= out["data"]["n_per_group"] <= 100
    assert out["data"]["n_total"] == 2 * out["data"]["n_per_group"]


def test_one_way_anova_family():
    payload = {"test": "one_way_anova", "effect_size": 0.25, "k_groups": 4,
               "alpha": 0.05, "power": 0.80}
    out = run_engine(payload)
    assert out["status"] == "ok"
    # canonical per-group n for f=.25 (medium), k=4 ~ 45
    assert 40 <= out["data"]["n_per_group"] <= 50
    assert out["data"]["n_total"] == 4 * out["data"]["n_per_group"]
