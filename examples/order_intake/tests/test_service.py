import importlib
from dataclasses import FrozenInstanceError
from types import ModuleType

import pytest


def _load_api() -> ModuleType:
    try:
        return importlib.import_module("examples.order_intake")
    except ModuleNotFoundError as error:
        pytest.fail(f"order intake API is missing: {error}")


def test_command_and_result_are_immutable_values() -> None:
    api = _load_api()
    command = api.PartnerOrderCommand(
        request_id="req-1",
        partner_id="partner-1",
        order_id="order-1",
        sku="sku-1",
        quantity=2,
    )
    accepted = api.AcceptedOrder(
        request_id="req-1",
        partner_id="partner-1",
        order_id="order-1",
        sku="sku-1",
        quantity=2,
    )

    assert accepted.status == "accepted"
    with pytest.raises(FrozenInstanceError):
        command.quantity = 3  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        accepted.status = "rejected"  # type: ignore[misc]


def test_invalid_order_maps_to_a_safe_immutable_problem() -> None:
    api = _load_api()
    error = api.InvalidOrderCommand("sku", "must not be blank")

    assert str(error) == "sku: must not be blank"
    assert api.map_order_error(error) == api.OrderIntakeProblem(
        code="invalid_order_command",
        field="sku",
        message="sku must not be blank",
    )
    with pytest.raises(FrozenInstanceError):
        api.map_order_error(error).field = "other"  # type: ignore[misc]
