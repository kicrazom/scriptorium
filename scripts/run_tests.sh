#!/usr/bin/env bash
# Run the full Scriptorium test suite (pytest L0/lib). Pre-push quality gate.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [ ! -x ".venv/bin/pytest" ]; then
    echo "error: .venv missing — run: python3 -m venv .venv && .venv/bin/pip install -e '.[dev]'" >&2
    exit 1
fi

echo "== pytest =="
.venv/bin/pytest -q

echo "== structure validators =="
bash scripts/validate_structure.sh

echo "ALL GREEN"
