from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True, slots=True, kw_only=True)
class PartnerOrderCommand:
    request_id: str
    partner_id: str
    order_id: str
    sku: str
    quantity: int


@dataclass(frozen=True, slots=True, kw_only=True)
class AcceptedOrder:
    request_id: str
    partner_id: str
    order_id: str
    sku: str
    quantity: int
    status: Literal["accepted"] = "accepted"
