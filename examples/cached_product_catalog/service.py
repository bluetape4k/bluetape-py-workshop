import re

from bluetape.cache import AsyncTTLCache, CacheStats, TTLCache
from bluetape.core import require_instance, require_not_blank

from .models import ProductSummary
from .providers import AsyncProductLoader, SyncProductLoader

MAX_PRODUCT_ID_LENGTH = 64
_PRODUCT_ID = re.compile(r"[A-Z0-9][A-Z0-9._-]*\Z")


def _normalize_product_id(value: object) -> str:
    product_id = (
        require_not_blank(
            require_instance(value, str, "product_id"),
            "product_id",
        )
        .strip()
        .upper()
    )
    if len(product_id) > MAX_PRODUCT_ID_LENGTH:
        raise ValueError(f"product_id must contain at most {MAX_PRODUCT_ID_LENGTH} characters")
    if not product_id.isascii() or _PRODUCT_ID.fullmatch(product_id) is None:
        raise ValueError("product_id must use ASCII SKU characters")
    return product_id


class SyncProductCatalogService:
    def __init__(
        self,
        *,
        cache: TTLCache[str, ProductSummary],
        loader: SyncProductLoader,
    ) -> None:
        self._cache = cache
        self._loader = loader

    def get_product(self, product_id: str) -> ProductSummary:
        return self._cache.get_or_load(_normalize_product_id(product_id), self._loader)

    def stats(self) -> CacheStats:
        return self._cache.stats()


class AsyncProductCatalogService:
    def __init__(
        self,
        *,
        cache: AsyncTTLCache[str, ProductSummary],
        loader: AsyncProductLoader,
    ) -> None:
        self._cache = cache
        self._loader = loader

    async def get_product(self, product_id: str) -> ProductSummary:
        return await self._cache.get_or_load(_normalize_product_id(product_id), self._loader)

    async def stats(self) -> CacheStats:
        return await self._cache.stats()
