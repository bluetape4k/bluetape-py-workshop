from dataclasses import dataclass

from bluetape.serde import PayloadMetadata


@dataclass(frozen=True, slots=True, kw_only=True)
class EncodedPayload:
    metadata: PayloadMetadata
    compression: str
    encoding: str
    data: str

    def __post_init__(self) -> None:
        if type(self.metadata) is not PayloadMetadata:
            raise TypeError("metadata must be an exact PayloadMetadata")
        for name in ("compression", "encoding", "data"):
            value = getattr(self, name)
            if type(value) is not str:
                raise TypeError(f"{name} must be an exact str")
        if not self.compression:
            raise ValueError("compression must not be empty")
        if not self.encoding:
            raise ValueError("encoding must not be empty")


@dataclass(slots=True, kw_only=True)
class OrderSnapshot:
    order_id: str
    product_ids: list[str]
    total_cents: int
