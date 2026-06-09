"""Backends are pluggable and follow the repo's skip-if-unavailable convention (like the R
engines): a backend whose CLI is not on PATH reports available()==False, and the harness skips
it rather than failing. Availability is the only deterministic, model-free thing to test here;
the actual model call is exercised behind the llm_judge gate.
"""
import pytest

from scripts.behavioral.backends import (
    CliBackend,
    VllmBackend,
    available_backends,
    get_backend,
)


def test_backend_with_missing_cli_is_unavailable():
    assert CliBackend("ghost", "definitely-not-a-real-binary-xyz").available() is False


def test_backend_with_present_cli_is_available():
    # `sh` exists on any POSIX runner — decouples the test from claude/codex being installed.
    assert CliBackend("shell", "sh").available() is True


def test_registry_exposes_claude_codex_and_local_vllm_backends():
    names = available_backends()
    assert "claude_cli" in names
    assert "codex_cli" in names
    assert "local_vllm" in names


def test_get_backend_returns_named_backend():
    assert get_backend("claude_cli").name == "claude_cli"


def test_get_backend_rejects_unknown_name():
    with pytest.raises(KeyError):
        get_backend("no_such_backend")


# --- CLI argv is pinned deterministically (no process is ever spawned here) ------------------

def test_claude_cli_argv_is_pinned():
    # claude_cli flags are VERIFIED (`claude -p` headless print).
    assert get_backend("claude_cli").argv == ["claude", "-p"]


def test_codex_cli_argv_is_pinned_provisional():
    # codex_cli argv is PROVISIONAL — pinned so a future change is caught, but unverified until a
    # real codex install confirms `codex exec` syntax. No invocation happens in default CI.
    assert get_backend("codex_cli").argv == ["codex", "exec"]


# --- local_vllm: skip-if-unavailable + deterministic request construction (no model call) ----

def test_local_vllm_unavailable_without_endpoint():
    # No endpoint configured => unavailable, with NO network call (deterministic skip path).
    assert VllmBackend(endpoint="").available() is False


def test_local_vllm_unavailable_when_endpoint_unreachable():
    # A configured-but-closed endpoint must SKIP (available False), not raise. Port 1 is closed.
    backend = VllmBackend(endpoint="http://127.0.0.1:1", probe_timeout=0.2)
    assert backend.available() is False


def test_local_vllm_run_raises_when_unavailable():
    # Mirrors CliBackend: run() on an unavailable backend raises, the caller decides skip/error.
    with pytest.raises(RuntimeError):
        VllmBackend(endpoint="").run("hello")


def test_local_vllm_chat_url_is_openai_compatible():
    backend = VllmBackend(endpoint="http://localhost:8000/")
    assert backend.chat_url() == "http://localhost:8000/v1/chat/completions"


def test_local_vllm_payload_is_deterministic_and_greedy():
    backend = VllmBackend(endpoint="http://localhost:8000", model="my-model")
    payload = backend.build_payload("PROMPT TEXT")
    assert payload["model"] == "my-model"
    assert payload["messages"] == [{"role": "user", "content": "PROMPT TEXT"}]
    assert payload["temperature"] == 0          # greedy decode => reproducible
    assert payload["stream"] is False


def test_registry_local_vllm_is_unavailable_by_default():
    # The registered instance reads no endpoint by default, so it skips cleanly on a bare runner.
    assert get_backend("local_vllm").available() is False
