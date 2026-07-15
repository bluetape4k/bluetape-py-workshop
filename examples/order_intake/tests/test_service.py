import importlib
import logging
from dataclasses import FrozenInstanceError, replace
from types import ModuleType

import pytest
from bluetape.logging import ContextLogFilter, get_log_context
from bluetape.testing import eventually


def _load_api() -> ModuleType:
    try:
        return importlib.import_module("examples.order_intake")
    except ModuleNotFoundError as error:
        pytest.fail(f"order intake API is missing: {error}")


class CaptureHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__(logging.INFO)
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


@pytest.fixture
def log_capture():
    root = logging.getLogger()
    root_before = (root.level, tuple(root.handlers), tuple(root.filters))
    logger = logging.Logger("order-intake-test", level=logging.INFO)
    logger.propagate = False
    handler = CaptureHandler()
    handler.addFilter(ContextLogFilter())
    logger.addHandler(handler)
    try:
        yield logger, handler
    finally:
        logger.removeHandler(handler)
        handler.close()
        assert (root.level, tuple(root.handlers), tuple(root.filters)) == root_before


def valid_command():
    return _load_api().PartnerOrderCommand(
        request_id=" req-1 ",
        partner_id="partner-1",
        order_id="order-1",
        sku=" sku-1 ",
        quantity=2,
    )


def make_service(logger: object):
    service_type = getattr(_load_api(), "OrderIntakeService", None)
    assert service_type is not None, "OrderIntakeService is not exported"
    return service_type(logger)


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


def test_accept_preserves_values_and_captures_context(log_capture) -> None:
    logger, handler = log_capture
    command = valid_command()

    result = make_service(logger).accept(command)

    assert result == _load_api().AcceptedOrder(
        request_id=" req-1 ",
        partner_id="partner-1",
        order_id="order-1",
        sku=" sku-1 ",
        quantity=2,
    )
    assert command == valid_command()
    record = handler.records[-1]
    assert record.getMessage() == "order_intake.accepted"
    assert record.request_id == " req-1 "
    assert record.partner_id == "partner-1"
    assert record.order_id == "order-1"
    assert "sku" not in record.__dict__
    assert "quantity" not in record.__dict__
    assert "sku-1" not in record.getMessage()
    assert get_log_context() == {}


@pytest.mark.parametrize("field", ["request_id", "partner_id", "order_id", "sku"])
@pytest.mark.parametrize("value", ["", "   "])
def test_blank_text_is_rejected(field: str, value: str, log_capture) -> None:
    logger, handler = log_capture
    with pytest.raises(_load_api().InvalidOrderCommand) as raised:
        make_service(logger).accept(replace(valid_command(), **{field: value}))
    assert raised.value.field == field
    assert isinstance(raised.value.__cause__, ValueError)
    assert handler.records[-1].getMessage() == "order_intake.rejected"
    assert handler.records[-1].error_field == field
    assert get_log_context() == {}


@pytest.mark.parametrize("field", ["request_id", "partner_id", "order_id", "sku"])
def test_non_string_text_is_rejected(field: str, log_capture) -> None:
    logger, _ = log_capture
    with pytest.raises(_load_api().InvalidOrderCommand) as raised:
        make_service(logger).accept(replace(valid_command(), **{field: 7}))
    assert raised.value.field == field
    assert isinstance(raised.value.__cause__, TypeError)
    assert get_log_context() == {}


@pytest.mark.parametrize("quantity", [True, False, 1.5, "2", None, 0, -1])
def test_invalid_quantity_is_rejected(quantity: object, log_capture) -> None:
    logger, _ = log_capture
    with pytest.raises(_load_api().InvalidOrderCommand) as raised:
        make_service(logger).accept(replace(valid_command(), quantity=quantity))
    assert raised.value.field == "quantity"
    assert isinstance(raised.value.__cause__, TypeError | ValueError)
    assert get_log_context() == {}


def test_invalid_command_type_is_mapped(log_capture) -> None:
    logger, handler = log_capture
    with pytest.raises(_load_api().InvalidOrderCommand) as raised:
        make_service(logger).accept(object())  # type: ignore[arg-type]
    assert raised.value.field == "command"
    assert isinstance(raised.value.__cause__, TypeError)
    assert handler.records[-1].request_id == "<invalid>"
    assert get_log_context() == {}


def test_service_requires_a_real_logger() -> None:
    with pytest.raises(TypeError, match="logger must be Logger"):
        make_service(object())  # type: ignore[arg-type]


def test_invalid_identifier_is_not_rendered_for_context(log_capture) -> None:
    class HostileValue:
        def __str__(self) -> str:
            raise AssertionError("str called")

        def __repr__(self) -> str:
            raise AssertionError("repr called")

    logger, handler = log_capture
    command = replace(valid_command(), request_id=HostileValue())
    with pytest.raises(_load_api().InvalidOrderCommand):
        make_service(logger).accept(command)
    assert handler.records[-1].request_id == "<invalid>"
    assert get_log_context() == {}


def test_root_logger_state_is_unchanged(log_capture) -> None:
    logger, _ = log_capture
    make_service(logger).accept(valid_command())


def test_eventually_api_demo_observes_an_existing_record(log_capture) -> None:
    logger, handler = log_capture
    make_service(logger).accept(valid_command())
    record = eventually(
        lambda: next(
            (item for item in handler.records if item.msg == "order_intake.accepted"),
            None,
        ),
        timeout=0.02,
        interval=0.001,
    )
    assert record is handler.records[-1]


def test_logger_failure_propagates_and_context_resets() -> None:
    class FailingHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            raise RuntimeError("logging unavailable")

    logger = logging.Logger("order-intake-failure", level=logging.INFO)
    logger.propagate = False
    handler = FailingHandler()
    logger.addHandler(handler)
    try:
        with pytest.raises(RuntimeError, match="logging unavailable"):
            make_service(logger).accept(valid_command())
    finally:
        logger.removeHandler(handler)
        handler.close()
    assert get_log_context() == {}
