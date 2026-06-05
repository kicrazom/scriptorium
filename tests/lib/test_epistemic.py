import pytest
from scripts.lib import epistemic


def test_ladder_order():
    assert epistemic.rank("contradicted") < epistemic.rank("speculative_hypothesis")
    assert epistemic.rank("speculative_hypothesis") < epistemic.rank("canonical_fact")


def test_unknown_status_raises():
    with pytest.raises(ValueError):
        epistemic.rank("nonsense")


def test_weakest_link_picks_lowest_status():
    statuses = ["operational_fact", "working_hypothesis", "canonical_fact"]
    assert epistemic.weakest_link(statuses) == "working_hypothesis"


def test_weakest_link_contradicted_dominates():
    statuses = ["canonical_fact", "contradicted"]
    assert epistemic.weakest_link(statuses) == "contradicted"


def test_weakest_link_empty_raises():
    with pytest.raises(ValueError):
        epistemic.weakest_link([])


def test_make_finding_shape():
    f = epistemic.make_finding(
        claim="t-test inadequate",
        status="operational_fact",
        confidence=0.9,
        source="scripts/core/stat_run.py#run=x:assumptions",
        source_independence=1,
    )
    assert f == {
        "claim": "t-test inadequate",
        "status": "operational_fact",
        "confidence": 0.9,
        "source": "scripts/core/stat_run.py#run=x:assumptions",
        "source_independence": 1,
    }
