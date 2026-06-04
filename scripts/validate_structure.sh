#!/usr/bin/env bash
# Assert every roster component and core artifact exists.
set -uo pipefail
cd "$(dirname "$0")/.."
miss=0
need=(
  ".claude-plugin/plugin.json"
  ".claude-plugin/marketplace.json"
  "config/profile.example.md"
  ".claude/commands/scriptorium-init.md"
  "agents/peer-reviewer.md"
  "agents/librarian.md"
  "agents/research-scout.md"
  "agents/statistician.md"
)
for s in literature-search reporting-guideline-check epistemic-status \
         field-note-from-url manuscript-imrad peer-paraphrase \
         power-sample-size interim-analysis-reviewer; do
  need+=("skills/$s/SKILL.md")
done
for f in "${need[@]}"; do
  if [[ -f "$f" ]]; then echo "OK   $f"; else echo "MISS $f"; miss=1; fi
done
exit "$miss"
