"""KB provider: plain folder of markdown+frontmatter notes (local, reviewer-safe).

query(claim, path) scans *.md recursively, returns lines matching claim terms as graded
evidence. Each note's frontmatter `status:` (if present) becomes the evidence status; the
default is working_hypothesis. This is a keyword screen — a retrieval primitive, not a
semantic judge.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from scripts.lib import provenance, epistemic  # noqa: E402

import yaml  # noqa: E402

DEFAULT_STATUS = "working_hypothesis"


def _terms(claim):
    return {w.lower() for w in claim.split() if len(w) >= 4}


def _frontmatter_status(text):
    if not text.startswith("---"):
        return DEFAULT_STATUS
    end = text.find("\n---", 3)
    if end == -1:
        return DEFAULT_STATUS
    try:
        fm = yaml.safe_load(text[3:end]) or {}
    except yaml.YAMLError:
        return DEFAULT_STATUS
    status = fm.get("status", DEFAULT_STATUS)
    return status if status in epistemic.LADDER else DEFAULT_STATUS


def query(claim, path):
    terms = _terms(claim)
    root = Path(path)
    evidence = []
    for md in sorted(root.rglob("*.md")):
        text = md.read_text(encoding="utf-8")
        status = _frontmatter_status(text)
        rel = os.path.relpath(md, root)
        for lineno, line in enumerate(text.splitlines(), start=1):
            low = line.lower()
            if any(t in low for t in terms):
                evidence.append({
                    "doc": rel, "line": lineno, "snippet": line.strip(),
                    "status": status,
                    "source": provenance.kb_trace("folder", doc=rel, anchor=f"L{lineno}"),
                })

    if evidence:
        f_status, conf, claim_txt = "corroborated_inference", 0.7, \
            f"{len(evidence)} local passage(s) support the query"
    else:
        f_status, conf, claim_txt = "speculative_hypothesis", 0.2, \
            "no local support found"
    finding = epistemic.make_finding(
        claim=claim_txt, status=f_status, confidence=conf,
        source=provenance.kb_trace("folder", doc=str(path), anchor="query"),
        source_independence=len({e["doc"] for e in evidence}),
    )
    return {"evidence": evidence, "finding": finding}
