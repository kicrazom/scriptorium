"""Mode-guard: defense-in-depth egress control for the Sovereign reviewer path.

Three levels, strongest first:
  1. Mode declaration   — reviewer-mode refuses remote KB backends (assert_local_only, wired in kb/query.py).
  2. Capability removal — reviewer-mode audits the dispatched provider script for network
                          imports (assert_local_imports, wired in kb/query.py).
  3. Process sandbox    — run under `unshare -n` when available (run_sandboxed); scaffolded,
                          no reviewer subprocess chokepoint wires it yet.

The guard NEVER claims an isolation it cannot deliver — status() discloses the truth.
"""
import ast
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


def _imported_tops(node):
    """Top-level module names an ast Import/ImportFrom node brings in (absolute only)."""
    if isinstance(node, ast.Import):
        return [a.name.split(".")[0] for a in node.names]
    if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
        return [node.module.split(".")[0]]
    return []


def audit_imports(paths):
    """Scan .py files for network-library imports. Returns one violation per hit.

    AST-based, so it catches dotted (`from urllib.request import x`), comma
    (`import os, socket`), and aliased imports a line regex would miss.
    """
    violations = []
    for path in paths:
        if not path:
            continue  # e.g. inspect.getsourcefile returned None — nothing to audit
        with open(path, "r", encoding="utf-8") as fh:
            src = fh.read()
        try:
            tree = ast.parse(src, filename=str(path))
        except SyntaxError:
            continue  # unparseable -> can't run either; nothing to audit
        for node in ast.walk(tree):
            for mod in _imported_tops(node):
                if mod in NETWORK_MODULES:
                    violations.append({"file": str(path), "module": mod, "line": node.lineno})
    return violations


def assert_local_imports(paths, mode):
    """In reviewer-mode, refuse reviewer-path scripts that import a network module.

    Level-2 (capability removal) companion to assert_local_only. No-op outside reviewer-mode.
    """
    if mode != "reviewer":
        return None
    violations = audit_imports(paths)
    if violations:
        mods = sorted({v["module"] for v in violations})
        raise EgressViolation(
            f"reviewer-mode: network imports in reviewer-path script(s): {mods} ({violations})"
        )
    return None


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
