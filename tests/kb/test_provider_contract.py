import importlib
import pytest

PROVIDERS = ["scripts.kb.providers.folder", "scripts.kb.providers.obsidian"]


def _vault(tmp_path):
    (tmp_path / "n.md").write_text(
        "---\nstatus: corroborated_inference\n---\n"
        "Hypoxemia relates to [[gas-exchange]] in COPD.\n"
    )
    return tmp_path


@pytest.mark.parametrize("modname", PROVIDERS)
def test_query_contract_shape(modname, tmp_path):
    mod = importlib.import_module(modname)
    out = mod.query("hypoxemia gas-exchange COPD", str(_vault(tmp_path)))
    # every provider returns the same envelope shape
    assert set(out.keys()) == {"evidence", "finding"}
    assert isinstance(out["evidence"], list)
    for ev in out["evidence"]:
        assert {"doc", "line", "snippet", "status", "source"} <= set(ev.keys())
    f = out["finding"]
    assert {"claim", "status", "confidence", "source", "source_independence"} == set(f.keys())


def test_obsidian_extracts_wikilinks(tmp_path):
    from scripts.kb.providers import obsidian
    out = obsidian.query("hypoxemia gas-exchange COPD", str(_vault(tmp_path)))
    assert any("gas-exchange" in ev.get("links", []) for ev in out["evidence"])
