import logging
from collections.abc import Mapping

from bluetape.cache import AsyncTTLCache
from bluetape.compression import GzipCompressor

from examples.bounded_payload_processing import JsonPayloadService
from examples.cached_product_catalog import (
    AsyncProductCatalogService,
    AsyncProductLoader,
    ProductSummary,
)
from examples.catalog_enrichment import (
    CatalogEnrichmentService,
    CatalogRecord,
    OptionalRecommendationProvider,
)
from examples.order_intake import OrderIntakeService

from .application import OrderBackendApplication
from .service import OrderBackendService


class CachedCatalogProvider:
    def __init__(self, *, catalog: AsyncProductCatalogService) -> None:
        if type(catalog) is not AsyncProductCatalogService:
            raise TypeError("catalog must be an exact AsyncProductCatalogService")
        self._catalog = catalog

    async def fetch(self, product_ids: tuple[str, ...]) -> Mapping[str, CatalogRecord]:
        records: dict[str, CatalogRecord] = {}
        for product_id in product_ids:
            value = await self._catalog.get_product(product_id)
            records[product_id] = CatalogRecord(
                product_id=value.product_id,
                name=value.name,
                price_cents=value.price_cents,
            )
        return records


def build_application(
    *,
    logger: logging.Logger,
    catalog_loader: AsyncProductLoader,
    recommendation_provider: OptionalRecommendationProvider,
) -> OrderBackendApplication:
    if not callable(catalog_loader):
        raise TypeError("catalog_loader must be async-callable")
    cache: AsyncTTLCache[str, ProductSummary] = AsyncTTLCache(
        default_ttl=60,
        max_size=128,
    )
    catalog = AsyncProductCatalogService(cache=cache, loader=catalog_loader)
    enrichment = CatalogEnrichmentService(
        CachedCatalogProvider(catalog=catalog),
        recommendation_provider,
    )
    payloads = JsonPayloadService(
        compressor=GzipCompressor(max_output_size=64 * 1024),
        max_encoded_size=128 * 1024,
        max_compressed_size=64 * 1024,
        max_serialized_size=64 * 1024,
        max_nesting_depth=16,
    )
    service = OrderBackendService(
        intake=OrderIntakeService(logger),
        enrichment=enrichment,
        catalog=catalog,
        payloads=payloads,
        logger=logger,
        batch_size=50,
        concurrency_limit=4,
        provider_timeout=1.0,
    )
    return OrderBackendApplication(
        service=service,
        logger=logger,
        request_timeout=2.0,
        shutdown_grace_timeout=1.0,
        shutdown_cancel_timeout=1.0,
    )
