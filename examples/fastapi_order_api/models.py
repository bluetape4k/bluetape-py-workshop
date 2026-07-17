from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from examples.integrated_order_backend.models import OrderBackendCommand, OrderLineCommand

Identifier = Annotated[str, StringConstraints(min_length=1, max_length=128)]
Quantity = Annotated[int, Field(strict=True, ge=1, le=1_000_000)]


class OrderLineRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    sku: Identifier
    quantity: Quantity


class OrderRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    partner_id: Identifier
    order_id: Identifier
    lines: Annotated[list[OrderLineRequest], Field(min_length=1, max_length=100)]

    def to_command(self, request_id: str) -> OrderBackendCommand:
        return OrderBackendCommand(
            request_id=request_id,
            partner_id=self.partner_id,
            order_id=self.order_id,
            lines=tuple(
                OrderLineCommand(sku=line.sku, quantity=line.quantity) for line in self.lines
            ),
        )


class OrderResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    request_id: Identifier
    partner_id: Identifier
    order_id: Identifier
    line_count: Annotated[int, Field(strict=True, ge=1, le=100)]
    total_cents: Annotated[int, Field(strict=True, ge=0)]
    warning_count: Annotated[int, Field(strict=True, ge=0)]


class OrderProblem(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    code: str
    message: str
    request_id: str
    field: str | None = None
    line_index: int | None = None
