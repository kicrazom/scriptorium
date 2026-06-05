"""JSON I/O for L0 engines: read a request, emit a result/error envelope."""
import json
import sys


def read_input(stream=None):
    """Parse a JSON object from a text stream (default: stdin)."""
    stream = stream if stream is not None else sys.stdin
    return json.load(stream)


def ok(data):
    """Build a success envelope."""
    return {"status": "ok", "data": data}


def error(message):
    """Build an error envelope."""
    return {"status": "error", "message": message}


def emit(envelope, stream=None):
    """Write an envelope as JSON to a stream (default: stdout)."""
    stream = stream if stream is not None else sys.stdout
    json.dump(envelope, stream)
    stream.write("\n")
