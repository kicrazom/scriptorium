from scripts.lib import provenance


def test_engine_trace_format():
    t = provenance.engine_trace("power_sample_size", run_id="r1", anchor="result")
    assert t == "scripts/core/power_sample_size.py#run=r1:result"


def test_kb_trace_format():
    t = provenance.kb_trace("obsidian", doc="Studies/x.md", anchor="L12-L20")
    assert t == "kb://obsidian/Studies/x.md#L12-L20"


def test_run_id_is_deterministic_from_seed():
    a = provenance.run_id(seed="abc")
    b = provenance.run_id(seed="abc")
    assert a == b and len(a) == 12
