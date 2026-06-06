"""Mode-guard: defense-in-depth egress control for the Sovereign reviewer path.

Three levels, strongest first:
  1. Mode declaration   — reviewer-mode refuses remote KB backends (this module).
  2. Capability removal — audit reviewer-path scripts for network imports (Task 2).
  3. Process sandbox    — run under `unshare -n` when available, else best-effort (Task 3).

The guard NEVER claims an isolation it cannot deliver — status() discloses the truth.
"""
import re
import shutil
import subprocess

LOCAL_BACKENDS = {"folder", "obsidian", "cag"}
REMOTE_BACKENDS = {"rag"}


class EgressViolation(Exception):
    """Raised when reviewer-mode would touch a non-local egress path."""


def assert_local_only(backend, mode):
    """In reviewer-mode, only LOCAL_BACKENDS are allowed. Raises EgressViolation otherwise."""
    if mode != "reviewer":
        return None
    if backend in LOCAL_BACKENDS:
        return None
    raise EgressViolation(
        f"reviewer-mode forbids non-local KB backend {backend!r} "
        f"(allowed: {sorted(LOCAL_BACKENDS)})"
    )


NETWORK_MODULES = {
    "requests", "httpx", "urllib", "urllib2", "socket",
    "aiohttp", "http", "ftplib", "telnetlib",
}
_IMPORT_RE = re.compile(r"^\s*(?:import\s+(\w+)|from\s+(\w+)\s+import)")


def audit_imports(paths):
    """Scan .py files for network-library imports. Returns one violation per hit."""
    violations = []
    for path in paths:
        with open(path, "r", encoding="utf-8") as fh:
            for lineno, line in enumerate(fh, start=1):
                m = _IMPORT_RE.match(line)
                if not m:
                    continue
                module = m.group(1) or m.group(2)
                if module in NETWORK_MODULES:
                    violations.append({"file": path, "module": module, "line": lineno})
    return violations


_UNSHARE = shutil.which("unshare")


def sandbox_available():
    """True iff unprivileged network-isolating sandbox (`unshare -rn`) works here."""
    if _UNSHARE is None:
        return False
    try:
        r = subprocess.run(
            [_UNSHARE, "-rn", "true"], capture_output=True, timeout=10,
        )
        return r.returncode == 0
    except Exception:
        return False


def run_sandboxed(cmd):
    """Run cmd; isolate network via `unshare -rn` when available, else plain (honest)."""
    isolated = sandbox_available()
    full = [_UNSHARE, "-rn", *cmd] if isolated else list(cmd)
    proc = subprocess.run(full, capture_output=True, text=True)
    return {
        "ran": True, "isolated": isolated,
        "returncode": proc.returncode, "stdout": proc.stdout,
    }


def status(mode):
    """Disclose which defense levels are active. Never overclaims level 3."""
    if sandbox_available():
        level_3 = "active (unshare -rn)"
    else:
        level_3 = "unavailable — best-effort (levels 1+2)"
    return {"mode": mode, "level_1": "active", "level_2": "active", "level_3": level_3}
