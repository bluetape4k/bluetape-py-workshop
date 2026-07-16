import asyncio
import logging
import math
from collections.abc import Mapping

import pytest
from bluetape.cache import AsyncTTLCache, CacheStats
from bluetape.compression import GzipCompressor
from bluetape.logging import ContextLogFilter, get_log_context
from bluetape.serde import PayloadLimitError, TrustProfile

from examples.bounded_payload_processing import JsonPayloadService, TransportLimitError
from examples.cached_product_catalog import AsyncProductCatalogService, ProductSummary
from examples.catalog_enrichment import (
    CatalogEnrichmentFailed,
    CatalogEnrichmentService,
    ProviderUnavailable,
    RecommendationRecord,
)
from examples.integrated_order_backend import (
    CachedCatalogProvider,
    InvalidOrderBackendCommand,
    InvalidOrderLine,
    OrderBackendCommand,
    OrderBackendService,
    OrderLineCommand,
)
from examples.order_intake import InvalidOrderCommand, OrderIntakeService


class CaptureHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__(logging.INFO)
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


def capture_logger() -> tuple[logging.Logger, CaptureHandler]:
    logger = logging.Logger("integrated-order-backend-test", level=logging.INFO)
    logger.propagate = False
    handler = CaptureHandler()
    handler.addFilter(ContextLogFilter())
    logger.addHandler(handler)
    return logger, handler


class IntakeSpy:
    def __init__(self) -> None:
        self.calls: list[object] = []

    def accept(self, command: object) -> object:
        self.calls.append(command)
        return command


class EnrichmentSpy:
    def __init__(self) -> None:
        self.calls: list[object] = []

    async def enrich(self, product_ids, **configuration):
        self.calls.append((product_ids, configuration))
        return []


class CatalogStatsSpy:
    def __init__(self) -> None:
        self.calls = 0

    async def stats(self) -> CacheStats:
        self.calls += 1
        return CacheStats()


class PayloadSpy:
    def __init__(self) -> None:
        self.calls: list[object] = []

    def encode(self, document: object) -> object:
        self.calls.append(document)
        return object()


def spy_service() -> tuple[
    OrderBackendService,
    IntakeSpy,
    EnrichmentSpy,
    CatalogStatsSpy,
    PayloadSpy,
]:
    logger, _ = capture_logger()
    intake = IntakeSpy()
    enrichment = EnrichmentSpy()
    catalog = CatalogStatsSpy()
    payloads = PayloadSpy()
    service = OrderBackendService(
        intake=intake,  # type: ignore[arg-type]
        enrichment=enrichment,  # type: ignore[arg-type]
        catalog=catalog,  # type: ignore[arg-type]
        payloads=payloads,  # type: ignore[arg-type]
        logger=logger,
        batch_size=50,
        concurrency_limit=4,
        provider_timeout=1.0,
    )
    return service, intake, enrichment, catalog, payloads


@pytest.mark.parametrize(
    ("field", "value", "error_type"),
    [
        ("batch_size", True, TypeError),
        ("batch_size", 0, ValueError),
        ("batch_size", 101, ValueError),
        ("concurrency_limit", 0, ValueError),
        ("provider_timeout", True, TypeError),
        ("provider_timeout", 0.0, ValueError),
        ("provider_timeout", math.inf, ValueError),
    ],
)
def test_constructor_rejects_invalid_owned_configuration(
    field: str,
    value: object,
    error_type: type[Exception],
) -> None:
    logger, _ = capture_logger()
    values: dict[str, object] = {
        "batch_size": 50,
        "concurrency_limit": 4,
        "provider_timeout": 1.0,
    }
    values[field] = value

    with pytest.raises(error_type):
        OrderBackendService(
            intake=IntakeSpy(),  # type: ignore[arg-type]
            enrichment=EnrichmentSpy(),  # type: ignore[arg-type]
            catalog=CatalogStatsSpy(),  # type: ignore[arg-type]
            payloads=PayloadSpy(),  # type: ignore[arg-type]
            logger=logger,
            **values,  # type: ignore[arg-type]
        )


@pytest.mark.parametrize("dependency", ["intake", "enrichment", "catalog", "payloads"])
def test_constructor_rejects_missing_dependency_method(dependency: str) -> None:
    logger, _ = capture_logger()
    values: dict[str, object] = {
        "intake": IntakeSpy(),
        "enrichment": EnrichmentSpy(),
        "catalog": CatalogStatsSpy(),
        "payloads": PayloadSpy(),
    }
    values[dependency] = object()

    with pytest.raises(TypeError, match=dependency):
        OrderBackendService(
            logger=logger,
            batch_size=50,
            concurrency_limit=4,
            provider_timeout=1.0,
            **values,  # type: ignore[arg-type]
        )


def valid_command(*lines: OrderLineCommand) -> OrderBackendCommand:
    return OrderBackendCommand(
        request_id="req-1001",
        partner_id="partner-7",
        order_id="order-9001",
        lines=lines,
    )


@pytest.mark.parametrize(
    ("raw", "field"),
    [
        (object(), "command"),
        (
            OrderBackendCommand(
                request_id="req-1001",
                partner_id="partner-7",
                order_id="order-9001",
                lines=[],  # type: ignore[arg-type]
            ),
            "lines",
        ),
        (valid_command(), "lines"),
        (
            valid_command(*(OrderLineCommand(sku="SKU-1", quantity=1) for _ in range(101))),
            "lines",
        ),
        (
            OrderBackendCommand(
                request_id="req-1001",
                partner_id="partner-7",
                order_id="order-9001",
                lines=(object(),),  # type: ignore[arg-type]
            ),
            "lines[0]",
        ),
    ],
)
async def test_invalid_aggregate_shape_fails_before_focused_or_external_work(
    raw: object,
    field: str,
) -> None:
    service, intake, enrichment, catalog, payloads = spy_service()

    with pytest.raises(InvalidOrderBackendCommand) as captured:
        await service.process(raw)  # type: ignore[arg-type]

    assert captured.value.field == field
    assert intake.calls == []
    assert enrichment.calls == []
    assert catalog.calls == 0
    assert payloads.calls == []


async def test_line_validation_reports_exact_occurrence_before_external_work() -> None:
    logger, _ = capture_logger()
    enrichment = EnrichmentSpy()
    catalog = CatalogStatsSpy()
    payloads = PayloadSpy()
    service = OrderBackendService(
        intake=OrderIntakeService(logger),
        enrichment=enrichment,  # type: ignore[arg-type]
        catalog=catalog,  # type: ignore[arg-type]
        payloads=payloads,  # type: ignore[arg-type]
        logger=logger,
        batch_size=50,
        concurrency_limit=4,
        provider_timeout=1.0,
    )
    command = valid_command(
        OrderLineCommand(sku="SKU-1", quantity=1),
        OrderLineCommand(sku="SKU-2", quantity=2),
        OrderLineCommand(sku="SKU-3", quantity=0),
    )

    with pytest.raises(InvalidOrderLine) as captured:
        await service.process(command)

    assert (captured.value.index, captured.value.field) == (2, "quantity")
    assert isinstance(captured.value.__cause__, InvalidOrderCommand)
    assert enrichment.calls == []
    assert catalog.calls == 0
    assert payloads.calls == []
    assert get_log_context() == {}


class RecommendationProvider:
    def __init__(self, records: Mapping[str, str] | None = None) -> None:
        self.records = dict(records or {})
        self.error: BaseException | None = None

    async def fetch(
        self,
        product_ids: tuple[str, ...],
    ) -> Mapping[str, RecommendationRecord]:
        if self.error is not None:
            raise self.error
        return {
            product_id: RecommendationRecord(
                product_id=product_id,
                recommendation=self.records[product_id],
            )
            for product_id in product_ids
            if product_id in self.records
        }


def json_payloads(
    *,
    max_encoded_size: int = 128 * 1024,
    max_compressed_size: int = 64 * 1024,
    max_serialized_size: int = 64 * 1024,
    max_nesting_depth: int = 16,
) -> JsonPayloadService:
    return JsonPayloadService(
        compressor=GzipCompressor(max_output_size=max_serialized_size),
        max_encoded_size=max_encoded_size,
        max_compressed_size=max_compressed_size,
        max_serialized_size=max_serialized_size,
        max_nesting_depth=max_nesting_depth,
    )


def real_service(
    *,
    loader,
    recommendations: RecommendationProvider | None = None,
    payloads: JsonPayloadService | PayloadSpy | None = None,
) -> tuple[OrderBackendService, AsyncProductCatalogService, CaptureHandler]:
    logger, handler = capture_logger()
    catalog = AsyncProductCatalogService(
        cache=AsyncTTLCache(default_ttl=60, max_size=128),
        loader=loader,
    )
    enrichment = CatalogEnrichmentService(
        CachedCatalogProvider(catalog=catalog),
        recommendations or RecommendationProvider(),
    )
    service = OrderBackendService(
        intake=OrderIntakeService(logger),
        enrichment=enrichment,
        catalog=catalog,
        payloads=payloads or json_payloads(),  # type: ignore[arg-type]
        logger=logger,
        batch_size=50,
        concurrency_limit=4,
        provider_timeout=1.0,
    )
    return service, catalog, handler


async def test_success_preserves_occurrences_duplicates_totals_and_allowlisted_payload() -> None:
    calls: list[str] = []
    products = {
        "SKU-1": ("Desk", 12_000),
        "SKU-2": ("Chair", 8_000),
    }

    async def loader(product_id: str) -> ProductSummary:
        calls.append(product_id)
        name, price = products[product_id]
        return ProductSummary(product_id=product_id, name=name, price_cents=price)

    source_lines = (
        OrderLineCommand(sku=" sku-2 ", quantity=2),
        OrderLineCommand(sku="SKU-1", quantity=1),
        OrderLineCommand(sku="sku-2", quantity=3),
    )
    command = OrderBackendCommand(
        request_id="req-1001",
        partner_id="partner-7",
        order_id="order-9001",
        lines=source_lines,
    )
    payloads = json_payloads()
    service, catalog, handler = real_service(
        loader=loader,
        recommendations=RecommendationProvider({"SKU-1": "PAIR-SKU-9"}),
        payloads=payloads,
    )

    result = await service.process(command)
    decoded = payloads.decode(result.artifact)
    stats = await service.cache_stats()

    assert command.lines is source_lines
    assert [line.sku for line in result.lines] == ["SKU-2", "SKU-1", "SKU-2"]
    assert [line.line_index for line in result.lines] == [0, 1, 2]
    assert [line.line_total_cents for line in result.lines] == [16_000, 12_000, 24_000]
    assert result.total_cents == 52_000
    assert calls == ["SKU-2", "SKU-1"]
    assert result.lines[0].warnings[0].code == "optional_record_missing"
    assert result.lines[2].warnings == result.lines[0].warnings
    assert result.artifact.metadata.trust_profile is TrustProfile.UNTRUSTED
    assert decoded == {
        "request_id": "req-1001",
        "partner_id": "partner-7",
        "order_id": "order-9001",
        "lines": [
            {
                "line_index": 0,
                "sku": "SKU-2",
                "quantity": 2,
                "name": "Chair",
                "unit_price_cents": 8_000,
                "line_total_cents": 16_000,
                "recommendation": None,
                "warnings": [
                    {
                        "provider": "recommendations",
                        "code": "optional_record_missing",
                        "message": "recommendation is unavailable",
                    }
                ],
            },
            {
                "line_index": 1,
                "sku": "SKU-1",
                "quantity": 1,
                "name": "Desk",
                "unit_price_cents": 12_000,
                "line_total_cents": 12_000,
                "recommendation": "PAIR-SKU-9",
                "warnings": [],
            },
            {
                "line_index": 2,
                "sku": "SKU-2",
                "quantity": 3,
                "name": "Chair",
                "unit_price_cents": 8_000,
                "line_total_cents": 24_000,
                "recommendation": None,
                "warnings": [
                    {
                        "provider": "recommendations",
                        "code": "optional_record_missing",
                        "message": "recommendation is unavailable",
                    }
                ],
            },
        ],
        "total_cents": 52_000,
    }
    assert "artifact" not in decoded
    assert (stats.misses, stats.loads, stats.hits) == (2, 2, 0)
    assert await catalog.stats() == stats
    assert get_log_context() == {}
    messages = [record.getMessage() for record in handler.records]
    assert not any("PAIR-SKU-9" in message or "Desk" in message for message in messages)


async def test_required_failure_propagates_and_loader_failure_is_not_cached() -> None:
    attempts = 0
    payloads = PayloadSpy()

    async def loader(product_id: str) -> ProductSummary:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise ProviderUnavailable()
        return ProductSummary(product_id=product_id, name="Recovered", price_cents=900)

    service, _, _ = real_service(loader=loader, payloads=payloads)
    command = valid_command(OrderLineCommand(sku="SKU-1", quantity=1))

    with pytest.raises(CatalogEnrichmentFailed):
        await service.process(command)
    result = await service.process(command)
    stats = await service.cache_stats()

    assert result.lines[0].name == "Recovered"
    assert attempts == 2
    assert (stats.misses, stats.loads, stats.load_failures) == (2, 2, 1)
    assert len(payloads.calls) == 1
    assert get_log_context() == {}


async def test_optional_failure_is_preserved_as_warning() -> None:
    async def loader(product_id: str) -> ProductSummary:
        return ProductSummary(product_id=product_id, name="Desk", price_cents=1_000)

    recommendations = RecommendationProvider()
    recommendations.error = ProviderUnavailable()
    service, _, _ = real_service(loader=loader, recommendations=recommendations)

    result = await service.process(valid_command(OrderLineCommand(sku="SKU-1", quantity=1)))

    assert result.lines[0].recommendation is None
    assert result.lines[0].warnings[0].code == "optional_provider_failed"


async def test_shared_cache_hits_across_requests() -> None:
    calls = 0

    async def loader(product_id: str) -> ProductSummary:
        nonlocal calls
        calls += 1
        return ProductSummary(product_id=product_id, name="Desk", price_cents=1_000)

    service, _, _ = real_service(loader=loader)
    command = valid_command(OrderLineCommand(sku="SKU-1", quantity=1))

    await service.process(command)
    await service.process(command)
    stats = await service.cache_stats()

    assert calls == 1
    assert (stats.misses, stats.loads, stats.hits) == (1, 1, 1)


@pytest.mark.parametrize(
    ("payloads", "error_type", "stage"),
    [
        (json_payloads(max_serialized_size=256), PayloadLimitError, None),
        (json_payloads(max_compressed_size=1), TransportLimitError, "compressed"),
        (json_payloads(max_encoded_size=1), TransportLimitError, "encoded"),
        (json_payloads(max_nesting_depth=2), PayloadLimitError, None),
    ],
)
async def test_payload_limits_propagate_and_context_resets(
    payloads: JsonPayloadService,
    error_type: type[Exception],
    stage: str | None,
) -> None:
    async def loader(product_id: str) -> ProductSummary:
        return ProductSummary(
            product_id=product_id,
            name="X" * 500,
            price_cents=1_000,
        )

    service, _, _ = real_service(loader=loader, payloads=payloads)

    with pytest.raises(error_type) as captured:
        await service.process(valid_command(OrderLineCommand(sku="SKU-1", quantity=1)))

    if stage is not None:
        assert isinstance(captured.value, TransportLimitError)
        assert captured.value.stage == stage
    assert get_log_context() == {}


async def test_caller_cancellation_propagates_and_context_resets() -> None:
    started = asyncio.Event()
    cleaned = asyncio.Event()

    async def loader(product_id: str) -> ProductSummary:
        started.set()
        try:
            await asyncio.Event().wait()
        finally:
            cleaned.set()
        raise AssertionError("unreachable")

    service, _, _ = real_service(loader=loader)
    task = asyncio.create_task(
        service.process(valid_command(OrderLineCommand(sku="SKU-1", quantity=1)))
    )
    await asyncio.wait_for(started.wait(), timeout=1)
    task.cancel()

    with pytest.raises(asyncio.CancelledError):
        await task
    await asyncio.wait_for(cleaned.wait(), timeout=1)
    assert get_log_context() == {}
