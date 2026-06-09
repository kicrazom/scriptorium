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


def test_mann_whitney_matches_scipy():
    a = [1, 2, 3, 4, 5]; b = [6, 7, 8, 9, 10]
    out = run_engine({"op": "mann_whitney", "groups": [a, b]})
    assert out["status"] == "ok"
    ref = _sps.mannwhitneyu(a, b, alternative="two-sided")
    assert abs(out["data"]["u"] - float(ref.statistic)) < 1e-9
    assert abs(out["data"]["p"] - float(ref.pvalue)) < 1e-9
    assert out["data"]["finding"]["confidence"] == 1.0


def test_chi_square_matches_scipy():
    table = [[10, 20], [30, 40]]
    out = run_engine({"op": "chi_square", "table": table})
    assert out["status"] == "ok"
    chi2, p, dof, _ = _sps.chi2_contingency(table)
    assert abs(out["data"]["chi2"] - float(chi2)) < 1e-9
    assert out["data"]["dof"] == int(dof)


def test_fisher_matches_scipy():
    table = [[8, 2], [1, 9]]
    out = run_engine({"op": "fisher", "table": table})
    odds, p = _sps.fisher_exact(table)
    assert abs(out["data"]["p"] - float(p)) < 1e-9


# --- permutation_test: reference-validated vs scipy.stats.permutation_test (exact path) ---

import numpy as _np  # noqa: E402


def _diff_means(x, y):
    return _np.mean(x) - _np.mean(y)


def _scipy_perm(a, b, alternative):
    return _sps.permutation_test(
        (a, b), _diff_means, permutation_type="independent",
        alternative=alternative, n_resamples=_np.inf, vectorized=False,
    ).pvalue


def test_permutation_test_exact_matches_scipy_two_sided():
    a = [5.1, 4.9, 5.0, 5.2, 4.8, 5.05]
    b = [6.0, 5.9, 6.1, 5.8, 6.2, 5.95]
    out = run_engine({"op": "permutation_test", "groups": [a, b]})
    assert out["status"] == "ok"
    assert out["data"]["exact"] is True
    # C(12,6) = 924 <= 10000 default -> exact enumeration, no RNG.
    assert out["data"]["seed"] is None
    assert abs(out["data"]["p"] - float(_scipy_perm(a, b, "two-sided"))) < 1e-12
    assert out["data"]["finding"]["status"] == "operational_fact"
    assert out["data"]["finding"]["confidence"] == 1.0


def test_permutation_test_exact_one_sided_matches_scipy():
    a = [5.1, 4.9, 5.0, 5.2, 4.8, 5.05]
    b = [6.0, 5.9, 6.1, 5.8, 6.2, 5.95]
    for alt in ("less", "greater"):
        out = run_engine({"op": "permutation_test", "groups": [a, b], "alternative": alt})
        assert abs(out["data"]["p"] - float(_scipy_perm(a, b, alt))) < 1e-12


def test_permutation_test_monte_carlo_is_seeded_and_corroborated():
    # Force MC by lowering exact_max below C(8,4)=70.
    a = [1.0, 2.0, 3.0, 4.0]
    b = [3.0, 4.0, 5.0, 6.0]
    payload = {"op": "permutation_test", "groups": [a, b],
               "exact_max_perms": 10, "n_resamples": 2000}
    out1 = run_engine(payload)
    out2 = run_engine(payload)
    assert out1["data"]["exact"] is False
    assert out1["data"]["seed"] is not None
    # Deterministic: same payload -> byte-identical seeded result.
    assert out1["data"]["p"] == out2["data"]["p"]
    assert out1["data"]["finding"]["status"] == "corroborated_inference"
    # Agrees with scipy's exact p within Monte-Carlo sampling error.
    exact_p = float(_scipy_perm(a, b, "two-sided"))
    assert abs(out1["data"]["p"] - exact_p) < 0.05


# --- multiple_testing: reference-validated vs statsmodels multipletests ---

from statsmodels.stats.multitest import multipletests as _multipletests  # noqa: E402


def test_multiple_testing_matches_statsmodels():
    pv = [0.001, 0.008, 0.039, 0.041, 0.042, 0.060, 0.074, 0.205, 0.212, 0.216, 0.222, 0.480]
    out = run_engine({"op": "multiple_testing", "pvalues": pv, "alpha": 0.05})
    assert out["status"] == "ok"

    rej_b, pc_b, _, _ = _multipletests(pv, alpha=0.05, method="bonferroni")
    assert _np.allclose(out["data"]["bonferroni"]["p_adjusted"], pc_b, atol=1e-9)
    assert out["data"]["bonferroni"]["reject"] == list(rej_b)

    rej_bh, pc_bh, _, _ = _multipletests(pv, alpha=0.05, method="fdr_bh")
    assert _np.allclose(out["data"]["benjamini_hochberg"]["p_adjusted"], pc_bh, atol=1e-9)
    assert out["data"]["benjamini_hochberg"]["reject"] == list(rej_bh)

    assert out["data"]["finding"]["status"] == "operational_fact"


def test_multiple_testing_rejects_out_of_range():
    out = run_engine({"op": "multiple_testing", "pvalues": [0.1, 1.5]})
    assert out["status"] == "error"
