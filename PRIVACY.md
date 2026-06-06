# Privacy model

Scriptorium is built local-first. Its strongest guarantee is around **manuscript review**,
where confidentiality is a professional obligation (e.g. COPE peer-review ethics).

## Local profile
Personalization lives in a `profile.md` you create (`./.scriptorium/` or `~/.scriptorium/`).
It is yours, kept out of version control, and never transmitted by any component.

## Offline peer-review mode
The `peer-reviewer` agent is granted **no network tools** (no WebFetch / WebSearch / MCP).
It reads the manuscript, reasons, and returns a report; it has no mechanism to send the
manuscript anywhere. Where the host supports it, the reviewer path can additionally run under
a network-isolating sandbox. This is an operational boundary, not cryptographic isolation —
see [SECURITY.md](SECURITY.md) and [LIMITATIONS.md](LIMITATIONS.md).

## Read-only retrieval agents
`research-scout` returns proposals and never writes to your knowledge base; the human applies
any change. Retrieval uses public metadata, previews, and public reviews only.

## No manuscript indexing
A manuscript under review is privileged material. It is **never** added to a knowledge base,
index, or map-of-content. The review is returned to you to save next to the manuscript, not
catalogued.

## No shadow-library links by default
No paywall bypass, no piracy, no ToS-violating scraping. Where a shadow-library resolver is
offered at all, it is opt-in and clearly labelled — never an automatic fetch.

## What still depends on the host environment
Scriptorium runs inside your Claude Code environment. Anything that environment logs, caches,
or transmits (the model backend, your shell history, OS-level telemetry) is outside
Scriptorium's control. The privacy guarantees above concern Scriptorium's own components, not
the surrounding host.
