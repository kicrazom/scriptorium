"""L0 engine: scan an *authored instruction* for directives that steer the evidence base.

Companion to injection_scan, and deliberately NOT the same check:

    injection_scan                    evidence_selection_neutrality
    -------------------------------   ----------------------------------------------
    Protects the MODEL from hostile   Protects the USER (and the record) from an
    text.                             instruction that is perfectly authorised.
    "Is this instruction from an      "Does this instruction, from a legitimate
     UNAUTHORISED source?"             author, distort what counts as evidence?"

A prompt can be syntactically clean, come from the project owner, and execute exactly as
designed — and still tell the system to prove a foregone conclusion, cite only supportive
sources, drop the limitations, or hide that AI was used. That is not a security
vulnerability; it is an abuse of the orchestration layer, and it is the failure mode that
produces systematically dishonest science. injection_scan cannot see it, because nothing
about it is unauthorised.

Scope note: this engine screens INSTRUCTIONS (prompts, skill bodies, task specs, reviewer
requests) — not manuscripts. Steering language *quoted* inside a manuscript under review is
data, not a directive; run this on what you are told to do, not on what you are asked to read.

Input  (stdin JSON): {"text": "<instruction text>"}
Output (stdout JSON): {steering: [{pattern, category, severity, line, snippet}],
                       verdict, risk_score, finding}

HEURISTIC, and the limits are real: fixed patterns catch blunt phrasing and miss polite
phrasing, and a clean scan proves nothing. Treat a hit as a finding to escalate, and a miss
as silence — not as a certificate of neutrality.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.lib import json_io, provenance, epistemic  # noqa: E402

# Categories that make the run FAIL outright: each one, if obeyed, fabricates or suppresses
# evidence. There is no legitimate research instruction that needs them.
BLOCKING = {
    "foregone_conclusion",
    "source_cherry_picking",
    "statistical_steering",
    "citation_coercion",
    "disclosure_evasion",
}
# Categories that warrant human review but have occasional benign readings
# (e.g. an editor legitimately asking to tighten hedging in an over-hedged draft).
REVIEWABLE = {"uncertainty_suppression", "spin_directive"}

# (label, category, regex). Targeted imperative phrasings, not bare keywords: the cost of a
# false positive here is a needless escalation, which is cheap; the cost of a false negative
# is dishonest output, which is not.
PATTERNS = [
    # --- foregone conclusion: the answer is fixed before the evidence is consulted ---
    # inflections matter: "so that it proves our hypothesis" is the same instruction as
    # "prove our hypothesis", and a reviewer would not accept the difference as exculpatory.
    ("prove-the-claim", "foregone_conclusion",
     r"\b(?:prove|demonstrate|establish|confirm|validate)(?:s|d|n)?\s+(?:that\s+)?(?:our|my|the)\s+(?:hypothesis|claim|thesis|theory|drug|method|model|approach|product|intervention)\b"),
    ("show-it-works", "foregone_conclusion",
     r"\b(?:show|demonstrate)(?:s|d|ing)?\s+(?:that\s+)?(?:it|this|our|the)\s+\w*\s*(?:works|is\s+effective|is\s+superior|is\s+better|outperforms)\b"),
    ("conclusion-preset", "foregone_conclusion",
     r"\b(?:the\s+)?conclusion\s+(?:must|should|has\s+to)\s+be\b"),
    ("must-support", "foregone_conclusion",
     r"\b(?:results?|findings?|analysis|review)\s+(?:must|should)\s+support\b"),
    ("always-favourable", "foregone_conclusion",
     r"\balways\s+(?:present|portray|describe|frame)\s+[^\n]{0,40}\b(?:positively|favou?rably|in\s+a\s+positive\s+light)\b"),

    # --- source cherry-picking: the evidence base is filtered to fit ---
    ("cite-only-supportive", "source_cherry_picking",
     r"\b(?:cite|include|use|select)\s+only\s+(?:studies|papers|sources|references|evidence|articles|trials)\s+(?:that|which)\s+(?:support|agree|confirm|favou?r|back)\b"),
    ("exclude-contradictory", "source_cherry_picking",
     r"\b(?:exclude|omit|ignore|leave\s+out|discard|skip)\s+(?:any\s+|all\s+)?(?:studies|papers|sources|references|evidence|trials|results?|findings?|data)\s+(?:that|which)\s+(?:contradict|disagree|conflict|oppose|do\s+not\s+support|undermine|challenge)\b"),
    ("omit-negative", "source_cherry_picking",
     r"\b(?:omit|exclude|ignore|suppress|leave\s+out|do\s+not\s+(?:report|mention|include))\s+(?:the\s+)?(?:negative|null|non-?significant|unfavou?rable|contrary|disconfirming)\s+(?:results?|findings?|studies|trials|evidence|data|outcomes?)\b"),
    ("only-favourable-outcomes", "source_cherry_picking",
     r"\breport\s+only\s+(?:the\s+)?(?:outcomes?|endpoints?|results?|analyses)\s+(?:that|which)\s+(?:reached|achieved|were)\b"),

    # --- statistical steering: torture the analysis until it confesses ---
    ("find-significance", "statistical_steering",
     r"\b(?:find|obtain|get|produce|achieve|reach)\s+(?:a\s+)?(?:statistical(?:ly)?\s+)?significan(?:t|ce)\b"),
    ("until-significant", "statistical_steering",
     r"\b(?:adjust|tweak|change|try|vary|re-?run|reanalyse|reanalyze)\s+[^\n]{0,60}\buntil\s+[^\n]{0,30}\b(?:significant|p\s*<|works|positive)\b"),
    ("pick-favourable-test", "statistical_steering",
     r"\b(?:choose|use|pick|select)\s+(?:the\s+|whichever\s+)?(?:test|model|method|analysis|covariates?|subgroup)\s+(?:that|which)\s+(?:gives?|yields?|produces?|shows?|makes?)\b"),
    ("drop-inconvenient-data", "statistical_steering",
     r"\b(?:drop|remove|exclude|delete)\s+(?:the\s+)?(?:outliers?|cases?|patients?|subjects?|data\s+points?)\s+(?:that|which|until)\s+[^\n]{0,40}\b(?:significan|improve|fit|help)\b"),

    # --- citation coercion: references demanded, not argued for ---
    ("cite-these-ids", "citation_coercion",
     r"\b(?:cite|add|include|insert)\s+(?:the\s+following|these)\s+[^\n]{0,40}\b(?:PMID|DOI|PMC)\b"),
    ("cite-my-work", "citation_coercion",
     r"\b(?:cite|add|include)\s+(?:my|our)\s+(?:own\s+)?(?:papers?|work|publications?|articles?|studies)\b[^\n]{0,40}\b(?:regardless|whether\s+or\s+not|even\s+if|without)\b"),
    ("citation-quota", "citation_coercion",
     r"\b(?:add|include|insert)\s+at\s+least\s+\d+\s+(?:citations?|references?)\s+(?:to|from)\b"),

    # --- disclosure evasion: hide the machinery or the conflict ---
    ("conceal-ai", "disclosure_evasion",
     r"\b(?:do\s+not|don'?t|never)\s+(?:disclose|declare|mention|reveal|state|acknowledge)\s+(?:that\s+)?[^\n]{0,30}\b(?:AI|LLM|GPT|Claude|generative\s+(?:AI|model)|language\s+model)\b"),
    ("conceal-coi", "disclosure_evasion",
     r"\b(?:do\s+not|don'?t|never|avoid)\s+(?:disclose|declare|mention|reveal|state)\s+(?:the\s+|any\s+|our\s+)?(?:conflict\s+of\s+interest|competing\s+interests?|funding|sponsor|COI)\b"),
    ("hide-method-change", "disclosure_evasion",
     r"\b(?:do\s+not|don'?t|never)\s+(?:tell|inform|mention\s+to|disclose\s+to)\s+(?:the\s+)?(?:user|reader|editor|reviewer)\s+(?:that|about)\b"),

    # --- uncertainty suppression: the caveats are edited out ---
    ("drop-limitations", "uncertainty_suppression",
     r"\b(?:remove|delete|drop|omit|cut|do\s+not\s+(?:include|write|add))\s+(?:the\s+|any\s+|all\s+)?(?:limitations?|caveats?|weaknesses|uncertaint(?:y|ies))\b"),
    ("no-hedging", "uncertainty_suppression",
     r"\b(?:remove|drop|avoid|eliminate|no)\s+(?:the\s+|all\s+|any\s+)?(?:hedg(?:e|ing|es)|qualifiers?|tentative\s+language)\b"),
    ("state-as-fact", "uncertainty_suppression",
     r"\b(?:state|present|write|report|describe)\s+(?:it|this|the\s+\w+)\s+as\s+(?:an?\s+)?(?:established\s+)?(?:fact|certainty|proven|definitive)\b"),

    # --- spin: non-significant reframed as promising ---
    ("spin-null", "spin_directive",
     r"\b(?:frame|present|describe|spin|position|portray)\s+(?:the\s+)?(?:non-?significant|null|negative|inconclusive|failed)\s+[^\n]{0,30}\b(?:as|positively|favou?rably)\b"),
    ("emphasise-trend", "spin_directive",
     r"\b(?:emphasi[sz]e|stress|highlight|play\s+up)\s+(?:the\s+)?(?:trend|near-?significan|promising)\b[^\n]{0,40}\b(?:instead|rather\s+than|not\s+the)\b"),
]
_COMPILED = [(label, cat, re.compile(rx, re.IGNORECASE)) for label, cat, rx in PATTERNS]


def _severity(category):
    return "critical" if category in BLOCKING else "warning"


def scan(text):
    hits = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        for label, category, rx in _COMPILED:
            if rx.search(line):
                hits.append({
                    "pattern": label,
                    "category": category,
                    "severity": _severity(category),
                    "line": lineno,
                    "snippet": line.strip()[:200],
                })
    return hits


def assess(hits):
    """Map hits to a verdict and a 0-4 risk score.

    0 none | 1-2 reviewable steering | 3 blocking steering | 4 blocking across >1 category
    (a prompt that both fixes the conclusion and filters the sources is not a slip).
    """
    cats = {h["category"] for h in hits}
    blocking = cats & BLOCKING
    if not hits:
        return "pass", 0
    if not blocking:
        return "review", 1 if len(hits) == 1 else 2
    return "fail", 4 if len(blocking) > 1 else 3


def compute(req):
    text = req["text"]
    hits = scan(text)
    verdict, risk = assess(hits)
    rid = provenance.run_id(seed=json.dumps({"n": len(text), "h": len(hits)}, sort_keys=True))
    source = provenance.engine_trace("evidence_selection_neutrality", run_id=rid, anchor="scan")

    if verdict == "fail":
        cats = sorted({h["category"] for h in hits if h["category"] in BLOCKING})
        claim = (f"instruction contains evidence-steering directives ({', '.join(cats)}) — "
                 f"obeying them would distort the evidence base; refuse and escalate")
        confidence = 0.75
    elif verdict == "review":
        claim = (f"{len(hits)} directive(s) may narrow or soften the evidence base — "
                 f"human review required before the instruction is executed")
        confidence = 0.55
    else:
        claim = ("no known evidence-steering patterns detected (a heuristic screen — "
                 "does not establish that the instruction is neutral)")
        confidence = 0.6

    finding = epistemic.make_finding(
        claim=claim, status="working_hypothesis", confidence=confidence, source=source)
    return {"steering": hits, "verdict": verdict, "risk_score": risk, "finding": finding}


def main():
    try:
        json_io.emit(json_io.ok(compute(json_io.read_input())))
    except Exception as exc:
        json_io.emit(json_io.error(str(exc)))


if __name__ == "__main__":
    main()
