class InvalidOrderBackendCommand(ValueError):  # noqa: N818 - domain exception
    def __init__(self, field: str, reason: str) -> None:
        self.field = field
        self.reason = reason
        super().__init__(f"{field}: {reason}")


class InvalidOrderLine(ValueError):  # noqa: N818 - domain exception
    def __init__(self, *, index: int, field: str, reason: str) -> None:
        self.index = index
        self.field = field
        self.reason = reason
        super().__init__(f"lines[{index}].{field}: {reason}")


class OrderBackendClosedError(RuntimeError):
    def __init__(self) -> None:
        super().__init__("order backend is closed")


class OrderBackendShutdownError(RuntimeError):
    def __init__(self, pending_count: int) -> None:
        self.pending_count = pending_count
        super().__init__(f"order backend shutdown left {pending_count} pending requests")
