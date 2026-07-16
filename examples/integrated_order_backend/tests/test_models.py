from dataclasses import FrozenInstanceError

import pytest
from bluetape.serde import PayloadMetadata, TrustProfile

from examples.bounded_payload_processing import EncodedPayload
from examples.catalog_enrichment import EnrichmentWarning
from examples.integrated_order_backend import (
    InvalidOrderBackendCommand,
    InvalidOrderLine,
    OrderBackendClosedError,
    OrderBackendCommand,
    OrderBackendShutdownError,
    OrderLineCommand,
    ProcessedOrder,
    ProcessedOrderLine,
)
from examples.order_intake import InvalidOrderCommand


def test_command_models_are_keyword_only_frozen_slotted_and_preserve_input() -> None:
    line = OrderLineCommand(sku=" sku-1 ", quantity=2)
    lines = (line,)
    command = OrderBackendCommand(
        request_id="req-1001",
        partner_id="partner-7",
        order_id="order-9001",
        lines=lines,
    )

    assert command.lines is lines
    assert command.lines[0] is line
    assert line.sku == " sku-1 "
    assert not hasattr(command, "__dict__")
    assert not hasattr(line, "__dict__")
    with pytest.raises(FrozenInstanceError):
        line.quantity = 3  # type: ignore[misc]
    with pytest.raises(TypeError):
        OrderLineCommand("SKU-1", 2)  # type: ignore[misc]


def test_processed_models_are_immutable_and_keep_existing_value_contracts() -> None:
    warning = EnrichmentWarning(
        product_id="SKU-1",
        provider="recommendations",
        code="optional_record_missing",
        message="recommendation is unavailable",
    )
    line = ProcessedOrderLine(
        line_index=0,
        sku="SKU-1",
        quantity=2,
        name="Desk",
        unit_price_cents=12_000,
        line_total_cents=24_000,
        recommendation=None,
        warnings=(warning,),
    )
    artifact = EncodedPayload(
        metadata=PayloadMetadata(
            format="json",
            version=1,
            content_type="application/json",
            trust_profile=TrustProfile.UNTRUSTED,
        ),
        compression="gzip",
        encoding="base64url",
        data="encoded",
    )
    result = ProcessedOrder(
        request_id="req-1001",
        partner_id="partner-7",
        order_id="order-9001",
        lines=(line,),
        total_cents=24_000,
        artifact=artifact,
    )

    assert result.lines == (line,)
    assert result.artifact is artifact
    assert result.lines[0].warnings == (warning,)
    assert not hasattr(result, "__dict__")
    with pytest.raises(FrozenInstanceError):
        result.total_cents = 0  # type: ignore[misc]


def test_public_errors_expose_only_safe_structured_metadata() -> None:
    aggregate = InvalidOrderBackendCommand("lines", "must contain between 1 and 100 lines")
    cause = InvalidOrderCommand("sku", "must not be blank")
    line = InvalidOrderLine(index=3, field=cause.field, reason=cause.reason)
    line.__cause__ = cause
    closed = OrderBackendClosedError()
    shutdown = OrderBackendShutdownError(2)

    assert (aggregate.field, aggregate.reason) == (
        "lines",
        "must contain between 1 and 100 lines",
    )
    assert str(aggregate) == "lines: must contain between 1 and 100 lines"
    assert (line.index, line.field, line.reason) == (3, "sku", "must not be blank")
    assert str(line) == "lines[3].sku: must not be blank"
    assert line.__cause__ is cause
    assert str(closed) == "order backend is closed"
    assert shutdown.pending_count == 2
    assert str(shutdown) == "order backend shutdown left 2 pending requests"


def test_public_export_surface_is_deliberate() -> None:
    from examples import integrated_order_backend as api

    assert set(api.__all__) == {
        "InvalidOrderBackendCommand",
        "InvalidOrderLine",
        "OrderBackendClosedError",
        "OrderBackendCommand",
        "OrderBackendShutdownError",
        "OrderLineCommand",
        "ProcessedOrder",
        "ProcessedOrderLine",
    }
