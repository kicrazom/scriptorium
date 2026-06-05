# Scriptorium v2 — Plan 1: Foundation + Epistemic Spine + First Engine

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up the L0 deterministic core's tooling, shared lib, the epistemic-status spine, and the densest first engine (power/sample-size), as a vertical slice proving Approach A end-to-end with golden tests.

**Architecture:** Layered (Approach A). This plan builds L0 (`scripts/core/`) + shared `scripts/lib/` + the test harness. Each engine is a Python CLI reading JSON on stdin and writing a JSON result envelope on stdout — testable without a model and without network. The epistemic-status module is the lingua franca every engine emits.

**Tech Stack:** Python 3 (stdlib + statsmodels, scipy, pingouin, lifelines, PyYAML), pytest, bash harness.

**Decomposition (this plan = Plan 1 of 4):**
- **Plan 1 (this doc):** project tooling, `lib/` (json_io, provenance, epistemic), `core/epistemic_grade.py`, `core/power_sample_size.py`, golden-test harness + pre-push gate.
- **Plan 2 (later):** remaining L0 engines — `stat_run.py` (assumptions + recompute), `guideline_check.py` (checklist-as-YAML), `citation_parse.py`, `rbridge/gsdesign.R`.
- **Plan 3 (later):** L1 KB-provider (contract + folder/obsidian adapters, rag/cag stubs) + L3 mode-guard (defense-in-depth).
- **Plan 4 (later):** L2 agent/skill migration to call L0/L1, prompt lint, integration smoke.

---

## File Structure (Plan 1)

| File | Responsibility |
|---|---|
| `pyproject.toml` | Project metadata + deps + pytest config. Create. |
| `scripts/lib/json_io.py` | Read JSON (stdin or `--in`), emit JSON result/error envelope. |
| `scripts/lib/provenance.py` | Build `source_trace` strings + per-run id. |
| `scripts/lib/epistemic.py` | Status ladder, rank, weakest-link aggregation, finding/result schema helpers. |
| `scripts/core/epistemic_grade.py` | CLI: list of findings → aggregate graded result (the spine). |
| `scripts/core/power_sample_size.py` | CLI: effect/alpha/power → N per group (+ graded result). |
| `scripts/run_tests.sh` | Activate venv, run pytest + shell harness; pre-push gate. |
| `tests/lib/test_json_io.py` | Tests for json_io. |
| `tests/lib/test_epistemic.py` | Tests for epistemic ladder + weakest-link. |
| `tests/core/test_epistemic_grade.py` | Golden tests for the spine engine. |
| `tests/core/test_power_sample_size.py` | Golden tests (Cohen textbook cases). |
| `tests/golden/**` | Input/expected JSON fixture pairs. |

---

## Task 0: Project tooling

**Files:**
- Create: `pyproject.toml`
- Create: `tests/__init__.py`, `tests/lib/__init__.py`, `tests/core/__init__.py`
- Create: `scripts/__init__.py`, `scripts/lib/__init__.py`, `scripts/core/__init__.py`

- [ ] **Step 1: Create `pyproject.toml`**

```toml
[project]
name = "scriptorium"
version = "0.2.0.dev0"
description = "Sovereign rigor/audit layer for the scientific knowledge lifecycle"
requires-python = ">=3.10"
dependencies = [
    "statsmodels>=0.14",
    "scipy>=1.11",
    "pingouin>=0.5.4",
    "lifelines>=0.27",
    "PyYAML>=6.0",
]

[project.optional-dependencies]
dev = ["pytest>=8.0"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
```

- [ ] **Step 2: Create package marker files**

```bash
cd ~/code/scriptorium
mkdir -p scripts/lib scripts/core tests/lib tests/core tests/golden
touch scripts/__init__.py scripts/lib/__init__.py scripts/core/__init__.py
touch tests/__init__.py tests/lib/__init__.py tests/core/__init__.py
```

- [ ] **Step 3: Create venv and install deps**

```bash
cd ~/code/scriptorium
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```
Expected: installs statsmodels, scipy, pingouin, lifelines, pyyaml, pytest without error.

- [ ] **Step 4: Verify pytest runs (no tests yet)**

Run: `cd ~/code/scriptorium && .venv/bin/pytest -q`
Expected: `no tests ran` (exit 5) — confirms pytest is wired.

- [ ] **Step 5: Add `.venv/` to `.gitignore`**

Append line `.venv/` to `.gitignore` if not already present.

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml scripts tests .gitignore
git commit -m "build: python project tooling — pyproject, venv deps, test scaffold"
```

---

## Task 1: `lib/json_io.py` — JSON I/O envelope

**Files:**
- Create: `scripts/lib/json_io.py`
- Test: `tests/lib/test_json_io.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/lib/test_json_io.py
import json
import io
from scripts.lib import json_io


def test_read_input_from_stream():
    stream = io.StringIO('{"a": 1}')
    assert json_io.read_input(stream) == {"a": 1}


def test_ok_envelope_shape():
    env = json_io.ok({"n": 64})
    assert env["status"] == "ok"
    assert env["data"] == {"n": 64}


def test_error_envelope_shape():
    env = json_io.error("bad input")
    assert env["status"] == "error"
    assert env["message"] == "bad input"


def test_emit_writes_json(capsys):
    json_io.emit({"status": "ok", "data": {"x": 2}})
    out = capsys.readouterr().out
    assert json.loads(out) == {"status": "ok", "data": {"x": 2}}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd ~/code/scriptorium && .venv/bin/pytest tests/lib/test_json_io.py -v`
Expected: FAIL with `ModuleNotFoundError: scripts.lib.json_io` (or AttributeError).

- [ ] **Step 3: Write minimal implementation**

```python
# scripts/lib/json_io.py
"""JSON I/O for L0 engines: read a request, emit a result/error envelope."""
import json
import sys


def read_input(stream=None):
    """Parse a JSON object from a text stream (default: stdin)."""
    stream = stream if stream is not None else sys.stdin
    return json.load(stream)


def ok(data):
    """Build a success envelope."""
    return {"status": "ok", "data": data}


def error(message):
    """Build an error envelope."""
    return {"status": "error", "message": message}


def emit(envelope, stream=None):
    """Write an envelope as JSON to a stream (default: stdout)."""
    stream = stream if stream is not None else sys.stdout
    json.dump(envelope, stream)
    stream.write("\n")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd ~/code/scriptorium && .venv/bin/pytest tests/lib/test_json_io.py -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/lib/json_io.py tests/lib/test_json_io.py
git commit -m "feat(lib): json_io — request parsing + result/error envelope"
```

---

## Task 2: `lib/provenance.py` — source traces

**Files:**
- Create: `scripts/lib/provenance.py`
- Test: `tests/lib/test_provenance.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/lib/test_provenance.py
from scripts.lib import provenance


def test_engine_trace_format():
    t = provenance.engine_trace("power_sample_size", run_id="r1", anchor="result")
    assert t == "scripts/core/power_sample_size.py#run=r1:result"


def test_kb_trace_format():
    t = provenance.kb_trace("obsidian", doc="Studies/x.md", anchor="L12-L20")
    assert t == "kb://obsidian/Studies/x.md#L12-L20"


def test_run_id_is_deterministic_from_seed():
    a = provenance.run_id(seed="abc")
    b = provenance.run_id(seed="abc")
    assert a == b and len(a) == 12
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd ~/code/scriptorium && .venv/bin/pytest tests/lib/test_provenance.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Write minimal implementation**

```python
# scripts/lib/provenance.py
"""Build provenance strings. Format mirrors the vault convention `source: path#anchor`.

Run ids are derived from a caller-supplied seed (NOT wall-clock) so engine output is
reproducible and golden-testable. The seed is the caller's responsibility (e.g. a hash of
the request payload).
"""
import hashlib


def run_id(seed):
    """Deterministic 12-char id from a seed string."""
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12]


def engine_trace(engine, run_id, anchor):
    """Trace pointing at an L0 engine run, e.g. scripts/core/<engine>.py#run=<id>:<anchor>."""
    return f"scripts/core/{engine}.py#run={run_id}:{anchor}"


def kb_trace(backend, doc, anchor):
    """Trace pointing at a KB document, e.g. kb://<backend>/<doc>#<anchor>."""
    return f"kb://{backend}/{doc}#{anchor}"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd ~/code/scriptorium && .venv/bin/pytest tests/lib/test_provenance.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/lib/provenance.py tests/lib/test_provenance.py
git commit -m "feat(lib): provenance — engine/kb source traces, seed-derived run ids"
```

---

## Task 3: `lib/epistemic.py` — status ladder + weakest-link

**Files:**
- Create: `scripts/lib/epistemic.py`
- Test: `tests/lib/test_epistemic.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/lib/test_epistemic.py
import pytest
from scripts.lib import epistemic


def test_ladder_order():
    assert epistemic.rank("contradicted") < epistemic.rank("speculative_hypothesis")
    assert epistemic.rank("speculative_hypothesis") < epistemic.rank("canonical_fact")


def test_unknown_status_raises():
    with pytest.raises(ValueError):
        epistemic.rank("nonsense")


def test_weakest_link_picks_lowest_status():
    statuses = ["operational_fact", "working_hypothesis", "canonical_fact"]
    assert epistemic.weakest_link(statuses) == "working_hypothesis"


def test_weakest_link_contradicted_dominates():
    statuses = ["canonical_fact", "contradicted"]
    assert epistemic.weakest_link(statuses) == "contradicted"


def test_weakest_link_empty_raises():
    with pytest.raises(ValueError):
        epistemic.weakest_link([])


def test_make_finding_shape():
    f = epistemic.make_finding(
        claim="t-test inadequate",
        status="operational_fact",
        confidence=0.9,
        source="scripts/core/stat_run.py#run=x:assumptions",
        source_independence=1,
    )
    assert f == {
        "claim": "t-test inadequate",
        "status": "operational_fact",
        "confidence": 0.9,
        "source": "scripts/core/stat_run.py#run=x:assumptions",
        "source_independence": 1,
    }
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd ~/code/scriptorium && .venv/bin/pytest tests/lib/test_epistemic.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Write minimal implementation**

```python
# scripts/lib/epistemic.py
"""Graduated epistemic-status spine: the lingua franca every engine emits.

Statuses, weakest-to-strongest (contradicted sits below the ladder as the weakest of all):
    contradicted < speculative_hypothesis < working_hypothesis
        < corroborated_inference < operational_fact < canonical_fact
"""

LADDER = [
    "contradicted",
    "speculative_hypothesis",
    "working_hypothesis",
    "corroborated_inference",
    "operational_fact",
    "canonical_fact",
]
_RANK = {s: i for i, s in enumerate(LADDER)}


def rank(status):
    """Integer rank of a status; higher = stronger. Raises ValueError if unknown."""
    if status not in _RANK:
        raise ValueError(f"unknown epistemic status: {status!r}")
    return _RANK[status]


def weakest_link(statuses):
    """Aggregate a list of statuses to the weakest one (report = min)."""
    if not statuses:
        raise ValueError("weakest_link requires at least one status")
    return min(statuses, key=rank)


def make_finding(claim, status, confidence, source, source_independence=1):
    """Build a finding object. Validates status; keeps the canonical key order."""
    rank(status)  # validate
    return {
        "claim": claim,
        "status": status,
        "confidence": confidence,
        "source": source,
        "source_independence": source_independence,
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd ~/code/scriptorium && .venv/bin/pytest tests/lib/test_epistemic.py -v`
Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/lib/epistemic.py tests/lib/test_epistemic.py
git commit -m "feat(lib): epistemic — status ladder, weakest-link aggregation, finding schema"
```

---

## Task 4: `core/epistemic_grade.py` — the spine engine (CLI)

**Files:**
- Create: `scripts/core/epistemic_grade.py`
- Test: `tests/core/test_epistemic_grade.py`
- Test fixtures: `tests/golden/epistemic_grade/weak_dominates.in.json`, `.out.json`

Contract — input:
```json
{"findings": [{"status": "operational_fact", "confidence": 0.9},
              {"status": "working_hypothesis", "confidence": 0.6}]}
```
Output envelope `data`:
```json
{"overall_status": "working_hypothesis", "overall_confidence": 0.6, "n_findings": 2}
```
Rule: `overall_status` = weakest-link of finding statuses; `overall_confidence` = min of confidences (weakest-link on confidence too).

- [ ] **Step 1: Write the failing test**

```python
# tests/core/test_epistemic_grade.py
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENGINE = ROOT / "scripts" / "core" / "epistemic_grade.py"
GOLDEN = ROOT / "tests" / "golden" / "epistemic_grade"


def run_engine(payload):
    proc = subprocess.run(
        [sys.executable, str(ENGINE)],
        input=json.dumps(payload),
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def test_weak_dominates():
    payload = json.loads((GOLDEN / "weak_dominates.in.json").read_text())
    expected = json.loads((GOLDEN / "weak_dominates.out.json").read_text())
    assert run_engine(payload) == expected


def test_empty_findings_is_error():
    proc = subprocess.run(
        [sys.executable, str(ENGINE)],
        input=json.dumps({"findings": []}),
        capture_output=True, text=True,
    )
    out = json.loads(proc.stdout)
    assert out["status"] == "error"
```

- [ ] **Step 2: Create golden fixtures**

```bash
mkdir -p tests/golden/epistemic_grade
```
`tests/golden/epistemic_grade/weak_dominates.in.json`:
```json
{"findings": [{"status": "operational_fact", "confidence": 0.9},
              {"status": "working_hypothesis", "confidence": 0.6},
              {"status": "canonical_fact", "confidence": 0.99}]}
```
`tests/golden/epistemic_grade/weak_dominates.out.json`:
```json
{"status": "ok", "data": {"overall_status": "working_hypothesis", "overall_confidence": 0.6, "n_findings": 3}}
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd ~/code/scriptorium && .venv/bin/pytest tests/core/test_epistemic_grade.py -v`
Expected: FAIL — engine file does not exist.

- [ ] **Step 4: Write minimal implementation**

```python
# scripts/core/epistemic_grade.py
"""L0 engine: aggregate a list of findings to one graded result (weakest-link).

Input (stdin JSON): {"findings": [{"status": <ladder>, "confidence": <float>}, ...]}
Output (stdout JSON): ok envelope with {overall_status, overall_confidence, n_findings}.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.lib import json_io, epistemic  # noqa: E402


def grade(findings):
    statuses = [f["status"] for f in findings]
    confidences = [f["confidence"] for f in findings]
    return {
        "overall_status": epistemic.weakest_link(statuses),
        "overall_confidence": min(confidences),
        "n_findings": len(findings),
    }


def main():
    try:
        req = json_io.read_input()
        findings = req.get("findings", [])
        if not findings:
            json_io.emit(json_io.error("no findings provided"))
            return
        json_io.emit(json_io.ok(grade(findings)))
    except Exception as exc:  # surface as a structured error, never a traceback
        json_io.emit(json_io.error(str(exc)))


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd ~/code/scriptorium && .venv/bin/pytest tests/core/test_epistemic_grade.py -v`
Expected: 2 passed.

- [ ] **Step 6: Commit**

```bash
git add scripts/core/epistemic_grade.py tests/core/test_epistemic_grade.py tests/golden/epistemic_grade
git commit -m "feat(core): epistemic_grade engine — weakest-link aggregation CLI + golden tests"
```

---

## Task 5: `core/power_sample_size.py` — first rigor engine (CLI)

**Files:**
- Create: `scripts/core/power_sample_size.py`
- Test: `tests/core/test_power_sample_size.py`
- Test fixtures: `tests/golden/power_sample_size/cohen_medium.in.json`, `.out.json`

Contract — input (two-sample t-test, solve for N per group):
```json
{"test": "two_sample_t", "effect_size": 0.5, "alpha": 0.05, "power": 0.80, "ratio": 1.0}
```
Output `data`:
```json
{"n_per_group": 64, "n_total": 128, "finding": { ...graded finding... }}
```
Golden anchor: Cohen's medium effect d=0.5, α=0.05, power=0.80 → n≈63.77 → ceil 64/group (canonical textbook value). The engine returns a finding with status `operational_fact` (deterministic closed-form) and confidence 1.0, source via provenance.

- [ ] **Step 1: Write the failing test**

```python
# tests/core/test_power_sample_size.py
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENGINE = ROOT / "scripts" / "core" / "power_sample_size.py"
GOLDEN = ROOT / "tests" / "golden" / "power_sample_size"


def run_engine(payload):
    proc = subprocess.run(
        [sys.executable, str(ENGINE)],
        input=json.dumps(payload),
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def test_cohen_medium_effect():
    payload = json.loads((GOLDEN / "cohen_medium.in.json").read_text())
    out = run_engine(payload)
    assert out["status"] == "ok"
    assert out["data"]["n_per_group"] == 64
    assert out["data"]["n_total"] == 128
    assert out["data"]["finding"]["status"] == "operational_fact"
    assert out["data"]["finding"]["confidence"] == 1.0
    assert out["data"]["finding"]["source"].startswith("scripts/core/power_sample_size.py#run=")


def test_unknown_test_is_error():
    proc = subprocess.run(
        [sys.executable, str(ENGINE)],
        input=json.dumps({"test": "telepathy", "effect_size": 0.5}),
        capture_output=True, text=True,
    )
    out = json.loads(proc.stdout)
    assert out["status"] == "error"
```

- [ ] **Step 2: Create golden fixtures**

```bash
mkdir -p tests/golden/power_sample_size
```
`tests/golden/power_sample_size/cohen_medium.in.json`:
```json
{"test": "two_sample_t", "effect_size": 0.5, "alpha": 0.05, "power": 0.80, "ratio": 1.0}
```
(The `.out.json` is asserted field-by-field in the test rather than whole-file, because the run-id in `source` is payload-derived; no separate `.out.json` needed for this case.)

- [ ] **Step 3: Run test to verify it fails**

Run: `cd ~/code/scriptorium && .venv/bin/pytest tests/core/test_power_sample_size.py -v`
Expected: FAIL — engine file does not exist.

- [ ] **Step 4: Write minimal implementation**

```python
# scripts/core/power_sample_size.py
"""L0 engine: closed-form power / sample-size for a two-sample t-test.

Input (stdin JSON): {"test": "two_sample_t", "effect_size": <d>, "alpha": <a>,
                     "power": <1-beta>, "ratio": <n2/n1, default 1.0>}
Output (stdout JSON): ok envelope with {n_per_group, n_total, finding}.

n_per_group is ceil of the analytic solution. The finding carries operational_fact /
confidence 1.0 because the computation is deterministic closed-form, with a provenance
trace whose run id is derived from the request payload (reproducible).
"""
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.lib import json_io, provenance, epistemic  # noqa: E402

from statsmodels.stats.power import TTestIndPower  # noqa: E402


def two_sample_t(effect_size, alpha, power, ratio):
    analysis = TTestIndPower()
    n1 = analysis.solve_power(
        effect_size=effect_size, alpha=alpha, power=power,
        ratio=ratio, alternative="two-sided",
    )
    return int(math.ceil(n1))


def compute(req):
    test = req.get("test")
    if test != "two_sample_t":
        raise ValueError(f"unsupported test: {test!r}")
    effect_size = float(req["effect_size"])
    alpha = float(req.get("alpha", 0.05))
    power = float(req.get("power", 0.80))
    ratio = float(req.get("ratio", 1.0))

    n_per_group = two_sample_t(effect_size, alpha, power, ratio)
    n_total = n_per_group + int(math.ceil(n_per_group * ratio))

    rid = provenance.run_id(seed=json.dumps(req, sort_keys=True))
    finding = epistemic.make_finding(
        claim=f"n={n_per_group}/group for d={effect_size}, alpha={alpha}, power={power}",
        status="operational_fact",
        confidence=1.0,
        source=provenance.engine_trace("power_sample_size", run_id=rid, anchor="result"),
        source_independence=1,
    )
    return {"n_per_group": n_per_group, "n_total": n_total, "finding": finding}


def main():
    try:
        req = json_io.read_input()
        json_io.emit(json_io.ok(compute(req)))
    except Exception as exc:
        json_io.emit(json_io.error(str(exc)))


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd ~/code/scriptorium && .venv/bin/pytest tests/core/test_power_sample_size.py -v`
Expected: 2 passed. (If `n_per_group` is 63 not 64, the ratio for `n_total` rounding is fine — but the canonical value is 64; statsmodels returns ≈63.77 → ceil 64.)

- [ ] **Step 6: Commit**

```bash
git add scripts/core/power_sample_size.py tests/core/test_power_sample_size.py tests/golden/power_sample_size
git commit -m "feat(core): power_sample_size engine — two-sample t closed-form + graded finding + golden test"
```

---

## Task 6: Test harness + pre-push gate

**Files:**
- Create: `scripts/run_tests.sh`

- [ ] **Step 1: Write `scripts/run_tests.sh`**

```bash
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
```

- [ ] **Step 2: Make it executable**

```bash
chmod +x scripts/run_tests.sh
```

- [ ] **Step 3: Run the whole suite**

Run: `cd ~/code/scriptorium && scripts/run_tests.sh`
Expected: pytest reports all tests passed, validators pass, prints `ALL GREEN`.

- [ ] **Step 4: Commit**

```bash
git add scripts/run_tests.sh
git commit -m "build: run_tests.sh — full-suite pre-push quality gate"
```

---

## Task 7: Plan-1 docs note

**Files:**
- Modify: `CHANGELOG.md` (prepend an Unreleased entry)

- [ ] **Step 1: Prepend Unreleased entry to `CHANGELOG.md`**

Add at the top of the changelog body:
```markdown
## [Unreleased] — v0.2.0 (in progress)

### Added
- L0 deterministic core foundation: `scripts/lib/` (json_io, provenance, epistemic spine)
  and first engines `core/epistemic_grade.py`, `core/power_sample_size.py`, with golden tests.
- `scripts/run_tests.sh` pre-push quality gate.
```

- [ ] **Step 2: Commit**

```bash
git add CHANGELOG.md
git commit -m "docs(changelog): note v0.2.0 L0 foundation in progress"
```

---

## Self-Review

**Spec coverage (Plan 1 portion):** epistemic-status spine (§1, §4 invariant 2) → Tasks 3, 4.
Deterministic L0 + JSON contract (§2 Q19, §3) → all engine tasks. Provenance mandatory
(§4 invariant 1) → Task 2 + used in Task 5. Golden tests dense at L0 (§6) → Tasks 4, 5
fixtures. Three quality gates / pre-push (§6) → Task 6. Remaining spec areas (stat_run,
guideline_check, citation_parse, gsdesign, KB-provider, mode-guard, L2 migration) are
explicitly deferred to Plans 2–4 — not gaps.

**Placeholder scan:** no TBD/TODO; every code step shows full code; every run step shows
command + expected output. Clean.

**Type consistency:** finding object keys (`claim, status, confidence, source,
source_independence`) identical across `epistemic.make_finding` (Task 3),
`epistemic_grade` input (Task 4 reads `status`/`confidence`), and `power_sample_size`
output (Task 5). Envelope shape (`status`/`data`/`message`) consistent across `json_io`
(Task 1) and both engines. `weakest_link` / `rank` / `make_finding` names match between
lib (Task 3) and consumers (Task 4). `engine_trace(engine, run_id, anchor)` /
`run_id(seed)` signatures match between Task 2 and Task 5.
