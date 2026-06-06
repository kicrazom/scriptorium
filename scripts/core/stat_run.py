# scripts/core/stat_run.py
"""L0 engine: statistical sanity checks. Op-dispatched via the JSON "op" field.

Ops:
  check_assumptions — Shapiro normality (per group) + Levene equal-variance; recommend
                      a nonparametric alternative when a parametric test's assumptions fail.
  recompute_ttest   — recompute t/df/p/CI for two groups; flag mismatch vs a claimed p.
  grim              — Granularity-Related Inconsistency of Means (integer reachability).

Input/Output: stdin/stdout JSON envelopes (see scripts/lib/json_io.py).
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.lib import json_io, provenance, epistemic  # noqa: E402

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
    import math
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


OPS = {"check_assumptions": check_assumptions, "recompute_ttest": recompute_ttest, "grim": grim,
       "mann_whitney": mann_whitney}


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
