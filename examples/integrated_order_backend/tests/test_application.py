import asyncio
import logging
import math

import pytest
from bluetape.cache import AsyncTTLCache, CacheStats
from bluetape.compression import GzipCompressor

from examples.bounded_payload_processing import JsonPayloadService
from examples.cached_product_catalog import AsyncProductCatalogService, ProductSummary
from examples.catalog_enrichment import CatalogEnrichmentService
from examples.integrated_order_backend import (
    CachedCatalogProvider,
    OrderBackendApplication,
    OrderBackendClosedError,
    OrderBackendCommand,
    OrderBackendService,
    OrderBackendShutdownError,
    OrderLineCommand,
)
from examples.order_intake import OrderIntakeService


def command() -> OrderBackendCommand:
    return OrderBackendCommand(
        request_id="req-1001",
        partner_id="partner-7",
        order_id="order-9001",
        lines=(),
    )


class Processor:
    def __init__(self) -> None:
        self.calls = 0
        self.task_names: list[str] = []
        self.result = object()
        self.stats = CacheStats(
            hits=2,
            misses=1,
            loads=1,
            load_failures=0,
            load_rejections=0,
            coalesced_waiters=0,
            evictions=0,
            expirations=0,
            invalidations=0,
            inflight_loads=0,
            abandoned_loads=0,
            superseded_loads=0,
        )

    async def process(self, request: OrderBackendCommand):
        self.calls += 1
        task = asyncio.current_task()
        self.task_names.append(task.get_name() if task is not None else "")
        return self.result

    async def cache_stats(self) -> CacheStats:
        return self.stats


class ResistantProcessor(Processor):
    def __init__(self) -> None:
        super().__init__()
        self.started = asyncio.Event()
        self.cancelled = asyncio.Event()
        self.release = asyncio.Event()
        self.cancellations = 0

    async def process(self, request: OrderBackendCommand):
        self.started.set()
        while not self.release.is_set():
            try:
                await self.release.wait()
            except asyncio.CancelledError:
                self.cancellations += 1
                self.cancelled.set()
        raise RuntimeError("late provider failure")


class CooperativeProcessor(Processor):
    def __init__(self) -> None:
        super().__init__()
        self.started = asyncio.Event()
        self.cancelled = asyncio.Event()

    async def process(self, request: OrderBackendCommand):
        self.started.set()
        try:
            await asyncio.Event().wait()
        finally:
            self.cancelled.set()


class FailingHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        raise RuntimeError("logging unavailable")


class EmptyRecommendationProvider:
    async def fetch(self, product_ids: tuple[str, ...]):
        return {}


class FailOnceApplication(OrderBackendApplication):
    def __init__(self, *, cancel: bool, **kwargs) -> None:
        super().__init__(**kwargs)
        self.cancel = cancel
        self.attempts = 0

    async def _close_once(self, snapshot) -> None:
        self.attempts += 1
        if self.attempts == 1:
            if self.cancel:
                raise asyncio.CancelledError
            raise RuntimeError("unexpected close failure")
        await super()._close_once(snapshot)


def logger(*, failing: bool = False) -> logging.Logger:
    value = logging.Logger("integrated-order-backend-application-test")
    if failing:
        value.addHandler(FailingHandler())
    return value


def application(
    processor: Processor,
    *,
    request_timeout: float = 1.0,
    shutdown_grace_timeout: float = 0.01,
    shutdown_cancel_timeout: float = 0.01,
    failing_logger: bool = False,
) -> OrderBackendApplication:
    return OrderBackendApplication(
        service=processor,  # type: ignore[arg-type]
        logger=logger(failing=failing_logger),
        request_timeout=request_timeout,
        shutdown_grace_timeout=shutdown_grace_timeout,
        shutdown_cancel_timeout=shutdown_cancel_timeout,
    )


@pytest.mark.parametrize(
    ("field", "value", "error_type"),
    [
        ("request_timeout", True, TypeError),
        ("request_timeout", 0, ValueError),
        ("shutdown_grace_timeout", math.inf, ValueError),
        ("shutdown_cancel_timeout", -1.0, ValueError),
    ],
)
def test_constructor_rejects_invalid_timeouts(
    field: str,
    value: object,
    error_type: type[Exception],
) -> None:
    values: dict[str, object] = {
        "request_timeout": 1.0,
        "shutdown_grace_timeout": 1.0,
        "shutdown_cancel_timeout": 1.0,
    }
    values[field] = value
    with pytest.raises(error_type):
        OrderBackendApplication(
            service=Processor(),  # type: ignore[arg-type]
            logger=logger(),
            **values,  # type: ignore[arg-type]
        )


@pytest.mark.parametrize("dependency", [object(), Processor()])
def test_constructor_rejects_invalid_dependencies(dependency: object) -> None:
    if isinstance(dependency, Processor):
        dependency.cache_stats = None  # type: ignore[method-assign]
    with pytest.raises(TypeError):
        OrderBackendApplication(
            service=dependency,  # type: ignore[arg-type]
            logger=logger(),
            request_timeout=1.0,
            shutdown_grace_timeout=1.0,
            shutdown_cancel_timeout=1.0,
        )


async def test_process_uses_one_named_task_and_delegates_stats() -> None:
    processor = Processor()
    app = application(processor)

    assert await app.process(command()) is processor.result
    assert processor.task_names == ["integrated-order-backend-request-1"]
    assert await app.cache_stats() == processor.stats
    await app.aclose()
    await app.aclose()

    with pytest.raises(OrderBackendClosedError):
        await app.process(command())


async def test_timeout_cancels_owned_task_and_close_can_be_retried() -> None:
    processor = ResistantProcessor()
    app = application(processor, request_timeout=0.001)

    with pytest.raises(TimeoutError):
        await asyncio.wait_for(app.process(command()), timeout=1)
    await asyncio.wait_for(processor.cancelled.wait(), timeout=1)

    with pytest.raises(OrderBackendShutdownError) as captured:
        await asyncio.wait_for(app.aclose(), timeout=1)
    assert captured.value.pending_count == 1

    processor.release.set()
    await asyncio.wait_for(processor.cancelled.wait(), timeout=1)
    await asyncio.wait_for(app.aclose(), timeout=1)
    assert processor.cancellations == 2


async def test_late_failure_is_observed_after_timeout_returns() -> None:
    processor = ResistantProcessor()
    app = application(processor, request_timeout=0.001)
    loop = asyncio.get_running_loop()
    reports: list[dict[str, object]] = []
    previous = loop.get_exception_handler()
    loop.set_exception_handler(lambda _loop, context: reports.append(context))
    try:
        with pytest.raises(TimeoutError):
            await asyncio.wait_for(app.process(command()), timeout=1)
        await asyncio.wait_for(processor.cancelled.wait(), timeout=1)
        processor.release.set()
        await asyncio.wait_for(app.aclose(), timeout=1)
        assert reports == []
    finally:
        loop.set_exception_handler(previous)


async def test_caller_cancellation_cancels_owned_task_promptly() -> None:
    processor = ResistantProcessor()
    app = application(processor)
    caller = asyncio.create_task(app.process(command()))
    await asyncio.wait_for(processor.started.wait(), timeout=1)

    caller.cancel()
    with pytest.raises(asyncio.CancelledError):
        await asyncio.wait_for(caller, timeout=1)
    await asyncio.wait_for(processor.cancelled.wait(), timeout=1)

    processor.release.set()
    await asyncio.wait_for(app.aclose(), timeout=1)


async def test_real_cache_loader_is_cooperatively_drained_after_timeout() -> None:
    loader_started = asyncio.Event()
    loader_finished = asyncio.Event()

    async def loader(product_id: str) -> ProductSummary:
        loader_started.set()
        try:
            await asyncio.Event().wait()
        finally:
            loader_finished.set()

    app_logger = logger()
    catalog = AsyncProductCatalogService(
        cache=AsyncTTLCache(default_ttl=60, max_size=128),
        loader=loader,
    )
    service = OrderBackendService(
        intake=OrderIntakeService(app_logger),
        enrichment=CatalogEnrichmentService(
            CachedCatalogProvider(catalog=catalog),
            EmptyRecommendationProvider(),  # type: ignore[arg-type]
        ),
        catalog=catalog,
        payloads=JsonPayloadService(
            compressor=GzipCompressor(max_output_size=64 * 1024),
            max_encoded_size=128 * 1024,
            max_compressed_size=64 * 1024,
            max_serialized_size=64 * 1024,
            max_nesting_depth=16,
        ),
        logger=app_logger,
        batch_size=50,
        concurrency_limit=4,
        provider_timeout=1.0,
    )
    app = OrderBackendApplication(
        service=service,
        logger=app_logger,
        request_timeout=0.001,
        shutdown_grace_timeout=0.1,
        shutdown_cancel_timeout=0.1,
    )
    request = OrderBackendCommand(
        request_id="req-1001",
        partner_id="partner-7",
        order_id="order-9001",
        lines=(OrderLineCommand(sku="SKU-1", quantity=1),),
    )

    with pytest.raises(TimeoutError):
        await asyncio.wait_for(app.process(request), timeout=1)
    await asyncio.wait_for(loader_started.wait(), timeout=1)
    await asyncio.wait_for(loader_finished.wait(), timeout=1)

    stats = await app.cache_stats()
    assert (stats.inflight_loads, stats.abandoned_loads) == (0, 0)
    assert not any(
        task.get_name().startswith("bluetape-cache-")
        for task in asyncio.all_tasks()
        if not task.done()
    )
    await app.aclose()


async def test_close_waits_for_admitted_request_then_completes() -> None:
    processor = CooperativeProcessor()
    app = application(processor, shutdown_grace_timeout=0.001)
    request = asyncio.create_task(app.process(command()))
    await asyncio.wait_for(processor.started.wait(), timeout=1)

    close = asyncio.create_task(app.aclose())
    await asyncio.wait_for(processor.cancelled.wait(), timeout=1)
    with pytest.raises(asyncio.CancelledError):
        await request
    await asyncio.wait_for(close, timeout=1)


async def test_concurrent_close_callers_share_one_cancellation() -> None:
    processor = CooperativeProcessor()
    app = application(processor)
    request = asyncio.create_task(app.process(command()))
    await asyncio.wait_for(processor.started.wait(), timeout=1)

    first = asyncio.create_task(app.aclose())
    second = asyncio.create_task(app.aclose())
    await asyncio.gather(first, second)
    with pytest.raises(asyncio.CancelledError):
        await request
    assert processor.cancelled.is_set()


async def test_cancelling_one_close_waiter_does_not_cancel_shared_close() -> None:
    processor = CooperativeProcessor()
    app = application(processor, shutdown_grace_timeout=1.0)
    request = asyncio.create_task(app.process(command()))
    await asyncio.wait_for(processor.started.wait(), timeout=1)

    first = asyncio.create_task(app.aclose())
    second = asyncio.create_task(app.aclose())
    first.cancel()
    with pytest.raises(asyncio.CancelledError):
        await first
    request.cancel()
    with pytest.raises(asyncio.CancelledError):
        await request
    await asyncio.wait_for(second, timeout=1)


async def test_context_body_exception_remains_primary_when_cleanup_fails() -> None:
    processor = ResistantProcessor()
    app = application(processor)

    with pytest.raises(ValueError, match="body failed") as captured:
        async with app:
            request = asyncio.create_task(app.process(command()))
            await asyncio.wait_for(processor.started.wait(), timeout=1)
            raise ValueError("body failed")
    assert captured.value.__notes__ == ["order backend cleanup did not reach terminal state"]
    processor.release.set()
    await app.aclose()
    with pytest.raises(RuntimeError, match="late provider failure"):
        await request


async def test_successful_context_exposes_cleanup_failure() -> None:
    processor = ResistantProcessor()
    app = application(processor)

    with pytest.raises(OrderBackendShutdownError):
        async with app:
            request = asyncio.create_task(app.process(command()))
            await asyncio.wait_for(processor.started.wait(), timeout=1)
    processor.release.set()
    await app.aclose()
    with pytest.raises(RuntimeError, match="late provider failure"):
        await request


async def test_failing_lifecycle_logger_does_not_change_outcomes() -> None:
    processor = Processor()
    app = application(processor, failing_logger=True)

    assert await app.process(command()) is processor.result
    await app.aclose()


@pytest.mark.parametrize("cancel", [False, True])
async def test_abnormal_close_completion_can_be_retried(cancel: bool) -> None:
    processor = Processor()
    app = FailOnceApplication(
        service=processor,  # type: ignore[arg-type]
        logger=logger(),
        request_timeout=1.0,
        shutdown_grace_timeout=1.0,
        shutdown_cancel_timeout=1.0,
        cancel=cancel,
    )

    expected = asyncio.CancelledError if cancel else RuntimeError
    with pytest.raises(expected):
        await app.aclose()
    await app.aclose()
    assert app.attempts == 2


def test_application_rejects_use_from_a_second_event_loop() -> None:
    processor = Processor()
    app = application(processor)
    asyncio.run(app.process(command()))

    with pytest.raises(RuntimeError, match="bound to another event loop"):
        asyncio.run(app.aclose())
    assert processor.calls == 1
