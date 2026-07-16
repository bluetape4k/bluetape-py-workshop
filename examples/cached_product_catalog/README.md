# Cached Product Catalog

English | [한국어](README.ko.md)

This runnable example wraps a product loader with caller-owned local TTL caches.
It keeps cache ownership, lifecycle counters, failure recovery, and asyncio
cancellation visible instead of hiding them behind a workshop abstraction.

## Scenario

A product catalog repeatedly reads immutable product summaries. The first read
is a cache `miss` and invokes the injected loader; a repeated read is a `hit`.
A manual clock demonstrates exact `expiry`, and a two-entry capacity demonstrates
LRU `eviction`. Loader failure is propagated and not cached, so a later call can
recover.

Non-goals:

- no Redis, distributed coordination, near-cache invalidation, or persistence;
- no HTTP, ASGI, provider SDK, retry, or background expiry worker;
- no global cache, singleton, service locator, or workshop cache adapter;
- no network, Docker, credential, or real-clock dependency.

## Architecture

![Cached Product Catalog Architecture](docs/images/architecture.png)

[Open the Architecture SVG source](docs/images/architecture.svg).

The composition root owns the cache, loader, clock, and event loop. It injects
either `TTLCache` into `SyncProductCatalogService` or `AsyncTTLCache` into
`AsyncProductCatalogService`. Both services normalize the key once, delegate to
the matching public cache API once, and return the same immutable
`ProductSummary` object. `CacheStats` remains a caller-readable snapshot.

| Component | Owner | Responsibility |
|---|---|---|
| Composition root | Caller | Construct cache, loader, clock, and async lifecycle |
| Sync/async catalog service | Example | Normalize product IDs and delegate once |
| `TTLCache` / `AsyncTTLCache` | Caller via `bluetape-cache` | TTL, LRU capacity, loading, coalescing, and stats |
| Product loader | Injected adapter | Produce an immutable `ProductSummary` |
| `ProductSummary` | Example | Frozen, slotted, keyword-only cached value |

## Sequence Diagram

![Cached Product Catalog Sequence Diagram](docs/images/sequence.png)

[Open the Sequence Diagram SVG source](docs/images/sequence.svg).

The Sequence Diagram shows miss → loader → publish → return, a direct hit,
exact-boundary expiry and reload, failure followed by recovery, two async
waiters sharing one load, and cancellation cleanup. Cancelling one waiter does
not cancel the loader while another waiter survives. Cancelling the last waiter
propagates `CancelledError`; a slow loader may remain temporarily abandoned
until terminal cleanup finishes.

## Packages and APIs

- `bluetape-cache`: `bluetape.cache.TTLCache`,
  `bluetape.cache.AsyncTTLCache`, and `bluetape.cache.CacheStats`;
- `bluetape-core`: `bluetape.core.require_instance` and
  `bluetape.core.require_not_blank`;
- `bluetape-testing`: `bluetape.testing.eventually_async` for a bounded terminal
  cleanup assertion in tests.

These packages resolve from pinned `bluetape-py` commit
[`4b7458f22cea0a9e757b5fbf7f5ff4bc8c23cb9a`](https://github.com/bluetape4k/bluetape-py/tree/4b7458f22cea0a9e757b5fbf7f5ff4bc8c23cb9a).

## Run

From the repository root, prepare Python 3.13.14 and the locked environment:

```bash
uv sync --locked --python 3.13.14
```

Run the deterministic in-memory scenario:

```bash
uv run --locked python -m examples.cached_product_catalog
```

Stdout contains one JSON object per line. Representative events are:

```json
{"event":"sync_miss","mode":"sync","name":"Mechanical Keyboard","price_cents":12500,"product_id":"SKU-1"}
{"event":"sync_hit","mode":"sync","name":"Mechanical Keyboard","price_cents":12500,"product_id":"SKU-1"}
{"error_code":"loader_unavailable","event":"sync_loader_failed","mode":"sync"}
```

The command never prints raw loader exception text or object representations.

## Cache Lifecycle

| Condition | Observable behavior |
|---|---|
| First valid key | `misses` and `loads` increase; loader result is published |
| Repeated key before TTL | `hits` increases; exact cached object is returned |
| Clock reaches `expires_at` | `expirations` increases; the next read reloads |
| A third LRU entry is inserted | `evictions` increases; least-recent entry is removed |
| Loader raises | Original exception propagates; `load_failures` increases; nothing is cached |
| Same async key overlaps | One load runs; `coalesced_waiters` increases |
| Last async waiter cancels | Native `CancelledError`; abandoned/inflight gauges reach zero after cleanup |

`hits`, `misses`, `loads`, `load_failures`, `evictions`, and `expirations` are
lifetime counters. `inflight_loads`, `abandoned_loads`, and `superseded_loads`
are point-in-time gauges. `clear()` removes entries but does not reset lifetime
counters.

## Ownership and Safety Boundaries

- Capacity is an entry count, not byte or memory sizing. Choose limits using
  measured value sizes in a real application.
- The normalized key is uppercase ASCII `[A-Z0-9][A-Z0-9._-]*`, at most 64
  characters. Invalid input fails before cache or loader access.
- Real keys must include every value-affecting tenant, authorization, locale,
  and policy dimension. This single-tenant sample does not model them.
- Cached values are returned by identity. Keep them immutable, as this example
  does with frozen `ProductSummary`.
- `AsyncTTLCache` binds to the first running event loop that uses it. Construct
  and consume it within one application loop; do not reuse it across loops.
- The service does not catch loader errors, `CacheLoadLimitError`,
  `RecursiveLoadError`, or `CancelledError`, and it emits no logs.
- Do not log raw cache keys, values, or loader exception text when adding real
  telemetry.

## Tests

Run this example independently:

```bash
uv run --locked pytest examples/cached_product_catalog/tests -q
```

The tests use a nanosecond manual clock and asyncio events rather than timing
sleeps. They prove sync/async hit, miss, expiry, LRU eviction, failure recovery,
caller-set value identity, shared async success/failure, partial cancellation,
last-waiter cleanup, CLI output, locale parity, and diagram presence.

## Cleanup and Troubleshooting

There is no server, container, file, or background service to remove. Each
cache is local and caller-owned; process exit releases it.

- Run commands from the repository root so the module is importable.
- If dependencies drift, rerun `uv sync --locked --python 3.13.14`.
- If async use reports a different event loop, create and use the cache inside
  one `asyncio.run` or application loop lifecycle.
- A persistent loader failure belongs to the injected provider; the service
  intentionally adds no retry.
- Redis and distributed invalidation require a different example and design.

## Source

- [models.py](models.py) — immutable cached product value
- [providers.py](providers.py) — sync and async loader protocols
- [service.py](service.py) — normalization and one-call cache delegation
- [__main__.py](__main__.py) — deterministic JSON scenario
- [tests](tests) — behavior, cancellation, CLI, documentation, and diagram checks
