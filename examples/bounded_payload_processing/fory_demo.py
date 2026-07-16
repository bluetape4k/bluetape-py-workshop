import json

from bluetape.compression import GzipCompressor
from bluetape.serde.fory import ForyAdapter, ForyLimits, ForyRegistration

from .fory_service import ForyPayloadService
from .models import OrderSnapshot


def _emit(**event: object) -> None:
    print(json.dumps(event, ensure_ascii=False, sort_keys=True))


def main() -> None:
    adapter = ForyAdapter(
        registration=ForyRegistration(
            python_type=OrderSnapshot,
            schema_id=1001,
            schema_version=1,
            type_id=1001,
            logical_name="workshop.order_snapshot",
        ),
        limits=ForyLimits(
            max_input_size=4096,
            max_output_size=4096,
            max_concurrency=2,
        ),
    )
    service = ForyPayloadService(
        adapter=adapter,
        compressor=GzipCompressor(max_output_size=4096),
        max_encoded_size=8192,
        max_compressed_size=4096,
    )
    snapshot = OrderSnapshot(
        order_id="ORDER-2001",
        product_ids=["SKU-9"],
        total_cents=14_000,
    )

    _emit(
        event="profile_selected",
        format=service.metadata.format,
        trust_profile=service.metadata.trust_profile.value,
    )
    payload = service.encode(snapshot)
    _emit(
        event="encoded",
        compression=payload.compression,
        encoding=payload.encoding,
        encoded_size=len(payload.data),
    )
    decoded = service.decode(payload)
    _emit(event="decoded", result="round_trip_ok" if decoded == snapshot else "mismatch")


if __name__ == "__main__":
    main()
