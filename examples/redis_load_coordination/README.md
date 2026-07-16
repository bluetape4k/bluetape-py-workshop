# Redis Load Coordination

English | [한국어](README.ko.md)

## Scenario

Two catalog service instances receive the same cold request for `SKU-42`.
Each instance owns a separate `AsyncTTLCache`, so a process-local cache alone
cannot prevent both instances from calling the authoritative product loader.
They borrow separate `AsyncRedisProvider` clients and share one versioned
coordination namespace through `AsyncRedisLoadCoordinator`.

Instance A becomes the owner, loads once, and publishes a bounded result.
Instance B follows the active lease and returns the matching published result
as `RESULT_REUSED`. Its next request is a local hit and never enters Redis.
The CLI exposes only safe counters and outcomes:

```json
{"follower_local_hits": 1, "follower_outcome": "result-reused", "loader_calls": 1, "owner_outcome": "loaded", "product_id": "SKU-42"}
```

This example adopts `bluetape-cache-redis==0.1.0` from exact upstream commit
`4b7458f22cea0a9e757b5fbf7f5ff4bc8c23cb9a`. Upstream provider work
[#54](https://github.com/bluetape4k/bluetape-py/issues/54) and load coordination
[#55](https://github.com/bluetape4k/bluetape-py/issues/55) are complete.

## Architecture

![Redis load coordination architecture](docs/images/architecture.png)

[Open the Architecture SVG source](docs/images/architecture.svg).

`run_workshop` owns one disposable `RedisServer`. `run_scenario` owns two
factory-created providers with `AsyncExitStack`, while each
`RedisCatalogInstance` owns its local cache and borrows its provider. The
upstream coordinator owns lease/snapshot/publish behavior. `ProductSummaryCodec`
owns a strict untrusted JSON allowlist, and `CoordinationEventRecorder` stores
only bounded terminal events.

The local caches are deliberately separate. Redis contains a short-lived
coordination marker and result envelope; it is not used as an L2 cache.

## Sequence Diagram

![Redis load coordination sequence](docs/images/sequence.png)

[Open the Sequence Diagram SVG source](docs/images/sequence.svg).

The application starts A first and waits for its loader admission. It starts B,
waits for B's bounded `SET_IF_ABSENT` attempt, then releases A. This event-driven
ordering proves the owner/follower path without timing sleeps. A publishes,
B returns `RESULT_REUSED`, and B's second call is a local hit with no provider
or coordination event.

## Public APIs Used

- `AsyncTTLCache`: one bounded local cache per instance;
- `AsyncRedisProvider`: one caller-owned, finite-timeout Redis client per instance;
- `AsyncRedisLoadCoordinator`: cache-first distributed load coordination;
- `RedisLoadOptions`: versioned namespace, lease/result TTL, polling, attempt,
  wait, and Redis I/O budgets;
- `ResultEnvelopeCodec`: owner-token-bound result envelope;
- `ProductSummaryCodec`: example-local strict JSON payload codec; and
- `RedisServer`: disposable Redis 8 integration infrastructure.

The package initializer remains dependency-free. Import the explicit optional
submodules only after installing the extra; default pytest collection stays
Redis-provider-free.

## Run

Prerequisites: Python 3.13.14, uv 0.11.28, and a reachable Docker runtime.
Run from the repository root:

```bash
UV_PROJECT_ENVIRONMENT=.venv-redis uv sync --locked \
  --extra redis-coordination --python 3.13.14

UV_PROJECT_ENVIRONMENT=.venv-redis uv run --locked \
  --extra redis-coordination python -m examples.redis_load_coordination
```

Expected fields are `loader_calls: 1`, owner `loaded`, follower
`result-reused`, and `follower_local_hits: 1`. Values, Redis keys, tokens,
endpoints, and raw exception text are not printed.

Run deterministic tests before the Docker lane:

```bash
UV_PROJECT_ENVIRONMENT=.venv-redis uv run --locked \
  --extra redis-coordination pytest -m "not testcontainers" \
  examples/redis_load_coordination/tests -q
```

Run the real Redis test sequentially and by itself:

```bash
UV_PROJECT_ENVIRONMENT=.venv-redis uv run --locked \
  --extra redis-coordination pytest -m testcontainers \
  examples/redis_load_coordination/tests/test_redis_integration.py -q
```

## Outcome and Failure Policy

| Outcome | Caller-visible policy |
|---|---|
| local hit | Return the local value; perform no Redis command and emit no coordination event. |
| `LOADED` | The owner loads, atomically publishes, returns, and populates only its local cache. |
| `RESULT_REUSED` | The follower returns the matching envelope without invoking the loader and populates its own local cache. |
| `LEASE_LOST` | Do not publish; return the owner value only to that caller and its local cache. A duplicate external load is still possible. |
| timeout/provider/envelope failure | Raise the stable upstream exception with no fallback to an uncoordinated loader. |
| loader failure | Preserve the original exception; best-effort cleanup may add only the static cleanup note. |
| cancellation | Preserve `asyncio.CancelledError`; the cache flight and coordinator perform bounded shielded cleanup. |
| stale envelope | Never return an owner-token mismatch; continue within the poll budget or fail boundedly. |

`AsyncExitStack` closes both providers in reverse order on success, failure, or
cancellation. `RedisServer` closes the disposable container when the CLI or
test body exits. Docker-backed paths are sequential, not parallel.

## Security, Operations, and Cleanup

The bundled Docker Redis is local test infrastructure, not a production recipe.
Production Redis requires `rediss://`, a trusted CA, certificate and hostname
verification, an ACL principal restricted to the documented coordination key
prefix and commands, finite connect/socket timeouts, zero retry, and no
plaintext downgrade or fallback.

Namespace and key digests are a pseudonym, not confidentiality. Do not place
secrets or sensitive identifiers in a namespace or key. Terminal observations
stay low-cardinality and exclude raw keys, values, tokens, endpoints, metadata,
and exception text.

Normal context exit removes the workshop container. To inspect an interrupted
local run before deleting anything:

```bash
docker ps -a --filter label=com.bluetape.testcontainers.redis=true
docker rm -f <confirmed-container-id>
```

Production rollback is an operator quiescence procedure, not an example API:
stop writers, restore the prior version, wait at least
`max(lease_ttl, result_ttl) + redis_io_timeout`, verify traffic remains quiet,
then scan and unlink only the retired namespace with bounded batches.

## Troubleshooting

- Docker connection errors: start the local runtime, then rerun only the serial
  `test_redis_integration.py` command.
- `ModuleNotFoundError: bluetape.cache.redis`: use `.venv-redis` and include
  `--extra redis-coordination` in the sync and run command.
- Timeout: inspect stable coordinator/provider codes and finite budgets; do not
  add an uncoordinated fallback.
- `loader_calls` greater than one: check namespace/configuration compatibility,
  lease expiry, and loader duration. Coordination is not fencing or exactly-once.

## Non-Goals

- near-cache invalidation, RESP3 push consumption, Pub/Sub, or polling;
- an L2 cache, fencing token, distributed transaction, or exactly-once loader
  side effect;
- a workshop-owned provider, lock, coordinator, envelope, retry, or cleanup
  library; and
- production authentication, authorization, deployment, or automated rollback.

near-cache invalidation remains blocked in workshop
[#20](https://github.com/bluetape4k/bluetape-py-workshop/issues/20), upstream
[#56](https://github.com/bluetape4k/bluetape-py/issues/56), and
[redis-py #3916](https://github.com/redis/redis-py/issues/3916). No private API
or workshop workaround is used here.
