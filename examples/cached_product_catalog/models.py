from dataclasses import dataclass


@dataclass(frozen=True, slots=True, kw_only=True)
class ProductSummary:
    product_id: str
    name: str
    price_cents: int
