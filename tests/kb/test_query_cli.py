import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / "scripts" / "kb" / "query.py"


def run_cli(payload):
    proc = subprocess.run(
        [sys.executable, str(CLI)],
        input=json.dumps(payload), capture_output=True, text=True,
    )
    return json.loads(proc.stdout)


def test_author_mode_folder_query(tmp_path):
    (tmp_path / "a.md").write_text("Spirometry shows obstruction in asthma.\n")
    out = run_cli({"claim": "spirometry obstruction asthma",
                   "backend": "folder", "path": str(tmp_path), "mode": "author"})
    assert out["status"] == "ok"
    assert len(out["data"]["evidence"]) >= 1


def test_reviewer_mode_refuses_rag(tmp_path):
    out = run_cli({"claim": "x", "backend": "rag", "path": str(tmp_path), "mode": "reviewer"})
    assert out["status"] == "error"
    assert "reviewer-mode forbids" in out["message"]


def test_author_mode_rag_is_clean_error(tmp_path):
    out = run_cli({"claim": "x", "backend": "rag", "path": str(tmp_path), "mode": "author"})
    assert out["status"] == "error"
    assert "stub" in out["message"]
