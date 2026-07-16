from __future__ import annotations

import asyncio

import pytest

pytest.importorskip("bluetape.cache.redis")

from bluetape.cache import AsyncTTLCache
from bluetape.cache.redis import (
    RedisCoordinationErrorCode,
    RedisCoordinationOutcome,
    RedisCoordinationSnapshot,
    RedisCoordinationTimeoutError,
    RedisErrorCode,
    RedisLoadOptions,
    RedisOperation,
    RedisProviderError,
    ResultEnvelopeCodec,
)

from examples.cached_product_catalog import ProductSummary
from examples.redis_load_coordination.codec import ProductSummaryCodec
from examples.redis_load_coordination.observer import CoordinationEventRecorder
from examples.redis_load_coordination.service import RedisCatalogInstance
from examples.redis_load_coordination.tests.fakes import (
    FakeAsyncRedisProvider,
    SharedRedisBackend,
)


def options(*, max_polls: int = 20) -> RedisLoadOptions:
    return RedisLoadOptions(
        namespace="catalog:test:product-v1",
        lease_ttl=0.5,
        result_ttl=0.2,
        poll_interval=0.001,
        max_poll_interval=0.001,
        wait_timeout=0.2,
        max_attempts=2,
        max_polls=max_polls,
        redis_io_timeout=0.05,
    )


def instance(
    provider: FakeAsyncRedisProvider,
    loader,
    *,
    recorder: CoordinationEventRecorder | None = None,
    load_options: RedisLoadOptions | None = None,
) -> RedisCatalogInstance:
    return RedisCatalogInstance(
        cache=AsyncTTLCache(default_ttl=60.0, max_size=32),
        provider=provider,
        loader=loader,
        codec=ResultEnvelopeCodec(payload_codec=ProductSummaryCodec()),
        options=load_options or options(),
        observer=recorder,
        local_ttl=30.0,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("product_id", [None, 42, "", " SKU-42 ", "한글", "A" * 65])
async def test_instance_rejects_invalid_key_before_redis(product_id: object) -> None:
    provider = FakeAsyncRedisProvider(SharedRedisBackend())
    catalog = instance(provider, lambda _: pytest.fail("loader called"))

    with pytest.raises((TypeError, ValueError)):
        await catalog.get_product(product_id)  # type: ignore[arg-type]

    assert provider.calls == []


@pytest.mark.asyncio
async def test_two_instances_load_once_reuse_result_and_keep_local_hit_off_redis() -> None:
    backend = SharedRedisBackend()
    owner_provider = FakeAsyncRedisProvider(backend)
    follower_provider = FakeAsyncRedisProvider(backend)
    owner_events = CoordinationEventRecorder()
    follower_events = CoordinationEventRecorder()
    loader_started = asyncio.Event()
    loader_release = asyncio.Event()
    calls = 0
    product = ProductSummary(product_id="SKU-42", name="Blue Mug", price_cents=1299)

    async def loader(_: str) -> ProductSummary:
        nonlocal calls
        calls += 1
        loader_started.set()
        await loader_release.wait()
        return product

    owner = instance(owner_provider, loader, recorder=owner_events)
    follower = instance(follower_provider, loader, recorder=follower_events)
    owner_task = asyncio.create_task(owner.get_product("SKU-42"))
    await asyncio.wait_for(loader_started.wait(), timeout=1.0)
    follower_task = asyncio.create_task(follower.get_product("SKU-42"))
    await asyncio.wait_for(follower_provider.snapshot_called.wait(), timeout=1.0)
    loader_release.set()

    assert await asyncio.wait_for(owner_task, timeout=1.0) == product
    assert await asyncio.wait_for(follower_task, timeout=1.0) == product
    assert calls == 1
    assert owner_events.snapshot()[-1].outcome is RedisCoordinationOutcome.LOADED
    assert follower_events.snapshot()[-1].outcome is RedisCoordinationOutcome.RESULT_REUSED

    calls_before = tuple(follower_provider.calls)
    events_before = follower_events.snapshot()
    assert await follower.get_product("SKU-42") == product
    assert tuple(follower_provider.calls) == calls_before
    assert follower_events.snapshot() == events_before


@pytest.mark.asyncio
async def test_timeout_does_not_fall_back_to_loader() -> None:
    backend = SharedRedisBackend(values={"placeholder": b"unused"})
    provider = FakeAsyncRedisProvider(backend)
    provider.snapshot_plan = [
        RedisCoordinationSnapshot(
            marker=b"active:remote",
            result=None,
            marker_oversized=False,
            result_oversized=False,
        )
    ]
    provider.backend.values.clear()
    provider.backend.values["force-occupied"] = b"unused"
    provider.set_if_absent = lambda *args, **kwargs: asyncio.sleep(0, result=False)  # type: ignore[method-assign]
    catalog = instance(
        provider,
        lambda _: pytest.fail("loader called"),
        load_options=options(max_polls=1),
    )

    with pytest.raises(RedisCoordinationTimeoutError) as captured:
        await catalog.get_product("SKU-42")

    assert captured.value.code is RedisCoordinationErrorCode.POLLS_EXHAUSTED


@pytest.mark.asyncio
async def test_provider_failure_propagates_without_loader() -> None:
    provider = FakeAsyncRedisProvider(SharedRedisBackend())
    error = RedisProviderError(
        operation=RedisOperation.SET_IF_ABSENT,
        code=RedisErrorCode.PROVIDER_FAILURE,
    )
    provider.failure = error
    catalog = instance(provider, lambda _: pytest.fail("loader called"))

    with pytest.raises(RedisProviderError) as captured:
        await catalog.get_product("SKU-42")

    assert captured.value is error


@pytest.mark.asyncio
async def test_loader_failure_is_preserved_and_cleans_marker_once() -> None:
    provider = FakeAsyncRedisProvider(SharedRedisBackend())
    cause = LookupError("caller-owned")

    async def loader(_: str) -> ProductSummary:
        raise cause

    catalog = instance(provider, loader)
    with pytest.raises(LookupError) as captured:
        await catalog.get_product("SKU-42")

    assert captured.value is cause
    assert provider.calls.count("delete_if_value") == 1
    assert provider.backend.values == {}


@pytest.mark.asyncio
async def test_cancellation_is_preserved_and_cleans_marker() -> None:
    provider = FakeAsyncRedisProvider(SharedRedisBackend())
    started = asyncio.Event()

    async def loader(_: str) -> ProductSummary:
        started.set()
        await asyncio.Event().wait()
        raise AssertionError("unreachable")

    catalog = instance(provider, loader)
    task = asyncio.create_task(catalog.get_product("SKU-42"))
    await asyncio.wait_for(started.wait(), timeout=1.0)
    task.cancel()

    with pytest.raises(asyncio.CancelledError):
        await asyncio.wait_for(task, timeout=1.0)

    assert provider.calls.count("delete_if_value") == 1
    assert provider.backend.values == {}


@pytest.mark.asyncio
async def test_stale_envelope_is_skipped_until_matching_result() -> None:
    provider = FakeAsyncRedisProvider(SharedRedisBackend())
    codec = ResultEnvelopeCodec(payload_codec=ProductSummaryCodec())
    stale = ProductSummary(product_id="SKU-OLD", name="Old", price_cents=1)
    fresh = ProductSummary(product_id="SKU-42", name="Fresh", price_cents=2)
    provider.snapshot_plan = [
        RedisCoordinationSnapshot(
            marker=b"completed:new-owner",
            result=codec.encode("old-owner", stale),
            marker_oversized=False,
            result_oversized=False,
        ),
        RedisCoordinationSnapshot(
            marker=b"completed:new-owner",
            result=codec.encode("new-owner", fresh),
            marker_oversized=False,
            result_oversized=False,
        ),
    ]
    provider.set_if_absent = lambda *args, **kwargs: asyncio.sleep(0, result=False)  # type: ignore[method-assign]
    catalog = instance(provider, lambda _: pytest.fail("loader called"))

    assert await catalog.get_product("SKU-42") == fresh


@pytest.mark.asyncio
async def test_lease_loss_returns_owner_value_without_remote_result() -> None:
    provider = FakeAsyncRedisProvider(SharedRedisBackend())
    provider.publish_result = False
    events = CoordinationEventRecorder()
    product = ProductSummary(product_id="SKU-42", name="Blue Mug", price_cents=1299)
    catalog = instance(provider, lambda _: asyncio.sleep(0, result=product), recorder=events)

    assert await catalog.get_product("SKU-42") == product
    assert events.snapshot()[-1].outcome is RedisCoordinationOutcome.LEASE_LOST
    assert all(not key.endswith(":result") for key in provider.backend.values)


@pytest.mark.asyncio
async def test_cleanup_failure_preserves_loader_error_and_static_note() -> None:
    provider = FakeAsyncRedisProvider(SharedRedisBackend())
    provider.cleanup_error = RuntimeError("provider-secret")
    cause = LookupError("caller-owned")

    async def loader(_: str) -> ProductSummary:
        raise cause

    catalog = instance(provider, loader)
    with pytest.raises(LookupError) as captured:
        await catalog.get_product("SKU-42")

    assert captured.value is cause
    assert captured.value.__notes__ == ["Redis owner cleanup also failed (cleanup-failure)"]
