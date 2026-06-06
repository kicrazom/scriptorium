"""L1 entry point: guard-checked KB query.

Input (stdin JSON): {"claim", "backend", "path", "mode"}.
Flow: egress_guard.assert_local_only → provider dispatch → ok envelope {evidence, finding}.
Reviewer-mode + remote backend → guard raises → error envelope (no egress).
"""
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
        egress_guard.assert_local_only(backend, mode)  # may raise EgressViolation
        fn = provider.get_provider(backend)
        result = fn(req["claim"], req["path"])
        json_io.emit(json_io.ok(result))
    except egress_guard.EgressViolation as exc:
        json_io.emit(json_io.error(str(exc)))
    except Exception as exc:
        json_io.emit(json_io.error(str(exc)))


if __name__ == "__main__":
    main()
