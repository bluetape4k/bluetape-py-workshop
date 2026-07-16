from dataclasses import dataclass

from examples.bounded_payload_processing import EncodedPayload
from examples.catalog_enrichment import EnrichmentWarning


@dataclass(frozen=True, slots=True, kw_only=True)
class OrderLineCommand:
    sku: str
    quantity: int


@dataclass(frozen=True, slots=True, kw_only=True)
class OrderBackendCommand:
    request_id: str
    partner_id: str
    order_id: str
    lines: tuple[OrderLineCommand, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class ProcessedOrderLine:
    line_index: int
    sku: str
    quantity: int
    name: str
    unit_price_cents: int
    line_total_cents: int
    recommendation: str | None
    warnings: tuple[EnrichmentWarning, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class ProcessedOrder:
    request_id: str
    partner_id: str
    order_id: str
    lines: tuple[ProcessedOrderLine, ...]
    total_cents: int
    artifact: EncodedPayload
