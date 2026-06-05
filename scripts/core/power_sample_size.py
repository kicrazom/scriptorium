"""L0 engine: closed-form power / sample-size for a two-sample t-test.

Input (stdin JSON): {"test": "two_sample_t", "effect_size": <d>, "alpha": <a>,
                     "power": <1-beta>, "ratio": <n2/n1, default 1.0>}
Output (stdout JSON): ok envelope with {n_per_group, n_total, finding}.

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

from statsmodels.stats.power import TTestIndPower  # noqa: E402


def two_sample_t(effect_size, alpha, power, ratio):
    analysis = TTestIndPower()
    n1 = analysis.solve_power(
        effect_size=effect_size, alpha=alpha, power=power,
        ratio=ratio, alternative="two-sided",
    )
    return int(math.ceil(n1))


def compute(req):
    test = req.get("test")
    if test != "two_sample_t":
        raise ValueError(f"unsupported test: {test!r}")
    effect_size = float(req["effect_size"])
    alpha = float(req.get("alpha", 0.05))
    power = float(req.get("power", 0.80))
    ratio = float(req.get("ratio", 1.0))

    n_per_group = two_sample_t(effect_size, alpha, power, ratio)
    n_total = n_per_group + int(math.ceil(n_per_group * ratio))

    rid = provenance.run_id(seed=json.dumps(req, sort_keys=True))
    finding = epistemic.make_finding(
        claim=f"n={n_per_group}/group for d={effect_size}, alpha={alpha}, power={power}",
        status="operational_fact",
        confidence=1.0,
        source=provenance.engine_trace("power_sample_size", run_id=rid, anchor="result"),
        source_independence=1,
    )
    return {"n_per_group": n_per_group, "n_total": n_total, "finding": finding}


def main():
    try:
        req = json_io.read_input()
        json_io.emit(json_io.ok(compute(req)))
    except Exception as exc:
        json_io.emit(json_io.error(str(exc)))


if __name__ == "__main__":
    main()
