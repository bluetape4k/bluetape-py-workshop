from typing import Literal


class UnsupportedEncodingError(ValueError):
    def __init__(self, actual: str) -> None:
        self.actual = actual
        super().__init__(f"unsupported encoding: {actual}")


class UnsupportedCompressionError(ValueError):
    def __init__(self, actual: str) -> None:
        self.actual = actual
        super().__init__(f"unsupported compression: {actual}")


class TransportLimitError(ValueError):
    def __init__(
        self,
        *,
        stage: Literal["encoded", "compressed"],
        actual_size: int,
        limit: int,
    ) -> None:
        self.stage = stage
        self.actual_size = actual_size
        self.limit = limit
        super().__init__(f"{stage} payload size {actual_size} exceeds limit {limit}")
