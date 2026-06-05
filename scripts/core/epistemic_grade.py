"""L0 engine: aggregate a list of findings to one graded result (weakest-link).

Input (stdin JSON): {"findings": [{"status": <ladder>, "confidence": <float>}, ...]}
Output (stdout JSON): ok envelope with {overall_status, overall_confidence, n_findings}.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.lib import json_io, epistemic  # noqa: E402


def grade(findings):
    statuses = [f["status"] for f in findings]
    confidences = [f["confidence"] for f in findings]
    return {
        "overall_status": epistemic.weakest_link(statuses),
        "overall_confidence": min(confidences),
        "n_findings": len(findings),
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
