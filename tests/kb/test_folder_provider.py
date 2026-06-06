from scripts.kb.providers import folder


def _make_vault(tmp_path):
    note = tmp_path / "study.md"
    note.write_text(
        "---\nstatus: operational_fact\n---\n"
        "# Capnography\n"
        "Transcutaneous PCO2 correlates with arterial values in stable patients.\n"
        "Unrelated line about coffee.\n"
    )
    return tmp_path


def test_folder_finds_supporting_line(tmp_path):
    vault = _make_vault(tmp_path)
    out = folder.query("transcutaneous PCO2 correlation", str(vault))
    assert len(out["evidence"]) >= 1
    ev = out["evidence"][0]
    assert ev["doc"] == "study.md"
    assert ev["status"] == "operational_fact"        # read from frontmatter
    assert ev["source"].startswith("kb://folder/study.md#L")
    assert out["finding"]["status"] == "corroborated_inference"


def test_folder_no_match_is_speculative(tmp_path):
    vault = _make_vault(tmp_path)
    out = folder.query("quantum gravity entanglement", str(vault))
    assert out["evidence"] == []
    assert out["finding"]["status"] == "speculative_hypothesis"
