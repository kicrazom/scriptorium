"""injection_scan engine — deterministic prompt-injection screen over untrusted documents.
Uses the adversarial fixture corpus: the injection manuscript must be flagged, the clean
control must pass, and findings must stay heuristic (working_hypothesis), never overclaim.
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENGINE = ROOT / "scripts" / "core" / "injection_scan.py"
FIX = ROOT / "tests" / "fixtures" / "adversarial"


def run_engine(text):
    proc = subprocess.run(
        [sys.executable, str(ENGINE)],
        input=json.dumps({"text": text}), capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def test_flags_injection_manuscript():
    text = (FIX / "injection_manuscript.md").read_text()
    out = run_engine(text)
    assert out["status"] == "ok"
    hits = out["data"]["injections"]
    patterns = {h["pattern"] for h in hits}
    # the embedded HTML-comment injection and the "Note to the AI reviewer" must be caught
    assert "ignore-previous" in patterns
    assert "role-reassign" in patterns
    assert len(hits) >= 3


def test_passes_clean_manuscript():
    text = (FIX / "clean_manuscript.md").read_text()
    out = run_engine(text)
    assert out["data"]["injections"] == []          # no false positives on legitimate prose


def test_finding_is_heuristic_not_overclaimed():
    # Whether it flags or not, the screen stays working_hypothesis — it never asserts a
    # document is definitively safe or definitively malicious.
    flagged = run_engine((FIX / "injection_manuscript.md").read_text())["data"]["finding"]
    clean = run_engine((FIX / "clean_manuscript.md").read_text())["data"]["finding"]
    assert flagged["status"] == "working_hypothesis"
    assert clean["status"] == "working_hypothesis"
    assert flagged["confidence"] < 1.0 and clean["confidence"] < 1.0
