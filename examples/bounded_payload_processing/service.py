from bluetape.codec import base64url_decode, base64url_encode
from bluetape.compression import GzipCompressor
from bluetape.serde import (
    ContentTypeMismatchError,
    FormatMismatchError,
    JsonValue,
    PayloadMetadata,
    SerializedPayload,
    TrustProfile,
    TrustProfileMismatchError,
    UnsupportedVersionError,
    json_deserialize,
    json_serialize,
)

from .errors import (
    TransportLimitError,
    UnsupportedCompressionError,
    UnsupportedEncodingError,
)
from .models import EncodedPayload

JSON_METADATA = PayloadMetadata(
    format="json",
    version=1,
    content_type="application/json",
    trust_profile=TrustProfile.UNTRUSTED,
)


def _require_positive_exact_int(name: str, value: object) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact int")
    if value <= 0:
        raise ValueError(f"{name} must be positive")
    return value


def _validate_json_metadata(metadata: PayloadMetadata) -> None:
    if metadata.format != JSON_METADATA.format:
        raise FormatMismatchError
    if metadata.version != JSON_METADATA.version:
        raise UnsupportedVersionError
    if metadata.content_type != JSON_METADATA.content_type:
        raise ContentTypeMismatchError
    if metadata.trust_profile is not JSON_METADATA.trust_profile:
        raise TrustProfileMismatchError


class JsonPayloadService:
    __slots__ = (
        "_compressor",
        "_max_compressed_size",
        "_max_encoded_size",
        "_max_nesting_depth",
        "_max_serialized_size",
    )

    def __init__(
        self,
        *,
        compressor: GzipCompressor,
        max_encoded_size: int,
        max_compressed_size: int,
        max_serialized_size: int,
        max_nesting_depth: int,
    ) -> None:
        if type(compressor) is not GzipCompressor:
            raise TypeError("compressor must be an exact GzipCompressor")
        self._max_encoded_size = _require_positive_exact_int("max_encoded_size", max_encoded_size)
        self._max_compressed_size = _require_positive_exact_int(
            "max_compressed_size", max_compressed_size
        )
        self._max_serialized_size = _require_positive_exact_int(
            "max_serialized_size", max_serialized_size
        )
        self._max_nesting_depth = _require_positive_exact_int(
            "max_nesting_depth", max_nesting_depth
        )
        if compressor.max_output_size > self._max_serialized_size:
            raise ValueError("compressor output limit must not exceed max_serialized_size")
        self._compressor = compressor

    @property
    def metadata(self) -> PayloadMetadata:
        return JSON_METADATA

    def encode(self, value: JsonValue) -> EncodedPayload:
        serialized = json_serialize(
            value,
            metadata=JSON_METADATA,
            max_output_size=self._max_serialized_size,
            max_nesting_depth=self._max_nesting_depth,
        )
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
            metadata=JSON_METADATA,
            compression="gzip",
            encoding="base64url",
            data=encoded,
        )

    def decode(self, payload: EncodedPayload) -> JsonValue:
        if type(payload) is not EncodedPayload:
            raise TypeError("payload must be an exact EncodedPayload")
        if payload.encoding != "base64url":
            raise UnsupportedEncodingError(payload.encoding)
        if payload.compression != "gzip":
            raise UnsupportedCompressionError(payload.compression)
        _validate_json_metadata(payload.metadata)
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
        return json_deserialize(
            serialized,
            expected_metadata=JSON_METADATA,
            max_input_size=self._max_serialized_size,
            max_nesting_depth=self._max_nesting_depth,
        )
