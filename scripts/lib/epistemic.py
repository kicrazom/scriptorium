"""Graduated epistemic-status spine: the lingua franca every engine emits.

Statuses, weakest-to-strongest (contradicted sits below the ladder as the weakest of all):
    contradicted < speculative_hypothesis < working_hypothesis
        < corroborated_inference < operational_fact < canonical_fact
"""

LADDER = [
    "contradicted",
    "speculative_hypothesis",
    "working_hypothesis",
    "corroborated_inference",
    "operational_fact",
    "canonical_fact",
]
_RANK = {s: i for i, s in enumerate(LADDER)}


def rank(status):
    """Integer rank of a status; higher = stronger. Raises ValueError if unknown."""
    if status not in _RANK:
        raise ValueError(f"unknown epistemic status: {status!r}")
    return _RANK[status]


def weakest_link(statuses):
    """Aggregate a list of statuses to the weakest one (report = min)."""
    if not statuses:
        raise ValueError("weakest_link requires at least one status")
    return min(statuses, key=rank)


def make_finding(claim, status, confidence, source, source_independence=1):
    """Build a finding object. Validates status; keeps the canonical key order."""
    rank(status)  # validate
    return {
        "claim": claim,
        "status": status,
        "confidence": confidence,
        "source": source,
        "source_independence": source_independence,
    }
