import math
import re

from bluetape.cache import AsyncTTLCache, CacheStats
from bluetape.cache.redis import (
    AsyncRedisLoadCoordinator,
    AsyncRedisProvider,
    RedisCoordinationObserver,
    RedisLoadOptions,
    ResultEnvelopeCodec,
)

from examples.cached_product_catalog import AsyncProductLoader, ProductSummary

MAX_PRODUCT_ID_LENGTH = 64
_PRODUCT_ID = re.compile(r"[A-Z0-9][A-Z0-9._-]*\Z")


def _validate_product_id(value: object) -> str:
    if type(value) is not str:
        raise TypeError("product_id must be an exact str")
    if not value or value != value.strip():
        raise ValueError("product_id must be non-blank without surrounding whitespace")
    if len(value) > MAX_PRODUCT_ID_LENGTH:
        raise ValueError(f"product_id must contain at most {MAX_PRODUCT_ID_LENGTH} characters")
    if not value.isascii() or _PRODUCT_ID.fullmatch(value) is None:
        raise ValueError("product_id must use uppercase ASCII SKU characters")
    return value


def _positive_ttl(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise TypeError("local_ttl must be a real number")
    result = float(value)
    if not math.isfinite(result) or result <= 0:
        raise ValueError("local_ttl must be finite and positive")
    return result


class RedisCatalogInstance:
    """Compose one local cache with the upstream Redis load coordinator."""

    def __init__(
        self,
        *,
        cache: AsyncTTLCache[str, ProductSummary],
        provider: AsyncRedisProvider,
        loader: AsyncProductLoader,
        codec: ResultEnvelopeCodec[ProductSummary],
        options: RedisLoadOptions,
        observer: RedisCoordinationObserver | None = None,
        local_ttl: float,
    ) -> None:
        if not callable(loader):
            raise TypeError("loader must be callable")
        self._loader = loader
        self._local_ttl = _positive_ttl(local_ttl)
        self._cache = cache
        self._coordinator = AsyncRedisLoadCoordinator(
            cache,
            provider,
            codec,
            options=options,
            observer=observer,
        )

    async def get_product(self, product_id: str) -> ProductSummary:
        key = _validate_product_id(product_id)
        return await self._coordinator.get_or_load(
            key,
            self._loader,
            ttl=self._local_ttl,
        )

    async def stats(self) -> CacheStats:
        return await self._cache.stats()
