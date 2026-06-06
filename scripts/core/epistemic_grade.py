"""L0 engine: aggregate a list of findings to one graded result (weakest-link).

Input (stdin JSON): {"findings": [{"status": <ladder>, "confidence": <float>}, ...]}
Output (stdout JSON): ok envelope with {overall_status, overall_confidence, n_findings, finding}.
The `finding` re-expresses the aggregate as a graded finding, so this engine conforms to the
uniform envelope contract every engine shares (see schemas/envelope.schema.json).
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.lib import json_io, provenance, epistemic  # noqa: E402


def grade(findings):
    statuses = [f["status"] for f in findings]
    confidences = [f["confidence"] for f in findings]
    overall_status = epistemic.weakest_link(statuses)
    overall_confidence = min(confidences)
    rid = provenance.run_id(
        seed=json.dumps({"s": statuses, "c": confidences}, sort_keys=True))
    finding = epistemic.make_finding(
        claim=f"aggregate of {len(findings)} findings: {overall_status} (weakest-link)",
        status=overall_status, confidence=overall_confidence,
        source=provenance.engine_trace("epistemic_grade", run_id=rid, anchor="aggregate"),
        source_independence=len(findings),
    )
    return {
        "overall_status": overall_status,
        "overall_confidence": overall_confidence,
        "n_findings": len(findings),
        "finding": finding,
    }


def main():
    try:
        req = json_io.read_input()
        findings = req.get("findings", [])
        if not findings:
            json_io.emit(json_io.error("no findings provided"))
            return
        json_io.emit(json_io.ok(grade(findings)))
    except Exception as exc:  # surface as a structured error, never a traceback
        json_io.emit(json_io.error(str(exc)))


if __name__ == "__main__":
    main()
