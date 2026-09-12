# scripts/core/citation_parse.py
"""L0 engine: structural citation hygiene (deterministic regex parse).

Extracts numeric in-text markers [n], cross-checks against the reference list:
  orphan_references   — references never cited in the body
  dangling_citations  — in-text markers with no matching reference index
This is STRUCTURAL hygiene, not semantic claim-support (does the source actually support
the claim) — that is a separate, deferred capability.
Input: {"body_text": <str>, "references": [<str>, ...]}.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.lib import json_io, provenance, epistemic  # noqa: E402

# A numeric marker group: starts with a digit, then only digits, commas, spaces, and
# hyphen/en-dash — so [1], [1,2,5], and [1-3]/[1–3] match, but [see 2] does not.
MARKER = re.compile(r"\[(\d[\d\s,–-]*)\]")
_RANGE = re.compile(r"(\d+)\s*[–-]\s*(\d+)")


def _expand(inner):
    """Expand one marker group's inner text into the set of integers it cites."""
    out = set()
    for part in inner.split(","):
        part = part.strip()
        r = _RANGE.fullmatch(part)
        if r:
            lo, hi = int(r.group(1)), int(r.group(2))
            if lo <= hi:
                out.update(range(lo, hi + 1))
        elif part.isdigit():
            out.add(int(part))
    return out


def parse(req):
    body = req["body_text"]
    refs = req["references"]
    n_refs = len(refs)

    cited = set().union(*(_expand(g) for g in MARKER.findall(body))) if MARKER.search(body) else set()
    markers = sorted(cited)
    orphan = [i for i in range(1, n_refs + 1) if i not in cited]
    dangling = [m for m in markers if m < 1 or m > n_refs]

    rid = provenance.run_id(seed=json.dumps({"b": len(body), "r": n_refs}, sort_keys=True))
    finding = epistemic.make_finding(
        claim=f"{len(orphan)} orphan reference(s), {len(dangling)} dangling citation(s)",
        status="operational_fact", confidence=1.0,
        source=provenance.engine_trace("citation_parse", run_id=rid, anchor="hygiene"),
    )
    return {
        "cited_markers": markers, "n_references": n_refs,
        "orphan_references": orphan, "dangling_citations": dangling, "finding": finding,
    }


def main():
    try:
        json_io.emit(json_io.ok(parse(json_io.read_input())))
    except Exception as exc:
        json_io.emit(json_io.error(str(exc)))


if __name__ == "__main__":
    main()
