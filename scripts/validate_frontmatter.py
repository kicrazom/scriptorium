#!/usr/bin/env python3
"""Validate YAML frontmatter of scriptorium agents and skills.

Checks, per agents/*.md and skills/*/SKILL.md:
  - frontmatter present and terminated
  - YAML parses, no tabs
  - required keys: name, description
  - name is slug-safe and equals the file/dir stem
Exit 0 if all pass, 1 otherwise.
"""
import glob
import os
import re
import sys

try:
    import yaml
except ImportError:
    print("PyYAML required: pip install pyyaml", file=sys.stderr)
    sys.exit(2)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SLUG = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def check(path, expect_name):
    rel = os.path.relpath(path, ROOT)
    errs = []
    txt = open(path, encoding="utf-8").read()
    if not txt.startswith("---"):
        errs.append("no frontmatter")
    else:
        parts = txt.split("---", 2)
        fm = parts[1] if len(parts) >= 3 else ""
        if not fm.strip():
            errs.append("unterminated/empty frontmatter")
        else:
            if "\t" in fm:
                errs.append("tab character in YAML")
            try:
                data = yaml.safe_load(fm) or {}
                for key in ("name", "description"):
                    if not data.get(key):
                        errs.append(f"missing '{key}'")
                name = str(data.get("name", ""))
                if not SLUG.match(name):
                    errs.append(f"name '{name}' not slug-safe")
                elif expect_name and name != expect_name:
                    errs.append(f"name '{name}' != expected '{expect_name}'")
            except yaml.YAMLError as exc:
                errs.append(f"YAML error: {exc}")
    if errs:
        print(f"FAIL {rel}: " + "; ".join(errs))
        return 1
    print(f"OK   {rel}")
    return 0


def main():
    rc = 0
    agents = sorted(glob.glob(os.path.join(ROOT, "agents", "*.md")))
    skills = sorted(glob.glob(os.path.join(ROOT, "skills", "*", "SKILL.md")))
    if not agents and not skills:
        print("note: no components found yet")
    for p in agents:
        rc |= check(p, os.path.splitext(os.path.basename(p))[0])
    for p in skills:
        rc |= check(p, os.path.basename(os.path.dirname(p)))
    sys.exit(rc)


if __name__ == "__main__":
    main()
