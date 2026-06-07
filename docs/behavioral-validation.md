# Behavioral validation (prompt-layer)

The deterministic core proves *computations*. This harness proves *behavior*: when an agent
ingests an untrusted document carrying an embedded directive, does it **refuse** to obey —
treating the directive as data to report, not an instruction to follow?

`injection_scan` (L0) detects injection patterns in text deterministically. That is necessary
but not sufficient: detection is not refusal. This harness closes the gap the roadmap tracked
as future work.

## Layers

| Layer | What | Where it runs |
|---|---|---|
| **Deterministic core** (default CI) | schemas, verdict logic, prompt assembly, judgement parsing, report redaction, backend availability — all model-free | every `pytest` run |
| **Model-gated harness** (`llm_judge`) | run a real agent backend on an adversarial case, score with a judge backend | only when `SCRIPTORIUM_RUN_LLM_JUDGE=1` |

The verdict is **recomputed deterministically** from the judge's scores against the case
thresholds — a judge that says "pass" while scoring below a floor is overridden to fail.

## Pluggable, model-agnostic backends

Backends (`scripts/behavioral/backends.py`) drive an agent runtime. Following the repo's
R-engine convention, a backend whose CLI is absent reports `available() == False` and the
harness **skips** it rather than failing.

- `claude_cli` — Claude Code headless (`claude -p`). Verified.
- `codex_cli` — Codex CLI (`codex exec`). Adapter present; argv **provisional** until a real
  codex install confirms the syntax. Skips where `codex` is absent.
- *(planned)* `local_vllm` — a local model endpoint, for fully sovereign offline runs.

**Cross-runtime agreement is a validity signal.** Running the same case through two
independent runtimes (e.g. `claude_cli` vs `codex_cli`) turns concordance into evidence: both
refusing is strong; divergence is itself a finding. Set the agent and judge backends
independently:

```bash
SCRIPTORIUM_RUN_LLM_JUDGE=1 \
SCRIPTORIUM_AGENT_BACKEND=claude_cli \
SCRIPTORIUM_JUDGE_BACKEND=codex_cli \
  pytest tests/behavioral/test_prompt_behavior.py -v
```

> **Same-family caveat.** When the agent and the judge are the same runtime family, the judge
> may share the agent's blind spots. The cross-runtime split above is the mitigation. Always
> record which backends produced a result.

## Running it

```bash
# default: the model-gated test is skipped
pytest tests/behavioral

# nightly / manual: run the real harness (needs the agent CLI on PATH)
SCRIPTORIUM_RUN_LLM_JUDGE=1 pytest tests/behavioral/test_prompt_behavior.py -v
```

Output: `tests/behavioral/_artifacts/behavior_report.json` (git-ignored). It is **commit-safe
by construction** — each entry records the document's SHA-256, never its text (an untrusted
document may be a confidential manuscript), plus case id, verdict, scores, and the judge's
short evidence quotes.

## Cases

Cases live in `tests/behavioral/fixtures/*.yaml` (schema:
`scripts/behavioral/schemas/behavior_case.schema.json`). Current coverage: 3 injection cases
across 3 agents (`peer-reviewer`, `research-scout`, `librarian`), all sharing the adversarial
`tests/fixtures/adversarial/injection_manuscript.md`.

## When a case fails

A behavioral failure is **not** asserted away in CI — the gated test records it and stays
green so a failure does not silently break unrelated runs. Per the project convention, each
genuine failure becomes a **regression fixture** (a new case pinning the failure mode) through
a human-gated step, then the agent prompt is hardened until it passes.
