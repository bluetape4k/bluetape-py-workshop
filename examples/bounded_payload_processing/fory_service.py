from bluetape.codec import base64url_decode, base64url_encode
from bluetape.compression import GzipCompressor
from bluetape.serde import (
    ContentTypeMismatchError,
    FormatMismatchError,
    PayloadMetadata,
    SerializedPayload,
    TrustProfile,
    TrustProfileMismatchError,
    UnsupportedVersionError,
)
from bluetape.serde.fory import (
    FORY_CONTENT_TYPE,
    FORY_FORMAT,
    FORY_VERSION,
    ForyAdapter,
)

from .errors import (
    TransportLimitError,
    UnsupportedCompressionError,
    UnsupportedEncodingError,
)
from .models import EncodedPayload, OrderSnapshot

FORY_METADATA = PayloadMetadata(
    format=FORY_FORMAT,
    version=FORY_VERSION,
    content_type=FORY_CONTENT_TYPE,
    trust_profile=TrustProfile.TRUSTED_INTERNAL,
)


def _require_positive_exact_int(name: str, value: object) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact int")
    if value <= 0:
        raise ValueError(f"{name} must be positive")
    return value


def _validate_fory_metadata(metadata: PayloadMetadata) -> None:
    if metadata.format != FORY_METADATA.format:
        raise FormatMismatchError
    if metadata.version != FORY_METADATA.version:
        raise UnsupportedVersionError
    if metadata.content_type != FORY_METADATA.content_type:
        raise ContentTypeMismatchError
    if metadata.trust_profile is not FORY_METADATA.trust_profile:
        raise TrustProfileMismatchError


class ForyPayloadService:
    __slots__ = (
        "_adapter",
        "_compressor",
        "_max_compressed_size",
        "_max_encoded_size",
    )

    def __init__(
        self,
        *,
        adapter: ForyAdapter[OrderSnapshot],
        compressor: GzipCompressor,
        max_encoded_size: int,
        max_compressed_size: int,
    ) -> None:
        if type(adapter) is not ForyAdapter:
            raise TypeError("adapter must be an exact ForyAdapter")
        if adapter.registration.python_type is not OrderSnapshot:
            raise TypeError("adapter must register OrderSnapshot")
        if type(compressor) is not GzipCompressor:
            raise TypeError("compressor must be an exact GzipCompressor")
        self._max_encoded_size = _require_positive_exact_int("max_encoded_size", max_encoded_size)
        self._max_compressed_size = _require_positive_exact_int(
            "max_compressed_size", max_compressed_size
        )
        if compressor.max_output_size > adapter.limits.max_input_size:
            raise ValueError("compressor output limit must not exceed Fory input limit")
        self._adapter = adapter
        self._compressor = compressor

    @property
    def metadata(self) -> PayloadMetadata:
        return FORY_METADATA

    def encode(self, value: OrderSnapshot) -> EncodedPayload:
        serialized = self._adapter.serialize(value, metadata=FORY_METADATA)
        compressed = self._compressor.compress(serialized.data)
        if len(compressed) > self._max_compressed_size:
            raise TransportLimitError(
                stage="compressed",
                actual_size=len(compressed),
                limit=self._max_compressed_size,
            )
        encoded = base64url_encode(compressed)
        if len(encoded) > self._max_encoded_size:
            raise TransportLimitError(
                stage="encoded",
                actual_size=len(encoded),
                limit=self._max_encoded_size,
            )
        return EncodedPayload(
            metadata=FORY_METADATA,
            compression="gzip",
            encoding="base64url",
            data=encoded,
        )

    def decode(self, payload: EncodedPayload) -> OrderSnapshot:
        if type(payload) is not EncodedPayload:
            raise TypeError("payload must be an exact EncodedPayload")
        if payload.encoding != "base64url":
            raise UnsupportedEncodingError(payload.encoding)
        if payload.compression != "gzip":
            raise UnsupportedCompressionError(payload.compression)
        _validate_fory_metadata(payload.metadata)
        if len(payload.data) > self._max_encoded_size:
            raise TransportLimitError(
                stage="encoded",
                actual_size=len(payload.data),
                limit=self._max_encoded_size,
            )
        compressed = base64url_decode(payload.data)
        if len(compressed) > self._max_compressed_size:
            raise TransportLimitError(
                stage="compressed",
                actual_size=len(compressed),
                limit=self._max_compressed_size,
            )
        serialized = SerializedPayload(
            metadata=payload.metadata,
            data=self._compressor.decompress(compressed),
        )
        return self._adapter.deserialize(serialized, expected_metadata=FORY_METADATA)
