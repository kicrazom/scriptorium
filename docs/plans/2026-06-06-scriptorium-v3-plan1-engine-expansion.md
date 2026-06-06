# Scriptorium v0.3.0 — Plan 1: Rigor Engine Expansion

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Grow the deterministic L0 engines to cover more peer-review-relevant computations — additional power/sample-size design families, nonparametric and categorical tests, and two more reporting guidelines (CONSORT, PRISMA) — following the proven JSON-contract + golden-test pattern.

**Architecture:** Layered (Approach A), L0 only. Each addition extends an existing engine
(`power_sample_size.py`, `stat_run.py`, `guideline_check.py`) with new `test`/`op` branches or
new YAML data, preserving the envelope + graded-finding contract. No new architecture.

**Tech Stack:** Python 3 (statsmodels, scipy, PyYAML), pytest.

**Prerequisite:** v0.2.0 complete (44 tests green; `scripts/lib/`, `scripts/core/` engines,
venv, `run_tests.sh`). Reuses `scripts/lib/{json_io,provenance,epistemic}.py`.

**Testing philosophy:** power-family results are version-sensitive floats → assert
**plausible ranges** around the canonical textbook value (wide enough to survive a
statsmodels point release, tight enough to catch a gross error) + structure + finding shape.
Nonparametric/categorical tests → **recompute the scipy reference inline** and assert the
engine matches (verifies wiring + envelope, not a brittle magic number). Guideline gaps →
exact keyword assertions. **GRIMMER (SD consistency) is deliberately deferred** — its
algorithm is subtle and a wrong statistic in a rigor tool is the worst failure mode; it gets
its own careful increment later.

---

## File Structure (Plan 1)

| File | Change |
|---|---|
| `scripts/core/power_sample_size.py` | Add `paired_t`, `two_proportions`, `one_way_anova` families. |
| `scripts/core/stat_run.py` | Add ops `mann_whitney`, `chi_square`, `fisher`. |
| `scripts/core/data/guidelines/consort.yaml` | New CONSORT checklist data. |
| `scripts/core/data/guidelines/prisma.yaml` | New PRISMA 2020 checklist data. |
| `tests/core/test_power_sample_size.py` | Add family tests. |
| `tests/core/test_stat_run.py` | Add op tests. |
| `tests/core/test_guideline_check.py` | Add CONSORT/PRISMA tests. |

---

## Task 1: `power_sample_size.py` — dispatch refactor + `paired_t`

**Files:**
- Modify: `scripts/core/power_sample_size.py`
- Modify: `tests/core/test_power_sample_size.py`

The current `compute()` hard-checks `test == "two_sample_t"`. Refactor it to dispatch on the
`test` field and compute `n_total` per family. Add the `paired_t` family (one-sample /
paired t-test power via `statsmodels.stats.power.TTestPower`); for paired, `n_total ==
n_per_group` (a single group of pairs).

- [ ] **Step 1: Add the failing test**

```python
# append to tests/core/test_power_sample_size.py
def test_paired_t_family():
    payload = {"test": "paired_t", "effect_size": 0.5, "alpha": 0.05, "power": 0.80}
    out = run_engine(payload)
    assert out["status"] == "ok"
    # canonical one-sample/paired n for d=0.5, power .80 ~ 34
    assert 33 <= out["data"]["n_per_group"] <= 35
    assert out["data"]["n_total"] == out["data"]["n_per_group"]  # single group of pairs
    assert out["data"]["finding"]["status"] == "operational_fact"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd ~/code/scriptorium && .venv/bin/pytest tests/core/test_power_sample_size.py -v -k paired`
Expected: FAIL — `unsupported test: 'paired_t'`.

- [ ] **Step 3: Refactor `compute()` to dispatch + add `paired_t`**

Replace the existing `compute` function and the `two_sample_t` helper region with:

```python
def two_sample_t(effect_size, alpha, power, ratio):
    from statsmodels.stats.power import TTestIndPower
    n1 = TTestIndPower().solve_power(
        effect_size=effect_size, alpha=alpha, power=power,
        ratio=ratio, alternative="two-sided",
    )
    return int(math.ceil(n1))


def paired_t(effect_size, alpha, power):
    from statsmodels.stats.power import TTestPower
    n = TTestPower().solve_power(
        effect_size=effect_size, alpha=alpha, power=power, alternative="two-sided",
    )
    return int(math.ceil(n))


def compute(req):
    test = req.get("test")
    alpha = float(req.get("alpha", 0.05))
    power = float(req.get("power", 0.80))

    if test == "two_sample_t":
        effect_size = float(req["effect_size"])
        ratio = float(req.get("ratio", 1.0))
        n_per_group = two_sample_t(effect_size, alpha, power, ratio)
        n_total = n_per_group + int(math.ceil(n_per_group * ratio))
        claim = f"n={n_per_group}/group for d={effect_size}, alpha={alpha}, power={power}"
    elif test == "paired_t":
        effect_size = float(req["effect_size"])
        n_per_group = paired_t(effect_size, alpha, power)
        n_total = n_per_group  # single group of pairs
        claim = f"n={n_per_group} pairs for d={effect_size}, alpha={alpha}, power={power}"
    else:
        raise ValueError(f"unsupported test: {test!r}")

    rid = provenance.run_id(seed=json.dumps(req, sort_keys=True))
    finding = epistemic.make_finding(
        claim=claim, status="operational_fact", confidence=1.0,
        source=provenance.engine_trace("power_sample_size", run_id=rid, anchor="result"),
        source_independence=1,
    )
    return {"n_per_group": n_per_group, "n_total": n_total, "finding": finding}
```

(Keep the existing imports at the top of the file; `TTestIndPower` is now imported inside
`two_sample_t`. If a module-level `from statsmodels.stats.power import TTestIndPower` exists,
remove it to avoid an unused-import lint, since both helpers now import locally.)

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ~/code/scriptorium && .venv/bin/pytest tests/core/test_power_sample_size.py -v`
Expected: all pass (existing two_sample_t tests + new paired_t).

- [ ] **Step 5: Commit**

```bash
git add scripts/core/power_sample_size.py tests/core/test_power_sample_size.py
git commit -m "feat(core): power_sample_size — dispatch refactor + paired_t family"
```

---

## Task 2: `power_sample_size.py` — `two_proportions`

**Files:**
- Modify: `scripts/core/power_sample_size.py`
- Modify: `tests/core/test_power_sample_size.py`

Two-proportion power via `statsmodels.stats.power.NormalIndPower` with effect size
`proportion_effectsize(p1, p2)` (Cohen's h). `n_total = 2 * n_per_group` (1:1).

- [ ] **Step 1: Add the failing test**

```python
# append to tests/core/test_power_sample_size.py
def test_two_proportions_family():
    payload = {"test": "two_proportions", "p1": 0.5, "p2": 0.3, "alpha": 0.05, "power": 0.80}
    out = run_engine(payload)
    assert out["status"] == "ok"
    # canonical n/group for p1=.5,p2=.3 ~ 93
    assert 85 <= out["data"]["n_per_group"] <= 100
    assert out["data"]["n_total"] == 2 * out["data"]["n_per_group"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd ~/code/scriptorium && .venv/bin/pytest tests/core/test_power_sample_size.py -v -k proportions`
Expected: FAIL — `unsupported test: 'two_proportions'`.

- [ ] **Step 3: Add the helper + dispatch branch**

Add this helper (next to the others):

```python
def two_proportions(p1, p2, alpha, power):
    from statsmodels.stats.power import NormalIndPower
    from statsmodels.stats.proportion import proportion_effectsize
    h = proportion_effectsize(p1, p2)
    n1 = NormalIndPower().solve_power(
        effect_size=abs(h), alpha=alpha, power=power, ratio=1.0, alternative="two-sided",
    )
    return int(math.ceil(n1))
```

Add this branch in `compute()` before the final `else`:

```python
    elif test == "two_proportions":
        p1 = float(req["p1"]); p2 = float(req["p2"])
        n_per_group = two_proportions(p1, p2, alpha, power)
        n_total = 2 * n_per_group
        claim = f"n={n_per_group}/group for p1={p1}, p2={p2}, alpha={alpha}, power={power}"
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ~/code/scriptorium && .venv/bin/pytest tests/core/test_power_sample_size.py -v`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add scripts/core/power_sample_size.py tests/core/test_power_sample_size.py
git commit -m "feat(core): power_sample_size — two_proportions family (Cohen's h)"
```

---

## Task 3: `power_sample_size.py` — `one_way_anova`

**Files:**
- Modify: `scripts/core/power_sample_size.py`
- Modify: `tests/core/test_power_sample_size.py`

One-way ANOVA power via `statsmodels.stats.power.FTestAnovaPower`, effect size `f`,
`k_groups`. `n_per_group` is the per-group N; `n_total = k_groups * n_per_group`.

- [ ] **Step 1: Add the failing test**

```python
# append to tests/core/test_power_sample_size.py
def test_one_way_anova_family():
    payload = {"test": "one_way_anova", "effect_size": 0.25, "k_groups": 4,
               "alpha": 0.05, "power": 0.80}
    out = run_engine(payload)
    assert out["status"] == "ok"
    # canonical per-group n for f=.25 (medium), k=4 ~ 45
    assert 40 <= out["data"]["n_per_group"] <= 50
    assert out["data"]["n_total"] == 4 * out["data"]["n_per_group"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd ~/code/scriptorium && .venv/bin/pytest tests/core/test_power_sample_size.py -v -k anova`
Expected: FAIL — `unsupported test: 'one_way_anova'`.

- [ ] **Step 3: Add the helper + dispatch branch**

Add helper:

```python
def one_way_anova(effect_size, k_groups, alpha, power):
    from statsmodels.stats.power import FTestAnovaPower
    n_total = FTestAnovaPower().solve_power(
        effect_size=effect_size, alpha=alpha, power=power, k_groups=k_groups,
    )
    return int(math.ceil(n_total / k_groups))  # per-group
```

Add branch in `compute()` before the final `else`:

```python
    elif test == "one_way_anova":
        effect_size = float(req["effect_size"]); k_groups = int(req["k_groups"])
        n_per_group = one_way_anova(effect_size, k_groups, alpha, power)
        n_total = k_groups * n_per_group
        claim = (f"n={n_per_group}/group ({k_groups} groups) for f={effect_size}, "
                 f"alpha={alpha}, power={power}")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ~/code/scriptorium && .venv/bin/pytest tests/core/test_power_sample_size.py -v`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add scripts/core/power_sample_size.py tests/core/test_power_sample_size.py
git commit -m "feat(core): power_sample_size — one_way_anova family (F-test)"
```

---

## Task 4: `stat_run.py` — op `mann_whitney`

**Files:**
- Modify: `scripts/core/stat_run.py`
- Modify: `tests/core/test_stat_run.py`

Nonparametric two-group comparison via `scipy.stats.mannwhitneyu`. Output `{u, p, finding}`.
Finding `operational_fact` conf 1.0 (deterministic).

- [ ] **Step 1: Add the failing test**

```python
# append to tests/core/test_stat_run.py
def test_mann_whitney_matches_scipy():
    a = [1, 2, 3, 4, 5]; b = [6, 7, 8, 9, 10]
    out = run_engine({"op": "mann_whitney", "groups": [a, b]})
    assert out["status"] == "ok"
    ref = _sps.mannwhitneyu(a, b, alternative="two-sided")
    assert abs(out["data"]["u"] - float(ref.statistic)) < 1e-9
    assert abs(out["data"]["p"] - float(ref.pvalue)) < 1e-9
    assert out["data"]["finding"]["confidence"] == 1.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd ~/code/scriptorium && .venv/bin/pytest tests/core/test_stat_run.py -v -k mann`
Expected: FAIL — `unknown op: 'mann_whitney'`.

- [ ] **Step 3: Add the implementation**

Add above `OPS` and register `"mann_whitney": mann_whitney`:

```python
def mann_whitney(req):
    a = list(map(float, req["groups"][0]))
    b = list(map(float, req["groups"][1]))
    res = stats.mannwhitneyu(a, b, alternative="two-sided")
    finding = epistemic.make_finding(
        claim="Mann-Whitney U computed", status="operational_fact", confidence=1.0,
        source=provenance.engine_trace("stat_run", run_id=_rid(req), anchor="mann_whitney"),
    )
    return {"u": float(res.statistic), "p": float(res.pvalue), "finding": finding}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ~/code/scriptorium && .venv/bin/pytest tests/core/test_stat_run.py -v`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add scripts/core/stat_run.py tests/core/test_stat_run.py
git commit -m "feat(core): stat_run mann_whitney — nonparametric two-group comparison"
```

---

## Task 5: `stat_run.py` — ops `chi_square` + `fisher`

**Files:**
- Modify: `scripts/core/stat_run.py`
- Modify: `tests/core/test_stat_run.py`

Categorical association: `chi_square` via `scipy.stats.chi2_contingency` (2D table);
`fisher` via `scipy.stats.fisher_exact` (2×2 table). Both deterministic.

- [ ] **Step 1: Add the failing tests**

```python
# append to tests/core/test_stat_run.py
def test_chi_square_matches_scipy():
    table = [[10, 20], [30, 40]]
    out = run_engine({"op": "chi_square", "table": table})
    assert out["status"] == "ok"
    chi2, p, dof, _ = _sps.chi2_contingency(table)
    assert abs(out["data"]["chi2"] - float(chi2)) < 1e-9
    assert out["data"]["dof"] == int(dof)


def test_fisher_matches_scipy():
    table = [[8, 2], [1, 9]]
    out = run_engine({"op": "fisher", "table": table})
    odds, p = _sps.fisher_exact(table)
    assert abs(out["data"]["p"] - float(p)) < 1e-9
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/code/scriptorium && .venv/bin/pytest tests/core/test_stat_run.py -v -k "chi or fisher"`
Expected: FAIL — unknown ops.

- [ ] **Step 3: Add the implementations**

Add above `OPS` and register both (`"chi_square": chi_square, "fisher": fisher`):

```python
def chi_square(req):
    table = req["table"]
    chi2, p, dof, _expected = stats.chi2_contingency(table)
    finding = epistemic.make_finding(
        claim="chi-square test of independence computed",
        status="operational_fact", confidence=1.0,
        source=provenance.engine_trace("stat_run", run_id=_rid(req), anchor="chi_square"),
    )
    return {"chi2": float(chi2), "p": float(p), "dof": int(dof), "finding": finding}


def fisher(req):
    table = req["table"]  # 2x2
    odds, p = stats.fisher_exact(table)
    finding = epistemic.make_finding(
        claim="Fisher exact test computed", status="operational_fact", confidence=1.0,
        source=provenance.engine_trace("stat_run", run_id=_rid(req), anchor="fisher"),
    )
    return {"odds_ratio": float(odds), "p": float(p), "finding": finding}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ~/code/scriptorium && .venv/bin/pytest tests/core/test_stat_run.py -v`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add scripts/core/stat_run.py tests/core/test_stat_run.py
git commit -m "feat(core): stat_run chi_square + fisher — categorical association tests"
```

---

## Task 6: `guideline_check.py` — CONSORT + PRISMA data

**Files:**
- Create: `scripts/core/data/guidelines/consort.yaml`
- Create: `scripts/core/data/guidelines/prisma.yaml`
- Modify: `tests/core/test_guideline_check.py`

The loader is already generic (reads `data/guidelines/<name>.yaml`); only data files are
needed. Each is a representative subset with `id`, `item`, `keywords` (same schema as STROBE).

- [ ] **Step 1: Create `consort.yaml`**

```yaml
# scripts/core/data/guidelines/consort.yaml
guideline: consort
version: "2010"
items:
  - id: "1a"
    item: "Identification as a randomised trial in the title"
    keywords: ["randomised", "randomized", "randomised controlled trial", "rct"]
  - id: "6a"
    item: "Completely defined pre-specified primary and secondary outcome measures"
    keywords: ["primary outcome", "primary endpoint", "secondary outcome"]
  - id: "7a"
    item: "How sample size was determined"
    keywords: ["sample size", "power calculation", "powered to detect"]
  - id: "8a"
    item: "Method used to generate the random allocation sequence"
    keywords: ["allocation sequence", "randomisation", "random allocation", "computer-generated"]
  - id: "11a"
    item: "Blinding — who was blinded after assignment"
    keywords: ["blinded", "blinding", "double-blind", "single-blind", "masking"]
  - id: "17a"
    item: "Outcomes and estimation — effect size and its precision (e.g. 95% CI)"
    keywords: ["confidence interval", "95% ci", "effect size", "hazard ratio", "risk ratio"]
```

- [ ] **Step 2: Create `prisma.yaml`**

```yaml
# scripts/core/data/guidelines/prisma.yaml
guideline: prisma
version: "2020"
items:
  - id: "1"
    item: "Identification as a systematic review in the title"
    keywords: ["systematic review", "meta-analysis"]
  - id: "5"
    item: "Eligibility criteria for the review"
    keywords: ["eligibility criteria", "inclusion criteria", "exclusion criteria"]
  - id: "6"
    item: "Information sources (databases, registers) and last search date"
    keywords: ["pubmed", "medline", "embase", "cochrane", "databases searched", "search date"]
  - id: "7"
    item: "Full search strategy presented"
    keywords: ["search strategy", "search terms", "boolean", "search string"]
  - id: "16a"
    item: "Risk of bias assessment of included studies"
    keywords: ["risk of bias", "rob 2", "robins", "quality assessment", "newcastle-ottawa"]
  - id: "21"
    item: "Registration and protocol (e.g. PROSPERO)"
    keywords: ["prospero", "registration", "protocol", "registered"]
```

- [ ] **Step 3: Add the failing tests**

```python
# append to tests/core/test_guideline_check.py
def test_consort_detects_missing_blinding():
    text = ("This randomised controlled trial defined a primary outcome. "
            "Sample size was determined to detect the effect. "
            "The allocation sequence was computer-generated. "
            "Results report the hazard ratio with 95% CI.")  # no blinding mention
    out = run_engine({"guideline": "consort", "manuscript_text": text})
    assert out["status"] == "ok"
    missing_ids = [m["id"] for m in out["data"]["missing"]]
    assert "11a" in missing_ids       # blinding missing
    assert "1a" in out["data"]["present"]


def test_prisma_detects_missing_registration():
    text = ("This systematic review defined eligibility criteria. "
            "We searched PubMed and Embase. The search strategy used boolean terms. "
            "Risk of bias was assessed with ROB 2.")  # no PROSPERO/registration
    out = run_engine({"guideline": "prisma", "manuscript_text": text})
    missing_ids = [m["id"] for m in out["data"]["missing"]]
    assert "21" in missing_ids        # registration missing
    assert "1" in out["data"]["present"]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ~/code/scriptorium && .venv/bin/pytest tests/core/test_guideline_check.py -v`
Expected: all pass (STROBE + CONSORT + PRISMA).

- [ ] **Step 5: Commit**

```bash
git add scripts/core/data/guidelines/consort.yaml scripts/core/data/guidelines/prisma.yaml tests/core/test_guideline_check.py
git commit -m "feat(core): guideline_check — CONSORT + PRISMA checklists as data"
```

---

## Task 7: Changelog + version bump

**Files:**
- Modify: `CHANGELOG.md`
- Modify: `pyproject.toml`, `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`

- [ ] **Step 1: Run the whole suite**

Run: `cd ~/code/scriptorium && scripts/run_tests.sh`
Expected: all tests pass (v0.2.0 set + new), ends `ALL GREEN`.

- [ ] **Step 2: Bump version to 0.3.0.dev0 in all three manifests**

In `pyproject.toml`: `version = "0.3.0.dev0"`.
In `.claude-plugin/plugin.json`: `"version": "0.3.0.dev0"`.
In `.claude-plugin/marketplace.json` (the plugin entry): `"version": "0.3.0.dev0"`.

- [ ] **Step 3: Prepend an Unreleased entry to `CHANGELOG.md`**

Above `## [0.2.0]`:
```markdown
## [Unreleased] — v0.3.0 (in progress)

### Added
- Power/sample-size families: `paired_t`, `two_proportions` (Cohen's h), `one_way_anova`.
- Statistical tests: `mann_whitney` (nonparametric), `chi_square` + `fisher` (categorical).
- Reporting guidelines as data: CONSORT (2010), PRISMA (2020) — alongside STROBE.

### Deferred
- GRIMMER (SD granularity consistency) — needs a careful, separately-tested algorithm.
```

- [ ] **Step 4: Commit**

```bash
git add CHANGELOG.md pyproject.toml .claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "build: v0.3.0.dev0 — changelog + version bump for engine expansion"
```

---

## Self-Review

**Spec coverage (v0.3.0 increment 1):** more power design families + more stat tests grow the
Rigor pillar (spec §1 moat #3) and the statistician's single-source-of-truth coverage; two
more reporting guidelines grow the guideline screen (spec §6 ★★). GRIMMER explicitly deferred
with a stated reason (asymmetric medical risk) — not a gap, a scoped decision. Real rag/cag,
contradiction-detection, semantic citation-support remain later v0.3.x increments.

**Placeholder scan:** no TBD/TODO; every step shows complete code/data; every run step shows
command + expected result.

**Type consistency:** every new family/op returns the envelope via `json_io` and a finding via
`epistemic.make_finding` with the established key set. `compute()` dispatch in
`power_sample_size.py` keeps `{n_per_group, n_total, finding}` across all families (Tasks 1–3).
`stat_run.py` `OPS` dict grows additively (Tasks 4–5) — each task adds keys, never renames;
all new ops reuse `_rid(req)` and `stats` from Plan-2 Task 1. New guidelines reuse the existing
`guideline_check.check()` loader unchanged (Task 6 adds data only). `_sps` alias in the stat
tests is the `scipy.stats` import added in Plan-2 Task 2.
