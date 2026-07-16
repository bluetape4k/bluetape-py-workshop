# Payload Format Selection Is a Trust Decision

## Context

Issue #6 needed to teach `bluetape-codec`, `bluetape-compression`, and
`bluetape-serde` together while also demonstrating Apache Fory. A single
processor with a registry would be compact, but it would invite readers to use
received metadata as a provider-selection key and blur the difference between
untrusted JSON and trusted registered objects.

## Lesson

Choose the deserializer in the composition root, before receiving payload
metadata. A small fixed-format service should own independent expected metadata
and reject every mismatched field before decoding, decompressing, or invoking a
provider. Duplicating a short pipeline is preferable when the duplication makes
the trust boundary executable and visible.

Apply limits at each representation boundary. The encoded string bound protects
the codec entry, the decoded compressed-byte bound protects decompression, and
the gzip output bound must fit inside the deserializer input bound. One generic
"payload size" setting cannot explain or prove all three allocation risks.

## Optional Provider Guard

An optional dependency can appear in `uv.lock` without belonging to the default
installed environment. Prove both states: the lock contains the exact provider
version for reproducibility, while installed-package and isolated-import tests
show that the default path neither installs nor imports it. Run the provider in
a separate disposable environment and remove that environment before returning
to the default verification lane.

## Provider Compatibility Guard

Pinned `pyfory==1.3.0` serialized a frozen slotted dataclass but failed to
deserialize it because the runtime could not populate frozen fields. The
provider's own conformance shape uses a mutable slotted dataclass. The example
therefore keeps only the transport envelope frozen and uses a mutable slotted
registered root, while round-trip tests prove the service does not mutate the
caller's object or nested list.

Compatibility claims about native or generated serializers require a real
round trip. Successful import, registration, or serialization alone is not
sufficient evidence.

## Review Learning

The first Fory suite implemented all metadata and transport checks but directly
tested only a subset. The final review added version/content-type,
encoding/compression substitution, and decompression-bound cases in the real
provider environment. For future trust-boundary examples, map every rejection
branch in the sequence diagram to a concrete negative test before considering
the diagram or implementation complete.

## Evidence

- Default dependency baseline: `19 passed`; `pyfory` absent from installed metadata.
- Default example: `41 passed`; full repository: `165 passed, 1 skipped`.
- Isolated `pyfory==1.3.0` round trip and optional suite: `17 passed`.
- Both diagram asset pairs passed XML, render, connector, geometry, endpoint,
  mixed-corner, and full-size visual inspection; Sequence also passed its style audit.
- Final implementation review converged at P0=0/P1=0.

