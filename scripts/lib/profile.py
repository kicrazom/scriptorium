"""Shared config-profile parser — turns the per-agent 'read profile.md' convention into one
tested contract.

The profile is a markdown file holding a fenced ```yaml block (see config/profile.example.md).
Resolution order, first match wins: ./.scriptorium/profile.md -> ~/.scriptorium/profile.md ->
none (universal defaults). Unknown top-level sections warn (never crash); malformed YAML raises
ProfileError.
"""
import re
from pathlib import Path

import yaml

# Universal defaults — mirror config/profile.example.md. Empty/zero means "no personalization".
DEFAULTS = {
    "reviewer": {"journals": [], "default_guidelines": ["STROBE", "CONSORT", "PRISMA", "TRIPOD"],
                 "language": "en"},
    "knowledge_base": {"path": "", "link_style": "wikilink", "frontmatter_schema": ""},
    "research": {"sources": ["pubmed", "openalex", "crossref", "arxiv", "europepmc"],
                 "full_text_resolver": "", "shadow_library_optin": False},
    "librarian": {"domains": [], "catalog_path": ""},
    "statistics": {"prefer_runtime": "python", "bayesian_backend": "pymc"},
    "epistemic": {"asymmetric_risk": False},
    "style": {"units_inline": True, "explain_jargon": False},
}

_YAML_BLOCK = re.compile(r"```yaml\s*\n(.*?)\n```", re.DOTALL)


class ProfileError(Exception):
    """Raised when a profile exists but its YAML cannot be parsed."""


def resolve_profile_path(cwd, home):
    """First existing of ./.scriptorium/profile.md (cwd) then ~/.scriptorium/profile.md (home)."""
    project = Path(cwd) / ".scriptorium" / "profile.md"
    if project.exists():
        return project
    user = Path(home) / ".scriptorium" / "profile.md"
    if user.exists():
        return user
    return None


def extract_yaml_block(text):
    """Return the contents of the first ```yaml fenced block, or '' if none."""
    m = _YAML_BLOCK.search(text)
    return m.group(1) if m else ""


def load_profile(path):
    """Parse the yaml block of a profile.md into a dict. {} if path is None or has no block."""
    if path is None:
        return {}
    block = extract_yaml_block(Path(path).read_text(encoding="utf-8"))
    if not block.strip():
        return {}
    try:
        data = yaml.safe_load(block)
    except yaml.YAMLError as exc:
        raise ProfileError(f"invalid YAML in profile {path}: {exc}") from exc
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ProfileError(f"profile {path} must be a YAML mapping, got {type(data).__name__}")
    return data


def merge_with_defaults(profile):
    """Deep-merge a profile over DEFAULTS. Returns (merged, warnings). Unknown top-level
    sections are kept but warned about; unknown sub-fields within a known section are kept too."""
    merged = {k: dict(v) for k, v in DEFAULTS.items()}
    warnings = []
    for section, values in (profile or {}).items():
        if section not in DEFAULTS:
            warnings.append(f"unknown profile section '{section}' (kept, but not a known field)")
            merged[section] = values
            continue
        if not isinstance(values, dict):
            warnings.append(f"profile section '{section}' should be a mapping; ignoring")
            continue
        merged[section].update(values)
    return merged, warnings


def get_profile(cwd, home):
    """Resolve, load, and merge in one call. Returns (merged_profile, warnings)."""
    path = resolve_profile_path(cwd, home)
    return merge_with_defaults(load_profile(path))


def main():
    """CLI: resolve the profile for the current working directory and print it as JSON, so any
    component (agent or skill) can obtain the merged config by running this script instead of
    parsing profile.md itself. Output: {"source": <path|null>, "warnings": [...], "profile": {...}}.
    """
    import json
    import os
    cwd, home = Path(os.getcwd()), Path.home()
    path = resolve_profile_path(cwd, home)
    try:
        merged, warnings = merge_with_defaults(load_profile(path))
    except ProfileError as exc:
        print(json.dumps({"error": str(exc)}))
        return
    print(json.dumps({"source": str(path) if path else None,
                      "warnings": warnings, "profile": merged}))


if __name__ == "__main__":
    main()
