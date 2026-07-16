import asyncio
import json
from dataclasses import asdict

from bluetape.cache import AsyncTTLCache, CacheStats, TTLCache

from .models import ProductSummary
from .service import AsyncProductCatalogService, SyncProductCatalogService


class _ManualClock:
    def __init__(self) -> None:
        self.now = 0

    def __call__(self) -> int:
        return self.now

    def advance(self, nanoseconds: int) -> None:
        self.now += nanoseconds


_PRODUCTS = {
    "SKU-1": ("Mechanical Keyboard", 12_500),
    "SKU-2": ("Vertical Mouse", 7_900),
    "SKU-3": ("USB-C Dock", 15_900),
    "FAIL": ("Recovered Product", 9_900),
}


def _product(product_id: str) -> ProductSummary:
    name, price_cents = _PRODUCTS[product_id]
    return ProductSummary(product_id=product_id, name=name, price_cents=price_cents)


def _emit(payload: dict[str, object]) -> None:
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))


def _emit_value(event: str, mode: str, value: ProductSummary) -> None:
    _emit({"event": event, "mode": mode, **asdict(value)})


def _emit_stats(event: str, mode: str, stats: CacheStats) -> None:
    _emit({"event": event, "mode": mode, **asdict(stats)})


def _run_sync_scenario() -> CacheStats:
    clock = _ManualClock()
    fail_once = True

    def loader(product_id: str) -> ProductSummary:
        nonlocal fail_once
        if product_id == "FAIL" and fail_once:
            fail_once = False
            raise LookupError("simulated provider failure")
        return _product(product_id)

    cache: TTLCache[str, ProductSummary] = TTLCache(
        default_ttl=10e-9,
        max_size=2,
        clock=clock,
    )
    service = SyncProductCatalogService(cache=cache, loader=loader)

    _emit_value("sync_miss", "sync", service.get_product(" sku-1 "))
    _emit_value("sync_hit", "sync", service.get_product("SKU-1"))
    clock.advance(10)
    _emit_value("sync_expired_reload", "sync", service.get_product("sku-1"))
    service.get_product("SKU-2")
    _emit_value("sync_eviction", "sync", service.get_product("SKU-3"))
    try:
        service.get_product("FAIL")
    except LookupError:
        _emit(
            {
                "event": "sync_loader_failed",
                "mode": "sync",
                "error_code": "loader_unavailable",
            }
        )
    _emit_value("sync_recovered", "sync", service.get_product("FAIL"))
    return service.stats()


async def _run_async_scenario() -> CacheStats:
    async def loader(product_id: str) -> ProductSummary:
        return _product(product_id)

    cache: AsyncTTLCache[str, ProductSummary] = AsyncTTLCache(default_ttl=10, max_size=2)
    service = AsyncProductCatalogService(cache=cache, loader=loader)
    _emit_value("async_miss", "async", await service.get_product(" sku-2 "))
    _emit_value("async_hit", "async", await service.get_product("SKU-2"))
    return await service.stats()


def main() -> None:
    sync_stats = _run_sync_scenario()
    async_stats = asyncio.run(_run_async_scenario())
    _emit_stats("sync_stats", "sync", sync_stats)
    _emit_stats("async_stats", "async", async_stats)


if __name__ == "__main__":
    main()
