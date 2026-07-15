# Issue #4 Bounded Catalog Enrichment Design

Status: reviewed design awaiting explicit written-spec approval

Issue: [#4](https://github.com/bluetape4k/bluetape-py-workshop/issues/4)

Work type: Type A — Full Feature

## Problem

Backend catalog requests commonly need to enrich several product identifiers
from required and optional downstream providers. Unbounded fan-out can exhaust
provider capacity, completion order can leak into response order, and treating
every provider failure alike either makes optional data too critical or hides
required-data loss.

This example must teach a deterministic application boundary using the pinned
`bluetape-collections` and `bluetape-async` packages. It normalizes identifiers,
avoids duplicate provider work, creates fixed-size batches, executes required
and optional provider jobs under one concurrency budget, and reconstructs
results in normalized input occurrence order.

The example remains framework-neutral and provider-neutral. It owns no HTTP
client, retry, circuit breaker, persistence, cache, or background worker.

## Current Evidence

The workshop resolves all focused packages from bluetape-py commit
`4b7458f22cea0a9e757b5fbf7f5ff4bc8c23cb9a`.

The design uses only APIs present at that exact source:

- `bluetape.collections.distinct`
- `bluetape.collections.chunked`
- `bluetape.asyncio.map_bounded`
- `bluetape.core.require_instance`
- `bluetape.core.require_not_blank`

`distinct` preserves first-seen order. `chunked` eagerly creates new fixed-size
lists and validates its size before consuming input. `map_bounded` preserves
job input order, creates call-scoped workers, limits active mapper calls to the
configured value, applies one total cooperative timeout, propagates external
`asyncio.CancelledError`, and finishes sibling cleanup before returning or
raising. Ordinary mapper failures retain native `ExceptionGroup` shapes.

The application adds fixed request bounds rather than presenting bounded task
concurrency as bounded memory: at most 1,000 identifier occurrences, at most 64
ASCII identifier characters, and batch sizes from 1 through 100. These limits
bound eager normalization, job construction, provider payload size, and result
projection independently of the mapper's concurrency ceiling.

The application-shaped package layout and required/optional provider policy
borrow from `bluetape-go-workshop/examples/product-enrichment-fanout`. The
Python version deliberately adds identifier batching, duplicate restoration,
total timeout semantics, and explicit task-cleanup proof. Bilingual navigation
and source-backed visuals follow this repository's issue #3 documentation
contract.

## Design Alternatives

### A. Batch-provider jobs under one bounded mapper — selected

Normalize and deduplicate product identifiers, split them into batches, create
one required and one optional job per batch, and execute the ordered job list
with a single `map_bounded` call.

Benefits:

- one visible concurrency ceiling covers every downstream call;
- batching and deterministic collection transforms are first-class;
- duplicate provider work is avoided while output cardinality is preserved;
- timeout, cancellation, failure, and cleanup use the library contract rather
  than workshop-owned concurrency helpers.

Cost: aggregation must validate provider responses and restore input order.

### B. One mapper call per product — rejected

This is smaller, but every duplicate identifier repeats downstream work and
batching becomes decorative rather than part of the provider contract.

### C. Direct `Semaphore` plus `TaskGroup` orchestration — rejected

This provides low-level control, but duplicates the exact concurrency ownership
that `map_bounded` exists to demonstrate and would grow a reusable-looking
workshop utility.

## Package Layout

```text
examples/
└── catalog_enrichment/
    ├── __init__.py
    ├── __main__.py
    ├── errors.py
    ├── models.py
    ├── providers.py
    ├── service.py
    ├── README.md
    ├── README.ko.md
    ├── docs/images/
    │   ├── architecture.svg
    │   ├── architecture.png
    │   ├── sequence.svg
    │   └── sequence.png
    └── tests/
        ├── test_application.py
        ├── test_documentation.py
        └── test_service.py
```

The example remains inside the root non-package uv project. It adds no runtime
dependency and does not change the pinned source commit or lockfile.

## Public Contracts

### Immutable models

All public values are frozen dataclasses.

`CatalogRecord` contains normalized `product_id`, non-blank `name`, and
non-negative integer `price_cents`; boolean prices are rejected.
`RecommendationRecord` contains normalized `product_id` and a non-blank
recommendation string. Provider response records are validated at the
application boundary rather than trusted implicitly. Names and recommendations
remain untrusted provider content: a future HTML or SQL adapter must escape or
bind them for its own output context.

`EnrichmentWarning` contains normalized `product_id`, provider name, stable
warning code, and safe message. It never includes raw exception text or a
provider payload.

`EnrichedProduct` contains normalized `product_id`, required catalog fields, an
optional recommendation, and an immutable warning tuple. One result is returned
for every accepted input occurrence, including duplicates, in the original
occurrence order after normalization.

### Provider protocols

`RequiredCatalogProvider.fetch(product_ids)` asynchronously accepts a non-empty
tuple of unique normalized identifiers and returns a mapping from every
requested identifier to `CatalogRecord`.

`OptionalRecommendationProvider.fetch(product_ids)` accepts the same batch and
returns zero or more requested identifiers mapped to `RecommendationRecord`.

Providers are caller-owned. The service does not open or close HTTP clients,
sessions, sockets, or processes. Providers must cooperate with cancellation and
must not swallow `asyncio.CancelledError`.

### Errors

`InvalidProductIdentifier` records the zero-based input index and a safe reason.
Non-string and blank identifiers fail before any provider is called.

`TooManyProductIdentifiers` records the fixed 1,000-occurrence limit without
retaining the caller's iterable or values.

`ProviderUnavailable` is the explicit operational-failure signal expected from
provider adapters. Adapters translate network or service errors into this safe
exception and may chain their private cause. The service never serializes its
message or cause.

`RequiredProviderFailure` records the deterministic batch index and safe
failure code. It wraps provider exceptions and required response-contract
violations without exposing raw payloads.

`CatalogEnrichmentFailed` is the public request failure. It contains required
failures sorted by batch index and chains the native `ExceptionGroup` produced
by `map_bounded`. It is never used for timeout or caller cancellation.

### CatalogEnrichmentService

The constructor receives one required and one optional provider. It validates
their protocol methods are callable without taking ownership of provider
resources.

`await enrich(product_ids, *, batch_size, concurrency_limit, timeout)`:

1. consumes the synchronous input once and validates each identifier in input
   order with `require_instance` and `require_not_blank`;
2. stops at 1,001 occurrences with `TooManyProductIdentifiers`, trims each
   accepted identifier, rejects non-ASCII or values longer than 64 characters,
   normalizes with `upper()`, and accepts only `[A-Z0-9][A-Z0-9._-]*`;
3. uses `distinct` for a first-seen unique list and `chunked` for deterministic
   non-empty batches, with an application batch-size ceiling of 100;
4. creates ordered jobs as required then optional for each batch;
5. calls `map_bounded` once with the complete job list, the requested global
   concurrency limit, and one total timeout;
6. required `ProviderUnavailable` or response-contract violations raise
   `RequiredProviderFailure`, which causes structured sibling cancellation;
7. optional `ProviderUnavailable` becomes one `optional_provider_failed`
   warning per product in the affected batch and does not fail the request;
8. validates required mappings contain exactly the requested identifiers and
   matching records; missing, extra, or mismatched required data fails closed;
9. accepts optional mappings only for requested identifiers with matching
   records; a missing record becomes `optional_record_missing`, an invalid
   requested record becomes `optional_record_invalid`, and any unexpected key
   discards that batch's optional response with `optional_response_invalid`
   warnings for every requested identifier;
10. aggregates successful unique results, then projects them back through the
    normalized original list so duplicates and input order are preserved.

Empty input returns an empty list without provider calls. Configuration values
still use the native validation boundaries: `chunked` validates `batch_size`,
and `map_bounded` validates `concurrency_limit` and `timeout` before executing
jobs. No partial result is returned after a required failure or timeout.

The service translates an `ExceptionGroup` into `CatalogEnrichmentFailed` only
when every leaf is a `RequiredProviderFailure`. If any unexpected exception is
present, the original group propagates so a programming defect cannot be hidden
behind an expected provider outage. Required failures are sorted by batch index
before entering the public domain error.

## Failure and Cancellation Policy

- Required provider failure or malformed required response:
  `CatalogEnrichmentFailed` after managed sibling cleanup.
- Optional `ProviderUnavailable`: successful response with
  `optional_provider_failed` warnings for the affected batch.
- Missing or malformed optional record: successful response with a stable
  per-product warning.
- Total deadline expiry: native `TimeoutError` after managed task cleanup.
- Caller cancellation: native `asyncio.CancelledError` with the caller's
  cancellation semantics preserved after managed sibling cleanup.
- Invalid identifier or configuration: validation error before any downstream
  call for that phase.
- Any provider exception other than `ProviderUnavailable`: propagates; it is
  not relabelled as an expected failure or optional warning.

The service owns only tasks created inside `map_bounded`. Provider-owned client
resources remain provider responsibility. Tests assert that no named
`bluetape.map_bounded.*` task remains after success, failure, timeout, or caller
cancellation.

## Observability Ownership

The service does not configure global logging or metrics. Its immutable warning
codes, `CatalogEnrichmentFailed`, native timeout, and native cancellation are
the caller's observability hooks. A production adapter decides which safe
codes, batch indexes, durations, and request identifiers become logs or metrics;
it must not serialize provider causes or provider payloads. The runnable CLI
prints deterministic result JSON only and owns no process-wide telemetry state.

Rollback is source-only: remove the example or revert its issue commit. There
is no data migration, external deployment, runtime configuration, or provider
resource to roll back in this issue.

## Data Flow

### Success with duplicates

1. Caller submits product identifiers with mixed case, whitespace, and
   duplicates.
2. Service validates and normalizes every occurrence.
3. `distinct` selects first-seen provider work; `chunked` creates batches.
4. Required and optional jobs enter one ordered `map_bounded` invocation.
5. Providers complete in any timing order while the helper preserves job order.
6. Service validates and aggregates provider mappings.
7. Service replays the normalized original identifier list and returns one
   immutable result per occurrence.

### Required failure, optional failure, timeout, or cancellation

1. A required job raises or violates its response contract: the mapper raises,
   sibling work is cancelled, and the service raises `CatalogEnrichmentFailed`.
2. An optional job raises: the mapper returns warnings and other work continues.
3. The total timeout expires: `map_bounded` cancels managed work and raises
   `TimeoutError` after cleanup.
4. The caller cancels: native cancellation propagates after managed cleanup.

## Test Contract

Tests must prove:

- empty input returns immediately without provider calls;
- whitespace/case normalization is deterministic, and Unicode, malformed,
  overlong, and over-capacity identifier inputs fail before provider calls;
- duplicate identifiers trigger one provider lookup but produce one result per
  input occurrence in stable normalized input order;
- `chunked` boundaries create the documented provider batches;
- active provider calls never exceed `concurrency_limit`;
- provider completion order cannot change result order;
- required provider exception, missing result, extra result, and mismatched
  record fail the request with safe domain errors;
- optional exception, missing record, unexpected record, and mismatched record
  produce explicit stable warnings without failing required data;
- optional operational failures use `ProviderUnavailable`, while unexpected
  provider defects propagate unchanged;
- invalid identifiers and invalid batch/limit/timeout values fail before the
  relevant downstream work;
- one total timeout raises `TimeoutError` only after mapper cleanup;
- caller cancellation remains `asyncio.CancelledError` and cleans siblings;
- every success and exit path leaves no named helper tasks;
- providers and caller-owned input containers are not mutated;
- the runnable module produces deterministic JSON without network access;
- English and Korean documents expose equivalent commands, policies, APIs,
  assets, and source links.

Concurrency tests use `asyncio.Event`, counters, and bounded `asyncio.wait_for`
guards. They do not use long sleeps or timing-only assertions.

## Documentation and Visuals

Both example README files use reciprocal `English | 한국어` navigation and
contain:

- business Scenario and explicit non-goals;
- Architecture diagram and textual task/provider ownership boundaries;
- Sequence Diagram with success, optional-warning, required-failure, timeout,
  and caller-cancellation branches;
- exact package and API inventory;
- repository-root setup, run, targeted test, and full validation commands;
- deterministic expected output and failure/warning policy;
- cleanup, troubleshooting, provider trust, and unsupported configuration.

The Architecture diagram shows Caller, CatalogEnrichmentService, deterministic
collection transforms, the single `map_bounded` task group, required and
optional providers, aggregation, and immutable results.

The Sequence Diagram shows normalization, batching, bounded provider jobs, and
an `alt` frame for success/optional warning versus required failure/timeout or
caller cancellation. Assets are authored only after implementation, shared by
both locales with English labels, rendered to SVG and PNG, audited, and opened
at full size.

## Failure Modes and Guards

1. **Duplicate inputs multiply provider load.** Guard with first-seen
   deduplication and provider-call assertions while restoring result cardinality.
2. **Completion order changes response order.** Guard with delayed event-driven
   providers and exact ordered result assertions.
3. **Required failure is downgraded to a warning.** Use separate job kinds and
   domain exceptions; test that no partial result escapes.
4. **Optional exception text leaks into output.** Emit stable codes and safe
   messages only; assert raw provider exceptions are absent.
5. **Timeout is confused with caller cancellation.** Catch neither as ordinary
   provider failure and test their exact native exception types.
6. **Tasks survive an exit path.** Assert no named helper tasks after success,
   required failure, timeout, and repeated external cancellation.
7. **Provider returns cross-request or extra data.** Validate response keys and
   record identifiers against the exact batch before aggregation.
8. **Concurrency is bounded per provider rather than globally.** Use one job
   list and one `map_bounded` call; measure active calls across both providers.
9. **Empty input bypasses invalid configuration policy.** Preserve native
   `chunked` and `map_bounded` validation order and cover it explicitly.
10. **A huge or Unicode-normalizing input defeats the concurrency bound.** Cap
    occurrences, raw ASCII identifier length, identifier grammar, and provider
    batch size before constructing the complete job list.

## Compatibility and Migration

- Python remains 3.13+ with reference interpreter 3.13.14.
- uv and uv-build remain pinned to 0.11.28.
- The existing bluetape-py source commit remains unchanged.
- No dependency, extra, provider, or Docker capability is added.
- Existing issue #3 commands and behavior remain unchanged.
- Issue #8 may compose the public service and models, but issue #4 introduces
  no abstraction solely for that future integration.

## Acceptance Mapping

| Issue acceptance criterion | Design proof |
|---|---|
| Deterministic grouping/chunking for empty, boundary, duplicate input | normalize, first-seen `distinct`, `chunked`, duplicate restoration tests |
| Fan-out never exceeds configured concurrency | one global `map_bounded` invocation plus active-call counter test |
| Required failure fails; optional failure warns | separate job policies and explicit domain error/warning contracts |
| Timeout and caller cancellation remain distinct | native `TimeoutError`/`CancelledError` policy and cleanup tests |
| Every owned task completes or cancels | helper-task inspection on every exit path |
| Bounded async test matrix | Event-driven success/failure/order/timeout/cancel tests without long sleeps |
| Equivalent bilingual docs and root navigation | paired README contract, runnable command, failure policy, shared assets |

## Non-Goals

- retry, backoff, circuit breaker, bulkhead abstraction, or resilience package
- HTTP client, ASGI/FastAPI route, provider authentication, or production IO
- cache, persistence, Redis, Testcontainers, or background workers
- package publication, release, tag, or milestone closure
- reusable workshop-owned concurrency or collection helpers

## Delivery Boundary

The approved delivery target is:

- repository: `bluetape4k/bluetape-py-workshop`
- base: `develop`
- head: `feat/issue-4-bounded-catalog-enrichment`
- issue: #4, milestone `0.1.0`, assignee `debop`

PR creation is in scope after spec, plan, implementation, documentation,
diagram, review, lesson, and validation gates pass. Merge remains a separate
fresh approval after the exact PR head is reported merge-ready. Auto-merge is
forbidden.

## Design DoD

- Exact pinned APIs and ownership boundaries are named.
- Alternatives and rejection reasons are explicit.
- Normalization, deduplication, batching, provider, aggregation, and public
  failure contracts are unambiguous.
- Stable ordering, concurrency, timeout, cancellation, and cleanup map to tests.
- At least three concrete failure modes have explicit guards.
- Bilingual documentation and post-implementation visual contracts are pinned.
- No dependency, release, Docker, or production-provider side effect is implied.
