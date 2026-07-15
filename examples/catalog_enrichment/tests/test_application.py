import json
import socket
import subprocess
import sys

from examples.catalog_enrichment.__main__ import main


def test_runnable_example_is_deterministic() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "examples.catalog_enrichment"],
        check=True,
        capture_output=True,
        text=True,
        timeout=2,
    )
    payload = json.loads(completed.stdout)
    assert completed.stderr == ""
    assert [item["product_id"] for item in payload] == ["SKU-2", "SKU-1", "SKU-2"]
    assert payload[0] == payload[2]
    assert payload[1]["warnings"] == [
        {
            "code": "optional_record_missing",
            "message": "recommendation is unavailable",
            "product_id": "SKU-1",
            "provider": "recommendations",
        }
    ]


async def test_main_uses_no_network(monkeypatch, capsys) -> None:
    def deny_socket(*args, **kwargs):
        raise AssertionError("the in-memory example must not open a socket")

    monkeypatch.setattr(socket, "socket", deny_socket)
    await main()
    assert json.loads(capsys.readouterr().out)
