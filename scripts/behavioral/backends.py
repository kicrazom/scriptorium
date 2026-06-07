"""Pluggable, model-agnostic backends for the behavioral harness.

Each backend drives one agent runtime (a CLI like Claude Code or Codex, or — later — a local
vLLM endpoint). Following the repo's R-engine convention, a backend whose CLI is absent reports
available()==False and the harness SKIPS it rather than failing. Running the same case through
two backends (e.g. claude_cli vs codex_cli) turns cross-runtime agreement into a validity
signal: both refusing an injection is strong evidence; divergence is itself a finding.
"""
import shutil
import subprocess


class CliBackend:
    """An agent runtime invoked as a headless CLI: prompt in on stdin, response out on stdout."""

    def __init__(self, name, cli_name, argv=None, timeout=180):
        self.name = name
        self.cli_name = cli_name
        self._argv = list(argv) if argv else [cli_name, "-p"]
        self.timeout = timeout

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


# claude_cli: verified flags (`claude -p` headless print). codex_cli: argv is PROVISIONAL — it
# skips wherever `codex` is absent, so no test depends on it; confirm the exec syntax before the
# first real codex run.
_REGISTRY = {
    "claude_cli": CliBackend("claude_cli", "claude", argv=["claude", "-p"]),
    "codex_cli": CliBackend("codex_cli", "codex", argv=["codex", "exec"]),
}


def available_backends():
    """Names of all registered backends (whether or not their CLI is installed)."""
    return sorted(_REGISTRY)


def get_backend(name):
    """Return the named backend. Raises KeyError for an unknown name."""
    return _REGISTRY[name]
