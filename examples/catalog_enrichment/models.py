from dataclasses import dataclass
from typing import Literal

WarningCode = Literal[
    "optional_provider_failed",
    "optional_record_missing",
    "optional_record_invalid",
    "optional_response_invalid",
]


@dataclass(frozen=True, slots=True, kw_only=True)
class CatalogRecord:
    product_id: str
    name: str
    price_cents: int


@dataclass(frozen=True, slots=True, kw_only=True)
class RecommendationRecord:
    product_id: str
    recommendation: str


@dataclass(frozen=True, slots=True, kw_only=True)
class EnrichmentWarning:
    product_id: str
    provider: Literal["recommendations"]
    code: WarningCode
    message: str


@dataclass(frozen=True, slots=True, kw_only=True)
class EnrichedProduct:
    product_id: str
    name: str
    price_cents: int
    recommendation: str | None
    warnings: tuple[EnrichmentWarning, ...] = ()
