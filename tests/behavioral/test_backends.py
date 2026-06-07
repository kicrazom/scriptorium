"""Backends are pluggable and follow the repo's skip-if-unavailable convention (like the R
engines): a backend whose CLI is not on PATH reports available()==False, and the harness skips
it rather than failing. Availability is the only deterministic, model-free thing to test here;
the actual model call is exercised behind the llm_judge gate.
"""
import pytest

from scripts.behavioral.backends import CliBackend, available_backends, get_backend


def test_backend_with_missing_cli_is_unavailable():
    assert CliBackend("ghost", "definitely-not-a-real-binary-xyz").available() is False


def test_backend_with_present_cli_is_available():
    # `sh` exists on any POSIX runner — decouples the test from claude/codex being installed.
    assert CliBackend("shell", "sh").available() is True


def test_registry_exposes_claude_and_codex_backends():
    names = available_backends()
    assert "claude_cli" in names
    assert "codex_cli" in names


def test_get_backend_returns_named_backend():
    assert get_backend("claude_cli").name == "claude_cli"


def test_get_backend_rejects_unknown_name():
    with pytest.raises(KeyError):
        get_backend("no_such_backend")
