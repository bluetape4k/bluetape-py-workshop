import asyncio
import json
import logging
from collections.abc import Mapping

from examples.cached_product_catalog import ProductSummary
from examples.catalog_enrichment import RecommendationRecord

from .composition import build_application
from .models import OrderBackendCommand, OrderLineCommand, ProcessedOrder

_PRODUCTS = {
    "SKU-1": ("Mechanical Keyboard", 12_500),
    "SKU-2": ("Vertical Mouse", 7_900),
    "SKU-3": ("USB-C Dock", 15_900),
}
_RECOMMENDATIONS = {
    "SKU-1": "PAIR-SKU-9",
    "SKU-3": "PAIR-SKU-8",
}


async def _catalog_loader(product_id: str) -> ProductSummary:
    name, price_cents = _PRODUCTS[product_id]
    return ProductSummary(
        product_id=product_id,
        name=name,
        price_cents=price_cents,
    )


class _RecommendationProvider:
    async def fetch(
        self,
        product_ids: tuple[str, ...],
    ) -> Mapping[str, RecommendationRecord]:
        return {
            product_id: RecommendationRecord(
                product_id=product_id,
                recommendation=_RECOMMENDATIONS[product_id],
            )
            for product_id in product_ids
            if product_id in _RECOMMENDATIONS
        }


def _emit(event: dict[str, object]) -> None:
    print(json.dumps(event, sort_keys=True, separators=(",", ":")))


def _order_event(order: ProcessedOrder) -> dict[str, object]:
    return {
        "event": "order_processed",
        "order_id": order.order_id,
        "line_count": len(order.lines),
        "total_cents": order.total_cents,
        "warning_count": sum(len(line.warnings) for line in order.lines),
        "artifact_format": order.artifact.metadata.format,
        "trust_profile": order.artifact.metadata.trust_profile.value,
        "compression": order.artifact.compression,
        "encoding": order.artifact.encoding,
        "encoded_size": len(order.artifact.data),
    }


async def _run_scenario() -> None:
    logger = logging.Logger("integrated-order-backend", level=logging.CRITICAL)
    application = build_application(
        logger=logger,
        catalog_loader=_catalog_loader,
        recommendation_provider=_RecommendationProvider(),
    )
    first = OrderBackendCommand(
        request_id="req-1001",
        partner_id="partner-7",
        order_id="order-9001",
        lines=(
            OrderLineCommand(sku="SKU-1", quantity=2),
            OrderLineCommand(sku="SKU-2", quantity=1),
            OrderLineCommand(sku="SKU-1", quantity=1),
        ),
    )
    second = OrderBackendCommand(
        request_id="req-1002",
        partner_id="partner-7",
        order_id="order-9002",
        lines=(
            OrderLineCommand(sku="SKU-2", quantity=2),
            OrderLineCommand(sku="SKU-3", quantity=1),
        ),
    )
    _emit({"event": "backend_started"})
    async with application:
        _emit(_order_event(await application.process(first)))
        _emit(_order_event(await application.process(second)))
        stats = await application.cache_stats()
        _emit(
            {
                "event": "cache_stats",
                "hits": stats.hits,
                "misses": stats.misses,
                "loads": stats.loads,
                "load_failures": stats.load_failures,
                "inflight_loads": stats.inflight_loads,
                "abandoned_loads": stats.abandoned_loads,
            }
        )
    _emit({"event": "backend_stopped"})


def main() -> None:
    asyncio.run(_run_scenario())


if __name__ == "__main__":
    main()
