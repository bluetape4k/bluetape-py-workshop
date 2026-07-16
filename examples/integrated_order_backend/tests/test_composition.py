import asyncio
import logging
from collections.abc import Mapping

import pytest
from bluetape.cache import AsyncTTLCache

from examples.cached_product_catalog import AsyncProductCatalogService, ProductSummary
from examples.catalog_enrichment import (
    CatalogRecord,
    ProviderUnavailable,
    RecommendationRecord,
)
from examples.integrated_order_backend import (
    CachedCatalogProvider,
    OrderBackendCommand,
    OrderLineCommand,
    build_application,
)


def _active_cache_tasks() -> list[asyncio.Task[object]]:
    current = asyncio.current_task()
    return [
        task
        for task in asyncio.all_tasks()
        if task is not current and task.get_name().startswith("bluetape-cache-")
    ]


async def test_adapter_maps_sequential_cached_products_to_catalog_records() -> None:
    calls: list[str] = []

    async def loader(product_id: str) -> ProductSummary:
        calls.append(product_id)
        return ProductSummary(
            product_id=product_id,
            name=f"Product {product_id}",
            price_cents=1_000,
        )

    catalog = AsyncProductCatalogService(
        cache=AsyncTTLCache(default_ttl=60, max_size=16),
        loader=loader,
    )
    provider = CachedCatalogProvider(catalog=catalog)

    assert await provider.fetch(("SKU-1", "SKU-2")) == {
        "SKU-1": CatalogRecord(
            product_id="SKU-1",
            name="Product SKU-1",
            price_cents=1_000,
        ),
        "SKU-2": CatalogRecord(
            product_id="SKU-2",
            name="Product SKU-2",
            price_cents=1_000,
        ),
    }
    assert calls == ["SKU-1", "SKU-2"]
    assert not _active_cache_tasks()


async def test_loader_failure_is_not_cached_and_later_call_recovers() -> None:
    attempts: dict[str, int] = {}
    failure = ProviderUnavailable()

    async def loader(product_id: str) -> ProductSummary:
        attempts[product_id] = attempts.get(product_id, 0) + 1
        if product_id == "FAIL" and attempts[product_id] == 1:
            raise failure
        return ProductSummary(
            product_id=product_id,
            name=f"Product {product_id}",
            price_cents=1_000,
        )

    catalog = AsyncProductCatalogService(
        cache=AsyncTTLCache(default_ttl=60, max_size=16),
        loader=loader,
    )
    provider = CachedCatalogProvider(catalog=catalog)

    with pytest.raises(ProviderUnavailable) as captured:
        await provider.fetch(("FAIL",))
    recovered = await provider.fetch(("FAIL",))
    stats = await catalog.stats()

    assert captured.value is failure
    assert recovered["FAIL"].product_id == "FAIL"
    assert attempts == {"FAIL": 2}
    assert (stats.misses, stats.loads, stats.load_failures) == (2, 2, 1)
    assert stats.inflight_loads == stats.abandoned_loads == 0
    assert not _active_cache_tasks()


def test_adapter_requires_the_existing_async_catalog_service() -> None:
    with pytest.raises(TypeError, match="exact AsyncProductCatalogService"):
        CachedCatalogProvider(catalog=object())  # type: ignore[arg-type]


class Recommendations:
    async def fetch(
        self,
        product_ids: tuple[str, ...],
    ) -> Mapping[str, RecommendationRecord]:
        return {}


async def test_composition_root_shares_one_cache_across_requests() -> None:
    calls: list[str] = []

    async def loader(product_id: str) -> ProductSummary:
        calls.append(product_id)
        return ProductSummary(
            product_id=product_id,
            name=f"Product {product_id}",
            price_cents=1_000,
        )

    application = build_application(
        logger=logging.Logger("composition-root-test", level=logging.CRITICAL),
        catalog_loader=loader,
        recommendation_provider=Recommendations(),
    )
    first = OrderBackendCommand(
        request_id="req-1",
        partner_id="partner-1",
        order_id="order-1",
        lines=(
            OrderLineCommand(sku="SKU-1", quantity=1),
            OrderLineCommand(sku="SKU-2", quantity=1),
            OrderLineCommand(sku="SKU-1", quantity=1),
        ),
    )
    second = OrderBackendCommand(
        request_id="req-2",
        partner_id="partner-1",
        order_id="order-2",
        lines=(OrderLineCommand(sku="SKU-2", quantity=1),),
    )

    async with application:
        await application.process(first)
        await application.process(second)
        stats = await application.cache_stats()

    assert calls == ["SKU-1", "SKU-2"]
    assert (stats.hits, stats.misses, stats.loads) == (1, 2, 2)
    assert (stats.inflight_loads, stats.abandoned_loads) == (0, 0)


def test_composition_root_rejects_non_callable_loader() -> None:
    with pytest.raises(TypeError, match="catalog_loader must be async-callable"):
        build_application(
            logger=logging.Logger("composition-root-test"),
            catalog_loader=object(),  # type: ignore[arg-type]
            recommendation_provider=Recommendations(),
        )
