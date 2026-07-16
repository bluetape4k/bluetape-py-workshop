from typing import cast

from bluetape.serde import (
    JsonValue,
    PayloadMetadata,
    SerializedPayload,
    TrustProfile,
    json_deserialize,
    json_serialize,
)

from examples.cached_product_catalog import ProductSummary

MAX_PRODUCT_PAYLOAD_SIZE = 4_096
MAX_PRODUCT_ID_LENGTH = 64
MAX_PRODUCT_NAME_LENGTH = 256
PRODUCT_METADATA = PayloadMetadata(
    format="json",
    version=1,
    content_type="application/json",
    trust_profile=TrustProfile.UNTRUSTED,
)
_PRODUCT_FIELDS = {"product_id", "name", "price_cents"}


def _bounded_text(value: object, *, field: str, maximum: int) -> str:
    if type(value) is not str:
        raise TypeError(f"{field} must be an exact str")
    if not value or value != value.strip():
        raise ValueError(f"{field} must be non-blank without surrounding whitespace")
    if len(value) > maximum:
        raise ValueError(f"{field} exceeds its supported length")
    return value


class ProductSummaryCodec:
    """Encode one bounded product summary as strict untrusted JSON."""

    def encode(self, value: ProductSummary) -> SerializedPayload:
        if type(value) is not ProductSummary:
            raise TypeError("value must be an exact ProductSummary")
        product_id = _bounded_text(
            value.product_id,
            field="product_id",
            maximum=MAX_PRODUCT_ID_LENGTH,
        )
        name = _bounded_text(value.name, field="name", maximum=MAX_PRODUCT_NAME_LENGTH)
        if type(value.price_cents) is not int:
            raise TypeError("price_cents must be an exact int")
        if value.price_cents < 0:
            raise ValueError("price_cents must be non-negative")
        document: dict[str, JsonValue] = {
            "product_id": product_id,
            "name": name,
            "price_cents": value.price_cents,
        }
        return json_serialize(
            document,
            metadata=PRODUCT_METADATA,
            max_output_size=MAX_PRODUCT_PAYLOAD_SIZE,
            max_nesting_depth=2,
        )

    def decode(self, payload: SerializedPayload) -> ProductSummary:
        document = json_deserialize(
            payload,
            expected_metadata=PRODUCT_METADATA,
            max_input_size=MAX_PRODUCT_PAYLOAD_SIZE,
            max_nesting_depth=2,
        )
        if type(document) is not dict:
            raise TypeError("product payload must be an exact object")
        if set(document) != _PRODUCT_FIELDS:
            raise ValueError("product payload fields do not match the contract")
        product_id = _bounded_text(
            document["product_id"],
            field="product_id",
            maximum=MAX_PRODUCT_ID_LENGTH,
        )
        name = _bounded_text(
            document["name"],
            field="name",
            maximum=MAX_PRODUCT_NAME_LENGTH,
        )
        price_cents = document["price_cents"]
        if type(price_cents) is not int:
            raise TypeError("price_cents must be an exact int")
        if price_cents < 0:
            raise ValueError("price_cents must be non-negative")
        return ProductSummary(
            product_id=product_id,
            name=name,
            price_cents=cast(int, price_cents),
        )
