"""Pluggable, model-agnostic backends for the behavioral harness.

Each backend drives one agent runtime (a CLI like Claude Code or Codex, or — later — a local
vLLM endpoint). Following the repo's R-engine convention, a backend whose CLI is absent reports
available()==False and the harness SKIPS it rather than failing. Running the same case through
two backends (e.g. claude_cli vs codex_cli) turns cross-runtime agreement into a validity
signal: both refusing an injection is strong evidence; divergence is itself a finding.
"""
import json
import os
import shutil
import socket
import subprocess
import urllib.request
from urllib.parse import urlparse


class CliBackend:
    """An agent runtime invoked as a headless CLI: prompt in on stdin, response out on stdout."""

    def __init__(self, name, cli_name, argv=None, timeout=180):
        self.name = name
        self.cli_name = cli_name
        self._argv = list(argv) if argv else [cli_name, "-p"]
        self.timeout = timeout

    @property
    def argv(self):
        """The pinned invocation argv (read-only copy). Lets tests assert the syntax without
        spawning the process — verified for claude_cli, argv-verified for codex_cli."""
        return list(self._argv)

    def available(self):
        return shutil.which(self.cli_name) is not None

    def run(self, prompt, mode="offline"):
        """Send prompt to the CLI and return its raw response text. Raises if unavailable or
        the process fails — the caller decides whether that is a skip or a hard error."""
        if not self.available():
            raise RuntimeError(f"backend {self.name!r}: {self.cli_name!r} not on PATH")
        proc = subprocess.run(self._argv, input=prompt, capture_output=True,
                              text=True, timeout=self.timeout)
        if proc.returncode != 0:
            raise RuntimeError(f"backend {self.name!r} exited {proc.returncode}: "
                               f"{proc.stderr.strip()[:200]}")
        return proc.stdout


class VllmBackend:
    """Local vLLM (OpenAI-compatible HTTP) backend — for fully sovereign, offline runs.

    SCAFFOLDED, skip-if-unavailable — NOT validated against a live model. available() is False
    unless an endpoint is configured AND a short TCP probe to it succeeds, so a runner with no
    vLLM server SKIPS rather than errors (mirrors the CLI backends' convention). When no endpoint
    is configured, available() short-circuits with NO network call at all, keeping the default
    CI skip path fully deterministic. The request payload is greedy (temperature 0) so a real run
    is as reproducible as the model allows.
    """

    def __init__(self, name="local_vllm", endpoint=None, model=None, timeout=180,
                 probe_timeout=0.5):
        self.name = name
        self.endpoint = (endpoint if endpoint is not None
                         else os.environ.get("SCRIPTORIUM_VLLM_ENDPOINT", ""))
        self.model = (model if model is not None
                      else os.environ.get("SCRIPTORIUM_VLLM_MODEL", "local-model"))
        self.timeout = timeout
        self.probe_timeout = probe_timeout

    def _host_port(self):
        parsed = urlparse(self.endpoint)
        host = parsed.hostname
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        return host, port

    def available(self):
        if not self.endpoint:
            return False
        host, port = self._host_port()
        if not host:
            return False
        try:
            with socket.create_connection((host, port), timeout=self.probe_timeout):
                return True
        except OSError:
            return False

    def chat_url(self):
        return self.endpoint.rstrip("/") + "/v1/chat/completions"

    def build_payload(self, prompt):
        """The OpenAI-compatible chat-completions request body. Deterministic and model-free —
        the unit tests assert this without ever contacting a server."""
        return {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
            "stream": False,
        }

    def run(self, prompt, mode="offline"):  # noqa: ARG002 - mode kept for interface parity
        """POST the prompt to the vLLM endpoint and return the assistant text. Raises if
        unavailable — the caller decides whether that is a skip or a hard error."""
        if not self.available():
            raise RuntimeError(f"backend {self.name!r}: no reachable vLLM endpoint "
                               f"(set SCRIPTORIUM_VLLM_ENDPOINT)")
        data = json.dumps(self.build_payload(prompt)).encode("utf-8")
        req = urllib.request.Request(self.chat_url(), data=data,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:  # noqa: S310 - local endpoint
            body = json.loads(resp.read().decode("utf-8"))
        return body["choices"][0]["message"]["content"]


# claude_cli: verified flags (`claude -p` headless print). codex_cli: argv `codex exec` is
# ARGV-VERIFIED against codex-cli 0.139.0 — `codex exec` runs non-interactively and reads the
# prompt from stdin when none is passed positionally, exactly how run() pipes it. Real
# cross-runtime runs additionally require `codex login` (an auth credential, not a code concern);
# the backend stays skip-if-unavailable wherever `codex` is absent from PATH. local_vllm:
# scaffolded, skip-if-unavailable, unvalidated against a model.
_REGISTRY = {
    "claude_cli": CliBackend("claude_cli", "claude", argv=["claude", "-p"]),
    "codex_cli": CliBackend("codex_cli", "codex", argv=["codex", "exec"]),
    "local_vllm": VllmBackend("local_vllm"),
}


def available_backends():
    """Names of all registered backends (whether or not their CLI is installed)."""
    return sorted(_REGISTRY)


def get_backend(name):
    """Return the named backend. Raises KeyError for an unknown name."""
    return _REGISTRY[name]
