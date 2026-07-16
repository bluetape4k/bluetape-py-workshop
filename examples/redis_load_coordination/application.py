from __future__ import annotations

import asyncio
from collections.abc import Callable
from contextlib import AsyncExitStack
from dataclasses import dataclass

from bluetape.cache import AsyncTTLCache, CacheStats
from bluetape.cache.redis import (
    AsyncRedisProvider,
    RedisCoordinationEvent,
    RedisEvent,
    RedisLoadOptions,
    RedisOperation,
    RedisOutcome,
    ResultEnvelopeCodec,
)
from bluetape.testcontainers import RedisServer

from examples.cached_product_catalog import AsyncProductLoader, ProductSummary

from .codec import ProductSummaryCodec
from .observer import CoordinationEventRecorder
from .service import RedisCatalogInstance

ProviderFactory = Callable[..., AsyncRedisProvider]
DEFAULT_PRODUCT = ProductSummary(
    product_id="SKU-42",
    name="Blue Mug",
    price_cents=1299,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class ScenarioResult:
    owner_value: ProductSummary
    follower_value: ProductSummary
    local_hit_value: ProductSummary
    loader_calls: int
    owner_events: tuple[RedisCoordinationEvent, ...]
    follower_events: tuple[RedisCoordinationEvent, ...]
    owner_stats: CacheStats
    follower_stats: CacheStats


class _ProviderOperationSignal:
    def __init__(self, operation: RedisOperation) -> None:
        self._operation = operation
        self._completed = asyncio.Event()

    def on_event(self, event: RedisEvent) -> None:
        if event.operation is self._operation and event.outcome is RedisOutcome.SUCCESS:
            self._completed.set()

    async def wait(self) -> None:
        await self._completed.wait()


def _require_url(value: object) -> str:
    if type(value) is not str:
        raise TypeError("redis_url must be an exact str")
    if not value or value != value.strip():
        raise ValueError("redis_url must be non-blank without surrounding whitespace")
    return value


def _coordination_options() -> RedisLoadOptions:
    return RedisLoadOptions(
        namespace="catalog:workshop:product-v1",
        lease_ttl=1.0,
        result_ttl=0.5,
        poll_interval=0.01,
        max_poll_interval=0.02,
        wait_timeout=2.0,
        max_attempts=3,
        max_polls=100,
        redis_io_timeout=0.6,
    )


async def _default_loader(product_id: str) -> ProductSummary:
    if product_id != DEFAULT_PRODUCT.product_id:
        raise LookupError("product is unavailable")
    return DEFAULT_PRODUCT


async def _cancel_tasks(tasks: tuple[asyncio.Task[ProductSummary], ...]) -> None:
    pending = tuple(task for task in tasks if not task.done())
    for task in pending:
        task.cancel()
    if pending:
        await asyncio.gather(*pending, return_exceptions=True)


async def run_scenario(
    redis_url: str,
    *,
    loader: AsyncProductLoader | None = None,
    provider_factory: ProviderFactory = AsyncRedisProvider.from_url,
) -> ScenarioResult:
    """Run one deterministic owner/follower/local-hit teaching scenario."""
    url = _require_url(redis_url)
    if loader is not None and not callable(loader):
        raise TypeError("loader must be callable or None")
    if not callable(provider_factory):
        raise TypeError("provider_factory must be callable")
    actual_loader = _default_loader if loader is None else loader
    loader_started = asyncio.Event()
    loader_release = asyncio.Event()
    loader_calls = 0

    async def controlled_loader(product_id: str) -> ProductSummary:
        nonlocal loader_calls
        loader_calls += 1
        loader_started.set()
        await loader_release.wait()
        return await actual_loader(product_id)

    owner_provider_signal = _ProviderOperationSignal(RedisOperation.SET_IF_ABSENT)
    follower_provider_signal = _ProviderOperationSignal(RedisOperation.SET_IF_ABSENT)
    owner_events = CoordinationEventRecorder()
    follower_events = CoordinationEventRecorder()
    tasks: tuple[asyncio.Task[ProductSummary], ...] = ()

    async with AsyncExitStack() as stack:
        owner_provider = await stack.enter_async_context(
            provider_factory(
                url,
                observer=owner_provider_signal,
                socket_connect_timeout=0.2,
                socket_timeout=0.3,
                retry_on_timeout=False,
            )
        )
        follower_provider = await stack.enter_async_context(
            provider_factory(
                url,
                observer=follower_provider_signal,
                socket_connect_timeout=0.2,
                socket_timeout=0.3,
                retry_on_timeout=False,
            )
        )
        codec = ResultEnvelopeCodec(payload_codec=ProductSummaryCodec())
        options = _coordination_options()
        owner = RedisCatalogInstance(
            cache=AsyncTTLCache(default_ttl=60.0, max_size=32),
            provider=owner_provider,
            loader=controlled_loader,
            codec=codec,
            options=options,
            observer=owner_events,
            local_ttl=30.0,
        )
        follower = RedisCatalogInstance(
            cache=AsyncTTLCache(default_ttl=60.0, max_size=32),
            provider=follower_provider,
            loader=controlled_loader,
            codec=codec,
            options=options,
            observer=follower_events,
            local_ttl=30.0,
        )
        owner_task = asyncio.create_task(owner.get_product(DEFAULT_PRODUCT.product_id))
        try:
            await loader_started.wait()
            follower_task = asyncio.create_task(follower.get_product(DEFAULT_PRODUCT.product_id))
            tasks = (owner_task, follower_task)
            await follower_provider_signal.wait()
            loader_release.set()
            owner_value, follower_value = await asyncio.gather(*tasks)
            local_hit_value = await follower.get_product(DEFAULT_PRODUCT.product_id)
            owner_stats, follower_stats = await asyncio.gather(owner.stats(), follower.stats())
        finally:
            loader_release.set()
            await _cancel_tasks(tasks or (owner_task,))

    return ScenarioResult(
        owner_value=owner_value,
        follower_value=follower_value,
        local_hit_value=local_hit_value,
        loader_calls=loader_calls,
        owner_events=owner_events.snapshot(),
        follower_events=follower_events.snapshot(),
        owner_stats=owner_stats,
        follower_stats=follower_stats,
    )


def run_workshop(
    *,
    server: RedisServer,
    loader: AsyncProductLoader | None = None,
) -> ScenarioResult:
    """Own one disposable Redis container around the async scenario."""
    with server as running:
        return asyncio.run(run_scenario(running.details.url, loader=loader))
