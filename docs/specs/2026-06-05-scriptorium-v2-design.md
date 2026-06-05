# Scriptorium v2 — Design Specification (repositioning)

**Date:** 2026-06-05
**Status:** approved (brainstorm → spec); awaiting build plan
**Author:** Łukasz Minarowski (ORCID 0000-0002-2536-3508)
**Repo:** `github.com/kicrazom/scriptorium` (private; public switch gated)
**Supersedes positioning of:** `docs/specs/2026-06-04-scriptorium-design.md` (v0.1 contract — still valid for packaging/roster); `docs/brainstorm/2026-06-04-v2-positioning-state.md` (closed: questions answered below)

---

## 1. Positioning verdict

Scriptorium is **not another writer**. `claude-scientific-writer` generates; Scriptorium
**scrutinizes / verifies / grades / computes / curates**. It occupies the under-served
rigor/verification frontier, not the saturated generation market.

**North Star (Q20):** a **hybrid of two co-equal pillars plus a cross-cutting spine.**

- **Sovereign** (the *where*) — confidential manuscript bytes never leave the machine;
  reviewer path runs offline, drivable by a local model (Bielik / PLLuM / Qwen via vLLM).
- **Rigor** (the *what*) — audit / verify / compute: statistician-that-executes,
  power/sample-size, citation-support, stat-sanity, reporting-guideline, GRADE,
  clinical-trial methodology.
- **Epistemic-status** (the *how*) — every output is expressed as a graduated claim
  (`status + confidence + source_independence + provenance`). It is the lingua franca of
  every finding, **not** a separate product.

**Boundary (Q1, Q3):** **complement + carving.** Both tools installable; Scriptorium hands
generation to `scientific-writer` and takes over for audit / offline / quantitation. Verb
split is the contract: writer = generate, Scriptorium = audit.

**Five moats (ranked):** (1) policy-manufactured — ICMJE/Elsevier/Springer prohibit cloud
LLM upload of manuscripts and demand reviewer accountability → cloud SaaS legally fenced
out, offline tooling demanded (strongest, verifiable); (2) sovereign/local (GDPR +
on-prem EU hospital LLM precedent + Bielik/PLLuM); (3) stats-execution on the LLM failure
boundary (StatQA: GPT-4 ≈64.8% on test applicability); (4) clinical-trial methodology
whitespace; (5) graduated epistemic-status (un-owned in science tooling).

---

## 2. Resolved design decisions

| # | Question | Decision |
|---|----------|----------|
| Q20 | North Star | Hybrid: Sovereign + Rigor pillars, epistemic-status as cross-cutting spine |
| Q1/Q3 | Boundary vs scientific-writer | Complement + carving (verb split: writer generates, Scriptorium audits) |
| Q2 | Overlapping roster items | **Keep, differentiated:** peer-reviewer (flagship), literature-search (narrowed to retrieval/dedup/OA-resolve), peer-paraphrase, manuscript-imrad (**reframed to audit-mode** — IMRaD conformance gap-check, not generation) |
| Q19 | Runtime / distribution | Claude Code plugin **+ vLLM-ready**: logic lives in deterministic `scripts/`, JSON contract, model-agnostic orchestration |
| Q17 | Deterministic-tools phasing | Confirmed: `scripts/` + JSON-contract-first → MCP later |
| Q11/Q12 | Statistician | **Python-primary** (statsmodels/scipy/pingouin/lifelines) **+ R-dispatch** (gsDesign/lme4); **primary value = assumption/applicability checking**, not just running tests |
| Q13 | Clinical-trial methodology | **Flagship v2** (interim-analysis-reviewer + R-dispatch gsDesign / ICH E9(R1)) |
| Q16 | Contradiction-detection vs vault | **Out-of-scope v2** (defer to v3 with KB-deep-integration) |
| Q18 | KB access | **Pluggable KB-provider** (contract-first): `folder` / `obsidian` / `rag` / `cag` selected in `profile.md`. v2 ships `folder` + `obsidian`; `rag`/`cag` are contract stubs |
| Q10 | Egress enforcement | **Enforce by tooling** (reviewer-path network-block), defense-in-depth, guard never fakes a block it cannot make |
| Q9 | Language | EN-default + PL via profile (carried from v0.1) |
| Q14 | Epistemic spine | Yes — organizing format of every output, weakest-link aggregation |
| Q15 | Aggregation | Weakest-link (report status = min of component statuses) + staleness flags |
| Q7/Q8 | Offline reviewer / local-first | Yes — reviewer path hard-offline; local model assumed available |

**Architecture choice:** **Approach A — layered.** Deterministic core + KB-provider +
thin model-agnostic orchestration + orthogonal mode-guard. Chosen because it realizes
Sovereign and Rigor simultaneously and is the only option that is genuinely vLLM-ready.

---

## 3. Component map

Plugin-idiomatic: everything non-agent/non-skill lives under `scripts/` (bundled-scripts
pattern). L2 agents/skills call `scripts/` via `$CLAUDE_PLUGIN_ROOT`.

```
scriptorium/
  .claude-plugin/          plugin.json, marketplace.json            [exists]
  agents/                  L2 — thin orchestration, model-agnostic prompts
    peer-reviewer.md         flagship auditor (offline-enforced)
    statistician.md          Python-primary + R-dispatch
    librarian.md             KB-provider consumer
    research-scout.md        retrieval/dedup
  skills/                  L2 — 8 skills
    literature-search/       NARROWED: retrieval/dedup/OA-resolve (synthesis → sci-writer)
    manuscript-imrad/        REFRAMED: audit-mode (conformance gap-check, not generation)
    interim-analysis-reviewer/  FLAGSHIP: R-dispatch gsDesign / ICH E9(R1)
    reporting-guideline-check/  power-sample-size/  epistemic-status/
    field-note-from-url/  peer-paraphrase/
  scripts/
    core/                  L0 — deterministic engines (Python CLI, JSON in/out)
      power_sample_size.py   stat_run.py (statsmodels/scipy/lifelines)
      guideline_check.py     epistemic_grade.py   citation_parse.py
      rbridge/gsdesign.R     R-dispatch (group-sequential)
      data/guidelines/*.yaml checklist-as-data (CONSORT/STROBE/PRISMA/TRIPOD)
    kb/                    L1 — KB-provider
      contract.md            interface: query(claim) → graded evidence + provenance
      providers/             folder.py  obsidian.py  rag.py(stub)  cag.py(stub)
    guard/                 L3 — mode-guard
      egress_guard.py        reviewer-path network-block (empty allowlist)
    lib/                   shared: json_io, provenance, epistemic schema
    validate_*.{py,sh}     [exists]
  config/profile.example.md  [exists] + kb.backend, mode, language
  docs/  examples/  README  LICENSE  CHANGELOG  CONTRIBUTING   [exist]
```

**Isolation principle:** each `core/` file = one engine, CLI with JSON contract, testable
without a model and without network. KB adapters interchangeable behind one interface.
Guard is orthogonal — agents do not know about it; it runs per-mode.

---

## 4. Data flow

Common invariant: **every finding returns as an object `{claim, source_trace,
epistemic_status, confidence}`** — never a bare model-emitted number.

**Flow 1 — peer-review audit (Sovereign + Rigor, flagship)**

```
"review manuscript.docx" (mode: reviewer)
  → L3 guard/egress_guard.py   sets network-block, stamps mode=reviewer; egress attempt = hard fail
  → L2 agents/peer-reviewer.md (model-agnostic orchestration) dispatches deterministic calls:
      L0 core/citation_parse.py   → {citations, DOI, claim-supported?}
      L0 core/stat_run.py         → recompute p/CI, GRIM/GRIMMER
      L0 core/guideline_check.py  → CONSORT/STROBE gap-list from data/*.yaml
      L0 core/power_sample_size.py→ power sanity vs declared N
      L1 kb/providers/<backend>   → query(claim) → graded evidence + provenance (LOCAL only in reviewer-mode)
  → L0 core/epistemic_grade.py    → status + confidence + source_independence per finding (weakest-link)
  → peer-reviewer aggregates → report: findings, each with source_trace + status.
      Absences (no limitations, no sample-size in Methods) = findings, not silently filled.
```

The model (Opus *or* local Bielik/PLLuM via vLLM) only orchestrates and writes report
prose. All numbers, p-values, statuses come from `scripts/core/`.

**Flow 2 — statistician assumption-check (primary value)**

```
"was the t-test appropriate for these data?"
  → L2 agents/statistician.md
      L0 core/stat_run.py --check-assumptions
          normality (Shapiro), variances (Levene), independence, n/group
          → {assumption: met|violated, evidence, recommended_alternative}
      [if group-sequential/trial] L0 core/rbridge/gsdesign.R via dispatch
          → {spending function, boundaries, alpha-adjustment}
  → epistemic_grade.py → status (e.g. "violated normality" = operational_fact, conf 0.9)
  → "t-test inadequate — normality violated (Shapiro p<.01); recommend Mann-Whitney.
     [source: stat_run.py#assumptions]"
```

**Three flow invariants:**
1. **Provenance mandatory** — every finding carries `source: scripts/core/X.py#run-id` or
   `kb://<backend>/<doc>#L..` (format per author's CLAUDE.md `source: file.md#L123`).
2. **Weakest-link aggregation** — report status = min of component statuses.
3. **Egress is a property of mode, not agent** — reviewer-mode sealed in L3; author/curate
   mode allows network (research-scout, literature-search online).

---

## 5. Mode-guard & egress enforcement

Carrier of moat #1, so enforced technically — but **honest about its limits** (a plugin is
not a VM; it cannot seal the kernel). Defense-in-depth, strongest first:

1. **Mode declaration (profile + runtime stamp).** `profile.md: mode = reviewer | author`.
   reviewer-mode starts `guard/egress_guard.py` → sets `SCRIPTORIUM_OFFLINE=1`. Every L0/L1
   script reads the flag on start; if `=1` and KB backend is remote (`rag`) → **hard
   refuse, not silent fallback**. Local backends (`folder`/`obsidian`/`cag`) pass.
2. **Capability removal (no network tools in path).** reviewer-path agents
   (peer-reviewer, statistician) carry an explicit prompt-level ban on WebFetch/WebSearch;
   no L0 script in that path imports a network library (`requests`/`httpx`). Audited by test
   (import grep = empty).
3. **Process sandbox (opt-in, hardest).** `egress_guard.py` wraps calls in a network-less
   sandbox when available (`unshare -n` / firejail on Linux). When unavailable, the guard
   **does not pretend** — it logs `egress-block: best-effort only (levels 1+2)` and says so.

**Why not "just block the network":** a plugin has no kernel authority; faking full
isolation is worse than not claiming it (asymmetric risk — false confidence is dangerous).
Levels 1+2 remove every normal-operation egress path; level 3 gives a hard guarantee where
the environment permits (author's Linux + AMD does) without requiring it of every user.

**User-visible boundary disclosure:**
```
[guard] reviewer-mode: SCRIPTORIUM_OFFLINE=1
[guard] level 1 (refuse-remote-KB):  ACTIVE
[guard] level 2 (no-net-imports):    ACTIVE (audited)
[guard] level 3 (process sandbox):   ACTIVE (unshare -n)   | or: UNAVAILABLE, best-effort
```

---

## 6. Testing strategy

The architecture is built so the most important things are deterministic → testable
without a model or network. Test the kitchen (L0) hard, the waiter (L2) lightly.

```
L0 core/  — golden tests, DENSE                         ← seat of trust
  Each engine = input JSON + expected output JSON fixture pair.
  power_sample_size.py: textbook cases (Cohen) → exact N
  stat_run.py: non-normal dataset → assumption=violated, recommend Mann-Whitney
  guideline_check.py: stub manuscript missing 'limitations' → finding present
  citation_parse.py: exists-but-unsupporting citation → flagged
  epistemic_grade.py: 1 weak + 2 strong claims → overall status = weak (weakest-link)
  rbridge/gsdesign.R: O'Brien-Fleming example → boundaries match published table
  Goal: regression impossible — a changed number turns a test red immediately.

L1 kb/    — contract tests, MEDIUM
  Every adapter (folder/obsidian) must satisfy the same query()→evidence interface.
  One shared contract-test suite run against each adapter.
  rag/cag stubs: test that reviewer-mode raises hard-refuse.

L3 guard/ — behavior tests, MEDIUM (moat carrier)
  - reviewer-mode + remote KB → refusal (not silent fallback)
  - import audit: grep requests/httpx in reviewer-path = empty
  - sandbox unavailable → guard logs 'best-effort', does NOT pretend (key test)

L2 agents/skills — light, RARE
  No prose testing. Test:
  - structure validators (validate_structure.sh — exists)
  - smoke: agent calls the right L0 script with valid JSON (mock L0, assert call)
  - prompt lint: no WebFetch/WebSearch in reviewer-path agents
```

**Three quality gates (pre-push: flawless, zero junk):** golden L0 green; contract L1
green for every adapter; guard behavior incl. the honesty test.

**Deliberately NOT tested** (recorded so we never fake coverage): reviewer report prose
quality (judgment, no "correct" answer); real kernel-level network cut-off outside the
sandbox (level 3 best-effort — the test checks *honesty of the declaration*, not isolation
itself).

**Runner:** `pytest` (present in author's PJATK venv) for Python; a small shell harness for
R-bridge and guard. `scripts/run_tests.sh` collects everything; pre-push gate runs it whole.

---

## 7. Scope boundaries (v2)

**In v2:** layered architecture; deterministic L0 core; pluggable KB-provider (folder +
obsidian adapters, rag/cag stubs); mode-guard defense-in-depth; clinical-trial methodology
flagship (gsDesign R-dispatch); epistemic-status spine; carving/complement with
scientific-writer; roster of 4 agents + 8 skills (literature-search narrowed,
manuscript-imrad reframed).

**Deferred to v3:** contradiction-detection vs vault; deep KB integration (live rag/cag
adapters); full vLLM-first packaging.

**Out of scope (permanent):** generative auto-review; paywall bypass / piracy / mass
scraping; any path that uploads manuscript bytes to a cloud LLM.

---

## 8. Open items for the build plan

- Concrete JSON schema per L0 engine (input/output) — define before coding each engine.
- `profile.md` schema extension: `mode`, `kb.backend`, `language`, optional R availability flag.
- R-dispatch mechanism choice (subprocess `Rscript` vs `rpy2`) — subprocess preferred for isolation.
- Migration: which v0.1 skill bodies need rewriting to call L0 vs stay prose.
