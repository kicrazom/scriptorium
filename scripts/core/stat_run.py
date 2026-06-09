# scripts/core/stat_run.py
"""L0 engine: statistical sanity checks. Op-dispatched via the JSON "op" field.

Ops:
  check_assumptions — Shapiro normality (per group) + Levene equal-variance; recommend
                      a nonparametric alternative when a parametric test's assumptions fail.
  recompute_ttest   — recompute t/df/p/CI for two groups; flag mismatch vs a claimed p.
  grim              — Granularity-Related Inconsistency of Means (integer reachability).
  mann_whitney      — Mann-Whitney U (two-sided).
  chi_square        — chi-square test of independence.
  fisher            — Fisher exact test (2x2).
  permutation_test  — two-sample permutation test for a difference in means; exact
                      enumeration for small n, else seeded Monte-Carlo. Validated to full
                      float precision against scipy.stats.permutation_test (exact path).
  multiple_testing  — Bonferroni + Benjamini-Hochberg (FDR) p-value correction. Validated
                      against statsmodels.stats.multitest.multipletests.

Input/Output: stdin/stdout JSON envelopes (see scripts/lib/json_io.py).
"""
import json
import sys
from itertools import combinations
from math import comb
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.lib import json_io, provenance, epistemic  # noqa: E402

import numpy as np  # noqa: E402
from scipy import stats  # noqa: E402

ALPHA = 0.05


def _rid(req):
    return provenance.run_id(seed=json.dumps(req, sort_keys=True))


def check_assumptions(req):
    groups = [list(map(float, g)) for g in req["groups"]]
    claimed_test = req.get("claimed_test")

    normal_violated = False
    per_group = []
    for i, g in enumerate(groups):
        w, p = stats.shapiro(g)
        viol = p < ALPHA
        normal_violated = normal_violated or viol
        per_group.append({"group": i, "shapiro_p": round(p, 4), "violated": bool(viol)})

    lev_w, lev_p = stats.levene(*groups)
    var_violated = lev_p < ALPHA

    recommended = None
    if claimed_test == "two_sample_t" and normal_violated:
        recommended = "mann_whitney"

    any_violation = normal_violated or var_violated
    status = "operational_fact" if any_violation else "corroborated_inference"
    confidence = 0.9 if any_violation else 0.8
    claim = (
        "parametric assumptions violated; nonparametric alternative recommended"
        if any_violation else "parametric assumptions hold"
    )
    finding = epistemic.make_finding(
        claim=claim, status=status, confidence=confidence,
        source=provenance.engine_trace("stat_run", run_id=_rid(req), anchor="assumptions"),
    )
    return {
        "assumptions": {
            "normality": {"violated": bool(normal_violated), "per_group": per_group},
            "equal_variance": {"violated": bool(var_violated), "levene_p": round(lev_p, 4)},
        },
        "recommended_alternative": recommended,
        "finding": finding,
    }


def recompute_ttest(req):
    a = list(map(float, req["groups"][0]))
    b = list(map(float, req["groups"][1]))
    equal_var = bool(req.get("equal_var", True))
    res = stats.ttest_ind(a, b, equal_var=equal_var)
    t = float(res.statistic)
    p = float(res.pvalue)

    mean_diff = (sum(a) / len(a)) - (sum(b) / len(b))
    if equal_var:
        df = len(a) + len(b) - 2
    else:  # Welch–Satterthwaite
        va, vb = _var(a), _var(b)
        na, nb = len(a), len(b)
        df = (va / na + vb / nb) ** 2 / (
            (va / na) ** 2 / (na - 1) + (vb / nb) ** 2 / (nb - 1)
        )
    se = mean_diff / t if t != 0 else float("nan")
    tcrit = stats.t.ppf(0.975, df)
    ci = [mean_diff - tcrit * abs(se), mean_diff + tcrit * abs(se)]

    claimed_p = req.get("claimed_p")
    p_matches = None if claimed_p is None else (abs(p - float(claimed_p)) <= 0.01)
    claim = "reported p inconsistent with recomputed p" if p_matches is False else "p recomputed"
    finding = epistemic.make_finding(
        claim=claim, status="operational_fact", confidence=1.0,
        source=provenance.engine_trace("stat_run", run_id=_rid(req), anchor="recompute_ttest"),
    )
    return {
        "t": round(t, 6), "df": round(float(df), 4), "p": p,
        "ci95": [round(ci[0], 6), round(ci[1], 6)],
        "claimed_p": claimed_p, "p_matches_claim": p_matches, "finding": finding,
    }


def _var(x):
    m = sum(x) / len(x)
    return sum((xi - m) ** 2 for xi in x) / (len(x) - 1)


def grim(req):
    mean = float(req["mean"])
    n = int(req["n"])
    decimals = int(req.get("decimals", 2))
    scale = 10 ** decimals
    # The integer sum that would round to the reported mean:
    candidate_sum = round(mean * n)
    reconstructed = round(candidate_sum / n, decimals)
    consistent = abs(reconstructed - round(mean, decimals)) < (0.5 / scale) / n
    lo = round((candidate_sum - 1) / n, decimals)
    hi = round((candidate_sum + 1) / n, decimals)
    finding = epistemic.make_finding(
        claim="reported mean is granularity-inconsistent (GRIM)" if not consistent
              else "reported mean is granularity-consistent",
        status="operational_fact", confidence=1.0,
        source=provenance.engine_trace("stat_run", run_id=_rid(req), anchor="grim"),
    )
    return {"consistent": bool(consistent), "mean": mean, "n": n,
            "nearest_consistent": [lo, hi], "finding": finding}


def mann_whitney(req):
    a = list(map(float, req["groups"][0]))
    b = list(map(float, req["groups"][1]))
    res = stats.mannwhitneyu(a, b, alternative="two-sided")
    finding = epistemic.make_finding(
        claim="Mann-Whitney U computed", status="operational_fact", confidence=1.0,
        source=provenance.engine_trace("stat_run", run_id=_rid(req), anchor="mann_whitney"),
    )
    return {"u": float(res.statistic), "p": float(res.pvalue), "finding": finding}


def chi_square(req):
    table = req["table"]
    chi2, p, dof, _expected = stats.chi2_contingency(table)
    finding = epistemic.make_finding(
        claim="chi-square test of independence computed",
        status="operational_fact", confidence=1.0,
        source=provenance.engine_trace("stat_run", run_id=_rid(req), anchor="chi_square"),
    )
    return {"chi2": float(chi2), "p": float(p), "dof": int(dof), "finding": finding}


def fisher(req):
    table = req["table"]  # 2x2
    odds, p = stats.fisher_exact(table)
    finding = epistemic.make_finding(
        claim="Fisher exact test computed", status="operational_fact", confidence=1.0,
        source=provenance.engine_trace("stat_run", run_id=_rid(req), anchor="fisher"),
    )
    return {"odds_ratio": float(odds), "p": float(p), "finding": finding}


def _mean_diff(x, y):
    return float(np.mean(x) - np.mean(y))


def permutation_test(req):
    """Two-sample permutation test for the difference in means (group[0] − group[1]).

    Exact enumeration of all C(n, n_a) pooled splits when that count <= ``exact_max_perms``
    (default 10000); otherwise a seeded Monte-Carlo estimate over ``n_resamples`` permutations.
    The Monte-Carlo seed is derived from the request payload via the provenance run-id, so
    runs are reproducible (no wall-clock).

    Reference-validated: the exact path reproduces scipy.stats.permutation_test
    (permutation_type='independent', n_resamples=inf) to < 1e-12 for two-sided/less/greater
    (see tests/core/test_stat_run.py). The Monte-Carlo path agrees within sampling error
    (it is a stochastic estimate of the same exact p, hence corroborated_inference not
    operational_fact).

    Input: {op, groups:[a,b], alternative?: two-sided|less|greater, n_resamples?: int,
            exact_max_perms?: int}
    """
    a = list(map(float, req["groups"][0]))
    b = list(map(float, req["groups"][1]))
    alternative = req.get("alternative", "two-sided")
    if alternative not in ("two-sided", "less", "greater"):
        raise ValueError(f"unknown alternative: {alternative!r}")
    exact_max = int(req.get("exact_max_perms", 10000))
    n_resamples = int(req.get("n_resamples", 10000))

    pooled = np.array(a + b, dtype=float)
    na = len(a)
    n = len(pooled)
    obs = _mean_diff(a, b)
    n_comb = comb(n, na)
    gamma = 1e-14 * max(1.0, abs(obs))

    def tally(stat_arr):
        if alternative == "two-sided":
            return int(np.sum(np.abs(stat_arr) >= abs(obs) - gamma))
        if alternative == "less":
            return int(np.sum(stat_arr <= obs + gamma))
        return int(np.sum(stat_arr >= obs - gamma))

    exact = n_comb <= exact_max
    seed = None
    if exact:
        # Enumerate every way to assign n_a of the pooled values to "group a".
        stat = np.empty(n_comb, dtype=float)
        all_idx = set(range(n))
        for i, combo in enumerate(combinations(range(n), na)):
            mask = list(combo)
            rest = list(all_idx.difference(combo))
            stat[i] = np.mean(pooled[mask]) - np.mean(pooled[rest])
        p = tally(stat) / n_comb  # exact: full enumeration, no +1 correction (matches scipy)
        n_used = n_comb
        method = "exact (full enumeration)"
        status, confidence = "operational_fact", 1.0
        claim = "exact permutation p-value computed"
    else:
        seed = int(_rid(req), 16)  # deterministic seed from payload provenance run-id
        rng = np.random.default_rng(seed)
        stat = np.empty(n_resamples, dtype=float)
        for i in range(n_resamples):
            perm = rng.permutation(pooled)
            stat[i] = np.mean(perm[:na]) - np.mean(perm[na:])
        # Monte-Carlo: +1 correction (Phipson & Smyth 2010) — never reports p=0.
        p = (tally(stat) + 1) / (n_resamples + 1)
        n_used = n_resamples
        method = "monte_carlo (seeded)"
        status, confidence = "corroborated_inference", 0.9
        claim = "approximate (Monte-Carlo) permutation p-value estimated"

    finding = epistemic.make_finding(
        claim=claim, status=status, confidence=confidence,
        source=provenance.engine_trace("stat_run", run_id=_rid(req), anchor="permutation_test"),
    )
    return {
        "statistic": "mean_diff", "observed": round(obs, 6),
        "p": p, "alternative": alternative, "exact": bool(exact),
        "method": method, "n_combinations": int(n_comb), "n_resamples": int(n_used),
        "seed": seed, "finding": finding,
    }


def multiple_testing(req):
    """Bonferroni + Benjamini-Hochberg (FDR) correction of a list of p-values.

    Reference-validated: adjusted p-values reproduce
    statsmodels.stats.multitest.multipletests(method='bonferroni') and ('fdr_bh') to < 1e-12
    (see tests/core/test_stat_run.py).

    The arithmetic is deterministic (operational_fact). The *interpretation* — which
    hypotheses survive alpha — is only as strong as the input p-values, so the claim is scoped
    to "adjustment computed", NOT "these effects are real".

    Input: {op, pvalues:[...], alpha?: float (default 0.05)}
    """
    pvals = list(map(float, req["pvalues"]))
    if not pvals:
        raise ValueError("pvalues must be a non-empty list")
    if any(p < 0.0 or p > 1.0 for p in pvals):
        raise ValueError("pvalues must lie in [0, 1]")
    alpha = float(req.get("alpha", 0.05))
    m = len(pvals)
    arr = np.array(pvals, dtype=float)

    # Bonferroni: p_adj = min(p * m, 1).
    bonf_adj = np.minimum(arr * m, 1.0)

    # Benjamini-Hochberg step-up: sort ascending, p_adj_(k) = min_{j>=k} (m/j) p_(j), cap at 1.
    order = np.argsort(arr, kind="stable")
    ranked = arr[order]
    running = 1.0
    adj_sorted = np.empty(m, dtype=float)
    for i in range(m - 1, -1, -1):
        running = min(running, ranked[i] * m / (i + 1))
        adj_sorted[i] = running
    bh_adj = np.empty(m, dtype=float)
    bh_adj[order] = np.minimum(adj_sorted, 1.0)

    bonf_reject = [bool(x <= alpha) for x in bonf_adj]
    bh_reject = [bool(x <= alpha) for x in bh_adj]

    finding = epistemic.make_finding(
        claim="multiple-testing adjustment computed (Bonferroni + Benjamini-Hochberg)",
        status="operational_fact", confidence=1.0,
        source=provenance.engine_trace("stat_run", run_id=_rid(req), anchor="multiple_testing"),
    )
    return {
        "n_tests": m, "alpha": alpha,
        "bonferroni": {
            "p_adjusted": [round(float(x), 10) for x in bonf_adj],
            "reject": bonf_reject, "n_significant": int(sum(bonf_reject)),
        },
        "benjamini_hochberg": {
            "p_adjusted": [round(float(x), 10) for x in bh_adj],
            "reject": bh_reject, "n_significant": int(sum(bh_reject)),
        },
        "finding": finding,
    }


OPS = {"check_assumptions": check_assumptions, "recompute_ttest": recompute_ttest, "grim": grim,
       "mann_whitney": mann_whitney, "chi_square": chi_square, "fisher": fisher,
       "permutation_test": permutation_test, "multiple_testing": multiple_testing}


def main():
    try:
        req = json_io.read_input()
        op = req.get("op")
        if op not in OPS:
            json_io.emit(json_io.error(f"unknown op: {op!r}"))
            return
        json_io.emit(json_io.ok(OPS[op](req)))
    except Exception as exc:
        json_io.emit(json_io.error(str(exc)))


if __name__ == "__main__":
    main()
