# scripts/core/interim_boundaries.py
"""L0 engine: group-sequential upper boundaries via gsDesign (R-dispatch).

Dispatches to scripts/core/rbridge/gsdesign.R through subprocess (isolation over rpy2).
Input: {"k": <int>, "alpha": <float>, "test_type": "one_sided", "sfu": "OF"}.
Output: {k, upper_bounds, sfu, finding}. If Rscript/gsDesign is unavailable, returns an
error envelope rather than crashing.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.lib import json_io, provenance, epistemic  # noqa: E402

RSCRIPT = shutil.which("Rscript")
R_FILE = Path(__file__).resolve().parent / "rbridge" / "gsdesign.R"


def compute(req):
    if RSCRIPT is None:
        raise RuntimeError("Rscript not found — install R + gsDesign for interim boundaries")
    proc = subprocess.run(
        [RSCRIPT, str(R_FILE)],
        input=json.dumps(req), capture_output=True, text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"gsDesign R dispatch failed: {proc.stderr.strip()}")
    r_out = json.loads(proc.stdout)
    bounds = [round(float(b), 6) for b in r_out["upper_bounds"]]

    rid = provenance.run_id(seed=json.dumps(req, sort_keys=True))
    finding = epistemic.make_finding(
        claim=f"{len(bounds)}-look O'Brien-Fleming upper boundaries computed",
        status="operational_fact", confidence=1.0,
        source=provenance.engine_trace("interim_boundaries", run_id=rid, anchor="gsdesign"),
    )
    return {"k": int(req["k"]), "upper_bounds": bounds, "sfu": req.get("sfu", "OF"),
            "finding": finding}


def main():
    try:
        json_io.emit(json_io.ok(compute(json_io.read_input())))
    except Exception as exc:
        json_io.emit(json_io.error(str(exc)))


if __name__ == "__main__":
    main()
