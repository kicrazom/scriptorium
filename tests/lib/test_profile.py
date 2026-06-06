import pytest
from pathlib import Path
from scripts.lib import profile as P

FIX = Path(__file__).resolve().parents[1] / "fixtures" / "profile"


def test_no_profile_uses_defaults(tmp_path):
    merged, warnings = P.get_profile(cwd=tmp_path, home=tmp_path)
    assert merged["statistics"]["prefer_runtime"] == "python"   # universal default
    assert warnings == []


def test_project_profile_wins(tmp_path):
    proj = FIX / "project"
    merged, _ = P.get_profile(cwd=proj, home=FIX / "home")
    assert merged["statistics"]["prefer_runtime"] == "r"        # project overrides
    assert merged["style"]["explain_jargon"] is True


def test_global_profile_used_when_project_missing(tmp_path):
    merged, _ = P.get_profile(cwd=tmp_path, home=FIX / "home")
    assert merged["statistics"]["prefer_runtime"] == "none"     # from ~/.scriptorium


def test_defaults_fill_unset_fields(tmp_path):
    merged, _ = P.get_profile(cwd=FIX / "home", home=FIX / "home")
    # home profile only sets prefer_runtime; other sections come from defaults
    assert merged["epistemic"]["asymmetric_risk"] is False


def test_invalid_yaml_raises_clear_error():
    path = FIX / "badyaml" / ".scriptorium" / "profile.md"
    with pytest.raises(P.ProfileError):
        P.load_profile(path)


def test_unknown_section_warns_not_crashes():
    path = FIX / "unknown" / ".scriptorium" / "profile.md"
    merged, warnings = P.merge_with_defaults(P.load_profile(path))
    assert any("nonsense_section" in w for w in warnings)
    assert merged["statistics"]["prefer_runtime"] == "python"   # known field still applied


def test_extract_yaml_block_handles_no_block():
    assert P.extract_yaml_block("# just markdown, no code block") == ""
