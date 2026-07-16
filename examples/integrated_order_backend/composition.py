from collections.abc import Mapping

from examples.cached_product_catalog import AsyncProductCatalogService
from examples.catalog_enrichment import CatalogRecord


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
