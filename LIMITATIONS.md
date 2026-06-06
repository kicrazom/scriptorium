# Limitations

Scriptorium is an early-stage tool with a deliberately narrow, honest scope. Read this
before relying on it for anything consequential.

## Not a replacement for expert judgement
Scriptorium assists a qualified researcher, reviewer, or statistician — it does not replace
one. Its agents surface issues and compute quantities; interpreting them is the user's job.

## Not a medical or clinical decision system
Nothing here is a diagnostic, dosing, or treatment tool. Clinical examples are illustrative.
Do not use any output to make a patient-care decision.

## The deterministic core is partial
Only a subset of the documented statistical designs is backed by a tested runtime engine
(see [STATUS.md](STATUS.md) for the exact matrix). Designs without an engine are handled as
**agent-guided** workflows — the agent reasons through the method and may run ad-hoc code,
which is not the same as a golden-tested engine. Treat agent-guided numbers as drafts to
verify, not as authoritative.

## LLM agents can still err
The agents are language-model driven. They can misread a document, mis-select a method, or
reason incorrectly, even with anti-hallucination conventions in place. The deterministic
engines exist precisely because model arithmetic is unreliable — but the agents that *call*
them are not infallible.

## Literature retrieval depends on available public sources
`research-scout` and `literature-search` see only what public APIs and search return. They
do not bypass paywalls, and coverage gaps in a source become coverage gaps in the result.

## Peer-review mode cannot verify online references by design
The `peer-reviewer` path is offline (no network tools) to preserve manuscript
confidentiality. The trade-off: it cannot check whether a cited reference exists or supports
a claim online. Reference verification is a separate, explicitly online step.

## Offline confidentiality is not cryptographic security
"Offline / no-egress" means the reviewer path has no network tools and (where supported) runs
under a network-isolating sandbox. It is a strong operational boundary, **not** an encryption
or formal-isolation guarantee. Host compromise, side channels, or a misconfigured environment
can still leak data. See [SECURITY.md](SECURITY.md) and [PRIVACY.md](PRIVACY.md).

## Configuration is convention until the parser lands
The `profile.md` resolution order is currently a documented convention each component follows
via its prompt. A shared, tested parser (`scripts/lib/profile.py`) is on the roadmap; until
then, inter-agent consistency is not mechanically enforced.
