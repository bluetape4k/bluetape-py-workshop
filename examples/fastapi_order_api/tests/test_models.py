import importlib
from types import ModuleType

import pytest

pytest.importorskip("fastapi", reason="requires the fastapi-order-api extra")

from pydantic import ValidationError

from examples.integrated_order_backend.models import OrderBackendCommand, OrderLineCommand


def _load_models() -> ModuleType:
    try:
        return importlib.import_module("examples.fastapi_order_api.models")
    except ModuleNotFoundError as error:
        pytest.fail(f"FastAPI order models are missing: {error}")


def _valid_body() -> dict[str, object]:
    return {
        "partner_id": "partner-7",
        "order_id": "order-9001",
        "lines": [{"sku": "SKU-1", "quantity": 2}],
    }


def test_order_request_converts_to_exact_backend_command() -> None:
    models = _load_models()
    payload = models.OrderRequest.model_validate(_valid_body())

    assert payload.to_command("req-1001") == OrderBackendCommand(
        request_id="req-1001",
        partner_id="partner-7",
        order_id="order-9001",
        lines=(OrderLineCommand(sku="SKU-1", quantity=2),),
    )


@pytest.mark.parametrize(
    ("target", "field"),
    [
        ("request", "unexpected"),
        ("line", "unexpected"),
    ],
)
def test_unknown_fields_are_rejected(target: str, field: str) -> None:
    models = _load_models()
    body = _valid_body()
    if target == "request":
        body[field] = "value"
    else:
        line = body["lines"][0]
        assert isinstance(line, dict)
        line[field] = "value"

    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        models.OrderRequest.model_validate(body)


@pytest.mark.parametrize("quantity", [True, False, 1.0, 2.5, "2", 0, 1_000_001])
def test_quantity_is_a_strict_bounded_integer(quantity: object) -> None:
    models = _load_models()
    body = _valid_body()
    line = body["lines"][0]
    assert isinstance(line, dict)
    line["quantity"] = quantity

    with pytest.raises(ValidationError):
        models.OrderRequest.model_validate(body)


@pytest.mark.parametrize("line_count", [0, 101])
def test_line_count_is_bounded(line_count: int) -> None:
    models = _load_models()
    body = _valid_body()
    body["lines"] = [{"sku": "SKU-1", "quantity": 1}] * line_count

    with pytest.raises(ValidationError):
        models.OrderRequest.model_validate(body)


@pytest.mark.parametrize("field", ["partner_id", "order_id"])
def test_request_identifiers_are_bounded(field: str) -> None:
    models = _load_models()
    body = _valid_body()
    body[field] = "x" * 129

    with pytest.raises(ValidationError):
        models.OrderRequest.model_validate(body)


def test_sku_is_bounded() -> None:
    models = _load_models()
    body = _valid_body()
    line = body["lines"][0]
    assert isinstance(line, dict)
    line["sku"] = "x" * 129

    with pytest.raises(ValidationError):
        models.OrderRequest.model_validate(body)


@pytest.mark.parametrize("value", [" ", "   "])
def test_whitespace_only_identifiers_reach_domain_validation(value: str) -> None:
    models = _load_models()
    body = _valid_body()
    body["partner_id"] = value
    line = body["lines"][0]
    assert isinstance(line, dict)
    line["sku"] = value

    command = models.OrderRequest.model_validate(body).to_command("req-1001")

    assert command.partner_id == value
    assert command.lines[0].sku == value


def test_response_and_problem_models_are_explicit_and_frozen() -> None:
    models = _load_models()
    response = models.OrderResponse(
        request_id="req-1001",
        partner_id="partner-7",
        order_id="order-9001",
        line_count=1,
        total_cents=2_500,
        warning_count=0,
    )
    problem = models.OrderProblem(
        code="invalid_order",
        message="order is invalid",
        request_id="req-1001",
        field="sku",
        line_index=0,
    )

    assert set(response.model_dump()) == {
        "request_id",
        "partner_id",
        "order_id",
        "line_count",
        "total_cents",
        "warning_count",
    }
    assert set(problem.model_dump()) == {
        "code",
        "message",
        "request_id",
        "field",
        "line_index",
    }
    with pytest.raises(ValidationError):
        models.OrderResponse.model_validate({**response.model_dump(), "artifact": "secret"})
    with pytest.raises(ValidationError):
        models.OrderProblem.model_validate({**problem.model_dump(), "detail": "secret"})
    with pytest.raises(ValidationError, match="frozen"):
        response.total_cents = 3_000
