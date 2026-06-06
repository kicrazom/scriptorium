"""Mode-guard: defense-in-depth egress control for the Sovereign reviewer path.

Three levels, strongest first:
  1. Mode declaration   — reviewer-mode refuses remote KB backends (this module).
  2. Capability removal — audit reviewer-path scripts for network imports (Task 2).
  3. Process sandbox    — run under `unshare -n` when available, else best-effort (Task 3).

The guard NEVER claims an isolation it cannot deliver — status() discloses the truth.
"""

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
