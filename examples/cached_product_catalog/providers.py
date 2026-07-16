from typing import Protocol

from .models import ProductSummary


class SyncProductLoader(Protocol):
    def __call__(self, product_id: str) -> ProductSummary: ...


class AsyncProductLoader(Protocol):
    async def __call__(self, product_id: str) -> ProductSummary: ...
