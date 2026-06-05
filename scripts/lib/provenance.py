"""Build provenance strings. Format mirrors the vault convention `source: path#anchor`.

Run ids are derived from a caller-supplied seed (NOT wall-clock) so engine output is
reproducible and golden-testable. The seed is the caller's responsibility (e.g. a hash of
the request payload).
"""
import hashlib


def run_id(seed):
    """Deterministic 12-char id from a seed string."""
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12]


def engine_trace(engine, run_id, anchor):
    """Trace pointing at an L0 engine run, e.g. scripts/core/<engine>.py#run=<id>:<anchor>."""
    return f"scripts/core/{engine}.py#run={run_id}:{anchor}"


def kb_trace(backend, doc, anchor):
    """Trace pointing at a KB document, e.g. kb://<backend>/<doc>#<anchor>."""
    return f"kb://{backend}/{doc}#{anchor}"
