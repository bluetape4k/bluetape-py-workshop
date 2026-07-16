from __future__ import annotations

import pytest
from bluetape.testcontainers import (
    DEFAULT_REDIS_IMAGE,
    RedisConnectionDetails,
    RedisServer,
)

from examples.redis_test_server import (
    RedisOrderStatusProbe,
    RedisProbeResult,
    run_workshop,
)

pytestmark = pytest.mark.testcontainers


class ExpectedBodyError(RuntimeError):
    pass


class FailingProbe:
    def verify(self, *, order_id: str, status: str) -> RedisProbeResult:
        raise ExpectedBodyError(f"application failed for {order_id}:{status}")


def test_real_redis_readiness_round_trip_and_cleanup() -> None:
    captured_details: list[RedisConnectionDetails] = []

    def capturing_factory(*, details: RedisConnectionDetails) -> RedisOrderStatusProbe:
        captured_details.append(details)
        return RedisOrderStatusProbe(details=details)

    first_server = RedisServer()
    result = run_workshop(server=first_server, probe_factory=capturing_factory)

    assert DEFAULT_REDIS_IMAGE == "redis:8"
    assert result == RedisProbeResult(
        order_id="ORD-1001",
        status="accepted",
        ping_succeeded=True,
        write_succeeded=True,
        read_succeeded=True,
    )
    assert len(captured_details) == 1
    assert captured_details[0].port > 0
    assert captured_details[0].url == (
        f"redis://{captured_details[0].host}:{captured_details[0].port}"
    )
    assert first_server.running is False
    with pytest.raises(RuntimeError, match="not running"):
        _ = first_server.details

    def failing_factory(*, details: RedisConnectionDetails) -> FailingProbe:
        assert details.port > 0
        return FailingProbe()

    failing_server = RedisServer()
    with pytest.raises(ExpectedBodyError, match="application failed"):
        run_workshop(
            server=failing_server,
            probe_factory=failing_factory,  # type: ignore[arg-type]
        )
    assert failing_server.running is False
    with pytest.raises(RuntimeError, match="not running"):
        _ = failing_server.details

    fresh_server = RedisServer()
    with fresh_server as running:
        probe = RedisOrderStatusProbe(details=running.details)
        assert probe.read_status(order_id="ORD-1001") is None
        assert probe.verify(order_id="ORD-1001", status="accepted") == result

    assert fresh_server.running is False
