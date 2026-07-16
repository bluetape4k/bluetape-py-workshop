from __future__ import annotations

import pytest
from bluetape.testcontainers import RedisServer

pytest.importorskip("bluetape.cache.redis")

from examples.redis_load_coordination.application import run_workshop

pytestmark = pytest.mark.testcontainers


class ExpectedBodyError(RuntimeError):
    pass


def test_real_redis_coordination_and_container_cleanup() -> None:
    server = RedisServer()
    result = run_workshop(server=server)

    assert result.loader_calls == 1
    assert result.owner_value == result.follower_value == result.local_hit_value
    assert result.follower_stats.hits == 1
    assert server.running is False

    failing_server = RedisServer()

    async def fail(_: str):
        raise ExpectedBodyError("application body failed")

    with pytest.raises(ExpectedBodyError, match="application body failed"):
        run_workshop(server=failing_server, loader=fail)
    assert failing_server.running is False

    fresh_server = RedisServer()
    fresh = run_workshop(server=fresh_server)
    assert fresh.loader_calls == 1
    assert fresh_server.running is False
