#!/usr/bin/env bash
# Validate that the plugin and marketplace manifests are well-formed JSON.
set -uo pipefail
cd "$(dirname "$0")/.."
fail=0
for f in .claude-plugin/plugin.json .claude-plugin/marketplace.json; do
  if [[ ! -f "$f" ]]; then
    echo "MISS $f"; fail=1; continue
  fi
  if python3 -m json.tool "$f" >/dev/null 2>&1; then
    echo "OK   $f"
  else
    echo "FAIL $f (invalid JSON)"; fail=1
  fi
done
exit "$fail"
