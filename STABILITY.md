# Stability & versioning policy

Scriptorium follows [SemVer](https://semver.org/). As of **v1.0.0**, the parts below are a
committed contract: they will not change incompatibly without a **major** version bump.

## Stable (contract — breaking change ⇒ major bump)

- **Engine invocation.** Every L0 engine is a CLI that reads one JSON object on stdin and writes
  one JSON object on stdout. Invocation is `python scripts/core/<engine>.py`.
- **Output envelope.** `{ "status": "ok"|"error", ... }`; on `ok` a `data` object is present and
  carries a graded `finding`; on `error` a `message` is present. Specified by
  `schemas/envelope.schema.json` and verified for every engine in `tests/test_envelope_contract.py`.
- **Finding shape.** `{ claim, status, confidence, source, source_independence }` with `status`
  drawn from the fixed epistemic ladder. Specified by `schemas/finding.schema.json`.
- **Power engine I/O.** `schemas/power_request.schema.json` / `power_response.schema.json`.
- **Profile resolution.** `./.scriptorium/profile.md` → `~/.scriptorium/profile.md` → defaults,
  via `scripts/lib/profile.py` (and its CLI). Schema: `schemas/profile.schema.json`.
- **Provenance.** Every finding carries a `source` trace; numbers come from engines, never the model.

## Evolving (may change in a minor release, backwards-compatibly)

- **Additive engine coverage** — new power families, new `stat_run` ops, new guidelines, new
  engines. Adding fields to a `data` object is minor (consumers must tolerate unknown fields).
- **Prompt-layer wording** — agent/skill instructions are refined continuously; their *behaviour
  contract* (tools granted, privacy boundary) is documented in `STATUS.md`.
- **The LLM-judged behavioural harness** (does an agent refuse an injection?) — experimental,
  not part of the stable contract.

## Deprecation

A capability slated for removal is marked **deprecated** in `CHANGELOG.md` and `STATUS.md` for at
least one minor release before removal, which then happens only in a major bump.

## What 1.0.0 does NOT claim

1.0.0 means the **deterministic-core contract is stable**, not that the tool is feature-complete
or that the model-driven prompt layer is infallible. Read `LIMITATIONS.md` — it is still not a
medical decision system and not a replacement for expert review.
