import logging
from collections.abc import Mapping

from examples.cached_product_catalog import ProductSummary
from examples.catalog_enrichment import ProviderUnavailable, RecommendationRecord
from examples.integrated_order_backend import build_application
from examples.integrated_order_backend.application import OrderBackendApplication

_PRODUCTS = {
    "SKU-1": ("Mechanical Keyboard", 12_500),
    "SKU-2": ("Vertical Mouse", 7_900),
    "SKU-3": ("USB-C Dock", 15_900),
}
_RECOMMENDATIONS = {
    "SKU-1": "PAIR-SKU-9",
    "SKU-3": "PAIR-SKU-8",
}


async def demo_catalog_loader(product_id: str) -> ProductSummary:
    try:
        name, price_cents = _PRODUCTS[product_id]
    except KeyError as error:
        raise ProviderUnavailable() from error
    return ProductSummary(
        product_id=product_id,
        name=name,
        price_cents=price_cents,
    )


class DemoRecommendationProvider:
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


def build_default_backend() -> OrderBackendApplication:
    return build_application(
        logger=logging.getLogger("examples.fastapi_order_api"),
        catalog_loader=demo_catalog_loader,
        recommendation_provider=DemoRecommendationProvider(),
    )
