# Scriptorium v2 — Plan 3: KB-provider (L1) + Mode-guard (L3)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the pluggable KB-provider layer (one `query()` contract, `folder` + `obsidian` adapters, `rag`/`cag` stubs) and the defense-in-depth mode-guard that enforces the Sovereign reviewer path — honestly, never faking a block it cannot make.

**Architecture:** Layered (Approach A), L1 + L3. The KB-provider exposes a single
`query(claim, path) → {evidence, finding}` interface; adapters are interchangeable behind it.
The mode-guard is orthogonal: three defense levels (mode-declaration, capability-removal,
process-sandbox), with `status()` disclosing exactly which are active. Local backends
(`folder`/`obsidian`/`cag`) pass in reviewer-mode; remote (`rag`) is hard-refused.

**Tech Stack:** Python 3 (stdlib + PyYAML), pytest, `unshare` (optional, for the sandbox).

**Prerequisite:** Plans 1–2 complete (`scripts/lib/`, `scripts/core/` engines, venv,
`run_tests.sh` green; 28 tests passing). Reuses `scripts/lib/{json_io,provenance,epistemic}.py`.

**Testing philosophy:** local providers are tested against a tiny temp-folder fixture
(deterministic). The mode-guard's level-3 test is an **honesty test**: it asserts the
status string about sandbox availability MATCHES the real probe result — the guard must not
claim isolation it cannot deliver.

---

## File Structure (Plan 3)

| File | Responsibility |
|---|---|
| `scripts/guard/__init__.py` | Package marker. |
| `scripts/guard/egress_guard.py` | 3-level egress defense + `status()` disclosure. |
| `scripts/kb/__init__.py` | Package marker. |
| `scripts/kb/contract.md` | The `query()` interface contract (doc). |
| `scripts/kb/provider.py` | Provider registry + dispatch (name → adapter), guard hook. |
| `scripts/kb/providers/__init__.py` | Package marker. |
| `scripts/kb/providers/folder.py` | Search md+frontmatter files in a folder. |
| `scripts/kb/providers/obsidian.py` | Folder + wikilink-anchor awareness. |
| `scripts/kb/providers/rag.py` | Remote stub — refused in reviewer-mode, NotImplemented otherwise. |
| `scripts/kb/providers/cag.py` | Local cache stub — NotImplemented placeholder. |
| `scripts/kb/query.py` | CLI entry: guard check → dispatch → evidence + finding. |
| `tests/guard/test_egress_guard.py` | Guard level 1/2/3 tests incl. honesty test. |
| `tests/kb/test_folder_provider.py` | Folder adapter behavior. |
| `tests/kb/test_provider_contract.py` | Shared contract suite over folder + obsidian. |
| `tests/kb/test_query_cli.py` | Integration: reviewer-mode refuses rag; author-mode folder works. |

---

## Task 0: Scaffold

- [ ] **Step 1: Create package dirs + markers**

```bash
cd ~/code/scriptorium
mkdir -p scripts/guard scripts/kb/providers tests/guard tests/kb
touch scripts/guard/__init__.py scripts/kb/__init__.py scripts/kb/providers/__init__.py
touch tests/guard/__init__.py tests/kb/__init__.py
```

No commit (committed with Task 1).

---

## Task 1: `egress_guard.py` — level 1 (mode declaration) + status

**Files:**
- Create: `scripts/guard/egress_guard.py`
- Test: `tests/guard/test_egress_guard.py`

Contract: `assert_local_only(backend, mode)` raises `EgressViolation` if `mode == "reviewer"`
and `backend` is remote (`rag`). Local backends (`folder`, `obsidian`, `cag`) pass in any
mode. `LOCAL_BACKENDS` / `REMOTE_BACKENDS` are explicit sets.

- [ ] **Step 1: Write the failing test**

```python
# tests/guard/test_egress_guard.py
import pytest
from scripts.guard import egress_guard as g


def test_reviewer_mode_refuses_remote_backend():
    with pytest.raises(g.EgressViolation):
        g.assert_local_only("rag", mode="reviewer")


def test_reviewer_mode_allows_local_backend():
    # returns None (no raise) for local backends
    assert g.assert_local_only("folder", mode="reviewer") is None
    assert g.assert_local_only("obsidian", mode="reviewer") is None


def test_author_mode_allows_remote_backend():
    assert g.assert_local_only("rag", mode="author") is None


def test_unknown_backend_refused_in_reviewer():
    with pytest.raises(g.EgressViolation):
        g.assert_local_only("mystery", mode="reviewer")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd ~/code/scriptorium && .venv/bin/pytest tests/guard/test_egress_guard.py -v`
Expected: FAIL — module missing.

- [ ] **Step 3: Write minimal implementation**

```python
# scripts/guard/egress_guard.py
"""Mode-guard: defense-in-depth egress control for the Sovereign reviewer path.

Three levels, strongest first:
  1. Mode declaration   — reviewer-mode refuses remote KB backends (this module).
  2. Capability removal — audit reviewer-path scripts for network imports (Task 2).
  3. Process sandbox    — run under `unshare -n` when available, else best-effort (Task 3).

The guard NEVER claims an isolation it cannot deliver — status() discloses the truth.
"""

LOCAL_BACKENDS = {"folder", "obsidian", "cag"}
REMOTE_BACKENDS = {"rag"}


class EgressViolation(Exception):
    """Raised when reviewer-mode would touch a non-local egress path."""


def assert_local_only(backend, mode):
    """In reviewer-mode, only LOCAL_BACKENDS are allowed. Raises EgressViolation otherwise."""
    if mode != "reviewer":
        return None
    if backend in LOCAL_BACKENDS:
        return None
    raise EgressViolation(
        f"reviewer-mode forbids non-local KB backend {backend!r} "
        f"(allowed: {sorted(LOCAL_BACKENDS)})"
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd ~/code/scriptorium && .venv/bin/pytest tests/guard/test_egress_guard.py -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/guard tests/guard
git commit -m "feat(guard): egress_guard level 1 — reviewer-mode refuses remote KB backends"
```

---

## Task 2: `egress_guard.py` — level 2 (capability removal / import audit)

**Files:**
- Modify: `scripts/guard/egress_guard.py` (add `audit_imports`)
- Modify: `tests/guard/test_egress_guard.py` (add tests)

Contract: `audit_imports(paths) → list[dict]` returns one entry per network-library import
found in the given `.py` files: `{"file": <path>, "module": <name>, "line": <n>}`. Network
modules screened: `requests`, `httpx`, `urllib`, `urllib2`, `socket`, `aiohttp`, `http`,
`ftplib`, `telnetlib`. Matches `import X` and `from X import ...` at line start (ignoring
leading whitespace).

- [ ] **Step 1: Add the failing tests**

```python
# append to tests/guard/test_egress_guard.py
def test_audit_imports_flags_network_module(tmp_path):
    f = tmp_path / "leaky.py"
    f.write_text("import os\nimport requests\nfrom socket import gethostname\n")
    violations = g.audit_imports([str(f)])
    modules = {v["module"] for v in violations}
    assert "requests" in modules
    assert "socket" in modules
    assert "os" not in modules


def test_audit_imports_clean_file(tmp_path):
    f = tmp_path / "clean.py"
    f.write_text("import json\nimport math\nfrom scipy import stats\n")
    assert g.audit_imports([str(f)]) == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/code/scriptorium && .venv/bin/pytest tests/guard/test_egress_guard.py -v -k audit`
Expected: FAIL — `audit_imports` not defined.

- [ ] **Step 3: Add the implementation**

Append to `scripts/guard/egress_guard.py`:

```python
import re

NETWORK_MODULES = {
    "requests", "httpx", "urllib", "urllib2", "socket",
    "aiohttp", "http", "ftplib", "telnetlib",
}
_IMPORT_RE = re.compile(r"^\s*(?:import\s+(\w+)|from\s+(\w+)\s+import)")


def audit_imports(paths):
    """Scan .py files for network-library imports. Returns one violation per hit."""
    violations = []
    for path in paths:
        with open(path, "r", encoding="utf-8") as fh:
            for lineno, line in enumerate(fh, start=1):
                m = _IMPORT_RE.match(line)
                if not m:
                    continue
                module = m.group(1) or m.group(2)
                if module in NETWORK_MODULES:
                    violations.append({"file": path, "module": module, "line": lineno})
    return violations
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ~/code/scriptorium && .venv/bin/pytest tests/guard/test_egress_guard.py -v`
Expected: 6 passed.

- [ ] **Step 5: Verify the real reviewer-path engines are clean (sanity, not a test)**

Run:
```bash
cd ~/code/scriptorium && .venv/bin/python -c "
from scripts.guard import egress_guard as g
import glob
paths = glob.glob('scripts/core/*.py') + glob.glob('scripts/lib/*.py')
print('violations:', g.audit_imports(paths))
"
```
Expected: `violations: []` (the L0 engines import only stdlib + scipy/statsmodels/yaml).

- [ ] **Step 6: Commit**

```bash
git add scripts/guard/egress_guard.py tests/guard/test_egress_guard.py
git commit -m "feat(guard): egress_guard level 2 — network-import audit of reviewer-path scripts"
```

---

## Task 3: `egress_guard.py` — level 3 (process sandbox, honest) + status

**Files:**
- Modify: `scripts/guard/egress_guard.py` (add sandbox + status)
- Modify: `tests/guard/test_egress_guard.py` (add honesty tests)

Contract:
- `sandbox_available() → bool` — probes `unshare -rn true` (unprivileged user-namespace
  network isolation); True iff returncode 0.
- `run_sandboxed(cmd) → dict` — `{"ran": bool, "isolated": bool, "returncode": int,
  "stdout": str}`. If `sandbox_available()`, prefixes `unshare -rn`; else runs the command
  plain with `isolated=False`. NEVER pretends isolation it did not apply.
- `status(mode) → dict` — discloses `{level_1, level_2, level_3}`. `level_3` reads
  `"active (unshare -rn)"` when available, else `"unavailable — best-effort (levels 1+2)"`.

**Honesty test:** `run_sandboxed(...)["isolated"] == sandbox_available()` and the `status`
level_3 string reflects the same probe. The guard's claim must equal reality.

- [ ] **Step 1: Add the failing tests**

```python
# append to tests/guard/test_egress_guard.py
def test_sandbox_claim_matches_reality():
    available = g.sandbox_available()
    result = g.run_sandboxed([__import__("sys").executable, "-c", "print('hi')"])
    assert result["ran"] is True
    assert result["returncode"] == 0
    assert "hi" in result["stdout"]
    # honesty: the isolated flag must equal the real probe, never overclaim.
    assert result["isolated"] == available


def test_status_level3_honest():
    st = g.status(mode="reviewer")
    available = g.sandbox_available()
    if available:
        assert "active" in st["level_3"]
    else:
        assert "best-effort" in st["level_3"]
    assert st["level_1"] == "active"
    assert st["level_2"] == "active"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/code/scriptorium && .venv/bin/pytest tests/guard/test_egress_guard.py -v -k "sandbox or status"`
Expected: FAIL — `sandbox_available`/`run_sandboxed`/`status` not defined.

- [ ] **Step 3: Add the implementation**

Append to `scripts/guard/egress_guard.py`:

```python
import shutil
import subprocess

_UNSHARE = shutil.which("unshare")


def sandbox_available():
    """True iff unprivileged network-isolating sandbox (`unshare -rn`) works here."""
    if _UNSHARE is None:
        return False
    try:
        r = subprocess.run(
            [_UNSHARE, "-rn", "true"], capture_output=True, timeout=10,
        )
        return r.returncode == 0
    except Exception:
        return False


def run_sandboxed(cmd):
    """Run cmd; isolate network via `unshare -rn` when available, else plain (honest)."""
    isolated = sandbox_available()
    full = [_UNSHARE, "-rn", *cmd] if isolated else list(cmd)
    proc = subprocess.run(full, capture_output=True, text=True)
    return {
        "ran": True, "isolated": isolated,
        "returncode": proc.returncode, "stdout": proc.stdout,
    }


def status(mode):
    """Disclose which defense levels are active. Never overclaims level 3."""
    if sandbox_available():
        level_3 = "active (unshare -rn)"
    else:
        level_3 = "unavailable — best-effort (levels 1+2)"
    return {"mode": mode, "level_1": "active", "level_2": "active", "level_3": level_3}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ~/code/scriptorium && .venv/bin/pytest tests/guard/test_egress_guard.py -v`
Expected: 8 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/guard/egress_guard.py tests/guard/test_egress_guard.py
git commit -m "feat(guard): egress_guard level 3 — honest process sandbox (unshare -rn) + status disclosure"
```

---

## Task 4: KB `folder` provider + base

**Files:**
- Create: `scripts/kb/providers/folder.py`
- Test: `tests/kb/test_folder_provider.py`

Contract: `query(claim, path) → {"evidence": [...], "finding": {...}}`. Scans `*.md` under
`path` recursively. For each line containing any claim term (case-insensitive, terms = words
≥ 4 chars from the claim), emit evidence `{"doc": <relpath>, "line": <n>, "snippet": <line>,
"status": <frontmatter status or "working_hypothesis">, "source": kb_trace}`. Finding:
`corroborated_inference` conf 0.7 if ≥1 evidence, else `speculative_hypothesis` conf 0.2
("no local support found").

- [ ] **Step 1: Write the failing test**

```python
# tests/kb/test_folder_provider.py
from scripts.kb.providers import folder


def _make_vault(tmp_path):
    note = tmp_path / "study.md"
    note.write_text(
        "---\nstatus: operational_fact\n---\n"
        "# Capnography\n"
        "Transcutaneous PCO2 correlates with arterial values in stable patients.\n"
        "Unrelated line about coffee.\n"
    )
    return tmp_path


def test_folder_finds_supporting_line(tmp_path):
    vault = _make_vault(tmp_path)
    out = folder.query("transcutaneous PCO2 correlation", str(vault))
    assert len(out["evidence"]) >= 1
    ev = out["evidence"][0]
    assert ev["doc"] == "study.md"
    assert ev["status"] == "operational_fact"        # read from frontmatter
    assert ev["source"].startswith("kb://folder/study.md#L")
    assert out["finding"]["status"] == "corroborated_inference"


def test_folder_no_match_is_speculative(tmp_path):
    vault = _make_vault(tmp_path)
    out = folder.query("quantum gravity entanglement", str(vault))
    assert out["evidence"] == []
    assert out["finding"]["status"] == "speculative_hypothesis"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd ~/code/scriptorium && .venv/bin/pytest tests/kb/test_folder_provider.py -v`
Expected: FAIL — module missing.

- [ ] **Step 3: Write minimal implementation**

```python
# scripts/kb/providers/folder.py
"""KB provider: plain folder of markdown+frontmatter notes (local, reviewer-safe).

query(claim, path) scans *.md recursively, returns lines matching claim terms as graded
evidence. Each note's frontmatter `status:` (if present) becomes the evidence status; the
default is working_hypothesis. This is a keyword screen — a retrieval primitive, not a
semantic judge.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from scripts.lib import provenance, epistemic  # noqa: E402

import yaml  # noqa: E402

DEFAULT_STATUS = "working_hypothesis"


def _terms(claim):
    return {w.lower() for w in claim.split() if len(w) >= 4}


def _frontmatter_status(text):
    if not text.startswith("---"):
        return DEFAULT_STATUS
    end = text.find("\n---", 3)
    if end == -1:
        return DEFAULT_STATUS
    try:
        fm = yaml.safe_load(text[3:end]) or {}
    except yaml.YAMLError:
        return DEFAULT_STATUS
    status = fm.get("status", DEFAULT_STATUS)
    return status if status in epistemic.LADDER else DEFAULT_STATUS


def query(claim, path):
    terms = _terms(claim)
    root = Path(path)
    evidence = []
    for md in sorted(root.rglob("*.md")):
        text = md.read_text(encoding="utf-8")
        status = _frontmatter_status(text)
        rel = os.path.relpath(md, root)
        for lineno, line in enumerate(text.splitlines(), start=1):
            low = line.lower()
            if any(t in low for t in terms):
                evidence.append({
                    "doc": rel, "line": lineno, "snippet": line.strip(),
                    "status": status,
                    "source": provenance.kb_trace("folder", doc=rel, anchor=f"L{lineno}"),
                })

    if evidence:
        f_status, conf, claim_txt = "corroborated_inference", 0.7, \
            f"{len(evidence)} local passage(s) support the query"
    else:
        f_status, conf, claim_txt = "speculative_hypothesis", 0.2, \
            "no local support found"
    finding = epistemic.make_finding(
        claim=claim_txt, status=f_status, confidence=conf,
        source=provenance.kb_trace("folder", doc=str(path), anchor="query"),
        source_independence=len({e["doc"] for e in evidence}),
    )
    return {"evidence": evidence, "finding": finding}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd ~/code/scriptorium && .venv/bin/pytest tests/kb/test_folder_provider.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/kb/providers/folder.py tests/kb/test_folder_provider.py
git commit -m "feat(kb): folder provider — markdown keyword retrieval with frontmatter-graded evidence"
```

---

## Task 5: KB `obsidian` provider + shared contract test

**Files:**
- Create: `scripts/kb/providers/obsidian.py`
- Test: `tests/kb/test_provider_contract.py`

Contract: `obsidian.query(claim, path)` behaves like `folder.query` but additionally
resolves `[[wikilink]]` targets it finds in matching lines into an `links` list on each
evidence item (anchor-awareness). It reuses folder's scan. The shared contract test runs the
SAME assertions against both `folder` and `obsidian` to guarantee interchangeability.

- [ ] **Step 1: Write the obsidian provider**

```python
# scripts/kb/providers/obsidian.py
"""KB provider: Obsidian vault — folder retrieval plus [[wikilink]] anchor awareness.

Delegates scanning to the folder provider, then enriches each evidence item with any
wikilink targets present in the matched line. Local, reviewer-safe.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from scripts.kb.providers import folder as _folder  # noqa: E402
from scripts.lib import provenance  # noqa: E402

_WIKILINK = re.compile(r"\[\[([^\]|#]+)")


def query(claim, path):
    result = _folder.query(claim, path)
    for ev in result["evidence"]:
        ev["links"] = _WIKILINK.findall(ev["snippet"])
        # re-stamp the trace backend as obsidian for provenance clarity
        ev["source"] = provenance.kb_trace("obsidian", doc=ev["doc"], anchor=f"L{ev['line']}")
    return result
```

- [ ] **Step 2: Write the shared contract test**

```python
# tests/kb/test_provider_contract.py
import importlib
import pytest

PROVIDERS = ["scripts.kb.providers.folder", "scripts.kb.providers.obsidian"]


def _vault(tmp_path):
    (tmp_path / "n.md").write_text(
        "---\nstatus: corroborated_inference\n---\n"
        "Hypoxemia relates to [[gas-exchange]] in COPD.\n"
    )
    return tmp_path


@pytest.mark.parametrize("modname", PROVIDERS)
def test_query_contract_shape(modname, tmp_path):
    mod = importlib.import_module(modname)
    out = mod.query("hypoxemia gas-exchange COPD", str(_vault(tmp_path)))
    # every provider returns the same envelope shape
    assert set(out.keys()) == {"evidence", "finding"}
    assert isinstance(out["evidence"], list)
    for ev in out["evidence"]:
        assert {"doc", "line", "snippet", "status", "source"} <= set(ev.keys())
    f = out["finding"]
    assert {"claim", "status", "confidence", "source", "source_independence"} == set(f.keys())


def test_obsidian_extracts_wikilinks(tmp_path):
    from scripts.kb.providers import obsidian
    out = obsidian.query("hypoxemia gas-exchange COPD", str(_vault(tmp_path)))
    assert any("gas-exchange" in ev.get("links", []) for ev in out["evidence"])
```

- [ ] **Step 3: Run tests to verify they fail then pass**

Run: `cd ~/code/scriptorium && .venv/bin/pytest tests/kb/test_provider_contract.py -v`
Expected first run (before obsidian.py exists): collection/import error. After Step 1 file
is saved: 3 passed (2 parametrized contract + 1 wikilink).

- [ ] **Step 4: Commit**

```bash
git add scripts/kb/providers/obsidian.py tests/kb/test_provider_contract.py
git commit -m "feat(kb): obsidian provider + shared contract test (folder/obsidian interchangeable)"
```

---

## Task 6: `rag`/`cag` stubs + `query.py` CLI (guard-integrated) + contract doc

**Files:**
- Create: `scripts/kb/providers/rag.py`
- Create: `scripts/kb/providers/cag.py`
- Create: `scripts/kb/provider.py`
- Create: `scripts/kb/query.py`
- Create: `scripts/kb/contract.md`
- Test: `tests/kb/test_query_cli.py`

Contract — `query.py` input:
```json
{"claim": "...", "backend": "folder", "path": "<dir>", "mode": "author"}
```
Flow: `egress_guard.assert_local_only(backend, mode)` → dispatch to the named provider →
emit `ok` envelope with `{evidence, finding}`. In reviewer-mode + `rag` → guard raises →
`error` envelope. `rag`/`cag` providers raise `NotImplementedError` (v2 stubs) so author-mode
`rag` returns a clean error, not a crash.

- [ ] **Step 1: Write the stubs**

```python
# scripts/kb/providers/rag.py
"""KB provider stub: remote RAG endpoint. NOT implemented in v2 (contract placeholder).

Remote by nature — the mode-guard refuses this in reviewer-mode before dispatch ever
reaches here. In author-mode it raises NotImplementedError until a real adapter lands (v3).
"""


def query(claim, path):
    raise NotImplementedError("rag backend is a v2 stub — implement in v3")
```

```python
# scripts/kb/providers/cag.py
"""KB provider stub: cache-augmented (preloaded) knowledge. NOT implemented in v2.

Local by nature (reviewer-safe) but a placeholder until a real preload adapter lands (v3).
"""


def query(claim, path):
    raise NotImplementedError("cag backend is a v2 stub — implement in v3")
```

- [ ] **Step 2: Write the provider registry**

```python
# scripts/kb/provider.py
"""KB provider registry + dispatch. Maps a backend name to its query(claim, path) callable."""
from scripts.kb.providers import folder, obsidian, rag, cag

REGISTRY = {
    "folder": folder.query,
    "obsidian": obsidian.query,
    "rag": rag.query,
    "cag": cag.query,
}


def get_provider(backend):
    if backend not in REGISTRY:
        raise ValueError(f"unknown KB backend: {backend!r} (have {sorted(REGISTRY)})")
    return REGISTRY[backend]
```

- [ ] **Step 3: Write the failing CLI test**

```python
# tests/kb/test_query_cli.py
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / "scripts" / "kb" / "query.py"


def run_cli(payload):
    proc = subprocess.run(
        [sys.executable, str(CLI)],
        input=json.dumps(payload), capture_output=True, text=True,
    )
    return json.loads(proc.stdout)


def test_author_mode_folder_query(tmp_path):
    (tmp_path / "a.md").write_text("Spirometry shows obstruction in asthma.\n")
    out = run_cli({"claim": "spirometry obstruction asthma",
                   "backend": "folder", "path": str(tmp_path), "mode": "author"})
    assert out["status"] == "ok"
    assert len(out["data"]["evidence"]) >= 1


def test_reviewer_mode_refuses_rag(tmp_path):
    out = run_cli({"claim": "x", "backend": "rag", "path": str(tmp_path), "mode": "reviewer"})
    assert out["status"] == "error"
    assert "reviewer-mode forbids" in out["message"]


def test_author_mode_rag_is_clean_error(tmp_path):
    out = run_cli({"claim": "x", "backend": "rag", "path": str(tmp_path), "mode": "author"})
    assert out["status"] == "error"
    assert "stub" in out["message"]
```

- [ ] **Step 4: Run test to verify it fails**

Run: `cd ~/code/scriptorium && .venv/bin/pytest tests/kb/test_query_cli.py -v`
Expected: FAIL — `query.py` missing.

- [ ] **Step 5: Write the CLI**

```python
# scripts/kb/query.py
"""L1 entry point: guard-checked KB query.

Input (stdin JSON): {"claim", "backend", "path", "mode"}.
Flow: egress_guard.assert_local_only → provider dispatch → ok envelope {evidence, finding}.
Reviewer-mode + remote backend → guard raises → error envelope (no egress).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.lib import json_io  # noqa: E402
from scripts.guard import egress_guard  # noqa: E402
from scripts.kb import provider  # noqa: E402


def main():
    try:
        req = json_io.read_input()
        backend = req["backend"]
        mode = req.get("mode", "author")
        egress_guard.assert_local_only(backend, mode)  # may raise EgressViolation
        fn = provider.get_provider(backend)
        result = fn(req["claim"], req["path"])
        json_io.emit(json_io.ok(result))
    except egress_guard.EgressViolation as exc:
        json_io.emit(json_io.error(str(exc)))
    except Exception as exc:
        json_io.emit(json_io.error(str(exc)))


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Write the contract doc**

```markdown
# scripts/kb/contract.md

# KB-provider contract

Every KB backend implements one function:

    query(claim: str, path: str) -> {"evidence": [...], "finding": {...}}

- **evidence**: list of `{doc, line, snippet, status, source}` (+ optional `links`). `status`
  is a graded epistemic status (scripts/lib/epistemic.LADDER). `source` is a `kb://<backend>/<doc>#<anchor>` trace.
- **finding**: a single graded finding (scripts/lib/epistemic.make_finding) summarising support.

Backends (selected via `profile.md` → `kb.backend`):

| backend  | locality | v2 status |
|----------|----------|-----------|
| folder   | local    | implemented |
| obsidian | local    | implemented (folder + wikilink awareness) |
| cag      | local    | stub (v3) |
| rag      | remote   | stub (v3) — refused by mode-guard in reviewer-mode |

The mode-guard (`scripts/guard/egress_guard.py`) calls `assert_local_only(backend, mode)`
before dispatch: in reviewer-mode only local backends pass.
```

- [ ] **Step 7: Run test to verify it passes**

Run: `cd ~/code/scriptorium && .venv/bin/pytest tests/kb/test_query_cli.py -v`
Expected: 3 passed.

- [ ] **Step 8: Commit**

```bash
git add scripts/kb/providers/rag.py scripts/kb/providers/cag.py scripts/kb/provider.py scripts/kb/query.py scripts/kb/contract.md tests/kb/test_query_cli.py
git commit -m "feat(kb): provider registry + guard-integrated query CLI + rag/cag stubs + contract doc"
```

---

## Task 7: Harness + changelog

**Files:**
- Modify: `scripts/run_tests.sh` (add a guard-disclosure echo)
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Add a mode-guard disclosure line to `run_tests.sh`**

Insert before the final `echo "ALL GREEN"`:

```bash
echo "== mode-guard =="
.venv/bin/python -c "from scripts.guard import egress_guard as g; import json; print(json.dumps(g.status('reviewer')))"
```

- [ ] **Step 2: Run the whole suite**

Run: `cd ~/code/scriptorium && scripts/run_tests.sh`
Expected: all tests pass (Plan 1+2+3), guard status line prints level_1/2/3, ends `ALL GREEN`.

- [ ] **Step 3: Update `CHANGELOG.md`**

Under `### Added`, append:
```markdown
- L1 KB-provider: pluggable `query()` contract, `folder` + `obsidian` adapters, `rag`/`cag`
  stubs, guard-integrated `kb/query.py`.
- L3 mode-guard: defense-in-depth egress control (mode declaration, import audit, honest
  process sandbox) with truthful `status()` disclosure.
```

- [ ] **Step 4: Commit**

```bash
git add scripts/run_tests.sh CHANGELOG.md
git commit -m "build: harness prints mode-guard status; changelog notes L1 KB + L3 guard"
```

---

## Self-Review

**Spec coverage (Plan 3 portion):** pluggable KB-provider, contract-first, folder/obsidian +
rag/cag stubs (spec §2 Q18, §3 L1) → Tasks 4–6. Mode-guard defense-in-depth, three levels,
"never fakes a block" (spec §5, §2 Q10) → Tasks 1–3. Local-vs-remote enforcement tying KB to
Sovereign (spec §4 invariant 3) → Task 6 guard integration. Remaining (L2 agent/skill
migration) is Plan 4. Real rag/cag adapters explicitly deferred to v3 (spec §7) — stubs only,
as planned.

**Placeholder scan:** the rag/cag providers are intentional stubs that raise
`NotImplementedError` with a clear v3 message — this is specified behavior tested in Task 6,
not an unfinished placeholder. No TBD/TODO; all code complete; all run steps show expected
output.

**Type consistency:** every provider returns `{"evidence", "finding"}`; evidence items share
`{doc, line, snippet, status, source}` (folder Task 4, obsidian Task 5, asserted by the
contract test). `finding` uses `epistemic.make_finding`'s exact key set. `provenance.kb_trace(
backend, doc, anchor)` signature matches Plan 1. `egress_guard.assert_local_only(backend,
mode)` / `audit_imports(paths)` / `sandbox_available()` / `run_sandboxed(cmd)` / `status(mode)`
names are consistent between guard tasks (1–3) and the `query.py` consumer (Task 6). All
epistemic statuses used (`corroborated_inference`, `speculative_hypothesis`,
`working_hypothesis`, `operational_fact`) are in the Plan-1 `epistemic.LADDER`.
