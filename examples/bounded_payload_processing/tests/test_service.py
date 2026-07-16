from copy import deepcopy
from dataclasses import FrozenInstanceError, replace

import pytest
from bluetape.codec import CodecError, base64url_encode
from bluetape.compression import CompressionError, DecompressionLimitError, GzipCompressor
from bluetape.serde import (
    ContentTypeMismatchError,
    FormatMismatchError,
    MalformedPayloadError,
    PayloadLimitError,
    PayloadMetadata,
    TrustProfile,
    TrustProfileMismatchError,
    UnsupportedVersionError,
)

from examples.bounded_payload_processing import (
    EncodedPayload,
    JsonPayloadService,
    OrderSnapshot,
    TransportLimitError,
    UnsupportedCompressionError,
    UnsupportedEncodingError,
)
from examples.bounded_payload_processing import service as service_module


def make_service(*, max_serialized_size: int = 4096) -> JsonPayloadService:
    return JsonPayloadService(
        compressor=GzipCompressor(max_output_size=max_serialized_size),
        max_encoded_size=8192,
        max_compressed_size=4096,
        max_serialized_size=max_serialized_size,
        max_nesting_depth=16,
    )


def test_models_are_keyword_only_and_slotted_with_an_immutable_envelope() -> None:
    metadata = PayloadMetadata(
        format="json",
        version=1,
        content_type="application/json",
        trust_profile=TrustProfile.UNTRUSTED,
    )
    payload = EncodedPayload(
        metadata=metadata,
        compression="gzip",
        encoding="base64url",
        data="abc",
    )
    snapshot = OrderSnapshot(order_id="ORDER-1", product_ids=["SKU-1"], total_cents=100)

    assert not hasattr(payload, "__dict__")
    assert not hasattr(snapshot, "__dict__")
    with pytest.raises(FrozenInstanceError):
        payload.data = "changed"  # type: ignore[misc]
    with pytest.raises(TypeError):
        EncodedPayload(metadata, "gzip", "base64url", "abc")  # type: ignore[misc]
    with pytest.raises(TypeError):
        OrderSnapshot("ORDER-1", ["SKU-1"], 100)  # type: ignore[misc]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("metadata", object()),
        ("compression", 1),
        ("encoding", b"base64url"),
        ("data", b"abc"),
    ],
)
def test_encoded_payload_requires_exact_field_types(field: str, value: object) -> None:
    arguments: dict[str, object] = {
        "metadata": PayloadMetadata(
            format="json",
            version=1,
            content_type="application/json",
            trust_profile=TrustProfile.UNTRUSTED,
        ),
        "compression": "gzip",
        "encoding": "base64url",
        "data": "abc",
    }
    arguments[field] = value

    with pytest.raises(TypeError):
        EncodedPayload(**arguments)  # type: ignore[arg-type]


@pytest.mark.parametrize("field", ["compression", "encoding"])
def test_encoded_payload_rejects_empty_transport_identifiers(field: str) -> None:
    arguments = {
        "metadata": PayloadMetadata(
            format="json",
            version=1,
            content_type="application/json",
            trust_profile=TrustProfile.UNTRUSTED,
        ),
        "compression": "gzip",
        "encoding": "base64url",
        "data": "abc",
    }
    arguments[field] = ""

    with pytest.raises(ValueError, match=field):
        EncodedPayload(**arguments)


def test_default_package_exports_only_provider_safe_contracts() -> None:
    import examples.bounded_payload_processing as package

    assert set(package.__all__) == {
        "EncodedPayload",
        "JsonPayloadService",
        "OrderSnapshot",
        "TransportLimitError",
        "UnsupportedCompressionError",
        "UnsupportedEncodingError",
    }
    assert not hasattr(package, "ForyPayloadService")


def test_json_service_round_trips_without_mutating_caller_input() -> None:
    service = make_service()
    document = {
        "order_id": "ORDER-1",
        "lines": [{"product_id": "SKU-1", "quantity": 2}],
        "tags": ["priority", "gift"],
    }
    original = deepcopy(document)

    encoded = service.encode(document)
    decoded = service.decode(encoded)

    assert encoded.metadata == service.metadata
    assert encoded.compression == "gzip"
    assert encoded.encoding == "base64url"
    assert "=" not in encoded.data
    assert decoded == original
    assert document == original
    assert decoded is not document


@pytest.mark.parametrize(
    ("metadata", "error_type"),
    [
        (
            PayloadMetadata(
                format="yaml",
                version=1,
                content_type="application/json",
                trust_profile=TrustProfile.UNTRUSTED,
            ),
            FormatMismatchError,
        ),
        (
            PayloadMetadata(
                format="json",
                version=2,
                content_type="application/json",
                trust_profile=TrustProfile.UNTRUSTED,
            ),
            UnsupportedVersionError,
        ),
        (
            PayloadMetadata(
                format="json",
                version=1,
                content_type="text/json",
                trust_profile=TrustProfile.UNTRUSTED,
            ),
            ContentTypeMismatchError,
        ),
        (
            PayloadMetadata(
                format="json",
                version=1,
                content_type="application/json",
                trust_profile=TrustProfile.TRUSTED_INTERNAL,
            ),
            TrustProfileMismatchError,
        ),
    ],
)
def test_metadata_mismatch_fails_before_codec(
    monkeypatch: pytest.MonkeyPatch,
    metadata: PayloadMetadata,
    error_type: type[Exception],
) -> None:
    service = make_service()
    payload = replace(service.encode({"ok": True}), metadata=metadata)
    codec_called = False

    def fail_if_called(value: str, *, padded: bool = False) -> bytes:
        nonlocal codec_called
        del value, padded
        codec_called = True
        raise AssertionError("codec must not run")

    monkeypatch.setattr(service_module, "base64url_decode", fail_if_called)

    with pytest.raises(error_type):
        service.decode(payload)
    assert not codec_called


@pytest.mark.parametrize(
    ("field", "value", "error_type"),
    [
        ("encoding", "hex", UnsupportedEncodingError),
        ("compression", "zlib", UnsupportedCompressionError),
    ],
)
def test_unsupported_transport_fails_before_codec(
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    value: str,
    error_type: type[Exception],
) -> None:
    service = make_service()
    payload = replace(service.encode({"ok": True}), **{field: value})

    monkeypatch.setattr(
        service_module,
        "base64url_decode",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("codec must not run")),
    )

    with pytest.raises(error_type):
        service.decode(payload)


def test_encoded_limit_fails_before_codec(monkeypatch: pytest.MonkeyPatch) -> None:
    service = JsonPayloadService(
        compressor=GzipCompressor(max_output_size=128),
        max_encoded_size=4,
        max_compressed_size=128,
        max_serialized_size=128,
        max_nesting_depth=8,
    )
    payload = EncodedPayload(
        metadata=service.metadata,
        compression="gzip",
        encoding="base64url",
        data="12345",
    )
    monkeypatch.setattr(
        service_module,
        "base64url_decode",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("codec must not run")),
    )

    with pytest.raises(TransportLimitError) as caught:
        service.decode(payload)
    assert caught.value.stage == "encoded"


def test_compressed_limit_fails_before_decompression(monkeypatch: pytest.MonkeyPatch) -> None:
    service = JsonPayloadService(
        compressor=GzipCompressor(max_output_size=128),
        max_encoded_size=128,
        max_compressed_size=2,
        max_serialized_size=128,
        max_nesting_depth=8,
    )
    payload = EncodedPayload(
        metadata=service.metadata,
        compression="gzip",
        encoding="base64url",
        data=base64url_encode(b"abc"),
    )
    monkeypatch.setattr(
        GzipCompressor,
        "decompress",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("decompress must not run")),
    )

    with pytest.raises(TransportLimitError) as caught:
        service.decode(payload)
    assert caught.value.stage == "compressed"


@pytest.mark.parametrize("data", ["*", "AB"])
def test_malformed_or_noncanonical_base64url_is_explicit(data: str) -> None:
    service = make_service()
    payload = EncodedPayload(
        metadata=service.metadata,
        compression="gzip",
        encoding="base64url",
        data=data,
    )

    with pytest.raises(CodecError):
        service.decode(payload)


@pytest.mark.parametrize(
    "compressed",
    [b"not-gzip", GzipCompressor().compress(b"{}") + b"trailing"],
)
def test_malformed_or_trailing_gzip_is_explicit(compressed: bytes) -> None:
    service = make_service()
    payload = EncodedPayload(
        metadata=service.metadata,
        compression="gzip",
        encoding="base64url",
        data=base64url_encode(compressed),
    )

    with pytest.raises(CompressionError):
        service.decode(payload)


def test_decompression_limit_is_explicit() -> None:
    compressor = GzipCompressor(max_output_size=8)
    service = JsonPayloadService(
        compressor=compressor,
        max_encoded_size=1024,
        max_compressed_size=1024,
        max_serialized_size=8,
        max_nesting_depth=8,
    )
    payload = EncodedPayload(
        metadata=service.metadata,
        compression="gzip",
        encoding="base64url",
        data=base64url_encode(GzipCompressor().compress(b'{"value":123}')),
    )

    with pytest.raises(DecompressionLimitError):
        service.decode(payload)


@pytest.mark.parametrize("serialized", [b"{", b'{"key":1,"key":2}', b"\xff"])
def test_malformed_serialized_json_is_explicit(serialized: bytes) -> None:
    service = make_service()
    payload = EncodedPayload(
        metadata=service.metadata,
        compression="gzip",
        encoding="base64url",
        data=base64url_encode(GzipCompressor().compress(serialized)),
    )

    with pytest.raises(MalformedPayloadError):
        service.decode(payload)


@pytest.mark.parametrize("value", [{}, [], "", None, False, 0])
def test_empty_and_scalar_json_values_round_trip(value: object) -> None:
    service = make_service()

    assert service.decode(service.encode(value)) == value


def test_exact_serialized_output_boundary_is_accepted() -> None:
    service = JsonPayloadService(
        compressor=GzipCompressor(max_output_size=2),
        max_encoded_size=128,
        max_compressed_size=128,
        max_serialized_size=2,
        max_nesting_depth=2,
    )

    assert service.decode(service.encode({})) == {}
    with pytest.raises(PayloadLimitError):
        service.encode({"a": 1})


@pytest.mark.parametrize(
    ("name", "value", "error_type"),
    [
        ("max_encoded_size", 0, ValueError),
        ("max_compressed_size", -1, ValueError),
        ("max_serialized_size", True, TypeError),
        ("max_nesting_depth", 0, ValueError),
    ],
)
def test_service_rejects_invalid_limits(
    name: str,
    value: object,
    error_type: type[Exception],
) -> None:
    arguments: dict[str, object] = {
        "compressor": GzipCompressor(max_output_size=128),
        "max_encoded_size": 128,
        "max_compressed_size": 128,
        "max_serialized_size": 128,
        "max_nesting_depth": 8,
    }
    arguments[name] = value

    with pytest.raises(error_type):
        JsonPayloadService(**arguments)  # type: ignore[arg-type]
