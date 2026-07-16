from dataclasses import replace

import pytest

pytest.importorskip("bluetape.cache.redis")

from bluetape.serde import (
    FormatMismatchError,
    SerializedPayload,
    json_serialize,
)

from examples.cached_product_catalog import ProductSummary
from examples.redis_load_coordination.codec import (
    MAX_PRODUCT_PAYLOAD_SIZE,
    PRODUCT_METADATA,
    ProductSummaryCodec,
)


def test_product_summary_codec_round_trips_exact_value() -> None:
    codec = ProductSummaryCodec()
    product = ProductSummary(product_id="SKU-42", name="Blue Mug", price_cents=1299)

    payload = codec.encode(product)

    assert payload.metadata == PRODUCT_METADATA
    assert codec.decode(payload) == product


def test_product_summary_codec_rejects_non_exact_input() -> None:
    codec = ProductSummaryCodec()

    with pytest.raises(TypeError, match="exact ProductSummary"):
        codec.encode({"product_id": "SKU-42"})  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "document",
    [
        {},
        {"product_id": "SKU-42", "name": "Blue Mug"},
        {
            "product_id": "SKU-42",
            "name": "Blue Mug",
            "price_cents": 1299,
            "extra": "not allowed",
        },
        {"product_id": "", "name": "Blue Mug", "price_cents": 1299},
        {"product_id": "SKU-42", "name": "", "price_cents": 1299},
        {"product_id": "SKU-42", "name": "Blue Mug", "price_cents": True},
        {"product_id": "SKU-42", "name": "Blue Mug", "price_cents": -1},
    ],
)
def test_product_summary_codec_rejects_invalid_document(document: object) -> None:
    codec = ProductSummaryCodec()
    payload = json_serialize(
        document,  # type: ignore[arg-type]
        metadata=PRODUCT_METADATA,
        max_output_size=MAX_PRODUCT_PAYLOAD_SIZE,
        max_nesting_depth=2,
    )

    with pytest.raises((TypeError, ValueError)):
        codec.decode(payload)


def test_product_summary_codec_rejects_wrong_metadata() -> None:
    codec = ProductSummaryCodec()
    payload = SerializedPayload(
        metadata=replace(PRODUCT_METADATA, format="text"),
        data=b"{}",
    )

    with pytest.raises(FormatMismatchError):
        codec.decode(payload)


def test_product_summary_codec_rejects_oversized_or_invalid_utf8() -> None:
    codec = ProductSummaryCodec()

    with pytest.raises(ValueError):
        codec.decode(
            SerializedPayload(
                metadata=PRODUCT_METADATA,
                data=b"x" * (MAX_PRODUCT_PAYLOAD_SIZE + 1),
            )
        )
    with pytest.raises(ValueError):
        codec.decode(SerializedPayload(metadata=PRODUCT_METADATA, data=b"\xff"))
