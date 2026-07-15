from dataclasses import dataclass
from typing import Literal


class InvalidOrderCommand(ValueError):  # noqa: N818 - approved domain exception name
    def __init__(self, field: str, reason: str) -> None:
        self.field = field
        self.reason = reason
        super().__init__(f"{field}: {reason}")


@dataclass(frozen=True, slots=True, kw_only=True)
class OrderIntakeProblem:
    code: Literal["invalid_order_command"]
    field: str
    message: str


def map_order_error(error: InvalidOrderCommand) -> OrderIntakeProblem:
    return OrderIntakeProblem(
        code="invalid_order_command",
        field=error.field,
        message=f"{error.field} {error.reason}",
    )
