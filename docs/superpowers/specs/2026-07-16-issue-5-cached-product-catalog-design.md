# Issue #5 Cached Product Catalog Design

## Status

- Issue: [#5 — add a cached product catalog service](https://github.com/bluetape4k/bluetape-py-workshop/issues/5)
- Milestone: `0.1.0`
- Branch: `feat/issue-5-cached-product-catalog`
- Base: `develop` at `762c20fc2e7ccf4e5a5c5afdb8b7ac1d70ebcc06`
- Work type: Type A — new sync and async application-service example
- Design approval: separate sync and async services, approved in the active
  thread on 2026-07-16 KST

## Problem

Readers need an application-shaped example that shows how `bluetape-cache`
fits around a product loader without hiding cache ownership, TTL behavior,
capacity limits, loader failures, or asyncio cancellation. A wrapper that only
returns values would obscure the package's observable hit, miss, expiry,
eviction, and load counters. A global cache or workshop-owned cache abstraction
would also teach the wrong lifecycle boundary.

## Reader Outcome

After running the example, a reader can:

1. inject a caller-owned `TTLCache` or `AsyncTTLCache` into an application
   service;
2. observe first-load misses, subsequent hits, TTL expiry, and LRU eviction;
3. understand that loader failures are shared with current callers but are not
   cached;
4. preserve caller-owned immutable values without copying or mutation;
5. propagate async cancellation without leaving an owned cache task; and
6. explain the same lifecycle from bilingual README files and source-backed
   Architecture and Sequence diagrams.

## Current Evidence

The pinned source baseline resolves `bluetape-cache==0.1.0` from
`bluetape-py@4b7458f22cea0a9e757b5fbf7f5ff4bc8c23cb9a`.

The public package exports:

- `TTLCache[K, V]`;
- `AsyncTTLCache[K, V]`;
- immutable `CacheStats`;
- `RecursiveLoadError`; and
- `CacheLoadLimitError`.

Both cache types accept keyword-only `default_ttl`, `max_size`, optional
`max_inflight`, and an injectable nanosecond clock. Both expose
`get_or_load(key, loader, *, ttl=None)`. The async cache binds to its first event
loop, exposes async public operations, and uses `size()` instead of `len()`.
`CacheStats` separates lifetime counters from the point-in-time inflight,
abandoned, and superseded gauges.

Repository patterns from `examples/order_intake` and
`examples/catalog_enrichment` establish independently runnable packages,
immutable contracts, injected dependencies, deterministic CLIs, focused tests,
and aligned bilingual README/diagram pairs.

## Constraints

- Python 3.13.14 and the committed uv lockfile remain authoritative.
- No dependency, `pyproject.toml`, or `uv.lock` change is expected.
- Cache instances, clocks, and loaders are created by the composition root and
  injected into services.
- Product IDs use the existing workshop SKU boundary: ASCII letters, digits,
  `.`, `_`, or `-`, normalized to uppercase, with a maximum length of 64.
- No mutable global cache, singleton registry, service locator, or workshop
  cache adapter is allowed.
- No Redis, distributed coordination, near-cache invalidation, HTTP, ASGI,
  persistence, background expiry worker, retry, or production provider client.
- Every runnable example README pair must embed Architecture and Sequence PNGs
  and link the corresponding SVG sources.
- The CLI and tests must be deterministic: no real clock sleeps, network,
  Docker, or credentials.

## Considered Approaches

### Chosen: separate sync and async application services

Create `SyncProductCatalogService` and `AsyncProductCatalogService`. They share
only immutable domain models and key validation. Each service accepts the exact
matching cache type and loader shape.

Why chosen:

- sync and async lifecycle contracts remain visible in type signatures;
- cancellation exists only on the async surface;
- the example uses the real cache API without adding a protocol that merely
  mirrors it; and
- readers can study either flow independently.

### Rejected: one service with sync and async methods

A single class would need to own or accept two cache implementations and two
loader shapes. That makes construction ambiguous and creates methods whose
dependencies are unrelated to half of the instance.

### Rejected: one service behind a workshop cache protocol

A protocol could normalize sync and async methods only by introducing an
awaitable abstraction, overloads, or adapters. It would hide the exact
`bluetape-cache` API and violate the non-goal of a workshop-owned cache layer.

## Package Layout

```text
examples/cached_product_catalog/
├── __init__.py
├── __main__.py
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
    ├── __init__.py
    ├── test_application.py
    ├── test_documentation.py
    └── test_service.py
```

`tests/__init__.py` prevents pytest basename collisions with the other example
test packages.

## Public Model and Provider Contracts

```python
@dataclass(frozen=True, slots=True, kw_only=True)
class ProductSummary:
    product_id: str
    name: str
    price_cents: int


class SyncProductLoader(Protocol):
    def __call__(self, product_id: str) -> ProductSummary: ...


class AsyncProductLoader(Protocol):
    async def __call__(self, product_id: str) -> ProductSummary: ...
```

`ProductSummary` is immutable so a cached instance can be returned by identity
without exposing application-service mutation. Loaders are callable protocols
because that is the exact shape accepted by `get_or_load`; the workshop does
not invent repository or cache interfaces.

Product keys are checked with `bluetape.core.require_instance` and
`require_not_blank`, stripped, uppercased, limited to 64 characters, and
validated against the existing ASCII SKU grammar. The normalized product ID is
the cache key. There is no tenant or authorization dimension in this
deterministic scenario; the README explicitly warns real applications to
include every tenant, authorization, locale, and other value-affecting context
in the key before applying this normalization pattern.

## Service Contracts

```python
class SyncProductCatalogService:
    def __init__(
        self,
        *,
        cache: TTLCache[str, ProductSummary],
        loader: SyncProductLoader,
    ) -> None: ...

    def get_product(self, product_id: str) -> ProductSummary: ...
    def stats(self) -> CacheStats: ...


class AsyncProductCatalogService:
    def __init__(
        self,
        *,
        cache: AsyncTTLCache[str, ProductSummary],
        loader: AsyncProductLoader,
    ) -> None: ...

    async def get_product(self, product_id: str) -> ProductSummary: ...
    async def stats(self) -> CacheStats: ...
```

Each `get_product` method validates the key and delegates once to the matching
cache's `get_or_load`. Services do not catch loader exceptions or
`asyncio.CancelledError`. The stats methods expose the immutable package
snapshot without reshaping, resetting, logging, or exporting it. README and CLI
explanations distinguish lifetime counters (`hits`, `misses`, `loads`,
`load_failures`, `evictions`, and `expirations`) from point-in-time inflight,
abandoned, and superseded gauges. `clear()` does not reset lifetime counters.
Services inspect no private cache fields; all behavior and observability use
the pinned public API.

The services do not expose `set`, `invalidate`, or `clear`. Those lifecycle and
mutation operations remain available to the composition root through its
owned cache instance. Tests use that ownership boundary to prove preservation
of a caller-set value.

## Data Flow

### Sync request

1. Caller passes a product ID to `SyncProductCatalogService.get_product`.
2. Service strips and validates the ID.
3. `TTLCache.get_or_load` records a hit or miss.
4. On a miss, the caller-provided loader returns `ProductSummary`.
5. The cache publishes the value with its configured TTL and returns it.
6. Service returns the same object and exposes the resulting `CacheStats`.

### Async request and cancellation

1. Caller awaits `AsyncProductCatalogService.get_product`.
2. Service normalizes the ID and awaits `AsyncTTLCache.get_or_load`.
3. The cache owns a bounded named loader task for a miss and coalesces same-key
   waiters.
4. Success publishes and returns the immutable value.
5. Caller cancellation propagates as `asyncio.CancelledError`.
6. When the last waiter cancels, the cache requests loader cancellation and
   may return to the caller before a slow loader finishes terminal cleanup.
7. While cleanup is deliberately held, tests observe one inflight abandoned
   load. After releasing the loader cleanup event, they await terminal state
   and prove both gauges return to zero and no cache-owned task remains.

## Observable Scenario

The module entry point constructs a manual monotonic clock, bounded sync and
async caches, and deterministic in-memory loaders. It prints stable JSON lines
for:

- sync miss then hit;
- sync expiry and reload;
- sync capacity eviction;
- sync loader failure followed by successful recovery;
- async miss then hit; and
- final sync/async stats snapshots.

Every line contains an `event` and `mode`. Value events additionally contain
normalized `product_id`, `name`, and `price_cents`; stats events contain the
public `CacheStats` fields; the expected loader-failure event contains only a
safe stable error code. The command exits nonzero on any unexpected exception
and never prints raw cache keys, loader exception text, or object reprs.

Cancellation is demonstrated in tests and explained in the README rather than
forced into the default CLI, keeping the command short and deterministic.

## Error and Cancellation Policy

- Non-string, blank, oversized, non-ASCII, or grammar-invalid IDs fail before
  cache access with explicit `TypeError` or `ValueError` and never reach the
  loader.
- `KeyError` is not used as a service-level missing-product sentinel; any
  loader exception is propagated unchanged.
- Loader exceptions are not cached. A later call may invoke a recovered loader
  and publish successfully.
- `CacheLoadLimitError` and `RecursiveLoadError` remain visible package
  exceptions; the service does not translate them.
- `asyncio.CancelledError` is never caught or converted by the service.
- Neither service logs product keys, exception text, or values. README guidance
  warns that cache keys and loader exceptions may contain sensitive context.

## Failure Modes and Required Proof

| Failure mode | Risk | Required proof |
|---|---|---|
| Invalid product ID | meaningless, colliding, oversized, or context-confused key | sync and async non-string, blank, oversized, non-ASCII, and grammar-invalid cases fail before loader invocation; normalization is exact |
| TTL boundary reached | stale product survives expiry or expires early | manual clock proves a hit at `expires_at - 1ns`, then expiry and reload exactly at `expires_at` for sync and async flows |
| Capacity exceeded | unbounded local memory or wrong eviction | `max_size=2`; third insertion evicts the LRU entry and increments eviction |
| Loader raises | failure poisons later requests | original exception propagates; subsequent load succeeds; `load_failures` and `loads` are exact |
| Caller sets a value | service overwrites or copies caller state | service returns the exact caller-set immutable object and loader is not called |
| Same-key async callers overlap | duplicate load, divergent outcome, or incorrect waiter ownership | two event-driven callers share one loader and the same value or failure; cancelling one waiter leaves the survivor and loader running |
| Async caller cancels | swallowed cancellation or leaked cache task | after caller `CancelledError`, held cleanup reports `inflight_loads=1` and `abandoned_loads=1`; after release and terminal completion both gauges are zero and no `bluetape-cache-*` task remains |
| Cache reused across event loops | invalid async ownership | README documents first-loop binding; example constructs and uses the async cache in one `asyncio.run` lifecycle |

## Testing Strategy

### Service tests

- shared normalization plus non-string, blank, oversized, non-ASCII, and
  grammar-invalid key rejection before cache or loader access;
- sync and async miss-to-hit identity and exact stats;
- expiry with a manual-clock hit at `expires_at - 1ns` and reload at the exact
  `expires_at` boundary for sync and async caches;
- LRU capacity eviction and reload;
- loader failure propagation and successful retry;
- caller-owned `set` value preservation;
- event-driven same-key async coalescing for shared success and failure with
  one loader invocation and exact `loads`/`coalesced_waiters` counters;
- cancellation of one of two async waiters while the survivor completes;
- last-waiter cancellation propagation, observable abandoned/inflight state,
  terminal cleanup, and named-task removal; and
- public constructor, method, protocol, and immutable model shape.

Tests use events for async coordination and a manually advanced callable clock.
They do not depend on sleeps longer than an event-loop checkpoint.

### Application and documentation tests

- run `python -m examples.cached_product_catalog` and parse deterministic JSON;
- confirm reciprocal `English | 한국어` navigation;
- confirm exact commands, package/API names, lifecycle limits, and source links;
- require Architecture and Sequence PNG/SVG assets in both README files; and
- rely on the root repository contract to auto-discover this runnable example.

### Validation ladder

```bash
uv sync --locked --python 3.13.14
uv run --locked python -m examples.cached_product_catalog
uv run --locked pytest examples/cached_product_catalog/tests -q
uv run --locked pytest tests/test_dependency_baseline.py -q
uv run --locked ruff format --check .
uv run --locked ruff check .
uv run --locked pytest
git diff --check
```

No package build, lock update, Docker, Testcontainers, network, or workflow
change is triggered by this design.

## Documentation and Diagrams

`README.md` and `README.ko.md` must remain equivalent and include:

- Scenario and non-goals;
- exact `bluetape-cache` source status and imports;
- sync and async run paths;
- hit, miss, expiry, eviction, failure, and cancellation interpretation;
- lifecycle, loop, key-sensitivity, logging, and troubleshooting boundaries;
- lifetime-counter versus point-in-time gauge semantics, including that
  `clear()` does not reset lifetime stats;
- entry-count capacity rather than byte sizing, value identity, and immutable
  application-boundary guidance;
- Architecture PNG embed plus SVG link; and
- Sequence PNG embed plus SVG link.

The Architecture diagram answers who owns the cache, loaders, services, clock,
and stats. The Sequence diagram shows the sync/async miss-to-load-to-publish
path plus expiry, loader-failure recovery, and cancellation branches. Assets
are created after the implementing source exists and are rendered and inspected
under the repository diagram contract.

Root `README.md`, `README.ko.md`, and `WIP.md` add the new example navigation,
current status, focused commands, validation evidence, and next dependency-ready
issue.

## Compatibility and Migration

This is a new workshop example. It adds no compatibility alias and changes no
existing example API. The pinned `bluetape-cache` public API is used directly.
If source inspection or tests reveal a mismatch with that pinned contract,
implementation stops and records the upstream dependency issue rather than
adding a workshop shim.

## Acceptance Criteria

- [ ] Separate sync and async application services use injected caller-owned
      caches and loaders.
- [ ] Immutable product values, normalization, and empty-key behavior are
      explicit.
- [ ] Sync and async tests prove hit, miss, expiry, LRU capacity, loader failure
      recovery, and caller-owned value preservation.
- [ ] Async tests prove cancellation propagation and terminal task cleanup with
      event-driven synchronization.
- [ ] Async tests prove same-key success/failure coalescing and that cancelling
      one waiter does not cancel a surviving waiter or loader.
- [ ] Cache stats make the scenario observable without callbacks or global
      logging.
- [ ] The deterministic CLI runs without network, Docker, real sleeps, or
      credentials.
- [ ] English and Korean README files are equivalent and embed required
      Architecture and Sequence diagrams with SVG source links.
- [ ] Root navigation and WIP status identify issue #5 and the next milestone
      step.
- [ ] Focused and full repository validation pass with P0=0 and P1=0.

## Definition of Done

The design is ready for planning when it contains no placeholders or ambiguous
ownership, all acceptance criteria map to observable tests or documentation,
the six required review perspectives converge at P0=0/P1=0, and the user
approves this written specification. Implementation and PR publication remain
out of scope until the subsequent executable plan is written, reviewed,
approved, and explicitly authorizes repository/base/head delivery.
