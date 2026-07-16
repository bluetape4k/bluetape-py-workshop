from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_default_cli_emits_deterministic_safe_events() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "examples.bounded_payload_processing"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert completed.returncode == 0, completed.stderr
    events = [json.loads(line) for line in completed.stdout.splitlines()]
    assert [event["event"] for event in events] == [
        "profile_selected",
        "encoded",
        "decoded",
        "rejected",
    ]
    assert events[0] == {
        "event": "profile_selected",
        "format": "json",
        "trust_profile": "untrusted",
    }
    assert events[1]["compression"] == "gzip"
    assert events[1]["encoding"] == "base64url"
    assert type(events[1]["encoded_size"]) is int
    assert events[2] == {"event": "decoded", "result": "round_trip_ok"}
    assert events[3] == {
        "error": "CodecError",
        "event": "rejected",
        "stage": "encoding",
    }
    assert "ORDER-1001" not in completed.stdout
    assert "SKU-1" not in completed.stdout


def test_default_import_and_cli_do_not_import_fory() -> None:
    probe = f"""
import runpy
import sys
sys.path.insert(0, {str(ROOT)!r})
import examples.bounded_payload_processing
runpy.run_module('examples.bounded_payload_processing', run_name='__main__')
assert 'bluetape.serde.fory' not in sys.modules
assert 'pyfory' not in sys.modules
"""
    completed = subprocess.run(
        [sys.executable, "-I", "-c", probe],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert completed.returncode == 0, completed.stderr
