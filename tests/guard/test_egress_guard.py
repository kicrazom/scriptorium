import pytest
from scripts.guard import egress_guard as g


def test_reviewer_mode_refuses_remote_backend():
    with pytest.raises(g.EgressViolation):
        g.assert_local_only("rag", mode="reviewer")


def test_reviewer_mode_allows_local_backend():
    # returns None (no raise) for local backends
    assert g.assert_local_only("folder", mode="reviewer") is None
    assert g.assert_local_only("obsidian", mode="reviewer") is None


def test_author_mode_allows_remote_backend():
    assert g.assert_local_only("rag", mode="author") is None


def test_unknown_backend_refused_in_reviewer():
    with pytest.raises(g.EgressViolation):
        g.assert_local_only("mystery", mode="reviewer")


def test_audit_imports_flags_network_module(tmp_path):
    f = tmp_path / "leaky.py"
    f.write_text("import os\nimport requests\nfrom socket import gethostname\n")
    violations = g.audit_imports([str(f)])
    modules = {v["module"] for v in violations}
    assert "requests" in modules
    assert "socket" in modules
    assert "os" not in modules


def test_audit_imports_clean_file(tmp_path):
    f = tmp_path / "clean.py"
    f.write_text("import json\nimport math\nfrom scipy import stats\n")
    assert g.audit_imports([str(f)]) == []


def test_sandbox_claim_matches_reality():
    available = g.sandbox_available()
    result = g.run_sandboxed([__import__("sys").executable, "-c", "print('hi')"])
    assert result["ran"] is True
    assert result["returncode"] == 0
    assert "hi" in result["stdout"]
    # honesty: the isolated flag must equal the real probe, never overclaim.
    assert result["isolated"] == available


def test_status_level3_honest():
    st = g.status(mode="reviewer")
    available = g.sandbox_available()
    if available:
        assert "active" in st["level_3"]
    else:
        assert "best-effort" in st["level_3"]
    assert st["level_1"] == "active"
    assert st["level_2"] == "active"
