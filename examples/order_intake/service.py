import logging

from bluetape.core import require_instance, require_not_blank
from bluetape.logging import log_context

from .errors import InvalidOrderCommand
from .models import AcceptedOrder, PartnerOrderCommand

INVALID_CONTEXT_VALUE = "<invalid>"


def _safe_identifier(value: object) -> str:
    return value if isinstance(value, str) else INVALID_CONTEXT_VALUE


def _safe_context(command: object) -> dict[str, str]:
    if not isinstance(command, PartnerOrderCommand):
        return {
            "request_id": INVALID_CONTEXT_VALUE,
            "partner_id": INVALID_CONTEXT_VALUE,
            "order_id": INVALID_CONTEXT_VALUE,
        }
    return {
        "request_id": _safe_identifier(command.request_id),
        "partner_id": _safe_identifier(command.partner_id),
        "order_id": _safe_identifier(command.order_id),
    }


def _validated_text(value: object, field: str) -> str:
    try:
        return require_not_blank(require_instance(value, str, field), field)
    except TypeError as error:
        raise InvalidOrderCommand(field, "must be text") from error
    except ValueError as error:
        raise InvalidOrderCommand(field, "must not be blank") from error


def _validated_quantity(value: object) -> int:
    if isinstance(value, bool):
        error = TypeError("quantity must be int")
        raise InvalidOrderCommand("quantity", "must be an integer") from error
    try:
        quantity = require_instance(value, int, "quantity")
    except TypeError as error:
        raise InvalidOrderCommand("quantity", "must be an integer") from error
    if quantity <= 0:
        error = ValueError("quantity must be greater than 0")
        raise InvalidOrderCommand("quantity", "must be greater than 0") from error
    return quantity


class OrderIntakeService:
    def __init__(self, logger: logging.Logger) -> None:
        self._logger = require_instance(logger, logging.Logger, "logger")

    def accept(self, command: PartnerOrderCommand) -> AcceptedOrder:
        with log_context(**_safe_context(command)):
            try:
                typed = require_instance(command, PartnerOrderCommand, "command")
                request_id = _validated_text(typed.request_id, "request_id")
                partner_id = _validated_text(typed.partner_id, "partner_id")
                order_id = _validated_text(typed.order_id, "order_id")
                sku = _validated_text(typed.sku, "sku")
                quantity = _validated_quantity(typed.quantity)
            except InvalidOrderCommand as error:
                self._logger.warning(
                    "order_intake.rejected",
                    extra={"error_field": error.field},
                )
                raise
            except TypeError as error:
                mapped = InvalidOrderCommand("command", "must be PartnerOrderCommand")
                self._logger.warning(
                    "order_intake.rejected",
                    extra={"error_field": mapped.field},
                )
                raise mapped from error

            result = AcceptedOrder(
                request_id=request_id,
                partner_id=partner_id,
                order_id=order_id,
                sku=sku,
                quantity=quantity,
            )
            self._logger.info("order_intake.accepted")
            return result
