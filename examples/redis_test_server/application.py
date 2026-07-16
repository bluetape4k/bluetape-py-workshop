from collections.abc import Callable

from bluetape.testcontainers import RedisServer

from .probe import RedisOrderStatusProbe, RedisProbeResult

ProbeFactory = Callable[..., RedisOrderStatusProbe]


def run_workshop(
    *,
    server: RedisServer,
    probe_factory: ProbeFactory = RedisOrderStatusProbe,
) -> RedisProbeResult:
    with server as running:
        probe = probe_factory(details=running.details)
        return probe.verify(order_id="ORD-1001", status="accepted")
