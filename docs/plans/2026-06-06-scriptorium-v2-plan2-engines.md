# Scriptorium v2 — Plan 2: Remaining L0 Engines

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the remaining L0 deterministic engines — statistical sanity (assumptions, recompute, GRIM), reporting-guideline gap-check, citation claim-support, and group-sequential boundaries (R-dispatch) — all following the Plan-1 engine pattern.

**Architecture:** Layered (Approach A), L0 only. Every engine is a Python CLI reading JSON on stdin, emitting an `ok`/`error` envelope (`scripts/lib/json_io.py`), with findings shaped by `scripts/lib/epistemic.py` and traces by `scripts/lib/provenance.py`. The group-sequential engine dispatches to R via `subprocess` (isolation over `rpy2`).

**Tech Stack:** Python 3 (scipy, statsmodels, PyYAML), R 4.3.3 + gsDesign (via `Rscript`), pytest.

**Prerequisite:** Plan 1 complete (`scripts/lib/`, `scripts/core/epistemic_grade.py`, `scripts/core/power_sample_size.py`, venv, `run_tests.sh` all present and green).

**Known-fix carried from Plan 1:** `pyproject.toml` already contains
`[tool.setuptools.packages.find] include = ["scripts*"]` — do not remove it.

**Testing philosophy (read before writing tests):** where a numeric result is
version-sensitive (scipy/statsmodels/gsDesign float output), assert **behavior and ranges**
(assumption violated? boundary count == k? final z ≈ 1.98?) or **recompute the reference
inline from the same library**, rather than pinning a brittle magic number. Where math is
exact and version-independent (GRIM integer arithmetic, guideline keyword gap), pin the
exact value. This matches the spec's honesty ethos: don't fake precision the tooling can't
guarantee.

---

## File Structure (Plan 2)

| File | Responsibility |
|---|---|
| `scripts/core/stat_run.py` | Op-dispatched stats engine: `check_assumptions`, `recompute_ttest`, `grim`. |
| `scripts/core/guideline_check.py` | Gap-check a manuscript against a reporting checklist (YAML data). |
| `scripts/core/data/guidelines/strobe.yaml` | STROBE checklist as data (first guideline). |
| `scripts/core/citation_parse.py` | Parse in-text citations + reference list; flag unsupported/orphan. |
| `scripts/core/rbridge/gsdesign.R` | R script: group-sequential boundaries via gsDesign. |
| `scripts/core/rbridge/__init__.py` | Package marker. |
| `scripts/core/interim_boundaries.py` | Python CLI wrapper dispatching to `gsdesign.R`. |
| `tests/core/test_stat_run.py` | Tests for the three stat ops. |
| `tests/core/test_guideline_check.py` | Tests for guideline gap-check. |
| `tests/core/test_citation_parse.py` | Tests for citation engine. |
| `tests/core/test_interim_boundaries.py` | Tests for R-dispatch boundaries. |
| `tests/golden/**` | Fixture pairs per engine. |

---

## Task 0: Verify R + gsDesign

**Files:** none (environment check).

- [ ] **Step 1: Confirm gsDesign installed**

Run: `Rscript -e 'cat(requireNamespace("gsDesign", quietly=TRUE))'`
Expected: prints `TRUE`. If it prints `FALSE`, install it:
```bash
Rscript -e 'install.packages("gsDesign", repos="https://cloud.r-project.org")'
```
then re-run the check until it prints `TRUE`.

- [ ] **Step 2: Create rbridge package dir**

```bash
cd ~/code/scriptorium && mkdir -p scripts/core/rbridge scripts/core/data/guidelines && touch scripts/core/rbridge/__init__.py
```

No commit (environment/scaffold only; committed alongside Task 6).

---

## Task 1: `stat_run.py` — op `check_assumptions`

**Files:**
- Create: `scripts/core/stat_run.py`
- Test: `tests/core/test_stat_run.py`

Contract — input:
```json
{"op": "check_assumptions", "groups": [[<numbers>], [<numbers>]], "claimed_test": "two_sample_t"}
```
Output `data`:
```json
{"assumptions": {"normality": {...}, "equal_variance": {...}},
 "recommended_alternative": "mann_whitney" | null,
 "finding": { ...graded... }}
```
Rules: Shapiro–Wilk per group (`scipy.stats.shapiro`); Levene across groups
(`scipy.stats.levene`). An assumption is `violated` if p < 0.05. If `claimed_test` is
`two_sample_t` and normality is violated → `recommended_alternative = "mann_whitney"`;
else `null`. Finding status `operational_fact`, confidence 0.9 when any violation, else
`corroborated_inference` confidence 0.8.

- [ ] **Step 1: Write the failing test**

```python
# tests/core/test_stat_run.py
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENGINE = ROOT / "scripts" / "core" / "stat_run.py"


def run_engine(payload):
    proc = subprocess.run(
        [sys.executable, str(ENGINE)],
        input=json.dumps(payload), capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def test_check_assumptions_flags_nonnormal():
    # Strongly non-normal group (one extreme outlier) vs a spread group.
    payload = {
        "op": "check_assumptions",
        "groups": [[1, 1, 1, 1, 1, 1, 1, 1, 2, 100], [2, 3, 4, 5, 6, 7, 8, 9, 10, 11]],
        "claimed_test": "two_sample_t",
    }
    out = run_engine(payload)
    assert out["status"] == "ok"
    assert out["data"]["assumptions"]["normality"]["violated"] is True
    assert out["data"]["recommended_alternative"] == "mann_whitney"
    assert out["data"]["finding"]["status"] == "operational_fact"
    assert out["data"]["finding"]["source"].startswith("scripts/core/stat_run.py#run=")


def test_unknown_op_is_error():
    proc = subprocess.run(
        [sys.executable, str(ENGINE)],
        input=json.dumps({"op": "divine"}), capture_output=True, text=True,
    )
    assert json.loads(proc.stdout)["status"] == "error"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd ~/code/scriptorium && .venv/bin/pytest tests/core/test_stat_run.py -v`
Expected: FAIL — engine file does not exist.

- [ ] **Step 3: Write minimal implementation**

```python
# scripts/core/stat_run.py
"""L0 engine: statistical sanity checks. Op-dispatched via the JSON "op" field.

Ops:
  check_assumptions — Shapiro normality (per group) + Levene equal-variance; recommend
                      a nonparametric alternative when a parametric test's assumptions fail.
  recompute_ttest   — recompute t/df/p/CI for two groups; flag mismatch vs a claimed p.
  grim              — Granularity-Related Inconsistency of Means (integer reachability).

Input/Output: stdin/stdout JSON envelopes (see scripts/lib/json_io.py).
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.lib import json_io, provenance, epistemic  # noqa: E402

from scipy import stats  # noqa: E402

ALPHA = 0.05


def _rid(req):
    return provenance.run_id(seed=json.dumps(req, sort_keys=True))


def check_assumptions(req):
    groups = [list(map(float, g)) for g in req["groups"]]
    claimed_test = req.get("claimed_test")

    normal_violated = False
    per_group = []
    for i, g in enumerate(groups):
        w, p = stats.shapiro(g)
        viol = p < ALPHA
        normal_violated = normal_violated or viol
        per_group.append({"group": i, "shapiro_p": round(p, 4), "violated": bool(viol)})

    lev_w, lev_p = stats.levene(*groups)
    var_violated = lev_p < ALPHA

    recommended = None
    if claimed_test == "two_sample_t" and normal_violated:
        recommended = "mann_whitney"

    any_violation = normal_violated or var_violated
    status = "operational_fact" if any_violation else "corroborated_inference"
    confidence = 0.9 if any_violation else 0.8
    claim = (
        "parametric assumptions violated; nonparametric alternative recommended"
        if any_violation else "parametric assumptions hold"
    )
    finding = epistemic.make_finding(
        claim=claim, status=status, confidence=confidence,
        source=provenance.engine_trace("stat_run", run_id=_rid(req), anchor="assumptions"),
    )
    return {
        "assumptions": {
            "normality": {"violated": bool(normal_violated), "per_group": per_group},
            "equal_variance": {"violated": bool(var_violated), "levene_p": round(lev_p, 4)},
        },
        "recommended_alternative": recommended,
        "finding": finding,
    }


OPS = {"check_assumptions": check_assumptions}


def main():
    try:
        req = json_io.read_input()
        op = req.get("op")
        if op not in OPS:
            json_io.emit(json_io.error(f"unknown op: {op!r}"))
            return
        json_io.emit(json_io.ok(OPS[op](req)))
    except Exception as exc:
        json_io.emit(json_io.error(str(exc)))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd ~/code/scriptorium && .venv/bin/pytest tests/core/test_stat_run.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/core/stat_run.py tests/core/test_stat_run.py
git commit -m "feat(core): stat_run check_assumptions — Shapiro/Levene + nonparametric recommendation"
```

---

## Task 2: `stat_run.py` — op `recompute_ttest`

**Files:**
- Modify: `scripts/core/stat_run.py` (add op)
- Modify: `tests/core/test_stat_run.py` (add tests)

Contract — input:
```json
{"op": "recompute_ttest", "groups": [[...], [...]], "equal_var": true, "claimed_p": 0.04}
```
Output `data`:
```json
{"t": <float>, "df": <float>, "p": <float>, "ci95": [<lo>, <hi>],
 "claimed_p": 0.04, "p_matches_claim": false, "finding": {...}}
```
Rules: use `scipy.stats.ttest_ind(a, b, equal_var=...)`. `p_matches_claim` true if
`abs(p - claimed_p) <= 0.01` (absolute, lenient — catches gross reporting errors, not
rounding). If `claimed_p` absent → `p_matches_claim = null`. CI95 of the mean difference
via the t-distribution. Finding: `operational_fact` conf 1.0 (deterministic recompute);
claim notes match/mismatch.

- [ ] **Step 1: Add the failing tests**

```python
# append to tests/core/test_stat_run.py
import scipy.stats as _sps  # for inline reference


def test_recompute_ttest_matches_scipy_and_flags_mismatch():
    a = [5.1, 4.9, 5.0, 5.2, 4.8]
    b = [6.0, 5.9, 6.1, 5.8, 6.2]
    payload = {"op": "recompute_ttest", "groups": [a, b], "equal_var": True, "claimed_p": 0.9}
    out = run_engine(payload)
    assert out["status"] == "ok"
    ref = _sps.ttest_ind(a, b, equal_var=True)
    assert abs(out["data"]["p"] - float(ref.pvalue)) < 1e-9
    assert out["data"]["p_matches_claim"] is False  # true p ~1e-4, claim 0.9
    assert out["data"]["finding"]["confidence"] == 1.0


def test_recompute_ttest_without_claim_returns_null_match():
    out = run_engine({"op": "recompute_ttest", "groups": [[1, 2, 3], [4, 5, 6]], "equal_var": True})
    assert out["data"]["p_matches_claim"] is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/code/scriptorium && .venv/bin/pytest tests/core/test_stat_run.py -v -k recompute`
Expected: FAIL — op `recompute_ttest` unknown (error envelope) → assertion fails.

- [ ] **Step 3: Add the implementation**

Add this function above the `OPS` dict and register it:

```python
def recompute_ttest(req):
    import math
    a = list(map(float, req["groups"][0]))
    b = list(map(float, req["groups"][1]))
    equal_var = bool(req.get("equal_var", True))
    res = stats.ttest_ind(a, b, equal_var=equal_var)
    t = float(res.statistic)
    p = float(res.pvalue)

    mean_diff = (sum(a) / len(a)) - (sum(b) / len(b))
    if equal_var:
        df = len(a) + len(b) - 2
    else:  # Welch–Satterthwaite
        va, vb = _var(a), _var(b)
        na, nb = len(a), len(b)
        df = (va / na + vb / nb) ** 2 / (
            (va / na) ** 2 / (na - 1) + (vb / nb) ** 2 / (nb - 1)
        )
    se = mean_diff / t if t != 0 else float("nan")
    tcrit = stats.t.ppf(0.975, df)
    ci = [mean_diff - tcrit * abs(se), mean_diff + tcrit * abs(se)]

    claimed_p = req.get("claimed_p")
    p_matches = None if claimed_p is None else (abs(p - float(claimed_p)) <= 0.01)
    claim = "reported p inconsistent with recomputed p" if p_matches is False else "p recomputed"
    finding = epistemic.make_finding(
        claim=claim, status="operational_fact", confidence=1.0,
        source=provenance.engine_trace("stat_run", run_id=_rid(req), anchor="recompute_ttest"),
    )
    return {
        "t": round(t, 6), "df": round(float(df), 4), "p": p,
        "ci95": [round(ci[0], 6), round(ci[1], 6)],
        "claimed_p": claimed_p, "p_matches_claim": p_matches, "finding": finding,
    }


def _var(x):
    m = sum(x) / len(x)
    return sum((xi - m) ** 2 for xi in x) / (len(x) - 1)
```
And update: `OPS = {"check_assumptions": check_assumptions, "recompute_ttest": recompute_ttest}`

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ~/code/scriptorium && .venv/bin/pytest tests/core/test_stat_run.py -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/core/stat_run.py tests/core/test_stat_run.py
git commit -m "feat(core): stat_run recompute_ttest — t/df/p/CI recompute + claimed-p mismatch flag"
```

---

## Task 3: `stat_run.py` — op `grim`

**Files:**
- Modify: `scripts/core/stat_run.py` (add op)
- Modify: `tests/core/test_stat_run.py` (add tests)

Contract — input:
```json
{"op": "grim", "mean": 3.45, "n": 10, "decimals": 2}
```
Output `data`:
```json
{"consistent": false, "mean": 3.45, "n": 10, "nearest_consistent": [3.4, 3.5], "finding": {...}}
```
GRIM: a reported mean to `decimals` places, from `n` integer-valued items, is only
reachable if `round(mean * n)` divided back equals the mean at that precision. Exact integer
math — version-independent. Finding `operational_fact` conf 1.0; status note flags
inconsistency.

- [ ] **Step 1: Add the failing tests**

```python
# append to tests/core/test_stat_run.py
def test_grim_detects_impossible_mean():
    out = run_engine({"op": "grim", "mean": 3.45, "n": 10, "decimals": 2})
    assert out["status"] == "ok"
    assert out["data"]["consistent"] is False


def test_grim_accepts_possible_mean():
    # 34/10 = 3.4 exactly reachable
    out = run_engine({"op": "grim", "mean": 3.4, "n": 10, "decimals": 1})
    assert out["data"]["consistent"] is True
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/code/scriptorium && .venv/bin/pytest tests/core/test_stat_run.py -v -k grim`
Expected: FAIL — op `grim` unknown.

- [ ] **Step 3: Add the implementation**

Add above `OPS` and register:

```python
def grim(req):
    mean = float(req["mean"])
    n = int(req["n"])
    decimals = int(req.get("decimals", 2))
    scale = 10 ** decimals
    # The integer sum that would round to the reported mean:
    candidate_sum = round(mean * n)
    reconstructed = round(candidate_sum / n, decimals)
    consistent = abs(reconstructed - round(mean, decimals)) < (0.5 / scale) / n
    lo = round((candidate_sum - 1) / n, decimals)
    hi = round((candidate_sum + 1) / n, decimals)
    finding = epistemic.make_finding(
        claim="reported mean is granularity-inconsistent (GRIM)" if not consistent
              else "reported mean is granularity-consistent",
        status="operational_fact", confidence=1.0,
        source=provenance.engine_trace("stat_run", run_id=_rid(req), anchor="grim"),
    )
    return {"consistent": bool(consistent), "mean": mean, "n": n,
            "nearest_consistent": [lo, hi], "finding": finding}
```
And update `OPS` to include `"grim": grim`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ~/code/scriptorium && .venv/bin/pytest tests/core/test_stat_run.py -v`
Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/core/stat_run.py tests/core/test_stat_run.py
git commit -m "feat(core): stat_run grim — granularity-related inconsistency of means (exact integer check)"
```

---

## Task 4: `guideline_check.py` + STROBE data

**Files:**
- Create: `scripts/core/data/guidelines/strobe.yaml`
- Create: `scripts/core/guideline_check.py`
- Test: `tests/core/test_guideline_check.py`
- Fixtures: `tests/golden/guideline_check/missing_limitations.in.json`

Contract — input:
```json
{"guideline": "strobe", "manuscript_text": "<full text>"}
```
Output `data`:
```json
{"guideline": "strobe", "present": [<ids>], "missing": [{"id": "...", "item": "..."}], "finding": {...}}
```
Detection (v2, deterministic keyword presence): each checklist item carries `keywords`; an
item is `present` if ANY keyword (case-insensitive) appears in the text, else `missing`.
Finding: status `working_hypothesis` conf 0.6 (keyword heuristic is a screen, not proof);
claim summarises the gap count.

- [ ] **Step 1: Create the STROBE checklist data (subset)**

```yaml
# scripts/core/data/guidelines/strobe.yaml
guideline: strobe
version: "cohort-2007"
items:
  - id: "1a"
    item: "Study design indicated in title or abstract"
    keywords: ["cohort", "case-control", "cross-sectional", "study design"]
  - id: "6"
    item: "Eligibility criteria, sources and selection of participants"
    keywords: ["eligibility", "inclusion criteria", "exclusion criteria", "participants were"]
  - id: "12a"
    item: "Statistical methods, including confounding control"
    keywords: ["statistical analysis", "adjusted for", "confound", "regression"]
  - id: "19"
    item: "Limitations of the study discussed"
    keywords: ["limitation", "limitations"]
  - id: "22"
    item: "Source of funding stated"
    keywords: ["funding", "funded by", "grant", "no funding"]
```

- [ ] **Step 2: Write the failing test**

```python
# tests/core/test_guideline_check.py
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENGINE = ROOT / "scripts" / "core" / "guideline_check.py"


def run_engine(payload):
    proc = subprocess.run(
        [sys.executable, str(ENGINE)],
        input=json.dumps(payload), capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def test_detects_missing_limitations():
    text = (
        "This cohort study enrolled participants who met the inclusion criteria. "
        "Statistical analysis adjusted for confounders via regression. "
        "The work was funded by a grant."
    )  # deliberately no 'limitation'
    out = run_engine({"guideline": "strobe", "manuscript_text": text})
    assert out["status"] == "ok"
    missing_ids = [m["id"] for m in out["data"]["missing"]]
    assert "19" in missing_ids        # limitations missing
    assert "1a" in out["data"]["present"]   # 'cohort study' present
    assert out["data"]["finding"]["status"] == "working_hypothesis"


def test_unknown_guideline_is_error():
    out = run_engine({"guideline": "nonexistent", "manuscript_text": "x"})
    assert out["status"] == "error"
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd ~/code/scriptorium && .venv/bin/pytest tests/core/test_guideline_check.py -v`
Expected: FAIL — engine missing.

- [ ] **Step 4: Write minimal implementation**

```python
# scripts/core/guideline_check.py
"""L0 engine: gap-check a manuscript against a reporting checklist (YAML data).

v2 detection is a deterministic keyword screen: an item is present if any of its keywords
appears (case-insensitive) in the manuscript text. This is a SCREEN (working_hypothesis),
not proof of adequate reporting — absence of a keyword is a reliable miss signal; presence
is a weak positive. Input: {"guideline": <name>, "manuscript_text": <str>}.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.lib import json_io, provenance, epistemic  # noqa: E402

import yaml  # noqa: E402

DATA = Path(__file__).resolve().parent / "data" / "guidelines"


def load_guideline(name):
    path = DATA / f"{name}.yaml"
    if not path.exists():
        raise ValueError(f"unknown guideline: {name!r}")
    return yaml.safe_load(path.read_text())


def check(req):
    name = req["guideline"]
    text = req["manuscript_text"].lower()
    spec = load_guideline(name)

    present, missing = [], []
    for it in spec["items"]:
        hit = any(kw.lower() in text for kw in it["keywords"])
        if hit:
            present.append(it["id"])
        else:
            missing.append({"id": it["id"], "item": it["item"]})

    rid = provenance.run_id(seed=json.dumps({"g": name, "n": len(text)}, sort_keys=True))
    finding = epistemic.make_finding(
        claim=f"{len(missing)} of {len(spec['items'])} {name.upper()} items not detected",
        status="working_hypothesis", confidence=0.6,
        source=provenance.engine_trace("guideline_check", run_id=rid, anchor=name),
    )
    return {"guideline": name, "present": present, "missing": missing, "finding": finding}


def main():
    try:
        json_io.emit(json_io.ok(check(json_io.read_input())))
    except Exception as exc:
        json_io.emit(json_io.error(str(exc)))


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd ~/code/scriptorium && .venv/bin/pytest tests/core/test_guideline_check.py -v`
Expected: 2 passed.

- [ ] **Step 6: Commit**

```bash
git add scripts/core/guideline_check.py scripts/core/data/guidelines/strobe.yaml tests/core/test_guideline_check.py
git commit -m "feat(core): guideline_check — STROBE checklist-as-data keyword gap screen"
```

---

## Task 5: `citation_parse.py`

**Files:**
- Create: `scripts/core/citation_parse.py`
- Test: `tests/core/test_citation_parse.py`

Contract — input:
```json
{"body_text": "...as shown [1] and [3]...", "references": ["Smith 2020", "Jones 2019", "Lee 2021"]}
```
Output `data`:
```json
{"cited_markers": [1, 3], "n_references": 3,
 "orphan_references": [2], "dangling_citations": [],
 "finding": {...}}
```
Rules (deterministic, regex): extract numeric in-text markers `[n]`; `orphan_references` =
reference indices (1-based) never cited; `dangling_citations` = markers with no matching
reference index. Finding `operational_fact` conf 1.0 (pure structural parse); claim
summarises orphans + danglers. This is structural citation hygiene, NOT semantic
claim-support (semantic support deferred — noted in open items).

- [ ] **Step 1: Write the failing test**

```python
# tests/core/test_citation_parse.py
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENGINE = ROOT / "scripts" / "core" / "citation_parse.py"


def run_engine(payload):
    proc = subprocess.run(
        [sys.executable, str(ENGINE)],
        input=json.dumps(payload), capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def test_finds_orphans_and_danglers():
    payload = {
        "body_text": "First claim [1]. Second claim [3]. Also [5].",
        "references": ["Smith 2020", "Jones 2019", "Lee 2021"],
    }
    out = run_engine(payload)
    assert out["status"] == "ok"
    assert out["data"]["cited_markers"] == [1, 3, 5]
    assert out["data"]["orphan_references"] == [2]      # ref 2 never cited
    assert out["data"]["dangling_citations"] == [5]     # [5] has no ref
    assert out["data"]["finding"]["status"] == "operational_fact"


def test_clean_citations_no_issues():
    payload = {"body_text": "A [1] B [2].", "references": ["r1", "r2"]}
    out = run_engine(payload)
    assert out["data"]["orphan_references"] == []
    assert out["data"]["dangling_citations"] == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd ~/code/scriptorium && .venv/bin/pytest tests/core/test_citation_parse.py -v`
Expected: FAIL — engine missing.

- [ ] **Step 3: Write minimal implementation**

```python
# scripts/core/citation_parse.py
"""L0 engine: structural citation hygiene (deterministic regex parse).

Extracts numeric in-text markers [n], cross-checks against the reference list:
  orphan_references   — references never cited in the body
  dangling_citations  — in-text markers with no matching reference index
This is STRUCTURAL hygiene, not semantic claim-support (does the source actually support
the claim) — that is a separate, deferred capability.
Input: {"body_text": <str>, "references": [<str>, ...]}.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.lib import json_io, provenance, epistemic  # noqa: E402

MARKER = re.compile(r"\[(\d+)\]")


def parse(req):
    body = req["body_text"]
    refs = req["references"]
    n_refs = len(refs)

    markers = sorted({int(m) for m in MARKER.findall(body)})
    cited = set(markers)
    orphan = [i for i in range(1, n_refs + 1) if i not in cited]
    dangling = [m for m in markers if m < 1 or m > n_refs]

    rid = provenance.run_id(seed=json.dumps({"b": len(body), "r": n_refs}, sort_keys=True))
    finding = epistemic.make_finding(
        claim=f"{len(orphan)} orphan reference(s), {len(dangling)} dangling citation(s)",
        status="operational_fact", confidence=1.0,
        source=provenance.engine_trace("citation_parse", run_id=rid, anchor="hygiene"),
    )
    return {
        "cited_markers": markers, "n_references": n_refs,
        "orphan_references": orphan, "dangling_citations": dangling, "finding": finding,
    }


def main():
    try:
        json_io.emit(json_io.ok(parse(json_io.read_input())))
    except Exception as exc:
        json_io.emit(json_io.error(str(exc)))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd ~/code/scriptorium && .venv/bin/pytest tests/core/test_citation_parse.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/core/citation_parse.py tests/core/test_citation_parse.py
git commit -m "feat(core): citation_parse — structural hygiene (orphan refs, dangling markers)"
```

---

## Task 6: `gsdesign.R` + `interim_boundaries.py` (R-dispatch)

**Files:**
- Create: `scripts/core/rbridge/gsdesign.R`
- Create: `scripts/core/interim_boundaries.py`
- Test: `tests/core/test_interim_boundaries.py`

Contract — input:
```json
{"k": 2, "alpha": 0.025, "test_type": "one_sided", "sfu": "OF"}
```
Output `data`:
```json
{"k": 2, "upper_bounds": [<z1>, <z2>], "sfu": "OF", "finding": {...}}
```
`gsdesign.R` reads a JSON request on stdin, calls `gsDesign::gsDesign()` with O'Brien-Fleming
(`sfu = sfLDOF`) spending, prints a JSON object `{"upper_bounds": [...]}`. The Python wrapper
dispatches via `subprocess.run(["Rscript", ...])`, wraps the result in an envelope + finding.
If `Rscript`/gsDesign is unavailable, the wrapper returns an `error` envelope (never a crash).

**Test robustness:** O'Brien-Fleming 2-look, one-sided α=0.025 yields a final boundary
z ≈ 1.98 and a higher first-look boundary. Assert structure + monot8 range, not an exact
float.

- [ ] **Step 1: Write the R script**

```r
# scripts/core/rbridge/gsdesign.R
# Group-sequential upper boundaries via gsDesign. Reads JSON {k, alpha, test_type, sfu}
# on stdin, writes JSON {"upper_bounds": [...]} on stdout.
suppressMessages(library(gsDesign))

con <- file("stdin")
raw <- paste(readLines(con), collapse = "")
close(con)

# Minimal JSON parse without extra deps: rely on jsonlite if present, else a tiny fallback.
parse_req <- function(s) {
  if (requireNamespace("jsonlite", quietly = TRUE)) {
    return(jsonlite::fromJSON(s))
  }
  # Fallback: extract numbers/strings by key (sufficient for our flat schema).
  getnum <- function(key) as.numeric(sub(
    paste0('.*"', key, '"\\s*:\\s*([0-9.]+).*'), "\\1", s))
  list(k = getnum("k"), alpha = getnum("alpha"))
}

req <- parse_req(raw)
k <- as.integer(req$k)
alpha <- as.numeric(req$alpha)

# sfLDOF = Lan-DeMets O'Brien-Fleming spending; test.type=1 = one-sided.
d <- gsDesign(k = k, test.type = 1, alpha = alpha, sfu = sfLDOF)
bounds <- as.numeric(d$upper$bound)

cat(sprintf('{"upper_bounds": [%s]}', paste(sprintf("%.6f", bounds), collapse = ", ")))
```

- [ ] **Step 2: Write the failing test**

```python
# tests/core/test_interim_boundaries.py
import json
import shutil
import subprocess
import sys
import pytest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENGINE = ROOT / "scripts" / "core" / "interim_boundaries.py"

pytestmark = pytest.mark.skipif(shutil.which("Rscript") is None, reason="Rscript not available")


def run_engine(payload):
    proc = subprocess.run(
        [sys.executable, str(ENGINE)],
        input=json.dumps(payload), capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def test_obrien_fleming_two_look():
    out = run_engine({"k": 2, "alpha": 0.025, "test_type": "one_sided", "sfu": "OF"})
    assert out["status"] == "ok"
    bounds = out["data"]["upper_bounds"]
    assert len(bounds) == 2
    # O'Brien-Fleming: first look stricter than the final; final ~1.98.
    assert bounds[0] > bounds[1]
    assert 1.9 < bounds[1] < 2.05
    assert out["data"]["finding"]["status"] == "operational_fact"
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd ~/code/scriptorium && .venv/bin/pytest tests/core/test_interim_boundaries.py -v`
Expected: FAIL — wrapper missing.

- [ ] **Step 4: Write the Python wrapper**

```python
# scripts/core/interim_boundaries.py
"""L0 engine: group-sequential upper boundaries via gsDesign (R-dispatch).

Dispatches to scripts/core/rbridge/gsdesign.R through subprocess (isolation over rpy2).
Input: {"k": <int>, "alpha": <float>, "test_type": "one_sided", "sfu": "OF"}.
Output: {k, upper_bounds, sfu, finding}. If Rscript/gsDesign is unavailable, returns an
error envelope rather than crashing.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.lib import json_io, provenance, epistemic  # noqa: E402

RSCRIPT = shutil.which("Rscript")
R_FILE = Path(__file__).resolve().parent / "rbridge" / "gsdesign.R"


def compute(req):
    if RSCRIPT is None:
        raise RuntimeError("Rscript not found — install R + gsDesign for interim boundaries")
    proc = subprocess.run(
        [RSCRIPT, str(R_FILE)],
        input=json.dumps(req), capture_output=True, text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"gsDesign R dispatch failed: {proc.stderr.strip()}")
    r_out = json.loads(proc.stdout)
    bounds = [round(float(b), 6) for b in r_out["upper_bounds"]]

    rid = provenance.run_id(seed=json.dumps(req, sort_keys=True))
    finding = epistemic.make_finding(
        claim=f"{len(bounds)}-look O'Brien-Fleming upper boundaries computed",
        status="operational_fact", confidence=1.0,
        source=provenance.engine_trace("interim_boundaries", run_id=rid, anchor="gsdesign"),
    )
    return {"k": int(req["k"]), "upper_bounds": bounds, "sfu": req.get("sfu", "OF"),
            "finding": finding}


def main():
    try:
        json_io.emit(json_io.ok(compute(json_io.read_input())))
    except Exception as exc:
        json_io.emit(json_io.error(str(exc)))


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd ~/code/scriptorium && .venv/bin/pytest tests/core/test_interim_boundaries.py -v`
Expected: 1 passed (or skipped if Rscript absent — but Task 0 ensured it is present).

- [ ] **Step 6: Commit**

```bash
git add scripts/core/rbridge scripts/core/interim_boundaries.py tests/core/test_interim_boundaries.py
git commit -m "feat(core): interim_boundaries — group-sequential O'Brien-Fleming via gsDesign R-dispatch"
```

---

## Task 7: Extend test harness + changelog

**Files:**
- Modify: `scripts/run_tests.sh` (add an R availability note)
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Add an R note to `run_tests.sh`**

Insert before the final `echo "ALL GREEN"` line:

```bash
echo "== R / gsDesign =="
if command -v Rscript >/dev/null 2>&1 && \
   Rscript -e 'quit(status = !requireNamespace("gsDesign", quietly=TRUE))' >/dev/null 2>&1; then
    echo "OK   gsDesign available (interim_boundaries tests active)"
else
    echo "WARN gsDesign not available — interim_boundaries tests skipped"
fi
```

- [ ] **Step 2: Run the whole suite**

Run: `cd ~/code/scriptorium && scripts/run_tests.sh`
Expected: all pytest tests pass (Plan 1 + Plan 2 engines), gsDesign line `OK`, ends `ALL GREEN`.

- [ ] **Step 3: Update `CHANGELOG.md`**

Under the existing `## [Unreleased] — v0.2.0 (in progress)` → `### Added`, append:
```markdown
- L0 engines: `stat_run` (assumptions, recompute, GRIM), `guideline_check` (STROBE),
  `citation_parse` (structural hygiene), `interim_boundaries` (gsDesign R-dispatch).
```

- [ ] **Step 4: Commit**

```bash
git add scripts/run_tests.sh CHANGELOG.md
git commit -m "build: harness reports gsDesign availability; changelog notes Plan 2 engines"
```

---

## Self-Review

**Spec coverage (Plan 2 portion):** stat-sanity / recompute / GRIM (spec §4 Flow 1,
§2 Q12 assumption-checking) → Tasks 1–3. Reporting-guideline check, checklist-as-data
(§3 `data/guidelines/*.yaml`, §6 ★★ partial) → Task 4. Citation hygiene (§4 Flow 1
citation_parse) → Task 5. Clinical-trial group-sequential, gsDesign R-dispatch (§2 Q13
flagship, §8 R-dispatch via subprocess) → Task 6. Remaining (KB-provider, mode-guard,
L2 migration) deferred to Plans 3–4. Semantic claim-support explicitly scoped OUT of v2
here (Task 5 docstring) — consistent with spec §7 (not promised in v2).

**Placeholder scan:** no TBD/TODO; every code step shows complete code; every run step
shows command + expected result. The R fallback JSON parser is complete, not a stub.

**Type consistency:** every engine emits the envelope (`status`/`data`/`message`) from
`json_io` and findings from `epistemic.make_finding` with the Plan-1 key set
(`claim, status, confidence, source, source_independence`). `provenance.engine_trace(engine,
run_id, anchor)` and `provenance.run_id(seed)` signatures match Plan 1. `stat_run` op
dispatch (`OPS` dict) is consistent across Tasks 1–3 (each task adds one key, never renames).
All statuses used (`operational_fact`, `corroborated_inference`, `working_hypothesis`) are in
the Plan-1 `epistemic.LADDER`.

**Note for executor:** "monot8" in Task 6 intro is shorthand for "monotone/ordered range" —
the assertion is `bounds[0] > bounds[1]` and `1.9 < bounds[1] < 2.05`, as written in the test.
