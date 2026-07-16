import asyncio
from dataclasses import FrozenInstanceError

import pytest
from bluetape.cache import AsyncTTLCache, CacheStats, TTLCache
from bluetape.testing import eventually_async

from examples.cached_product_catalog import (
    AsyncProductCatalogService,
    ProductSummary,
    SyncProductCatalogService,
)


class ManualClock:
    def __init__(self) -> None:
        self.now = 0

    def __call__(self) -> int:
        return self.now

    def advance(self, nanoseconds: int) -> None:
        self.now += nanoseconds


def product(product_id: str, *, version: int = 1) -> ProductSummary:
    return ProductSummary(
        product_id=product_id,
        name=f"Product {product_id} v{version}",
        price_cents=1_000 + version,
    )


def assert_stats(stats: CacheStats, **expected: int) -> None:
    for field, value in expected.items():
        assert getattr(stats, field) == value


def cache_tasks() -> list[asyncio.Task[object]]:
    current = asyncio.current_task()
    return [
        task
        for task in asyncio.all_tasks()
        if task is not current and task.get_name().startswith("bluetape-cache-")
    ]


def test_product_summary_is_keyword_only_frozen_and_slotted() -> None:
    value = product("SKU-1")
    assert value.product_id == "SKU-1"
    assert not hasattr(value, "__dict__")
    with pytest.raises(FrozenInstanceError):
        value.name = "changed"  # type: ignore[misc]
    with pytest.raises(TypeError):
        ProductSummary("SKU-1", "Keyboard", 12_500)  # type: ignore[misc]


def test_services_expose_only_the_approved_application_methods() -> None:
    assert {name for name in vars(SyncProductCatalogService) if not name.startswith("_")} == {
        "get_product",
        "stats",
    }
    assert {name for name in vars(AsyncProductCatalogService) if not name.startswith("_")} == {
        "get_product",
        "stats",
    }


@pytest.mark.parametrize("raw", [None, 123, "", "   ", "A" * 65, "상품-1", "SKU/1", "SKU 1"])
def test_sync_invalid_product_id_fails_before_cache_or_loader(raw: object) -> None:
    calls: list[str] = []
    cache: TTLCache[str, ProductSummary] = TTLCache(default_ttl=10, max_size=2)
    service = SyncProductCatalogService(
        cache=cache, loader=lambda key: calls.append(key) or product(key)
    )

    with pytest.raises((TypeError, ValueError)):
        service.get_product(raw)  # type: ignore[arg-type]

    assert calls == []
    assert_stats(cache.stats(), hits=0, misses=0, loads=0)


@pytest.mark.parametrize("raw", [None, 123, "", "   ", "A" * 65, "상품-1", "SKU/1", "SKU 1"])
async def test_async_invalid_product_id_fails_before_cache_or_loader(raw: object) -> None:
    calls: list[str] = []

    async def loader(key: str) -> ProductSummary:
        calls.append(key)
        return product(key)

    cache: AsyncTTLCache[str, ProductSummary] = AsyncTTLCache(default_ttl=10, max_size=2)
    service = AsyncProductCatalogService(cache=cache, loader=loader)

    with pytest.raises((TypeError, ValueError)):
        await service.get_product(raw)  # type: ignore[arg-type]

    assert calls == []
    assert_stats(await cache.stats(), hits=0, misses=0, loads=0)


def test_sync_normalizes_before_loading() -> None:
    calls: list[str] = []
    cache: TTLCache[str, ProductSummary] = TTLCache(default_ttl=10, max_size=2)
    service = SyncProductCatalogService(
        cache=cache, loader=lambda key: calls.append(key) or product(key)
    )

    assert service.get_product(" sku-1 ").product_id == "SKU-1"
    assert calls == ["SKU-1"]


async def test_async_normalizes_before_loading() -> None:
    calls: list[str] = []

    async def loader(key: str) -> ProductSummary:
        calls.append(key)
        return product(key)

    cache: AsyncTTLCache[str, ProductSummary] = AsyncTTLCache(default_ttl=10, max_size=2)
    service = AsyncProductCatalogService(cache=cache, loader=loader)

    assert (await service.get_product(" sku-1 ")).product_id == "SKU-1"
    assert calls == ["SKU-1"]


def test_sync_miss_then_hit_preserves_identity_and_stats() -> None:
    calls = 0

    def loader(key: str) -> ProductSummary:
        nonlocal calls
        calls += 1
        return product(key)

    service = SyncProductCatalogService(cache=TTLCache(default_ttl=10, max_size=2), loader=loader)
    first = service.get_product("sku-1")
    second = service.get_product("SKU-1")

    assert first is second
    assert calls == 1
    assert_stats(service.stats(), misses=1, loads=1, hits=1, load_failures=0)


def test_sync_expiry_is_exact_at_the_nanosecond_boundary() -> None:
    clock = ManualClock()
    calls = 0

    def loader(key: str) -> ProductSummary:
        nonlocal calls
        calls += 1
        return product(key, version=calls)

    service = SyncProductCatalogService(
        cache=TTLCache(default_ttl=10e-9, max_size=2, clock=clock), loader=loader
    )
    first = service.get_product("SKU-1")
    clock.advance(9)
    assert service.get_product("SKU-1") is first
    clock.advance(1)
    assert service.get_product("SKU-1") is not first
    assert_stats(service.stats(), expirations=1, loads=2, misses=2, hits=1)


def test_sync_lru_failure_recovery_and_caller_set_value() -> None:
    clock = ManualClock()
    attempts: dict[str, int] = {}
    failure = LookupError("catalog unavailable")

    def loader(key: str) -> ProductSummary:
        attempts[key] = attempts.get(key, 0) + 1
        if key == "FAIL" and attempts[key] == 1:
            raise failure
        return product(key, version=attempts[key])

    cache: TTLCache[str, ProductSummary] = TTLCache(default_ttl=10, max_size=2, clock=clock)
    service = SyncProductCatalogService(cache=cache, loader=loader)
    a = service.get_product("A")
    service.get_product("B")
    assert service.get_product("A") is a
    service.get_product("C")
    service.get_product("B")
    assert attempts["B"] == 2
    with pytest.raises(LookupError) as raised:
        service.get_product("FAIL")
    assert raised.value is failure
    assert service.get_product("FAIL").product_id == "FAIL"
    caller_value = product("OWNED", version=99)
    cache.set("OWNED", caller_value)
    assert service.get_product("owned") is caller_value
    assert attempts.get("OWNED", 0) == 0
    assert_stats(service.stats(), load_failures=1)


async def test_async_miss_hit_expiry_lru_failure_and_caller_set_value() -> None:
    clock = ManualClock()
    attempts: dict[str, int] = {}
    failure = LookupError("catalog unavailable")

    async def loader(key: str) -> ProductSummary:
        attempts[key] = attempts.get(key, 0) + 1
        if key == "FAIL" and attempts[key] == 1:
            raise failure
        return product(key, version=attempts[key])

    cache: AsyncTTLCache[str, ProductSummary] = AsyncTTLCache(
        default_ttl=10e-9, max_size=2, clock=clock
    )
    service = AsyncProductCatalogService(cache=cache, loader=loader)
    first = await service.get_product("sku-1")
    assert await service.get_product("SKU-1") is first
    clock.advance(9)
    assert await service.get_product("SKU-1") is first
    clock.advance(1)
    assert await service.get_product("SKU-1") is not first
    await service.get_product("A")
    await service.get_product("B")
    await service.get_product("A")
    await service.get_product("C")
    await service.get_product("B")
    assert attempts["B"] == 2
    with pytest.raises(LookupError) as raised:
        await service.get_product("FAIL")
    assert raised.value is failure
    assert (await service.get_product("FAIL")).product_id == "FAIL"
    caller_value = product("OWNED", version=99)
    await cache.set("OWNED", caller_value)
    assert await service.get_product("owned") is caller_value
    assert attempts.get("OWNED", 0) == 0
    assert_stats(await service.stats(), expirations=1, load_failures=1)


async def start_shared_calls(
    service: AsyncProductCatalogService,
) -> tuple[asyncio.Task[ProductSummary], asyncio.Task[ProductSummary]]:
    first = asyncio.create_task(service.get_product("sku-1"), name="catalog-caller-1")
    second = asyncio.create_task(service.get_product("SKU-1"), name="catalog-caller-2")
    return first, second


async def test_async_same_key_callers_share_success() -> None:
    started = asyncio.Event()
    release = asyncio.Event()
    calls = 0

    async def loader(key: str) -> ProductSummary:
        nonlocal calls
        calls += 1
        started.set()
        await release.wait()
        return product(key)

    service = AsyncProductCatalogService(
        cache=AsyncTTLCache(default_ttl=10, max_size=2), loader=loader
    )
    first, second = await start_shared_calls(service)
    await started.wait()
    await asyncio.sleep(0)
    release.set()
    one, two = await asyncio.gather(first, second)
    assert one is two
    assert calls == 1
    assert_stats(await service.stats(), loads=1, misses=2, coalesced_waiters=1, inflight_loads=0)


async def test_async_shared_failure_is_not_cached() -> None:
    started = asyncio.Event()
    release = asyncio.Event()
    failure = LookupError("shared")
    fail = True
    calls = 0

    async def loader(key: str) -> ProductSummary:
        nonlocal calls
        calls += 1
        started.set()
        await release.wait()
        if fail:
            raise failure
        return product(key)

    service = AsyncProductCatalogService(
        cache=AsyncTTLCache(default_ttl=10, max_size=2), loader=loader
    )
    first, second = await start_shared_calls(service)
    await started.wait()
    await asyncio.sleep(0)
    release.set()
    outcomes = await asyncio.gather(first, second, return_exceptions=True)
    assert outcomes == [failure, failure]
    fail = False
    assert (await service.get_product("SKU-1")).product_id == "SKU-1"
    assert calls == 2
    assert_stats(await service.stats(), loads=2, load_failures=1, coalesced_waiters=1)


async def test_async_cancelling_one_waiter_keeps_loader_and_survivor() -> None:
    started = asyncio.Event()
    release = asyncio.Event()
    loader_cancelled = False

    async def loader(key: str) -> ProductSummary:
        nonlocal loader_cancelled
        started.set()
        try:
            await release.wait()
        except asyncio.CancelledError:
            loader_cancelled = True
            raise
        return product(key)

    service = AsyncProductCatalogService(
        cache=AsyncTTLCache(default_ttl=10, max_size=2), loader=loader
    )
    first, second = await start_shared_calls(service)
    await started.wait()
    await asyncio.sleep(0)
    first.cancel()
    with pytest.raises(asyncio.CancelledError):
        await first
    release.set()
    assert (await second).product_id == "SKU-1"
    await asyncio.sleep(0)
    assert not loader_cancelled
    assert cache_tasks() == []


async def test_async_last_waiter_cancellation_exposes_then_cleans_abandoned_load() -> None:
    started = asyncio.Event()
    cancellation_seen = asyncio.Event()
    release_cleanup = asyncio.Event()

    async def loader(key: str) -> ProductSummary:
        started.set()
        try:
            await asyncio.Future()
        except asyncio.CancelledError:
            cancellation_seen.set()
            await release_cleanup.wait()
            raise

    service = AsyncProductCatalogService(
        cache=AsyncTTLCache(default_ttl=10, max_size=2), loader=loader
    )
    caller = asyncio.create_task(service.get_product("SKU-1"), name="catalog-last-waiter")
    await started.wait()
    caller.cancel()
    with pytest.raises(asyncio.CancelledError):
        await caller
    await cancellation_seen.wait()
    assert_stats(await service.stats(), inflight_loads=1, abandoned_loads=1)
    release_cleanup.set()

    async def terminal() -> bool:
        stats = await service.stats()
        return stats.inflight_loads == stats.abandoned_loads == 0 and not cache_tasks()

    await eventually_async(terminal, timeout=1, interval=0.001)
    assert cache_tasks() == []
