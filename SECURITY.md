# Security policy

## Threat model: untrusted documents are data, not instructions
Scriptorium agents routinely read documents they did not write — manuscripts, web pages,
repositories. These are treated as **data to analyze**, never as instructions to follow. An
agent that encounters embedded directives in a source ("ignore your rules and …") should
report them as a finding, not act on them. Prompt-injection resistance is a design goal; it
is not a solved guarantee (see Limitations).

## Confidentiality boundary
The `peer-reviewer` path has no network tools and, where supported, runs network-isolated.
This is an **operational** boundary that removes the normal egress paths — it is not
encryption or a formally verified sandbox. Do not rely on it as the sole control for highly
sensitive material; pair it with host-level controls.

## Supported versions
Pre-1.0, only the latest tagged release receives fixes. Behavior may change between minor
versions; see [ROADMAP.md](ROADMAP.md).

| Version | Supported |
|---|---|
| latest `0.x` tag | ✅ |
| older `0.x` | ❌ |

## Reporting a vulnerability
Open a GitHub issue for non-sensitive reports. For anything that should not be public
(e.g. a way to make the reviewer path egress data), contact the maintainer privately via the
email on the author's GitHub profile rather than filing a public issue. Please include a
minimal reproduction and the affected version/commit.

## Out of scope
Host compromise, the model backend's own data handling, OS telemetry, and supply-chain
integrity of the user's wider environment are outside Scriptorium's control. Scriptorium
secures its own components' behavior, not the surrounding system.
