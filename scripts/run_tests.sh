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

echo "== R / gsDesign =="
if command -v Rscript >/dev/null 2>&1 && \
   Rscript -e 'quit(status = !requireNamespace("gsDesign", quietly=TRUE))' >/dev/null 2>&1; then
    echo "OK   gsDesign available (interim_boundaries tests active)"
else
    echo "WARN gsDesign not available — interim_boundaries tests skipped"
fi

echo "== mode-guard =="
.venv/bin/python -c "from scripts.guard import egress_guard as g; import json; print(json.dumps(g.status('reviewer')))"

echo "ALL GREEN"
