import asyncio
import json
from collections.abc import Mapping
from dataclasses import asdict
from types import MappingProxyType

from .models import CatalogRecord, RecommendationRecord
from .service import CatalogEnrichmentService

_CATALOG: Mapping[str, CatalogRecord] = MappingProxyType(
    {
        "SKU-1": CatalogRecord(product_id="SKU-1", name="Desk", price_cents=12000),
        "SKU-2": CatalogRecord(product_id="SKU-2", name="Chair", price_cents=8000),
    }
)
_RECOMMENDATIONS: Mapping[str, RecommendationRecord] = MappingProxyType(
    {
        "SKU-2": RecommendationRecord(
            product_id="SKU-2",
            recommendation="PAIR-SKU-8",
        )
    }
)


class _InMemoryCatalogProvider:
    async def fetch(self, product_ids: tuple[str, ...]) -> Mapping[str, CatalogRecord]:
        return {product_id: _CATALOG[product_id] for product_id in product_ids}


class _InMemoryRecommendationProvider:
    async def fetch(
        self,
        product_ids: tuple[str, ...],
    ) -> Mapping[str, RecommendationRecord]:
        return {
            product_id: _RECOMMENDATIONS[product_id]
            for product_id in product_ids
            if product_id in _RECOMMENDATIONS
        }


async def main() -> None:
    service = CatalogEnrichmentService(
        _InMemoryCatalogProvider(),
        _InMemoryRecommendationProvider(),
    )
    results = await service.enrich(
        [" sku-2 ", "sku-1", "SKU-2"],
        batch_size=2,
        concurrency_limit=2,
        timeout=1.0,
    )
    print(json.dumps([asdict(result) for result in results], sort_keys=True))


if __name__ == "__main__":
    asyncio.run(main())
