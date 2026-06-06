# Scriptorium v0.4.0 — Plan 1: Power families + Profile parser

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Round out the `power_sample_size` engine with the remaining common designs
(`one_sample_t`, `correlation`, `survival_logrank_events`) and add the shared, tested config
parser `scripts/lib/profile.py` so profile handling becomes a contract instead of a
per-agent convention.

**Architecture:** L0 only. Power additions follow the existing dispatch pattern (new `test`
branches + helpers, returning `{n_per_group|events, n_total, method, assumptions, finding}`).
The profile parser is a new pure-Python library with no engine dependencies.

**Tech Stack:** Python 3 (statsmodels, scipy, PyYAML), pytest.

**Prerequisite:** v0.3.0 complete (54 tests green). Reuses `scripts/lib/{json_io,provenance,epistemic}`.

**Do NOT touch** `CHANGELOG.md`, `pyproject.toml`, or `.claude-plugin/*.json` — version bump
and changelog are consolidated by the maintainer after this plan (and after GRIMMER + JSON
schemas, which are handled separately). Commit only the files named in each task.

**Testing philosophy:** all three power additions are **closed-form** (no statsmodels
version sensitivity for correlation/survival; `one_sample_t` uses `TTestPower`). Tests
**recompute the same closed form inline** and assert the engine matches, plus a sanity range
against the textbook value. The profile parser is tested behaviorally (resolution order,
yaml-block extraction, defaults merge, unknown-field warnings, invalid YAML).

---

## File Structure

| File | Change |
|---|---|
| `scripts/core/power_sample_size.py` | Add `one_sample_t`, `correlation`, `survival_logrank_events`. |
| `scripts/lib/profile.py` | New: resolve / load / validate / merge config profile. |
| `tests/core/test_power_sample_size.py` | Add family tests. |
| `tests/lib/test_profile.py` | New: parser behavior tests. |
| `tests/fixtures/profile/*` | New: sample profile.md fixtures. |

---

## Task 1: `power_sample_size.py` — `one_sample_t`

**Files:** modify `scripts/core/power_sample_size.py`, `tests/core/test_power_sample_size.py`.

`one_sample_t` (a single mean vs a reference, or pre/post differences) uses the same
`TTestPower` routine as `paired_t`. `n_total == n_per_group` (one group).

- [ ] **Step 1: Add the failing test**

```python
# append to tests/core/test_power_sample_size.py
def test_one_sample_t_family():
    out = run_engine({"test": "one_sample_t", "effect_size": 0.5, "alpha": 0.05, "power": 0.80})
    assert out["status"] == "ok"
    assert 33 <= out["data"]["n_per_group"] <= 35   # d=0.5 one-sample ~ 34
    assert out["data"]["n_total"] == out["data"]["n_per_group"]
    assert out["data"]["method"].startswith("statsmodels")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd ~/code/scriptorium && .venv/bin/pytest tests/core/test_power_sample_size.py -v -k one_sample`
Expected: FAIL — `unsupported test: 'one_sample_t'`.

- [ ] **Step 3: Add the dispatch branch**

In `compute()`, add this branch before the final `else` (reuse the existing `paired_t` helper):

```python
    elif test == "one_sample_t":
        effect_size = float(req["effect_size"])
        n_per_group = paired_t(effect_size, alpha, power)  # one-sample t == TTestPower
        n_total = n_per_group
        method = "statsmodels.stats.power.TTestPower"
        assumptions = {**base, "effect_size_d": effect_size}
        claim = f"n={n_per_group} for d={effect_size}, alpha={alpha}, power={power}"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd ~/code/scriptorium && .venv/bin/pytest tests/core/test_power_sample_size.py -v`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add scripts/core/power_sample_size.py tests/core/test_power_sample_size.py
git commit -m "feat(core): power_sample_size — one_sample_t family"
```

---

## Task 2: `power_sample_size.py` — `correlation`

**Files:** modify `scripts/core/power_sample_size.py`, `tests/core/test_power_sample_size.py`.

Closed form via the Fisher z-transform: `n = ((z_{1-α/2} + z_{1-β}) / atanh(r))² + 3`.
Deterministic — no statsmodels dependence. `n_total == n_per_group` (one sample of pairs).

- [ ] **Step 1: Add the failing test (recomputes the closed form inline)**

```python
# append to tests/core/test_power_sample_size.py
def test_correlation_family():
    import math
    from scipy.stats import norm
    r, alpha, power = 0.30, 0.05, 0.80
    out = run_engine({"test": "correlation", "r": r, "alpha": alpha, "power": power})
    assert out["status"] == "ok"
    z_a = norm.ppf(1 - alpha / 2)
    z_b = norm.ppf(power)
    expected = math.ceil(((z_a + z_b) / math.atanh(r)) ** 2 + 3)
    assert out["data"]["n_per_group"] == expected   # exact closed form
    assert 80 <= out["data"]["n_per_group"] <= 90    # textbook sanity (~85)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd ~/code/scriptorium && .venv/bin/pytest tests/core/test_power_sample_size.py -v -k correlation`
Expected: FAIL — `unsupported test: 'correlation'`.

- [ ] **Step 3: Add helper + dispatch branch**

Add helper (next to the others):

```python
def correlation(r, alpha, power):
    from scipy.stats import norm
    z_a = norm.ppf(1 - alpha / 2)
    z_b = norm.ppf(power)
    n = ((z_a + z_b) / math.atanh(r)) ** 2 + 3
    return int(math.ceil(n))
```

Add branch in `compute()` before the final `else`:

```python
    elif test == "correlation":
        r = float(req["r"])
        n_per_group = correlation(r, alpha, power)
        n_total = n_per_group
        method = "Fisher z-transform (closed form)"
        assumptions = {**base, "r": r}
        claim = f"n={n_per_group} for r={r}, alpha={alpha}, power={power}"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd ~/code/scriptorium && .venv/bin/pytest tests/core/test_power_sample_size.py -v`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add scripts/core/power_sample_size.py tests/core/test_power_sample_size.py
git commit -m "feat(core): power_sample_size — correlation family (Fisher z, closed form)"
```

---

## Task 3: `power_sample_size.py` — `survival_logrank_events`

**Files:** modify `scripts/core/power_sample_size.py`, `tests/core/test_power_sample_size.py`.

Schoenfeld's formula for the **number of events** (not N) required to detect a hazard ratio:
`d_events = (z_{1-α/2} + z_{1-β})² / (p1 · p2 · (ln HR)²)`, where `p1, p2` are the allocation
fractions (default 0.5 each). The engine returns required events; mapping events → enrolled N
needs accrual/follow-up assumptions and stays an agent-guided step (documented in `assumptions`).

- [ ] **Step 1: Add the failing test (recomputes inline)**

```python
# append to tests/core/test_power_sample_size.py
def test_survival_logrank_events():
    import math
    from scipy.stats import norm
    hr, alpha, power = 0.5, 0.05, 0.80
    out = run_engine({"test": "survival_logrank_events", "hazard_ratio": hr,
                      "alpha": alpha, "power": power})
    assert out["status"] == "ok"
    z_a = norm.ppf(1 - alpha / 2); z_b = norm.ppf(power)
    expected = math.ceil((z_a + z_b) ** 2 / (0.5 * 0.5 * (math.log(hr)) ** 2))
    assert out["data"]["events_required"] == expected
    assert "events" in out["data"]["finding"]["claim"].lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd ~/code/scriptorium && .venv/bin/pytest tests/core/test_power_sample_size.py -v -k survival`
Expected: FAIL — `unsupported test: 'survival_logrank_events'`.

- [ ] **Step 3: Add helper + dispatch branch**

Add helper:

```python
def survival_logrank_events(hazard_ratio, alpha, power, p1=0.5, p2=0.5):
    from scipy.stats import norm
    z_a = norm.ppf(1 - alpha / 2)
    z_b = norm.ppf(power)
    d = (z_a + z_b) ** 2 / (p1 * p2 * (math.log(hazard_ratio)) ** 2)
    return int(math.ceil(d))
```

Add branch in `compute()` before the final `else`. This design returns `events_required`
rather than `n_per_group`/`n_total`, so it builds and returns its result directly:

```python
    elif test == "survival_logrank_events":
        hr = float(req["hazard_ratio"])
        p1 = float(req.get("p1", 0.5)); p2 = float(req.get("p2", 0.5))
        events = survival_logrank_events(hr, alpha, power, p1, p2)
        method = "Schoenfeld log-rank events (closed form)"
        assumptions = {**base, "hazard_ratio": hr, "p1": p1, "p2": p2,
                       "note": "returns required EVENTS; mapping to enrolled N needs accrual/follow-up"}
        rid = provenance.run_id(seed=json.dumps(req, sort_keys=True))
        finding = epistemic.make_finding(
            claim=f"{events} events required for HR={hr}, alpha={alpha}, power={power}",
            status="operational_fact", confidence=1.0,
            source=provenance.engine_trace("power_sample_size", run_id=rid, anchor="result"),
            source_independence=1,
        )
        return {"events_required": events, "method": method,
                "assumptions": assumptions, "finding": finding}
```

(Note: this `return` is inside the branch, mirroring the function's normal return shape but
with `events_required` instead of `n_per_group`/`n_total`. Leave the shared `return` at the
bottom of `compute()` for the other branches unchanged.)

- [ ] **Step 4: Run test to verify it passes**

Run: `cd ~/code/scriptorium && .venv/bin/pytest tests/core/test_power_sample_size.py -v`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add scripts/core/power_sample_size.py tests/core/test_power_sample_size.py
git commit -m "feat(core): power_sample_size — survival_logrank_events (Schoenfeld, closed form)"
```

---

## Task 4: `scripts/lib/profile.py` — config parser

**Files:** create `scripts/lib/profile.py`, `tests/lib/test_profile.py`, `tests/fixtures/profile/`.

The profile lives in a markdown file (`profile.md`) containing a fenced ` ```yaml ` block
(see `config/profile.example.md`). The parser resolves the path (project → user → none),
extracts and parses that YAML block, merges it over universal defaults, and reports unknown
top-level sections as **warnings** (never crashes). Invalid YAML raises a clear `ProfileError`.

Contract:
- `resolve_profile_path(cwd: Path, home: Path) -> Path | None`
- `extract_yaml_block(text: str) -> str` — the first ` ```yaml … ``` ` block, or `""`.
- `load_profile(path: Path | None) -> dict` — parsed YAML (or `{}` if path is None/empty block).
- `merge_with_defaults(profile: dict) -> tuple[dict, list[str]]` — deep-merge over `DEFAULTS`,
  returning `(merged, warnings)` where warnings name unknown top-level sections.
- `get_profile(cwd, home) -> tuple[dict, list[str]]` — convenience: resolve → load → merge.

- [ ] **Step 1: Create test fixtures**

```bash
cd ~/code/scriptorium && mkdir -p tests/fixtures/profile/project/.scriptorium \
  tests/fixtures/profile/home/.scriptorium tests/fixtures/profile/badyaml/.scriptorium \
  tests/fixtures/profile/unknown/.scriptorium
```

`tests/fixtures/profile/project/.scriptorium/profile.md`:
````markdown
# my profile
```yaml
statistics:
  prefer_runtime: r
style:
  explain_jargon: true
```
````

`tests/fixtures/profile/home/.scriptorium/profile.md`:
````markdown
```yaml
statistics:
  prefer_runtime: none
```
````

`tests/fixtures/profile/badyaml/.scriptorium/profile.md`:
````markdown
```yaml
statistics: : : not valid
  - broken
```
````

`tests/fixtures/profile/unknown/.scriptorium/profile.md`:
````markdown
```yaml
nonsense_section:
  foo: bar
statistics:
  prefer_runtime: python
```
````

- [ ] **Step 2: Write the failing tests**

```python
# tests/lib/test_profile.py
import pytest
from pathlib import Path
from scripts.lib import profile as P

FIX = Path(__file__).resolve().parents[1] / "fixtures" / "profile"


def test_no_profile_uses_defaults(tmp_path):
    merged, warnings = P.get_profile(cwd=tmp_path, home=tmp_path)
    assert merged["statistics"]["prefer_runtime"] == "python"   # universal default
    assert warnings == []


def test_project_profile_wins(tmp_path):
    proj = FIX / "project"
    merged, _ = P.get_profile(cwd=proj, home=FIX / "home")
    assert merged["statistics"]["prefer_runtime"] == "r"        # project overrides
    assert merged["style"]["explain_jargon"] is True


def test_global_profile_used_when_project_missing(tmp_path):
    merged, _ = P.get_profile(cwd=tmp_path, home=FIX / "home")
    assert merged["statistics"]["prefer_runtime"] == "none"     # from ~/.scriptorium


def test_defaults_fill_unset_fields(tmp_path):
    merged, _ = P.get_profile(cwd=FIX / "home", home=FIX / "home")
    # home profile only sets prefer_runtime; other sections come from defaults
    assert merged["epistemic"]["asymmetric_risk"] is False


def test_invalid_yaml_raises_clear_error():
    path = FIX / "badyaml" / ".scriptorium" / "profile.md"
    with pytest.raises(P.ProfileError):
        P.load_profile(path)


def test_unknown_section_warns_not_crashes():
    path = FIX / "unknown" / ".scriptorium" / "profile.md"
    merged, warnings = P.merge_with_defaults(P.load_profile(path))
    assert any("nonsense_section" in w for w in warnings)
    assert merged["statistics"]["prefer_runtime"] == "python"   # known field still applied


def test_extract_yaml_block_handles_no_block():
    assert P.extract_yaml_block("# just markdown, no code block") == ""
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd ~/code/scriptorium && .venv/bin/pytest tests/lib/test_profile.py -v`
Expected: FAIL — module missing.

- [ ] **Step 4: Write the implementation**

```python
# scripts/lib/profile.py
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
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd ~/code/scriptorium && .venv/bin/pytest tests/lib/test_profile.py -v`
Expected: 7 passed.

- [ ] **Step 6: Commit**

```bash
git add scripts/lib/profile.py tests/lib/test_profile.py tests/fixtures/profile
git commit -m "feat(lib): profile parser — resolve/load/merge config with defaults + unknown-field warnings"
```

---

## Self-Review

**Spec coverage (v0.4.0 part 1):** power families `one_sample_t` / `correlation` /
`survival_logrank_events` (ROADMAP v0.4.0) → Tasks 1–3; shared tested config parser
(ROADMAP v0.4.0, review priority 3) → Task 4. GRIMMER and JSON schemas are handled separately
by the maintainer (not in this plan). Regression power approximation is deferred (noted in
ROADMAP) — it is an approximation with several conventions and deserves its own careful task.

**Placeholder scan:** no TBD/TODO; every step shows complete code; run steps show command +
expected result. Fixture contents are complete, not sketched.

**Type consistency:** new power branches keep `{method, assumptions, finding}` and reuse the
existing `paired_t` helper (Task 1) and `base`/`provenance`/`epistemic` already in the module.
`survival_logrank_events` deliberately returns `events_required` (not `n_per_group`) and builds
its own return inside the branch — the test asserts that shape. Profile parser names
(`resolve_profile_path`, `extract_yaml_block`, `load_profile`, `merge_with_defaults`,
`get_profile`, `ProfileError`, `DEFAULTS`) are consistent between the implementation (Task 4
Step 4) and the tests (Step 2).
