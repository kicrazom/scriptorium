"""L0 engine: closed-form power / sample-size determination.

Supported designs (``test`` field): ``two_sample_t``, ``paired_t``, ``one_sample_t``,
``two_proportions``, ``one_way_anova``, ``correlation``, ``survival_logrank_events``. Each
returns the required N (or, for survival, ``events_required``) plus the analytic ``method``
used and the ``assumptions`` it rests on, so the number is self-documenting and reproducible.

Input (stdin JSON), e.g.: {"test": "two_sample_t", "effect_size": 0.5, "alpha": 0.05,
                           "power": 0.80, "ratio": 1.0}
Output (stdout JSON): ok envelope with {n_per_group, n_total, method, assumptions, finding}
(survival returns {events_required, method, assumptions, finding}).

n_per_group is ceil of the analytic solution. The finding carries operational_fact /
confidence 1.0 because the computation is deterministic closed-form, with a provenance
trace whose run id is derived from the request payload (reproducible).
"""
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.lib import json_io, provenance, epistemic  # noqa: E402

def two_sample_t(effect_size, alpha, power, ratio):
    from statsmodels.stats.power import TTestIndPower
    n1 = TTestIndPower().solve_power(
        effect_size=effect_size, alpha=alpha, power=power,
        ratio=ratio, alternative="two-sided",
    )
    return int(math.ceil(n1))


def paired_t(effect_size, alpha, power):
    from statsmodels.stats.power import TTestPower
    n = TTestPower().solve_power(
        effect_size=effect_size, alpha=alpha, power=power, alternative="two-sided",
    )
    return int(math.ceil(n))


def two_proportions(p1, p2, alpha, power):
    from statsmodels.stats.power import NormalIndPower
    from statsmodels.stats.proportion import proportion_effectsize
    h = proportion_effectsize(p1, p2)
    n1 = NormalIndPower().solve_power(
        effect_size=abs(h), alpha=alpha, power=power, ratio=1.0, alternative="two-sided",
    )
    return int(math.ceil(n1))


def correlation(r, alpha, power):
    from scipy.stats import norm
    z_a = norm.ppf(1 - alpha / 2)
    z_b = norm.ppf(power)
    n = ((z_a + z_b) / math.atanh(r)) ** 2 + 3
    return int(math.ceil(n))


def survival_logrank_events(hazard_ratio, alpha, power, p1=0.5, p2=0.5):
    from scipy.stats import norm
    z_a = norm.ppf(1 - alpha / 2)
    z_b = norm.ppf(power)
    d = (z_a + z_b) ** 2 / (p1 * p2 * (math.log(hazard_ratio)) ** 2)
    return int(math.ceil(d))


def one_way_anova(effect_size, k_groups, alpha, power):
    from statsmodels.stats.power import FTestAnovaPower
    n_total = FTestAnovaPower().solve_power(
        effect_size=effect_size, alpha=alpha, power=power, k_groups=k_groups,
    )
    return int(math.ceil(n_total / k_groups))  # per-group


def _validate(req):
    """Range-check inputs before computing — a rigor tool must not assume good inputs.
    Raises ValueError with a clear message (surfaced as an error envelope)."""
    test = req.get("test")
    alpha = float(req.get("alpha", 0.05))
    power = float(req.get("power", 0.80))
    if not 0 < alpha < 1:
        raise ValueError("alpha must be in (0, 1)")
    if not 0 < power < 1:
        raise ValueError("power must be in (0, 1)")
    if test in ("two_sample_t", "paired_t", "one_sample_t"):
        if float(req["effect_size"]) <= 0:
            raise ValueError("effect_size (d) must be > 0")
        if test == "two_sample_t" and float(req.get("ratio", 1.0)) <= 0:
            raise ValueError("ratio must be > 0")
    elif test == "one_way_anova":
        if float(req["effect_size"]) <= 0:
            raise ValueError("effect_size (f) must be > 0")
        if int(req["k_groups"]) < 2:
            raise ValueError("k_groups must be >= 2")
    elif test == "two_proportions":
        p1, p2 = float(req["p1"]), float(req["p2"])
        if not (0 < p1 < 1 and 0 < p2 < 1):
            raise ValueError("p1 and p2 must each be in (0, 1)")
        if p1 == p2:
            raise ValueError("p1 and p2 must differ (no effect to detect when equal)")
    elif test == "correlation":
        r = float(req["r"])
        if not -1 < r < 1 or r == 0:
            raise ValueError("correlation r must be non-zero and in (-1, 1)")
    elif test == "survival_logrank_events":
        hr = float(req["hazard_ratio"])
        if hr <= 0 or hr == 1:
            raise ValueError("hazard_ratio must be > 0 and != 1 (ln HR drives the formula)")


def compute(req):
    _validate(req)
    test = req.get("test")
    alpha = float(req.get("alpha", 0.05))
    power = float(req.get("power", 0.80))
    base = {"alpha": alpha, "power": power, "alternative": "two-sided"}

    if test == "two_sample_t":
        effect_size = float(req["effect_size"])
        ratio = float(req.get("ratio", 1.0))
        n_per_group = two_sample_t(effect_size, alpha, power, ratio)
        n_total = n_per_group + int(math.ceil(n_per_group * ratio))
        method = "statsmodels.stats.power.TTestIndPower"
        assumptions = {**base, "effect_size_d": effect_size, "ratio": ratio}
        claim = f"n={n_per_group}/group for d={effect_size}, alpha={alpha}, power={power}"
    elif test == "paired_t":
        effect_size = float(req["effect_size"])
        n_per_group = paired_t(effect_size, alpha, power)
        n_total = n_per_group  # single group of pairs
        method = "statsmodels.stats.power.TTestPower"
        assumptions = {**base, "effect_size_d": effect_size}
        claim = f"n={n_per_group} pairs for d={effect_size}, alpha={alpha}, power={power}"
    elif test == "two_proportions":
        p1 = float(req["p1"])
        p2 = float(req["p2"])
        n_per_group = two_proportions(p1, p2, alpha, power)
        n_total = 2 * n_per_group
        method = "statsmodels.stats.power.NormalIndPower (Cohen's h)"
        assumptions = {**base, "p1": p1, "p2": p2}
        claim = f"n={n_per_group}/group for p1={p1}, p2={p2}, alpha={alpha}, power={power}"
    elif test == "one_way_anova":
        effect_size = float(req["effect_size"])
        k_groups = int(req["k_groups"])
        n_per_group = one_way_anova(effect_size, k_groups, alpha, power)
        n_total = k_groups * n_per_group
        method = "statsmodels.stats.power.FTestAnovaPower"
        assumptions = {**base, "effect_size_f": effect_size, "k_groups": k_groups}
        claim = (f"n={n_per_group}/group ({k_groups} groups) for f={effect_size}, "
                 f"alpha={alpha}, power={power}")
    elif test == "one_sample_t":
        effect_size = float(req["effect_size"])
        n_per_group = paired_t(effect_size, alpha, power)  # one-sample t == TTestPower
        n_total = n_per_group
        method = "statsmodels.stats.power.TTestPower"
        assumptions = {**base, "effect_size_d": effect_size}
        claim = f"n={n_per_group} for d={effect_size}, alpha={alpha}, power={power}"
    elif test == "correlation":
        r = float(req["r"])
        n_per_group = correlation(r, alpha, power)
        n_total = n_per_group
        method = "Fisher z-transform (closed form)"
        assumptions = {**base, "r": r}
        claim = f"n={n_per_group} for r={r}, alpha={alpha}, power={power}"
    elif test == "survival_logrank_events":
        hr = float(req["hazard_ratio"])
        p1 = float(req.get("p1", 0.5))
        p2 = float(req.get("p2", 0.5))
        events = survival_logrank_events(hr, alpha, power, p1, p2)
        method = "Schoenfeld log-rank events (closed form)"
        assumptions = {**base, "hazard_ratio": hr, "p1": p1, "p2": p2,
                       "note": "returns required EVENTS; mapping to enrolled N needs accrual/follow-up"}
        rid = provenance.run_id(seed=json.dumps(req, sort_keys=True))
        finding = epistemic.make_finding(
            claim=f"{events} events required for HR={hr}, alpha={alpha}, power={power}",
            status="operational_fact", confidence=1.0,
            source=provenance.engine_trace("power_sample_size", run_id=rid, anchor="result"),
            source_independence=1,
        )
        return {"events_required": events, "method": method,
                "assumptions": assumptions, "finding": finding}
    else:
        raise ValueError(f"unsupported test: {test!r}")

    rid = provenance.run_id(seed=json.dumps(req, sort_keys=True))
    finding = epistemic.make_finding(
        claim=claim, status="operational_fact", confidence=1.0,
        source=provenance.engine_trace("power_sample_size", run_id=rid, anchor="result"),
        source_independence=1,
    )
    return {"n_per_group": n_per_group, "n_total": n_total,
            "method": method, "assumptions": assumptions, "finding": finding}


def main():
    try:
        req = json_io.read_input()
        json_io.emit(json_io.ok(compute(req)))
    except Exception as exc:
        json_io.emit(json_io.error(str(exc)))


if __name__ == "__main__":
    main()
