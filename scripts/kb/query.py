"""L1 entry point: guard-checked KB query.

Input (stdin JSON): {"claim", "backend", "path", "mode"}.
Flow: egress_guard.assert_local_only → provider dispatch → ok envelope {evidence, finding}.
Reviewer-mode + remote backend → guard raises → error envelope (no egress).
"""
import inspect
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.lib import json_io  # noqa: E402
from scripts.guard import egress_guard  # noqa: E402
from scripts.kb import provider  # noqa: E402


def main():
    try:
        req = json_io.read_input()
        backend = req["backend"]
        mode = req.get("mode", "author")
        egress_guard.assert_local_only(backend, mode)  # L1: refuse remote backend by name
        fn = provider.get_provider(backend)
        # L2: in reviewer-mode, audit the dispatched provider's source for network imports.
        egress_guard.assert_local_imports([inspect.getsourcefile(fn)], mode)
        result = fn(req["claim"], req["path"])
        json_io.emit(json_io.ok(result))
    except egress_guard.EgressViolation as exc:
        json_io.emit(json_io.error(str(exc)))
    except Exception as exc:
        json_io.emit(json_io.error(str(exc)))


if __name__ == "__main__":
    main()
