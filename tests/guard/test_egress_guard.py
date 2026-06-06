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
