import json
import io
from scripts.lib import json_io


def test_read_input_from_stream():
    stream = io.StringIO('{"a": 1}')
    assert json_io.read_input(stream) == {"a": 1}


def test_ok_envelope_shape():
    env = json_io.ok({"n": 64})
    assert env["status"] == "ok"
    assert env["data"] == {"n": 64}


def test_error_envelope_shape():
    env = json_io.error("bad input")
    assert env["status"] == "error"
    assert env["message"] == "bad input"


def test_emit_writes_json(capsys):
    json_io.emit({"status": "ok", "data": {"x": 2}})
    out = capsys.readouterr().out
    assert json.loads(out) == {"status": "ok", "data": {"x": 2}}
