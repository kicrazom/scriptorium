"""L0 engine: GRIMMER test (granularity consistency of a reported mean + SD) via R-dispatch
to the `scrutiny` package (the reference implementation).

Input (stdin JSON): {"x": "<mean-as-string>", "sd": "<sd-as-string>", "n": <int>, "items": <int=1>}
(x and sd are strings so their reported decimals are preserved exactly).
Output (stdout JSON): {consistent, reliable, reason, finding}.

Why R-dispatch rather than a Python reimplementation: GRIMMER's analytic algorithm (Allard
2018) is subtle and `scrutiny` is the validated reference, so we call it directly — correct by
construction. IMPORTANT: scrutiny has a known bug (issue #80) where GRIMMER "test 3" can flag
consistent values as inconsistent. We therefore DEMOTE a test-3-only failure to an
indeterminate finding (working_hypothesis, low confidence) instead of asserting inconsistency —
no false positives. GRIM and tests 1-2 are sound and reported as operational_fact.

Requires R + scrutiny; returns an error envelope when they are absent.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.lib import json_io, provenance, epistemic  # noqa: E402

RSCRIPT = shutil.which("Rscript")
R_FILE = Path(__file__).resolve().parent / "rbridge" / "grimmer.R"


def compute(req):
    if RSCRIPT is None:
        raise RuntimeError("Rscript not found — install R + scrutiny for the GRIMMER test")
    proc = subprocess.run(
        [RSCRIPT, str(R_FILE)],
        input=json.dumps(req), capture_output=True, text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"scrutiny GRIMMER dispatch failed: {proc.stderr.strip()[-300:]}")
    r_out = json.loads(proc.stdout)
    consistent = bool(r_out["consistent"])
    reason = r_out["reason"]
    # scrutiny issue #80: GRIMMER test 3 can false-positive → a test-3-only failure is unreliable.
    reliable = "test 3" not in reason.lower()

    rid = provenance.run_id(seed=json.dumps(req, sort_keys=True))
    source = provenance.engine_trace("grimmer", run_id=rid, anchor="scrutiny")

    if consistent:
        finding = epistemic.make_finding(
            claim="reported mean+SD are granularity-consistent (GRIMMER: passed)",
            status="operational_fact", confidence=1.0, source=source)
    elif reliable:
        finding = epistemic.make_finding(
            claim=f"reported mean+SD are granularity-INCONSISTENT (GRIMMER: {reason})",
            status="operational_fact", confidence=1.0, source=source)
    else:  # inconsistent only via the buggy test 3 → indeterminate, never a confident flag
        finding = epistemic.make_finding(
            claim=("GRIMMER test-3 flagged a possible inconsistency, but scrutiny issue #80 "
                   "can false-positive here — INDETERMINATE, verify manually"),
            status="working_hypothesis", confidence=0.5, source=source)

    return {"consistent": consistent, "reliable": reliable, "reason": reason,
            "finding": finding}


def main():
    try:
        json_io.emit(json_io.ok(compute(json_io.read_input())))
    except Exception as exc:
        json_io.emit(json_io.error(str(exc)))


if __name__ == "__main__":
    main()
