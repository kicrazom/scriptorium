# scripts/core/guideline_check.py
"""L0 engine: gap-check a manuscript against a reporting checklist (YAML data).

v2 detection is a deterministic keyword screen: an item is present if any of its keywords
appears (case-insensitive) in the manuscript text. This is a SCREEN (working_hypothesis),
not proof of adequate reporting — absence of a keyword is a reliable miss signal; presence
is a weak positive. Input: {"guideline": <name>, "manuscript_text": <str>}.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.lib import json_io, provenance, epistemic  # noqa: E402

import yaml  # noqa: E402

DATA = Path(__file__).resolve().parent / "data" / "guidelines"


def load_guideline(name):
    path = DATA / f"{name}.yaml"
    if not path.exists():
        raise ValueError(f"unknown guideline: {name!r}")
    return yaml.safe_load(path.read_text())


def check(req):
    name = req["guideline"]
    text = req["manuscript_text"].lower()
    spec = load_guideline(name)

    present, missing = [], []
    for it in spec["items"]:
        hit = any(kw.lower() in text for kw in it["keywords"])
        if hit:
            present.append(it["id"])
        else:
            missing.append({"id": it["id"], "item": it["item"]})

    rid = provenance.run_id(seed=json.dumps({"g": name, "n": len(text)}, sort_keys=True))
    finding = epistemic.make_finding(
        claim=f"{len(missing)} of {len(spec['items'])} {name.upper()} items not detected",
        status="working_hypothesis", confidence=0.6,
        source=provenance.engine_trace("guideline_check", run_id=rid, anchor=name),
    )
    return {"guideline": name, "present": present, "missing": missing, "finding": finding}


def main():
    try:
        json_io.emit(json_io.ok(check(json_io.read_input())))
    except Exception as exc:
        json_io.emit(json_io.error(str(exc)))


if __name__ == "__main__":
    main()
