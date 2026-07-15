from collections.abc import Mapping
from typing import Protocol

from .models import CatalogRecord, RecommendationRecord


class RequiredCatalogProvider(Protocol):
    async def fetch(self, product_ids: tuple[str, ...]) -> Mapping[str, CatalogRecord]: ...


class OptionalRecommendationProvider(Protocol):
    async def fetch(
        self,
        product_ids: tuple[str, ...],
    ) -> Mapping[str, RecommendationRecord]: ...
