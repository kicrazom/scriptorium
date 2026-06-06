# tests/core/test_guideline_check.py
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENGINE = ROOT / "scripts" / "core" / "guideline_check.py"


def run_engine(payload):
    proc = subprocess.run(
        [sys.executable, str(ENGINE)],
        input=json.dumps(payload), capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def test_detects_missing_limitations():
    text = (
        "This cohort study enrolled participants who met the inclusion criteria. "
        "Statistical analysis adjusted for confounders via regression. "
        "The work was funded by a grant."
    )  # deliberately no 'limitation'
    out = run_engine({"guideline": "strobe", "manuscript_text": text})
    assert out["status"] == "ok"
    missing_ids = [m["id"] for m in out["data"]["missing"]]
    assert "19" in missing_ids        # limitations missing
    assert "1a" in out["data"]["present"]   # 'cohort study' present
    assert out["data"]["finding"]["status"] == "working_hypothesis"


def test_unknown_guideline_is_error():
    out = run_engine({"guideline": "nonexistent", "manuscript_text": "x"})
    assert out["status"] == "error"


def test_consort_detects_missing_blinding():
    text = ("This randomised controlled trial defined a primary outcome. "
            "Sample size was determined to detect the effect. "
            "The allocation sequence was computer-generated. "
            "Results report the hazard ratio with 95% CI.")  # no blinding mention
    out = run_engine({"guideline": "consort", "manuscript_text": text})
    assert out["status"] == "ok"
    missing_ids = [m["id"] for m in out["data"]["missing"]]
    assert "11a" in missing_ids       # blinding missing
    assert "1a" in out["data"]["present"]


def test_prisma_detects_missing_registration():
    text = ("This systematic review defined eligibility criteria. "
            "We searched PubMed and Embase. The search strategy used boolean terms. "
            "Risk of bias was assessed with ROB 2.")  # no PROSPERO/registration
    out = run_engine({"guideline": "prisma", "manuscript_text": text})
    missing_ids = [m["id"] for m in out["data"]["missing"]]
    assert "21" in missing_ids        # registration missing
    assert "1" in out["data"]["present"]
