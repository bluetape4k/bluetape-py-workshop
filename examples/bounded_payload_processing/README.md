# Bounded Payload Processing

English | [한국어](README.ko.md)

An application-shaped example that accepts a transport envelope only after checking its declared format and every byte boundary. The default path uses JSON with `TrustProfile.UNTRUSTED`; an optional, isolated environment demonstrates Apache Fory with `TrustProfile.TRUSTED_INTERNAL` and `pyfory==1.3.0`.

## Scenario

An order service stores or forwards compressed payloads as a base64url string. A malicious or misconfigured sender can lie about metadata, send oversized encoded data, hide a large gzip body behind a small input, or try to make the receiver select a powerful deserializer.

The composition root therefore chooses one fixed service before receiving the payload:

- `JsonPayloadService` is the default for untrusted JSON documents.
- `ForyPayloadService` is optional and accepts only the fixed `OrderSnapshot` registration in a trusted internal boundary.
- Neither service performs automatic format selection from payload metadata. If metadata crosses a trust boundary, it must be authenticated by the surrounding protocol; even authenticated metadata is validated against the already-selected service.

## Architecture

[![Bounded payload processing architecture](docs/images/architecture.png)](docs/images/architecture.svg)

The caller owns the policy decision. Both services expose the same transport shape—`EncodedPayload` with exact metadata, `gzip`, and `base64url`—but they do not share a dynamic provider registry. The decode path checks `max_encoded_size`, then `max_compressed_size`, then the decompressed/serialized limit before calling JSON or Fory.

## Sequence Diagram

[![Bounded payload processing sequence](docs/images/sequence.png)](docs/images/sequence.svg)

The early rejection branches are part of the contract. Unsupported encoding, compression, or metadata fails before codecs run. An encoded or compressed limit raises `TransportLimitError`; bounded gzip expansion remains visible as `DecompressionLimitError`; only a fully bounded value reaches deserialization.

## Limit model

| Boundary | Checked when | Why it exists |
| --- | --- | --- |
| `max_encoded_size` | Before base64url decoding | Caps the transport string accepted from the caller. |
| `max_compressed_size` | After decoding and before gzip expansion | Caps the compressed byte buffer. |
| JSON `max_serialized_size` / Fory `ForyLimits.max_input_size` | During bounded gzip output and deserialization | Prevents decompression bombs and oversized serialized inputs. |
| JSON `max_nesting_depth` | During JSON serialization/deserialization | Rejects pathologically deep documents. |

Limits are positive exact integers. The configured gzip output limit must not exceed the downstream deserializer input limit.

## Run the default JSON example

Requirements: CPython 3.13 and `uv`. The locked development environment deliberately does not install `pyfory`.

```bash
uv sync --locked --python 3.13.14
uv run --locked python -m examples.bounded_payload_processing
uv run --locked pytest examples/bounded_payload_processing/tests/test_service.py \
  examples/bounded_payload_processing/tests/test_application.py -q
```

The CLI prints metadata and sizes, never the payload body. Its final event demonstrates malformed base64url rejection.

## Run the optional Fory example

Keep Fory isolated so the repository's provider-baseline test can prove that the default environment remains provider-free.

```bash
UV_PROJECT_ENVIRONMENT=.venv-fory uv sync --locked --extra fory --python 3.13.14
source .venv-fory/bin/activate
python -m examples.bounded_payload_processing.fory_demo
pytest examples/bounded_payload_processing/tests/test_fory_service.py -q
deactivate
rm -rf .venv-fory
```

`ForyPayloadService` validates the fixed Fory metadata, root type, schema ID, type ID, and limits. Do not expose this trusted-internal profile to arbitrary network input.

## Source map

- [`models.py`](models.py) — immutable transport envelope and the Fory `OrderSnapshot` domain model.
- [`errors.py`](errors.py) — explicit transport algorithm and size-limit failures.
- [`service.py`](service.py) — default JSON service with fixed untrusted metadata and bounded codecs.
- [`fory_service.py`](fory_service.py) — optional Fory service with fixed trusted-internal metadata.
- [`__main__.py`](__main__.py) — deterministic JSON CLI.
- [`fory_demo.py`](fory_demo.py) — explicit Fory composition root and registration.
- [`tests`](tests) — boundary, failure-order, provider-isolation, CLI, and documentation tests.

## Design notes

- Provider selection is code, not data: the application imports and constructs the service it intends to trust.
- Metadata preflight happens before base64url decoding, gzip decompression, or provider execution.
- Fory is not re-exported from the default package initializer, so importing the JSON example cannot pull in its optional provider.
- `OrderSnapshot` is a mutable slotted dataclass because `pyfory==1.3.0` cannot currently deserialize the frozen slotted variant; tests prove the service still preserves caller input.

