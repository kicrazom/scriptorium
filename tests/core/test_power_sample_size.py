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


def test_output_carries_method_and_assumptions():
    out = run_engine({"test": "two_sample_t", "effect_size": 0.5, "alpha": 0.05,
                      "power": 0.80, "ratio": 1.0})
    assert out["data"]["method"].startswith("statsmodels")
    assert out["data"]["assumptions"]["alpha"] == 0.05
    assert out["data"]["assumptions"]["power"] == 0.80
    assert out["data"]["assumptions"]["alternative"] == "two-sided"


def test_engine_deterministic_for_same_input():
    payload = {"test": "two_sample_t", "effect_size": 0.4, "alpha": 0.05,
               "power": 0.80, "ratio": 1.0}
    a = run_engine(payload)
    b = run_engine(payload)
    # identical input → identical output, including the seed-derived provenance run id
    assert a == b


def test_one_sample_t_family():
    out = run_engine({"test": "one_sample_t", "effect_size": 0.5, "alpha": 0.05, "power": 0.80})
    assert out["status"] == "ok"
    assert 33 <= out["data"]["n_per_group"] <= 35   # d=0.5 one-sample ~ 34
    assert out["data"]["n_total"] == out["data"]["n_per_group"]
    assert out["data"]["method"].startswith("statsmodels")


def test_correlation_family():
    import math
    from scipy.stats import norm
    r, alpha, power = 0.30, 0.05, 0.80
    out = run_engine({"test": "correlation", "r": r, "alpha": alpha, "power": power})
    assert out["status"] == "ok"
    z_a = norm.ppf(1 - alpha / 2)
    z_b = norm.ppf(power)
    expected = math.ceil(((z_a + z_b) / math.atanh(r)) ** 2 + 3)
    assert out["data"]["n_per_group"] == expected   # exact closed form
    assert 80 <= out["data"]["n_per_group"] <= 90    # textbook sanity (~85)


def test_survival_logrank_events():
    import math
    from scipy.stats import norm
    hr, alpha, power = 0.5, 0.05, 0.80
    out = run_engine({"test": "survival_logrank_events", "hazard_ratio": hr,
                      "alpha": alpha, "power": power})
    assert out["status"] == "ok"
    z_a = norm.ppf(1 - alpha / 2); z_b = norm.ppf(power)
    expected = math.ceil((z_a + z_b) ** 2 / (0.5 * 0.5 * (math.log(hr)) ** 2))
    assert out["data"]["events_required"] == expected
    assert "events" in out["data"]["finding"]["claim"].lower()


# --- input validation (a rigor tool must reject bad inputs, not divide by zero) ---

def test_correlation_rejects_zero_r():
    out = run_engine({"test": "correlation", "r": 0.0, "alpha": 0.05, "power": 0.80})
    assert out["status"] == "error"
    assert "r must be" in out["message"]


def test_survival_rejects_hazard_ratio_one():
    out = run_engine({"test": "survival_logrank_events", "hazard_ratio": 1.0,
                      "alpha": 0.05, "power": 0.80})
    assert out["status"] == "error"
    assert "hazard_ratio" in out["message"]


def test_two_proportions_rejects_equal_p():
    out = run_engine({"test": "two_proportions", "p1": 0.4, "p2": 0.4,
                      "alpha": 0.05, "power": 0.80})
    assert out["status"] == "error"
    assert "differ" in out["message"]


def test_rejects_out_of_range_alpha():
    out = run_engine({"test": "two_sample_t", "effect_size": 0.5, "alpha": 1.5, "power": 0.80})
    assert out["status"] == "error"
    assert "alpha" in out["message"]
