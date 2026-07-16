import json

from examples.integrated_order_backend.__main__ import _run_scenario


async def test_cli_emits_exact_safe_two_order_scenario(capsys) -> None:
    await _run_scenario()
    captured = capsys.readouterr()
    events = [json.loads(line) for line in captured.out.splitlines()]

    assert captured.err == ""
    assert [event["event"] for event in events] == [
        "backend_started",
        "order_processed",
        "order_processed",
        "cache_stats",
        "backend_stopped",
    ]
    assert events[1]["line_count"] == 3
    assert events[2]["line_count"] == 2
    assert events[1]["total_cents"] == 45_400
    assert events[2]["total_cents"] == 31_700
    assert events[1]["warning_count"] == events[2]["warning_count"] == 1
    order_event_keys = {
        "event",
        "order_id",
        "line_count",
        "total_cents",
        "warning_count",
        "artifact_format",
        "trust_profile",
        "compression",
        "encoding",
        "encoded_size",
    }
    assert set(events[1]) == set(events[2]) == order_event_keys
    assert events[3] == {
        "event": "cache_stats",
        "hits": 1,
        "misses": 3,
        "loads": 3,
        "load_failures": 0,
        "inflight_loads": 0,
        "abandoned_loads": 0,
    }
    assert all("data" not in event and "recommendation" not in event for event in events)
