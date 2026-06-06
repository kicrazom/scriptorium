# Architecture

Scriptorium is a **layered** Claude Code plugin. The point of the layering is to keep the
trustworthy parts (deterministic, tested) separate from the judgement parts (model-reasoned),
and to make the privacy boundary explicit.

```
User request
   │
   ▼
L2  Agent / skill  (prompt layer — model-reasoned orchestration)
   │   peer-reviewer · statistician · librarian · research-scout · 8 skills
   │
   ├─ Policy boundary (per component, by granted tools)
   │     read-only / offline   →  Read, Grep, Glob        (e.g. peer-reviewer: zero egress)
   │     web-enabled           →  +WebSearch, WebFetch    (e.g. research-scout, author mode)
   │     compute-enabled       →  +Bash                   (e.g. statistician → runs engines)
   │
   ▼
L0  Deterministic core  (tested Python engines — invoked as JSON-in/JSON-out CLIs)
   │   power_sample_size · stat_run · guideline_check · citation_parse · epistemic_grade
   │   interim_boundaries→R/gsDesign · grimmer→R/scrutiny · injection_scan
   │
L1  KB-provider  (folder / obsidian / rag·cag stubs — query(claim)→graded evidence)
   │
L3  Mode-guard  (orthogonal — reviewer path: offline, network-sandboxed where supported)
   │
   ▼
JSON envelope:  { status, data, finding{ claim, status, confidence, source } }
   │            every number carries a provenance trace; absences are reported, not filled
   ▼
Human-reviewed output  (the human approves; nothing auto-written to the knowledge base)
```

## Why each layer

- **L0 deterministic core** — numbers (power, p-values, GRIM/GRIMMER, boundaries) come from
  tested engines, never from the model. Each is a `python scripts/core/<engine>.py` CLI with a
  JSON contract (see `schemas/`). R-backed engines dispatch to the reference implementations
  (`gsDesign`, `scrutiny`) rather than reimplementing subtle algorithms.
- **L1 KB-provider** — one `query()` contract, pluggable backend (`profile.kb.backend`). Remote
  backends are refused on the reviewer path by L3.
- **L2 prompt layer** — agents/skills decide *what* to ask and *how* to phrase findings; they
  call L0/L1 for anything quantitative or factual. Model-agnostic (Opus or a local model).
- **L3 mode-guard** — defense-in-depth for the Sovereign reviewer path; honest about what it
  can and cannot enforce (it never claims isolation it did not apply). See `SECURITY.md`.

## The two invariants

1. **Provenance mandatory** — every finding carries a `source` (engine run id or `kb://…`).
2. **Graduated epistemic status** — findings are labelled speculative → … → canonical (+
   contradicted), never a binary fact/inference split. Heuristic screens (injection_scan,
   guideline keyword check) stay `working_hypothesis` on purpose.

## What is tested vs reasoned

`STATUS.md` draws the exact line: the deterministic core (L0) + libraries (L1 contract, lib/)
are unit/golden-tested and CI-gated; the prompt layer (L2) is judgement, validated by structure
checks, prompt-lint, and the adversarial fixture corpus (`tests/fixtures/adversarial/`) — with
the behavioural "does the agent refuse an injection?" harness tracked honestly as future work.
