from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from copy import deepcopy
from dataclasses import replace
from pathlib import Path

import pytest

if importlib.util.find_spec("pyfory") is None:
    pytest.skip("optional Apache Fory provider is not installed", allow_module_level=True)

from bluetape.codec import base64url_decode, base64url_encode
from bluetape.compression import DecompressionLimitError, GzipCompressor
from bluetape.serde import (
    ContentTypeMismatchError,
    FormatMismatchError,
    MalformedPayloadError,
    PayloadLimitError,
    PayloadMetadata,
    SchemaMismatchError,
    TrustProfile,
    TrustProfileMismatchError,
    TypeMismatchError,
    UnsupportedVersionError,
)
from bluetape.serde.fory import (
    ForyAdapter,
    ForyLimits,
    ForyRegistration,
)

from examples.bounded_payload_processing import (
    EncodedPayload,
    OrderSnapshot,
    TransportLimitError,
    UnsupportedCompressionError,
    UnsupportedEncodingError,
)
from examples.bounded_payload_processing.fory_service import (
    FORY_METADATA,
    ForyPayloadService,
)

ROOT = Path(__file__).resolve().parents[3]


def make_adapter(*, max_input_size: int = 4096, max_output_size: int = 4096) -> ForyAdapter:
    return ForyAdapter(
        registration=ForyRegistration(
            python_type=OrderSnapshot,
            schema_id=1001,
            schema_version=1,
            type_id=1001,
            logical_name="workshop.order_snapshot",
        ),
        limits=ForyLimits(
            max_input_size=max_input_size,
            max_output_size=max_output_size,
            max_concurrency=2,
        ),
    )


def make_service() -> ForyPayloadService:
    return ForyPayloadService(
        adapter=make_adapter(),
        compressor=GzipCompressor(max_output_size=4096),
        max_encoded_size=8192,
        max_compressed_size=4096,
    )


def test_fixed_registration_and_trusted_metadata() -> None:
    adapter = make_adapter()
    service = ForyPayloadService(
        adapter=adapter,
        compressor=GzipCompressor(max_output_size=4096),
        max_encoded_size=8192,
        max_compressed_size=4096,
    )

    assert adapter.registration.python_type is OrderSnapshot
    assert adapter.registration.schema_id == 1001
    assert adapter.registration.schema_version == 1
    assert adapter.registration.type_id == 1001
    assert adapter.registration.logical_name == "workshop.order_snapshot"
    assert service.metadata == FORY_METADATA
    assert service.metadata.trust_profile is TrustProfile.TRUSTED_INTERNAL


@pytest.mark.parametrize("product_ids", [[], ["SKU-1", "SKU-2"]])
def test_fory_round_trip_preserves_caller_input(product_ids: list[str]) -> None:
    service = make_service()
    snapshot = OrderSnapshot(
        order_id="ORDER-1",
        product_ids=product_ids,
        total_cents=25_000,
    )
    original = deepcopy(snapshot)

    payload = service.encode(snapshot)
    decoded = service.decode(payload)

    assert decoded == original
    assert snapshot == original
    assert decoded is not snapshot
    assert decoded.product_ids is not snapshot.product_ids
    assert payload.metadata == FORY_METADATA
    assert payload.compression == "gzip"
    assert payload.encoding == "base64url"


@pytest.mark.parametrize(
    ("metadata", "error_type"),
    [
        (
            PayloadMetadata(
                format="json",
                version=1,
                content_type="application/x-apache-fory",
                trust_profile=TrustProfile.TRUSTED_INTERNAL,
            ),
            FormatMismatchError,
        ),
        (
            PayloadMetadata(
                format="apache-fory-xlang",
                version=2,
                content_type="application/x-apache-fory",
                trust_profile=TrustProfile.TRUSTED_INTERNAL,
            ),
            UnsupportedVersionError,
        ),
        (
            PayloadMetadata(
                format="apache-fory-xlang",
                version=1,
                content_type="application/octet-stream",
                trust_profile=TrustProfile.TRUSTED_INTERNAL,
            ),
            ContentTypeMismatchError,
        ),
        (
            PayloadMetadata(
                format="apache-fory-xlang",
                version=1,
                content_type="application/x-apache-fory",
                trust_profile=TrustProfile.UNTRUSTED,
            ),
            TrustProfileMismatchError,
        ),
    ],
)
def test_fory_metadata_mismatch_precedes_codec(
    monkeypatch: pytest.MonkeyPatch,
    metadata: PayloadMetadata,
    error_type: type[Exception],
) -> None:
    import examples.bounded_payload_processing.fory_service as module

    service = make_service()
    payload = replace(
        service.encode(OrderSnapshot(order_id="ORDER-1", product_ids=[], total_cents=0)),
        metadata=metadata,
    )
    monkeypatch.setattr(
        module,
        "base64url_decode",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("codec must not run")),
    )

    with pytest.raises(error_type):
        service.decode(payload)


@pytest.mark.parametrize(
    ("field", "value", "error_type"),
    [
        ("encoding", "hex", UnsupportedEncodingError),
        ("compression", "zlib", UnsupportedCompressionError),
    ],
)
def test_fory_transport_substitution_precedes_codec(
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    value: str,
    error_type: type[Exception],
) -> None:
    import examples.bounded_payload_processing.fory_service as module

    service = make_service()
    payload = replace(
        service.encode(OrderSnapshot(order_id="ORDER-1", product_ids=[], total_cents=0)),
        **{field: value},
    )
    monkeypatch.setattr(
        module,
        "base64url_decode",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("codec must not run")),
    )

    with pytest.raises(error_type):
        service.decode(payload)


def test_fory_transport_limits_precede_downstream_stages(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import examples.bounded_payload_processing.fory_service as module

    service = ForyPayloadService(
        adapter=make_adapter(max_input_size=128),
        compressor=GzipCompressor(max_output_size=128),
        max_encoded_size=4,
        max_compressed_size=2,
    )
    oversized_encoded = EncodedPayload(
        metadata=FORY_METADATA,
        compression="gzip",
        encoding="base64url",
        data="12345",
    )
    monkeypatch.setattr(
        module,
        "base64url_decode",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("codec must not run")),
    )
    with pytest.raises(TransportLimitError) as encoded_error:
        service.decode(oversized_encoded)
    assert encoded_error.value.stage == "encoded"

    monkeypatch.undo()
    oversized_compressed = replace(oversized_encoded, data=base64url_encode(b"abc"))
    monkeypatch.setattr(
        GzipCompressor,
        "decompress",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("decompress must not run")),
    )
    with pytest.raises(TransportLimitError) as compressed_error:
        service.decode(oversized_compressed)
    assert compressed_error.value.stage == "compressed"


def test_fory_decompression_limit_precedes_deserialization() -> None:
    service = ForyPayloadService(
        adapter=make_adapter(max_input_size=20),
        compressor=GzipCompressor(max_output_size=20),
        max_encoded_size=1024,
        max_compressed_size=1024,
    )
    payload = EncodedPayload(
        metadata=FORY_METADATA,
        compression="gzip",
        encoding="base64url",
        data=base64url_encode(GzipCompressor().compress(b"serialized data over eight bytes")),
    )

    with pytest.raises(DecompressionLimitError):
        service.decode(payload)


def test_fory_rejects_malformed_serialized_input() -> None:
    service = make_service()
    payload = EncodedPayload(
        metadata=FORY_METADATA,
        compression="gzip",
        encoding="base64url",
        data=base64url_encode(GzipCompressor().compress(b"not-fory")),
    )

    with pytest.raises(MalformedPayloadError):
        service.decode(payload)


@pytest.mark.parametrize(
    ("offset", "error_type"),
    [(9, SchemaMismatchError), (15, TypeMismatchError)],
)
def test_fory_rejects_tampered_schema_and_type(
    offset: int,
    error_type: type[Exception],
) -> None:
    service = make_service()
    payload = service.encode(
        OrderSnapshot(order_id="ORDER-1", product_ids=["SKU-1"], total_cents=100)
    )
    serialized = bytearray(GzipCompressor().decompress(base64url_decode(payload.data)))
    serialized[offset] ^= 1
    tampered = replace(
        payload,
        data=base64url_encode(GzipCompressor().compress(bytes(serialized))),
    )

    with pytest.raises(error_type):
        service.decode(tampered)


def test_fory_adapter_output_limit_remains_visible() -> None:
    service = ForyPayloadService(
        adapter=make_adapter(max_input_size=4096, max_output_size=64),
        compressor=GzipCompressor(max_output_size=4096),
        max_encoded_size=8192,
        max_compressed_size=4096,
    )
    snapshot = OrderSnapshot(
        order_id="ORDER-1",
        product_ids=["X" * 256],
        total_cents=100,
    )

    with pytest.raises(PayloadLimitError):
        service.encode(snapshot)


def test_fory_rejects_wrong_root_type() -> None:
    service = make_service()

    with pytest.raises(TypeMismatchError):
        service.encode(object())  # type: ignore[arg-type]


def test_fory_cli_emits_safe_trusted_internal_events() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "examples.bounded_payload_processing.fory_demo"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert completed.returncode == 0, completed.stderr
    events = [json.loads(line) for line in completed.stdout.splitlines()]
    assert [event["event"] for event in events] == [
        "profile_selected",
        "encoded",
        "decoded",
    ]
    assert events[0] == {
        "event": "profile_selected",
        "format": "apache-fory-xlang",
        "trust_profile": "trusted_internal",
    }
    assert events[2] == {"event": "decoded", "result": "round_trip_ok"}
    assert "ORDER-2001" not in completed.stdout
    assert "SKU-9" not in completed.stdout
