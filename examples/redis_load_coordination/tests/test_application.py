from __future__ import annotations

import asyncio

import pytest

pytest.importorskip("bluetape.cache.redis")

from bluetape.cache.redis import AsyncRedisProvider, RedisCoordinationOutcome

from examples.cached_product_catalog import ProductSummary
from examples.redis_load_coordination.application import run_scenario
from examples.redis_load_coordination.tests.fakes import (
    FakeAsyncRedisProvider,
    SharedRedisBackend,
)


class ProviderFactory:
    def __init__(self) -> None:
        self.backend = SharedRedisBackend()
        self.providers: list[FakeAsyncRedisProvider] = []

    def __call__(self, url: str, **options: object) -> AsyncRedisProvider:
        assert url == "redis://fake:6379/0"
        provider = FakeAsyncRedisProvider(
            self.backend,
            observer=options["observer"],  # type: ignore[arg-type]
        )
        self.providers.append(provider)
        return provider


@pytest.mark.asyncio
async def test_scenario_owns_two_providers_and_proves_cold_reuse_and_local_hit() -> None:
    factory = ProviderFactory()
    product = ProductSummary(product_id="SKU-42", name="Blue Mug", price_cents=1299)
    calls = 0

    async def loader(_: str) -> ProductSummary:
        nonlocal calls
        calls += 1
        return product

    result = await run_scenario(
        "redis://fake:6379/0",
        loader=loader,
        provider_factory=factory,
    )

    assert result.owner_value == result.follower_value == result.local_hit_value == product
    assert result.loader_calls == calls == 1
    assert result.owner_events[-1].outcome is RedisCoordinationOutcome.LOADED
    assert result.follower_events[-1].outcome is RedisCoordinationOutcome.RESULT_REUSED
    assert result.owner_stats.loads == result.follower_stats.loads == 1
    assert result.follower_stats.hits == 1
    assert len(factory.providers) == 2
    assert all(provider.closed for provider in factory.providers)


@pytest.mark.asyncio
async def test_scenario_cancellation_closes_both_providers() -> None:
    factory = ProviderFactory()
    started = asyncio.Event()

    async def loader(_: str) -> ProductSummary:
        started.set()
        await asyncio.Event().wait()
        raise AssertionError("unreachable")

    task = asyncio.create_task(
        run_scenario(
            "redis://fake:6379/0",
            loader=loader,
            provider_factory=factory,
        )
    )
    await asyncio.wait_for(started.wait(), timeout=1.0)
    task.cancel()

    with pytest.raises(asyncio.CancelledError):
        await asyncio.wait_for(task, timeout=1.0)

    assert len(factory.providers) == 2
    assert all(provider.closed for provider in factory.providers)


@pytest.mark.asyncio
@pytest.mark.parametrize("url", [None, 42, "", " redis://fake:6379/0 "])
async def test_scenario_rejects_invalid_url_before_provider_creation(url: object) -> None:
    factory = ProviderFactory()

    with pytest.raises((TypeError, ValueError)):
        await run_scenario(url, provider_factory=factory)  # type: ignore[arg-type]

    assert factory.providers == []
