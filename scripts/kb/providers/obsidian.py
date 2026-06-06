"""KB provider: Obsidian vault — folder retrieval plus [[wikilink]] anchor awareness.

Delegates scanning to the folder provider, then enriches each evidence item with any
wikilink targets present in the matched line. Local, reviewer-safe.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from scripts.kb.providers import folder as _folder  # noqa: E402
from scripts.lib import provenance  # noqa: E402

_WIKILINK = re.compile(r"\[\[([^\]|#]+)")


def query(claim, path):
    result = _folder.query(claim, path)
    for ev in result["evidence"]:
        ev["links"] = _WIKILINK.findall(ev["snippet"])
        # re-stamp the trace backend as obsidian for provenance clarity
        ev["source"] = provenance.kb_trace("obsidian", doc=ev["doc"], anchor=f"L{ev['line']}")
    return result
