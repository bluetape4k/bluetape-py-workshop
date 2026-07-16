# Issue #8 Integrated Order Backend Design

## Status

- Issue: [#8 — compose the foundation examples into an order backend](https://github.com/bluetape4k/bluetape-py-workshop/issues/8)
- Milestone: `0.1.0`
- Work type: Type A — cross-example asynchronous application composition with
  aggregate, cache, payload, cancellation, and lifecycle boundaries
- Branch: `feat/issue-8-integrated-order-backend`
- Base: `develop@15bbe2efced086eb06ccf67aa03f4efb7633e7bb`
- Worktree:
  `/Users/debop/work/bluetape4k/bluetape-py-workshop/.worktrees/issue-8-integrated-order-backend`
- Design approval: bounded aggregate approach, approved in the active thread on
  2026-07-16 KST

## Problem

The focused examples prove validation, bounded asynchronous enrichment, local
cache ownership, and bounded payload processing independently. Readers still
need a realistic application-shaped example showing how those public service
boundaries compose into one framework-neutral backend without copying their
helpers or inventing production adapters.

The integration must use a real multi-line order aggregate. Treating several
independent `PartnerOrderCommand` values as an implicit order would repeat the
same header, permit inconsistent identifiers, and force the composition layer
to reconstruct a domain boundary after validation.

## Reader Outcome

After completing the example, a reader can:

1. model one immutable multi-line order command without duplicating line
   validation;
2. reuse `OrderIntakeService` for every line while reporting an exact failing
   line index;
3. compose an `AsyncTTLCache`-backed required catalog provider with
   `CatalogEnrichmentService`;
4. preserve occurrence order and duplicate SKU lines while reusing cached
   product summaries;
5. keep optional recommendation failures as existing warnings;
6. encode the processed order as a bounded untrusted JSON artifact;
7. propagate timeouts and caller cancellation without leaking owned tasks; and
8. stop accepting work, drain bounded in-flight requests, and cancel remaining
   requests through a framework-neutral lifecycle boundary.

## Current Evidence

- The repository baseline is `develop@15bbe2e` with Python 3.13.14, uv 0.11.28,
  and `221 passed, 1 skipped, 1 deselected` in the deterministic lane.
- `OrderIntakeService.accept()` validates one `PartnerOrderCommand`, preserves
  request logging context, returns immutable `AcceptedOrder`, and raises
  `InvalidOrderCommand` with field/reason context.
- `CatalogEnrichmentService.enrich()` normalizes input, deduplicates provider
  work, restores occurrence order, bounds provider jobs with `map_bounded`,
  fails required catalog work, and converts optional recommendation failures to
  `EnrichmentWarning` values.
- `AsyncProductCatalogService` delegates normalized product reads and cache
  statistics to caller-owned `AsyncTTLCache`.
- `AsyncTTLCache` binds to one event loop, coalesces same-key loads, does not
  cache loader failures, shields shared loads from individual waiters, and
  cancels an abandoned loader after its final waiter leaves.
- `JsonPayloadService` fixes untrusted JSON metadata, gzip compression,
  base64url encoding, serialized/compressed/encoded size limits, and nesting
  depth.
- Apache Fory remains a separate trusted-internal optional lane. It is not
  imported or automatically selected by the integrated backend.

## Constraints

- Keep Python 3.13.14, uv 0.11.28, the existing lockfile, and the pinned
  `bluetape-py` commit unchanged.
- Add no dependency and change no existing example implementation.
- Keep the new aggregate and adapters local to
  `examples/integrated_order_backend`; do not present them as reusable library
  APIs.
- Use the four focused public service boundaries rather than copying
  validation, enrichment, cache, codec, compression, or serde helpers.
- Remain framework-neutral: no HTTP, ASGI, FastAPI, SQL, Redis production
  provider, retry, circuit breaker, distributed cache, or telemetry adapter.
- Use no global application, cache, logger registry, provider, task set, or
  mutable singleton.
- Use deterministic `asyncio.Event` synchronization in lifecycle tests; no
  long sleeps or real external service is required.
- Every README locale must directly embed Architecture and Sequence PNGs and
  link the matching SVG sources.
- PR creation, merge, release, tag, publish, and milestone closure require the
  workflow gates and authority recorded in the later implementation plan.

## Considered Approaches

### Chosen: explicit bounded aggregate local to the integrated example

`OrderBackendCommand` owns one header and an immutable tuple of
`OrderLineCommand` values. The service maps each line to the existing
`PartnerOrderCommand`, delegates validation, enriches the validated occurrence
sequence, calculates line/order totals, and encodes the resulting document.

This is the most realistic teaching model. It makes stable ordering, duplicate
SKUs, cache behavior, warnings, totals, and aggregate lifecycle visible without
changing the focused examples.

### Rejected: accept several independent `PartnerOrderCommand` values

This maximizes direct type reuse but repeats the order header on every line and
requires consistency checks for request, partner, and order identifiers. It is
an implicit aggregate with a weaker API.

### Rejected: process one `PartnerOrderCommand`

This is the smallest implementation but does not meaningfully demonstrate
occurrence ordering, duplicate lines, batching, cross-request cache behavior,
or realistic order totals.

## Package Layout

```text
examples/integrated_order_backend/
├── __init__.py
├── __main__.py
├── application.py
├── composition.py
├── errors.py
├── models.py
├── service.py
├── README.md
├── README.ko.md
├── docs/images/
│   ├── architecture.svg
│   ├── architecture.png
│   ├── sequence.svg
│   └── sequence.png
└── tests/
    ├── __init__.py
    ├── test_models.py
    ├── test_service.py
    ├── test_application.py
    ├── test_cli.py
    └── test_documentation.py
```

## Domain Contracts

### `OrderLineCommand`

An immutable, slotted, keyword-only dataclass containing `sku` and `quantity`.
Construction stores caller values without normalization. The existing intake
service remains authoritative for SKU and quantity validation.

### `OrderBackendCommand`

An immutable, slotted, keyword-only dataclass containing `request_id`,
`partner_id`, `order_id`, and `lines: tuple[OrderLineCommand, ...]`.

The integrated service validates only its aggregate structure:

- exact `OrderBackendCommand` type;
- exact tuple for `lines`;
- between 1 and 100 lines; and
- exact `OrderLineCommand` type at every occurrence.

It does not mutate the tuple or line objects.

### `ProcessedOrderLine`

An immutable, slotted, keyword-only result containing:

- zero-based `line_index`;
- normalized `sku` and validated `quantity`;
- product `name` and `unit_price_cents`;
- calculated `line_total_cents`;
- optional `recommendation`; and
- the existing tuple of `EnrichmentWarning` values.

### `ProcessedOrder`

An immutable, slotted, keyword-only result containing the validated caller
request, partner, and order identifiers, the occurrence-ordered processed
lines, `total_cents`, and the bounded `EncodedPayload` artifact. Header values
preserve the existing intake contract; only SKU values are normalized by the
enrichment boundary.

The encoded JSON document is built from an explicit allowlist of header values,
processed line fields, totals, recommendations, and warning fields. It does not
serialize the `ProcessedOrder` object or include its `artifact` field, so the
result cannot recursively encode itself. Provider-originated names and
recommendations are treated as data and remain subject to the existing JSON
serialization and transport limits.

Cache statistics remain operational state exposed by the service's async
`cache_stats()` method rather than embedded in the domain result.

## Error Contracts

- `InvalidOrderBackendCommand(field, reason)` reports aggregate-shape errors
  before provider, cache, or payload work.
- `InvalidOrderLine(index, field, reason)` wraps the exact
  `InvalidOrderCommand` cause from existing validation.
- `OrderBackendClosedError` rejects new work after shutdown begins.
- `OrderBackendShutdownError(pending_count)` reports requests that remain
  non-terminal after bounded cancellation and preserves their tracked state for
  diagnosis or a later close attempt.
- `CatalogEnrichmentFailed`, timeout exceptions, cache/provider exceptions,
  payload limit/metadata exceptions, and `asyncio.CancelledError` retain their
  existing public contracts.
- Public errors and CLI output never include raw provider payloads, exception
  text, cache keys beyond normalized SKU, task representations, or serialized
  artifact data.

## Composition

### Cache-backed required provider

`CachedCatalogProvider` is an example-local adapter implementing the existing
`RequiredCatalogProvider` protocol. For each normalized product ID requested by
the enrichment service, it calls `AsyncProductCatalogService.get_product()` and
maps `ProductSummary` back to the existing `CatalogRecord` shape.

The `AsyncProductCatalogService` already receives the existing
`AsyncProductLoader` protocol at composition time. Loader failures, including
`ProviderUnavailable`, pass through the cache without being stored; the outer
enrichment service translates the required-provider failure through its
existing contract. Reads within a provider batch are sequential, so the outer
enrichment service remains the only owner of provider-job concurrency and no
nested unbounded tasks are created. This deliberately favors one visible
concurrency owner over maximum batch throughput; the README identifies it as a
teaching trade-off rather than a production performance recommendation.

The adapter does not expose arbitrary cache operations or construct its own
cache. `AsyncTTLCache` is created and owned by the composition root.

### `OrderBackendService`

The service receives existing focused services and fixed configuration through
keyword-only construction. Every owning constructor validates its own fixed
configuration before accepting work: the service owns batch size, concurrency,
and provider timeout; the application owns request and shutdown timeouts; and
the existing payload service owns serialization and transport limits. The
composition root supplies those already-valid objects and values but does not
duplicate their invariants. `process(command)` performs:

1. aggregate-shape validation;
2. per-line mapping to `PartnerOrderCommand` with the shared header;
3. delegated intake validation for every line before external work;
4. occurrence-ordered enrichment with fixed batch size, concurrency limit, and
   provider timeout;
5. exact positional zip of accepted lines and enriched products;
6. line and order total calculation;
7. construction of a bounded JSON document; and
8. encoding through `JsonPayloadService`.

The service creates no background request task. It exposes `cache_stats()` only
by delegating to the composed `AsyncProductCatalogService`.

## Application Lifecycle

`OrderBackendApplication` owns request tasks but not provider/cache internals.
It binds on the first async `process()` or `aclose()` call and provides an async
`process(command)` method plus idempotent `aclose()` and async context-manager
support. Later use from another loop fails with a stable `RuntimeError` before
task creation or lifecycle-state mutation.

For every accepted request, it creates one named task around the service call,
tracks it until terminal, and applies a finite overall `request_timeout`. On the
single bound loop, the accepting-state check, task creation, and task
registration occur in one no-`await` critical section. Shutdown flips the state
and captures its tracked snapshot in the same kind of no-`await` section, so no
request can register after the shutdown snapshot.

The caller awaits the owned request task through `asyncio.shield()` inside the
overall timeout. Timeout cancels the request task and raises `TimeoutError`
without waiting indefinitely for a cancellation-resistant provider. Normal
caller cancellation also cancels the request task and promptly re-raises
`asyncio.CancelledError`. In either case, a non-terminal task remains in the
tracked set and a done callback removes it only after it truly becomes
terminal. That callback observes the terminal result or exception, records only
a fixed outcome/error kind, and prevents un-retrieved task exceptions without
logging raw exception text; neither path silently detaches work.

Lifecycle state is explicit: `OPEN`, `CLOSING`, `CLOSE_FAILED`, or `CLOSED`.
The first `aclose()` caller creates one named close task. Concurrent close
callers await that same task through `asyncio.shield()`, so cancelling one close
caller neither cancels shared shutdown nor propagates cancellation into request
tasks. A failed close retains non-terminal request references and moves to
`CLOSE_FAILED`; a later call creates one retry close task. A terminal successful
close is idempotent. Close-task completion is also observed and retained in the
lifecycle state even when every current close waiter was cancelled.

`aclose()` follows this order:

1. atomically stop accepting new requests;
2. wait up to `shutdown_grace_timeout` for the current tracked snapshot;
3. cancel remaining tasks;
4. wait up to `shutdown_cancel_timeout` for terminal cancellation; and
5. return when none remain or raise `OrderBackendShutdownError` with the exact
   pending count while retaining references.

Repeated close after terminal completion is safe. A failed close can be retried
after non-cooperative tasks become terminal. `__aexit__` raises a shutdown error
directly when the context body succeeded. When the body already raised, it
preserves that exception as primary, adds only a redacted cleanup note, and
retains pending task references for a later retry instead of masking the body
failure. The application never reaches inside `AsyncTTLCache` to cancel loader
tasks; terminating request waiters activates the cache's existing abandonment
cleanup contract.

## Logging and Trust Boundary

The caller owns a stdlib logger configured at the composition root. Aggregate
context is established only after every line passes intake validation; invalid
input remains under the focused intake service's existing safe-context
contract. The integrated layer never interpolates identifiers into an event
name or message. Every token is reset in `finally`/context-manager paths,
including validation failure, provider failure, timeout, and cancellation.

Logs use fixed event names and fixed error-kind fields. Identifier context is
structured, not message text, and is documented as operational data rather than
a metric label. Logs exclude raw provider exceptions, artifact data,
recommendations, product names, task names, and connection details.

The integrated layer emits stable lifecycle events for request start, success,
failure, timeout, and cancellation plus shutdown start, completion, and failure.
Failure events use a fixed `error_kind`; shutdown failure may include only the
numeric `pending_count`. The README explains that caller identifiers are
non-secret operational context and that a production adapter must add its own
identifier length, privacy, authorization, and retention policy.

The generated artifact always uses `JsonPayloadService` and its untrusted JSON
metadata. Apache Fory remains an explicit trusted-internal demonstration in the
bounded payload example; the integrated backend neither imports it by default
nor selects a format from input.

## CLI Scenario

`python -m examples.integrated_order_backend` builds one application with
in-memory providers and processes two realistic multi-line orders on the same
event loop and cache.

The first order includes duplicate SKU occurrences and produces cache misses.
The second order reuses at least one SKU and produces a cache hit. Compact,
sorted JSON events show:

1. `backend_started`;
2. `order_processed` for the first order;
3. `order_processed` for the second order;
4. `cache_stats`; and
5. `backend_stopped`.

Events contain safe identifiers, line count, total, artifact metadata/size,
warning count, and cache counters. They do not emit encoded artifact data or raw
provider errors.

## Test Strategy

All tests are deterministic and run in the default non-Testcontainers lane.

### Domain and service

- immutable/keyword-only/slotted model shape and caller-value preservation;
- exact aggregate type, exact tuple, empty/101-line, and invalid line-type
  rejection before any provider/cache/payload call;
- existing line validation mapped to the exact occurrence index;
- realistic success with stable line order and duplicate SKU occurrences;
- required provider failure propagation and optional warning preservation;
- cache miss/hit behavior across two requests;
- cache loader failure not retained and later recovery;
- calculated line/order totals and decoded artifact equality;
- serialized, compressed, encoded, metadata, and nesting limits; and
- request logging context reset and redaction on every terminal path.

### Application lifecycle

- request success and task removal;
- overall request timeout with terminal cache/enrichment cleanup;
- caller cancellation propagation;
- admission/shutdown boundary race with no post-snapshot registration;
- timeout and caller cancellation against a cancellation-resistant provider,
  with prompt return and retained tracking until terminal;
- late success/failure after caller timeout or cancellation with no un-retrieved
  task exception or raw exception logging;
- graceful close while work completes;
- grace timeout followed by cancellation;
- concurrent close callers sharing one close operation;
- cancellation of one close caller without cancellation of shared shutdown;
- close-task completion after every current waiter is cancelled, with no
  un-retrieved task exception;
- rejection after shutdown begins;
- idempotent close;
- explicit shutdown failure for a cancellation-resistant provider, followed by
  retry after terminal completion;
- context-manager body-error precedence over cleanup failure, plus direct
  cleanup failure when the body succeeded; and
- first-use event-loop binding and pre-mutation cross-loop rejection.

Lifecycle tests coordinate with `asyncio.Event`; real sleeps and polling loops
are not acceptable proof.

### CLI and documentation

- exact ordered JSON events, first-request miss, second-request hit, safe
  artifact summary, and clean shutdown;
- reciprocal README locale links and meaning-equivalent commands/contracts;
- root README navigation and WIP issue checkpoint; and
- mandatory Architecture/Sequence PNG embeds plus SVG links and all four asset
  files.

## Documentation and Diagrams

Both example README locales explain the scenario, non-goals, aggregate
invariants, existing service reuse, cache-backed required provider, optional
warnings, artifact trust/limits, timeout/cancellation/shutdown, exact run/test
commands, expected events, troubleshooting, and unsupported production use.

The Architecture diagram is a static responsibility view of the application
lifecycle, aggregate service, four focused services, cache, providers, and
payload ownership. The Sequence diagram is a time-ordered view of multi-line
success plus invalid-input, optional-provider-warning, timeout/cancellation,
and shutdown branches.

Assets are created only after implementation exists. Both locales directly
embed the rendered PNG and link its SVG source. XML parsing, CairoSVG scale-2
rendering, connector/geometry/endpoint/mixed-corner audits, sequence-style
audit, and full-size PNG inspection are blocking completion evidence.

## Acceptance Mapping

| Issue acceptance criterion | Design proof |
|---|---|
| Compose focused application boundaries | Explicit composition root and example-local cache provider adapter |
| Stable ordering and caller-owned input | Immutable aggregate, occurrence-indexed results, no input mutation |
| Invalid input before external work | Two-phase aggregate and delegated line validation before enrichment |
| Required/optional provider failures | Existing enrichment failure and warning contracts preserved |
| Timeout/cancellation cleanup | Overall request timeout, provider timeout, tracked tasks, cache waiter cleanup |
| Cache hit/miss/loader failure | Shared caller-owned cache, operational stats, failure-recovery tests |
| Payload trust and limits | Fixed untrusted JSON service and decoded artifact/limit tests |
| Bounded shutdown | Stop-accept, grace, cancel, terminal verification, explicit pending error |
| Bilingual architecture/sequence guidance | Required README pair and source-backed PNG/SVG assets |

## Risks and Mitigations

- **Example becomes a new framework:** keep only one aggregate, one adapter, one
  orchestrator, and one lifecycle boundary; add no generic ports beyond the
  existing protocols.
- **Duplicate validation:** aggregate validates shape only; field semantics stay
  in `OrderIntakeService`.
- **Nested concurrency:** cache-backed provider performs sequential reads inside
  each batch; `CatalogEnrichmentService` owns bounded provider concurrency.
- **Cancellation swallowed by adapters:** do not catch `BaseException` or
  `asyncio.CancelledError`; test terminal task/cache state.
- **Shutdown can hang:** use separate finite grace and cancellation timeouts and
  expose remaining work explicitly.
- **Artifact leaks sensitive state:** encode only the documented processed order
  document; CLI emits metadata and size, never payload bytes.
- **Diagrams become decorative:** derive labels and arrows from implemented
  source and test README exposure plus source filenames.

## Rollback

Rollback removes the additive `integrated_order_backend` example, its root
README/WIP navigation, tests, diagrams, and Type A artifacts. No dependency,
lockfile, existing example, public library API, persisted schema, external
service, or production deployment is migrated.

## Stop Condition

Stop before merge after the approved implementation plan is complete, all
deterministic repository checks pass, diagrams are rendered/audited/inspected,
the final six-perspective review reaches P0=0/P1=0, and the exact PR head passes
hosted CI plus current review/thread verification. Merge requires a fresh
explicit approval and auto-merge remains forbidden.
