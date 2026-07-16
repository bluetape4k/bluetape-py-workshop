# Issue #6 Bounded Payload Processing Design

## Status

- Issue: [#6 — add a bounded payload processing service](https://github.com/bluetape4k/bluetape-py-workshop/issues/6)
- Milestone: `0.1.0`
- Branch: `feat/issue-6-bounded-payload-processing`
- Base: `develop` at `51d7e457384ea4f84b7f18afd00a13e939218ef1`
- Work type: Type A — cross-package application service with an optional native provider lane
- Design approval: separate JSON and Apache Fory services, approved in the active thread on 2026-07-16 KST

## Problem

Readers need an application-shaped example that composes serialization,
compression, and transport encoding without turning payload metadata into a
format-discovery mechanism. The example must show that metadata, trust profile,
decompressed size, and provider availability are caller-owned policy. It must
also demonstrate Apache Fory without making a native optional provider part of
the default installation or import path.

## Reader Outcome

After running the example, a reader can:

1. encode and decode a JSON document through strict JSON, gzip, and canonical
   unpadded base64url contracts;
2. reject unsupported transport algorithms and mismatched serde metadata before
   deserialization;
3. distinguish codec, compression-limit, and malformed-serialization failures;
4. preserve caller-owned input while round-tripping empty and bounded values;
5. run Apache Fory as a separate trusted-internal lane with a fixed registered
   type and CPython 3.13; and
6. explain both trust profiles through aligned English/Korean README files and
   source-backed Architecture and Sequence diagrams.

## Current Evidence

The pinned `bluetape-py` source baseline is commit
`4b7458f22cea0a9e757b5fbf7f5ff4bc8c23cb9a`.

- `bluetape.codec.base64url_encode` and `base64url_decode` use canonical
  unpadded URL-safe Base64 by default and raise `CodecError` for malformed or
  non-canonical text.
- `bluetape.compression.GzipCompressor` is immutable, reports algorithm
  `gzip`, and raises `DecompressionLimitError` when decompressed output exceeds
  its configured bound.
- `bluetape.serde.json_serialize` and `json_deserialize` require JSON v1
  metadata, exact content type, independent expected metadata, strict UTF-8,
  bounded input/output, and an explicit nesting limit.
- `bluetape.serde.fory.ForyAdapter` requires CPython 3.13 with
  `bluetape-serde[fory]`, accepts only `TRUSTED_INTERNAL`, binds one exact root
  type to fixed schema/type identifiers, and applies bounded input/output and
  concurrency limits.
- Existing workshop examples establish immutable keyword-only models,
  independently runnable packages, deterministic CLIs, focused tests, aligned
  README locales, and mandatory Architecture/Sequence SVG and PNG pairs.

## Constraints

- Python 3.13.14 and uv 0.11.28 remain authoritative.
- The default dependency lane must not install or import `pyfory`.
- The optional `fory` project extra may add `bluetape-serde[fory]`; the lockfile
  may contain `pyfory`, but default environment tests must prove it is absent.
- Received payload fields never select a serializer, compressor, codec,
  registration, schema, Python class, or adapter.
- Both services are fixed to gzip and canonical unpadded base64url.
- Both services bound received encoded text before decoding and bound decoded
  compressed bytes before decompression. These transport bounds are separate
  from the decompressed and serde input/output bounds.
- JSON uses `TrustProfile.UNTRUSTED`; Fory uses
  `TrustProfile.TRUSTED_INTERNAL` and is documented only for authenticated
  internal payloads.
- No registry, plugin discovery, pickle, dynamic import, HTTP, persistence,
  network, Docker, credentials, native compression provider, retry, or
  background task is introduced.
- Every README locale embeds both diagram PNGs and links their SVG sources.

## Considered Approaches

### Chosen: separate JSON and Fory application services

Create `JsonPayloadService` in the default package surface and
`ForyPayloadService` in an optional module that imports
`bluetape.serde.fory`. The services intentionally duplicate the small
serialize-compress-encode and decode-decompress-deserialize pipeline. They
share only immutable transport/domain models and transport-policy error types.

Why chosen:

- readers can see the different trust profiles and construction requirements;
- importing the default package cannot import `pyfory`;
- the Fory registration and Python root type remain statically visible; and
- no received field participates in runtime serializer selection.

### Rejected: one processor with an injected serializer adapter

This is the more reusable library design, but it hides the important
instructional difference between an untrusted JSON boundary and a trusted
registered-object boundary. The workshop would spend more code explaining the
adapter abstraction than the two concrete flows.

### Rejected: format registry or automatic detection

A registry encourages callers to route from received metadata. It expands the
attack surface, obscures independent expected policy, and violates the issue's
explicit non-goal.

## Package Layout

```text
examples/bounded_payload_processing/
├── __init__.py
├── __main__.py
├── errors.py
├── models.py
├── service.py
├── fory_service.py
├── fory_demo.py
├── README.md
├── README.ko.md
├── docs/images/
│   ├── architecture.svg
│   ├── architecture.png
│   ├── sequence.svg
│   └── sequence.png
└── tests/
    ├── __init__.py
    ├── test_application.py
    ├── test_documentation.py
    ├── test_fory_service.py
    └── test_service.py
```

`fory_service.py`, `fory_demo.py`, and `test_fory_service.py` are the only
example files allowed to import `bluetape.serde.fory` or `pyfory`.

## Immutable Contracts

```python
@dataclass(frozen=True, slots=True, kw_only=True)
class EncodedPayload:
    metadata: PayloadMetadata
    compression: str
    encoding: str
    data: str


@dataclass(frozen=True, slots=True, kw_only=True)
class OrderSnapshot:
    order_id: str
    product_ids: list[str]
    total_cents: int
```

`EncodedPayload` makes every transport decision visible. Services require an
exact instance and validate `compression`, `encoding`, and every metadata field
against independently constructed constants before decoding. `OrderSnapshot`
is the exact registered Fory root. Its list demonstrates a typed object graph;
the service does not mutate the snapshot or list.

`EncodedPayload.__post_init__` requires exact `PayloadMetadata` and exact
strings. It rejects empty transport identifiers and data larger than the model
does not know how to bound; size policy remains service-owned because the same
immutable payload may be evaluated by different trusted callers.

The default package exports `EncodedPayload`, `JsonPayloadService`, and the two
transport-policy errors. It may export `OrderSnapshot` because that model has
no provider import. It never re-exports `ForyPayloadService`.

## Error Contract

Two workshop errors cover transport policy that the libraries do not own:

- `UnsupportedEncodingError` for any encoding other than `base64url`;
- `UnsupportedCompressionError` for any compression other than `gzip`.
- `TransportLimitError` with stage `encoded` or `compressed` when received
  transport material exceeds the service-owned pre-decompression bound.

Library exceptions remain visible so readers learn the actual composition
boundary:

- `FormatMismatchError`, `UnsupportedVersionError`,
  `ContentTypeMismatchError`, or `TrustProfileMismatchError` for serde metadata;
- `CodecError` for malformed/non-canonical base64url;
- `CompressionError` for malformed gzip and `DecompressionLimitError` for an
  expanded output above the configured bound;
- `MalformedPayloadError`, `PayloadLimitError`, schema/type errors, and other
  typed serde failures for serialized content.

Services do not catch and flatten these exceptions.

## JSON Service

`JsonPayloadService` accepts a caller-owned `GzipCompressor`,
`max_encoded_size`, `max_compressed_size`, `max_serialized_size`, and
`max_nesting_depth`. Constructor validation requires positive exact integers
and requires the gzip decompression bound not to exceed the serde input bound.
It owns independent JSON v1 metadata:

```text
format=json
version=1
content_type=application/json
trust_profile=UNTRUSTED
```

### Encode

1. Call `json_serialize` with the service's metadata and bounds.
2. Compress the returned exact bytes with gzip.
3. Encode the compressed bytes as canonical unpadded base64url.
4. Return a new `EncodedPayload`; do not mutate or retain caller input.

### Decode

1. Require exact `EncodedPayload` and exact supported transport strings.
2. Compare every received metadata field to the service-owned expected
   metadata and raise the matching serde metadata error.
3. Reject encoded text above `max_encoded_size`.
4. Decode canonical base64url, then reject decoded compressed bytes above
   `max_compressed_size`.
5. Decompress under `GzipCompressor.max_output_size`.
6. Construct `SerializedPayload` with the already validated received metadata.
7. Call `json_deserialize` with the independently owned expected metadata and
   serde bounds.

Metadata checks therefore precede both construction of the serde payload and
deserialization.

## Fory Service

`ForyPayloadService` accepts a caller-owned
`ForyAdapter[OrderSnapshot]`, `GzipCompressor`, `max_encoded_size`, and
`max_compressed_size`. Its module owns independent Fory v1 trusted metadata.
The composition root constructs the adapter with a fixed registration:

```text
python_type=OrderSnapshot
schema_id=1001
schema_version=1
type_id=1001
logical_name=workshop.order_snapshot
```

The encode/decode order mirrors the JSON service, including encoded and
compressed pre-decompression bounds, but delegates serialized bytes to the
fixed adapter. Construction rejects a gzip decompression bound larger than the
adapter input bound, so decompression cannot feed an oversized value into
Fory. The service never derives schema, type, logical name, or Python class from
received data.

## Optional Dependency and Import Boundary

`pyproject.toml` adds:

```toml
[project.optional-dependencies]
fory = ["bluetape-serde[fory]==0.1.0"]
```

Default proof:

```bash
uv sync --locked --python 3.13.14
uv run --locked python -m examples.bounded_payload_processing
uv run --locked pytest -q
```

Optional proof uses a separate environment so it cannot contaminate the
default lane:

```bash
UV_PROJECT_ENVIRONMENT=.venv-fory uv sync --locked --extra fory --python 3.13.14
UV_PROJECT_ENVIRONMENT=.venv-fory uv run --locked --extra fory \
  python -m examples.bounded_payload_processing.fory_demo
UV_PROJECT_ENVIRONMENT=.venv-fory uv run --locked --extra fory \
  pytest examples/bounded_payload_processing/tests/test_fory_service.py -q
rm -rf .venv-fory
```

Default import tests scan `sys.modules` in an isolated interpreter and prove
that importing the package and running the JSON CLI does not import
`bluetape.serde.fory` or `pyfory`.

## Failure Modes

1. **Metadata spoofing:** format, version, content type, or trust mismatch is
   rejected before codec/decompression/deserialization work.
2. **Transport substitution:** non-`gzip` or non-`base64url` identifiers are
   rejected; no registry fallback exists.
3. **Oversized transport input:** encoded text and decoded compressed bytes are
   rejected before large codec/decompression allocations or serde work.
4. **Encoding corruption:** malformed or non-canonical text raises
   `CodecError` before decompression.
5. **Compression bomb/trailing input:** bounded gzip decompression raises
   `DecompressionLimitError` or `CompressionError` before serde.
6. **Malformed serialized content:** strict JSON/Fory deserialization raises
   its typed serde error after transport checks pass.
7. **Fory unavailable or wrong interpreter:** only the optional command imports
   the provider module and displays the upstream fixed installation guidance.
8. **Fory schema/type mismatch:** the fixed adapter rejects mismatched envelope
   identifiers; no payload-selected registration is attempted.

## Testing Strategy

- Public shape: immutable/keyword-only/slotted contracts and exact default
  exports.
- JSON success: object, scalar, empty object/list/string, and exact output-size
  boundary round trips.
- Input preservation: deep-copy before encode and assert the original nested
  value remains equal and structurally unchanged.
- Metadata/transport: every field mismatch fails before codec and compressor
  spies are called.
- Transport bounds: oversized encoded text fails before codec work; oversized
  decoded compressed bytes fail before decompression.
- Failure mapping: malformed base64url, malformed gzip, decompression limit,
  malformed JSON, input limit, and unsupported transport strings.
- Import isolation: default package, CLI, and default pytest collection do not
  import Fory/provider modules.
- Fory optional lane: actual registered `OrderSnapshot` round trip, empty list,
  boundary/limit behavior, metadata mismatch, schema/type mismatch, malformed
  serialized input, and caller input preservation.
- CLI/documentation: deterministic JSON events, exact commands, reciprocal
  locale links, root navigation, PNG embeds, SVG links, and trust warnings.
  Events report stage, selected fixed profile, sizes, and stable error class but
  never serialized data, encoded payload text, credentials, or object fields.

## Documentation and Diagrams

Both README locales follow the same reader path:

1. scenario and non-goals;
2. trust-profile comparison;
3. Architecture Diagram showing two explicitly selected composition roots and
   the shared transport model;
4. Sequence Diagram showing metadata-first decode plus failure branches;
5. default JSON commands and expected output;
6. optional Fory prerequisites and commands;
7. failure, limit, troubleshooting, and production-boundary guidance.
8. optional-environment cleanup and a warning never to route received metadata
   to the Fory command.

The diagrams use English labels and are shared between locales. Each README
embeds `architecture.png` and `sequence.png` and links the matching SVG source.

## Compatibility and Migration

This is a new example package and adds no reusable API to `bluetape-py`.
Existing examples and default commands remain unchanged. The project lockfile
changes only to model the optional Fory extra. Default installs still exclude
`pyfory`; native compression extras remain excluded.

## Acceptance Criteria

- Separate JSON and Fory services exist with fixed trust profiles and no format
  registry or automatic detection.
- Strict transport and metadata checks occur before deserialization.
- Typed upstream failures remain observable for malformed encoding,
  compression limits, and malformed serialized content.
- Caller input is not mutated.
- Default install/import/tests exclude Apache Fory.
- The optional CPython 3.13 Fory lane runs an actual fixed-registration round
  trip and negative tests.
- English/Korean README pairs and root navigation are aligned.
- Architecture and Sequence SVG/PNG pairs are source-backed, embedded, linked,
  audited, and inspected at full size.
- Focused, repository-wide, Ruff, actionlint, lock, and diff checks pass.
- Final Type A review converges at P0=0/P1=0 and a durable lesson is committed.

## Delivery Boundary

The approved workflow authorizes local edits, Lore commits, publishing
`feat/issue-6-bounded-payload-processing`, and creating a PR into `develop`
with issue #6 metadata. Merge, auto-merge, remote branch deletion, tags,
releases, publishing, workflow dispatch, and milestone closure are excluded.
The workflow stops after reporting the exact PR head as merge-ready and waits
for fresh explicit merge approval.
