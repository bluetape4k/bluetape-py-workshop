# Issue #10 Redis Load Coordination Design

## Status and Authority

- Issue: [#10 — add Redis cache coordination examples](https://github.com/bluetape4k/bluetape-py-workshop/issues/10)
- Milestone: `0.2.0`
- Work type: Type A — optional dependency, two-instance async cache topology,
  Redis/Testcontainers integration, and bilingual visual documentation
- Branch: `feat/issue-10-redis-load-coordination`
- Base: `develop@836ff2090eb6a998b7247e9bf89ea3d77065c29d`
- Worktree: `.worktrees/issue-10-redis-load-coordination`
- Design approval: the user approved the scoped two-instance load-coordination
  plan on 2026-07-17 KST. Near-cache invalidation is a separate blocked issue.
- Authorized delivery: push this branch and create a PR to `develop`; merge,
  auto-merge, release, tag, publish, milestone closure, and remote deletion are
  not authorized.

## Problem

The workshop already teaches a process-local `AsyncTTLCache` and a disposable
Redis test server. Learners still need an application-shaped example showing
how two independently cached service instances prevent a cold-key stampede by
using the upstream Redis load coordinator. Issue #10 currently mixes this ready
capability with near-cache invalidation, which remains blocked by upstream
`bluetape-py` issue #56 and redis-py issue #3916.

The example must not imply that load coordination is an L2 cache, distributed
invalidation, a transaction around loader side effects, or a fencing token.

## Current Evidence

- The deterministic baseline at `develop@836ff20` is `290 passed, 1 skipped,
  1 deselected` on Python 3.13.14 with uv 0.11.28.
- The workshop pins every upstream package to
  `4b7458f22cea0a9e757b5fbf7f5ff4bc8c23cb9a`.
- That exact commit contains `bluetape-cache-redis==0.1.0`,
  `AsyncRedisProvider`, `AsyncRedisLoadCoordinator`, `RedisLoadOptions`,
  `ResultEnvelopeCodec`, and stable event/error contracts.
- Upstream issues #54 and #55 are closed. Issue #56 remains open and
  `blocked:upstream`; its public sync/async invalidation-consumer gate is not
  satisfied.
- The upstream coordinator performs local-cache lookup first, joins one local
  same-key flight, uses bounded Redis lease/snapshot/publish operations, reuses
  a matching remote result, refuses silent uncoordinated fallback, preserves
  loader failure and cancellation, and prevents publication after lease loss.
- `examples/redis_test_server` already establishes `RedisServer` ownership and
  serial Docker cleanup conventions.

## Reader Outcome

After running the example, a reader can explain and observe:

1. why each service instance owns a separate local `AsyncTTLCache`;
2. how a shared versioned Redis namespace coordinates one cold load;
3. how the owner publishes a bounded result envelope and the follower reuses it;
4. why a later local hit performs no Redis coordination operation;
5. how timeout, provider failure, loader failure, cancellation, stale envelope,
   lease loss, and cleanup are surfaced; and
6. why near-cache invalidation and production Redis security remain separate
   concerns.

## Chosen Architecture

### Optional dependency boundary

Add `redis-coordination = ["bluetape-cache-redis==0.1.0"]` and a matching uv
Git source at the workshop's existing exact upstream commit. The default
environment remains Redis-provider-free; optional commands use the disposable
`.venv-redis` environment and `--extra redis-coordination`.

### Example-local components

```text
examples/redis_load_coordination/
├── __init__.py              explicit example exports
├── __main__.py              Docker-backed learner entry point
├── codec.py                 strict ProductSummary result-envelope payload codec
├── observer.py              redacted terminal event recorder
├── service.py               one independently cached catalog instance
├── application.py           two-provider scenario and lifecycle ownership
├── README.md
├── README.ko.md
├── docs/images/
│   ├── architecture.svg
│   ├── architecture.png
│   ├── sequence.svg
│   └── sequence.png
└── tests/
    ├── test_codec.py
    ├── test_service.py
    ├── test_application.py
    ├── test_redis_integration.py
    └── test_documentation.py
```

`ProductSummaryCodec` implements the upstream `PayloadCodec` contract using
the public untrusted JSON serde API and exact metadata. It accepts and returns
the existing immutable `ProductSummary`, uses an explicit three-field
allowlist, rejects wrong shapes/types/metadata, and never uses Fory or unsafe
deserialization.

`RedisCatalogInstance` receives a caller-owned `AsyncTTLCache`,
`AsyncRedisProvider`, loader, codec, options, and optional observer. It creates
one `AsyncRedisLoadCoordinator`, exposes `get_product(product_id)` and local
cache statistics, and owns no closeable resource. The key is validated as an
exact non-blank ASCII SKU with a 64-character limit before cache or Redis I/O.

`CoordinationEventRecorder` records only upstream low-cardinality terminal
events. It exposes an immutable snapshot and never stores raw keys, namespace,
tokens, endpoints, values, or exception text.

`run_scenario(redis_url, loader=..., provider_factory=...)` owns two
factory-created providers with
finite connect/socket timeouts and zero retries, two separate local caches,
two recorders, and two `RedisCatalogInstance` values sharing one versioned
namespace. It closes both providers on success, failure, and cancellation. The
default loader uses event-controlled orchestration so instance B starts only
after instance A owns the load, then both complete without timing guesses.
The default factory is `AsyncRedisProvider.from_url`; an injected test factory
must still return exact provider subclasses and exists only to prove lifecycle
closure without exposing production clients.

## Request Sequence

1. Instance A misses its local cache and acquires the Redis lease.
2. Instance A invokes the authoritative loader once.
3. Instance B misses its independent local cache, sees the active lease, and
   polls within the configured attempt/poll/deadline budgets.
4. Instance A encodes and atomically publishes the result and completion marker.
5. Instance B snapshots and reuses the matching envelope without loading.
6. Each local cache stores its returned value.
7. A later call to instance B returns its local value without a Redis command
   or coordination event.

## Failure and Lifecycle Contracts

- Redis timeout/provider/envelope failures raise the stable upstream exception;
  there is no silent cold-load fallback.
- Loader failure identity is preserved. Best-effort lease cleanup never
  replaces it and may add only the upstream static cleanup note.
- Caller cancellation preserves `asyncio.CancelledError`. The local cache owns
  same-key flight cancellation and the coordinator owns at most one shielded
  lease cleanup.
- A mismatched/stale owner envelope is never returned. It is polled past or
  ends in a bounded timeout/invalid-artifact error.
- Lease loss prevents result publication but returns the owner's loaded value
  to that caller and stores it only in that local cache.
- Provider contexts close in reverse construction order on every scenario path.
- The Docker entry point owns one `RedisServer` context; container cleanup is
  verified after success and application-body failure.

## Security and Operations Boundaries

- The workshop container is disposable local infrastructure only. It is not a
  production deployment recipe.
- Production requires `rediss://`, certificate and hostname verification, an
  ACL principal restricted to the documented commands/key prefix, finite
  connect/socket timeouts, zero retries, and no plaintext fallback.
- Namespace and key digests are pseudonyms, not confidentiality. Do not put
  secrets or sensitive identifiers in either.
- Events remain bounded and low-cardinality. External route/environment labels
  are caller-owned.
- Rollback means quiescing writers, reverting the application, waiting at least
  `max(lease_ttl, result_ttl) + redis_io_timeout`, then using bounded operator
  cleanup for only the retired namespace. The example does not automate it.

## Considered Approaches

### Chosen: standalone two-instance example with the upstream coordinator

This exposes the real ownership and failure contracts while keeping the
optional Redis dependency isolated from every existing example and default
install.

### Rejected: add Redis behavior to `cached_product_catalog`

It would turn a focused local-cache lesson into an optional distributed system,
make default imports conditional, and blur the difference between local hits
and cross-process coordination.

### Rejected: add near-cache invalidation now

The required public sync/async invalidation-consumer API does not exist. Using
redis-py internals, Pub/Sub, polling, or a workshop-owned invalidation layer
would bypass the explicit upstream blocker and teach an unsupported contract.

## Acceptance Criteria

- Issue #10 is narrowed to load coordination and no longer carries
  `blocked:upstream`; a separate milestone issue retains the invalidation
  blocker and upstream links.
- The optional extra resolves from the existing exact commit while default
  sync/import proof remains Redis-provider-free.
- Two independent instances collapse one cold key to one loader call, the
  follower reuses the result, and a later local hit emits no Redis event.
- Deterministic optional tests cover success, timeout, provider failure, loader
  failure, cancellation, stale envelope, lease loss, and cleanup.
- One serial Docker test uses `RedisServer` and proves real Redis success,
  failure cleanup, provider closure, and container cleanup.
- Both README locales are meaning-equivalent, reciprocal, runnable, explicit
  about unsupported production behavior, and directly embed Architecture and
  Sequence PNGs with SVG links.
- Root README locales and `WIP.md` register the example and exact optional
  commands.
- Ruff, dependency/documentation tests, optional tests, serial Docker test,
  full deterministic pytest, actionlint, diagram audits, and diff hygiene pass.
- Type A spec/plan/final reviews converge at `P0=0, P1=0`, a durable lesson is
  committed, and the exact PR head is verified before the merge gate.

## Non-Goals

- Near-cache invalidation, RESP3 push consumption, Pub/Sub, polling invalidation,
  or any private redis-py API.
- A workshop-owned Redis provider, lock, coordinator, result-envelope format,
  cache abstraction, retry policy, or production deployment helper.
- L2 caching, fencing, exactly-once side effects, distributed transactions,
  HTTP/ASGI integration, authentication, release, tag, publish, or milestone
  closure.

## Definition of Done

The feature is merge-ready only when every acceptance criterion has fresh
evidence on the exact pushed PR head, hosted checks and live review state are
green, and the workflow reports `P0=0, P1=0`. Completion stops at fresh merge
approval; merge and cleanup are a later separately authorized step.
