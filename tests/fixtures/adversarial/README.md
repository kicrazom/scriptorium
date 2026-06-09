# Adversarial fixtures

Inputs that try to subvert or mislead an agent. They exist to prove the **deterministic**
defenses work, and to be honest about what is *not* yet automatically tested.

## What is deterministically tested (in CI)

| Fixture | Engine | Asserted |
|---|---|---|
| `injection_manuscript.md` | `core/injection_scan` | embedded "ignore previous instructions" / role-reassign / reveal-prompt patterns are flagged (`tests/core/test_injection_scan.py`) |
| `injection_append_verbatim.md` | `core/injection_scan` | forced verbatim-output directive flagged (`append-verbatim`) |
| `injection_citation_laundering.md` | `core/injection_scan` | citation-laundering directive flagged (`citation-injection`) |
| `injection_tool_exfil.md` | `core/injection_scan` | command-exec + exfiltration flagged (`exfil-command`, `exfil-network`) |
| `injection_obfuscated.md` | `core/injection_scan` | base64 "decode and follow" payload flagged (`decode-execute`) |
| `clean_manuscript.md` | `core/injection_scan` | no false positives on legitimate prose |

`injection_scan` operationalises the [SECURITY.md](../../../SECURITY.md) threat model —
**untrusted documents are data, not instructions**. It is a *heuristic screen*: a hit is a
flag for human review (`working_hypothesis`), never a confident verdict, and the absence of a
hit does not prove a document is safe. Novel injections evade fixed patterns by design.

Structural **fake-citation** detection (orphan references, dangling in-text markers) is covered
deterministically by `core/citation_parse` (`tests/core/test_citation_parse.py`).

## What is NOT automatically tested yet (manual / LLM-judged)

These concern the **prompt layer** — how an agent *behaves* when it reads adversarial input.
The output is model-generated prose, so there is no golden answer to assert; evaluating it
needs a human or an LLM-judge harness. They are tracked honestly as future work, **not** as
tested guarantees:

- Whether `peer-reviewer`, reading `injection_manuscript.md`, actually **refuses** the embedded
  directive and reports it as a finding (rather than recommending "accept").
- Sample peer-review reports for the fixture corpus.
- A reporting-guideline behavioural fixture set.

The recommended workflow today: an agent that ingests untrusted text runs `injection_scan`
first and treats any hit as a finding to report. The LLM-judged behavioural harness is planned
(see [../../../ROADMAP.md](../../../ROADMAP.md)).
