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
