import json
import subprocess
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).parents[3]


def test_module_prints_the_deterministic_cache_scenario() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "examples.cached_product_catalog"],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    lines = [json.loads(line) for line in completed.stdout.splitlines() if line]
    assert [line["event"] for line in lines] == [
        "sync_miss",
        "sync_hit",
        "sync_expired_reload",
        "sync_eviction",
        "sync_loader_failed",
        "sync_recovered",
        "async_miss",
        "async_hit",
        "sync_stats",
        "async_stats",
    ]
    assert completed.stderr == ""

    for line in lines[:4] + lines[5:8]:
        assert set(line) == {"event", "mode", "name", "price_cents", "product_id"}
        assert line["product_id"] == line["product_id"].upper()

    assert lines[4] == {
        "error_code": "loader_unavailable",
        "event": "sync_loader_failed",
        "mode": "sync",
    }
    assert lines[-2]["mode"] == "sync"
    assert lines[-1]["mode"] == "async"
    for stats in lines[-2:]:
        assert stats["loads"] >= 1
        assert stats["misses"] >= 1
        assert stats["inflight_loads"] == 0
