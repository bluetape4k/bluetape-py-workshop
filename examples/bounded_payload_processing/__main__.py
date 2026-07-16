import json
from dataclasses import replace

from bluetape.codec import CodecError
from bluetape.compression import GzipCompressor

from .service import JsonPayloadService


def _emit(**event: object) -> None:
    print(json.dumps(event, ensure_ascii=False, sort_keys=True))


def main() -> None:
    service = JsonPayloadService(
        compressor=GzipCompressor(max_output_size=4096),
        max_encoded_size=8192,
        max_compressed_size=4096,
        max_serialized_size=4096,
        max_nesting_depth=16,
    )
    document = {
        "order_id": "ORDER-1001",
        "product_ids": ["SKU-1", "SKU-2"],
        "total_cents": 25_000,
    }

    _emit(event="profile_selected", format="json", trust_profile="untrusted")
    payload = service.encode(document)
    _emit(
        event="encoded",
        compression=payload.compression,
        encoding=payload.encoding,
        encoded_size=len(payload.data),
    )
    decoded = service.decode(payload)
    _emit(event="decoded", result="round_trip_ok" if decoded == document else "mismatch")

    try:
        service.decode(replace(payload, data="*"))
    except CodecError as error:
        _emit(event="rejected", stage="encoding", error=type(error).__name__)


if __name__ == "__main__":
    main()
