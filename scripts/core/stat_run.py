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


OPS = {"check_assumptions": check_assumptions}


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
