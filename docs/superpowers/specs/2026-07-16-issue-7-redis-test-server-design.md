# Issue #7 Redis Test Server Workshop Design

## Status

- Issue: [#7 — add a Redis-backed integration test workshop](https://github.com/bluetape4k/bluetape-py-workshop/issues/7)
- Milestone: `0.1.0`
- Branch: `feat/issue-7-redis-test-server`
- Base: `develop` at `55c0555bb0ac778df838db077afd1cbcf4eed21e`
- Work type: Type A — Docker-backed runnable example with lifecycle, failure, CI, and documentation boundaries
- Design approval: bounded application-owned RESP probe over `RedisServer`, approved in the active thread on 2026-07-16 KST

## Problem

Readers need a runnable integration-test example that demonstrates how to own a
temporary Redis dependency without duplicating container configuration or
turning workshop code into a production Redis provider. The example must keep
the deterministic test lane independent from Docker while proving real startup,
readiness, connection discovery, application interaction, and cleanup in an
explicit Docker lane.

## Reader Outcome

After completing the example, a reader can:

1. construct a `RedisServer` without contacting Docker and explain its
   unstarted state;
2. start it with a bounded readiness timeout and distinguish stable startup
   failure categories;
3. consume `RedisConnectionDetails` instead of reconstructing a host, port, or
   URL from container settings;
4. perform one application-shaped `PING` / `SET` / `GET` round trip through a
   bounded, workshop-owned probe;
5. prove cleanup after both success and an application-body failure; and
6. run deterministic and Docker-backed tests with separate commands while
   understanding the Architecture and Sequence diagrams in either README locale.

## Current Evidence

The workshop baseline is `origin/develop@55c0555` and the pinned
`bluetape-py` source is
`4b7458f22cea0a9e757b5fbf7f5ff4bc8c23cb9a`.

- `bluetape.testcontainers.RedisServer` is a synchronous, single-owner,
  single-use wrapper. Construction does not access Docker.
- `RedisServer.start()` performs cached-image lookup, bounded image pull,
  container startup, and `redis-cli ping` readiness using `startup_timeout`.
- A running server exposes immutable `RedisConnectionDetails`; `details`,
  `host`, `port`, and `url` reject unstarted or closed access.
- Startup failures expose `TestcontainerStartError.kind` as one of
  `runtime-unavailable`, `image-pull`, `readiness-timeout`, or
  `wrapper-failure`. Provider diagnostics are intentionally redacted.
- The wrapper labels managed containers with
  `com.bluetape.testcontainers.redis=true`, suppresses Ryuk, and retains a
  cleanup-pending container reference when stop fails so `close()` can retry.
- The upstream integration proof uses a small standard-library RESP client and
  runs Docker-backed tests serially. The wrapper deliberately has no
  `redis-py` dependency.
- The local baseline passes `165 passed, 1 skipped`; Docker server `28.4.0` is
  reachable and no labeled Redis test container exists before implementation.

## Constraints

- Python 3.13.14, uv 0.11.28, the committed lockfile, and the pinned
  `bluetape-testcontainers` source remain authoritative.
- Do not add `redis-py`, construct `GenericContainer`, initialize Ryuk, choose a
  fixed host port, or duplicate the Redis image/readiness configuration.
- Use the trusted default `redis:8` image. Received input never chooses an image
  or startup timeout.
- Keep the example synchronous and single-owner. It introduces no background
  task, shared fixture, parallel Docker launch, retry loop, cache provider,
  distributed coordination, HTTP adapter, credentials, or persistence.
- Default pytest and hosted CI must exclude `testcontainers`; only an explicit
  focused marker command may contact Docker.
- All Docker-backed commands run sequentially. Before and after them, inspect
  the Bluetape Redis label and remove only a confirmed stale workshop container.
- Both README locales embed source-backed Architecture and Sequence PNGs and
  link their SVG sources. Diagram labels remain English and assets are shared.
- Merging, release publication, tagging, and milestone closure remain outside
  this PR authority.

## Considered Approaches

### Chosen: domain-shaped bounded RESP probe over `RedisServer`

Create `RedisOrderStatusProbe`, which receives immutable
`RedisConnectionDetails` and performs only the fixed teaching flow `PING`,
`SET`, and `GET`. A small private RESP encoder/parser uses one connection per
command, a finite socket timeout, bounded command parts, bounded response lines,
and bounded bulk payloads. `run_workshop()` owns the `RedisServer` context and
constructs the probe only after `server.details` becomes available.

This keeps the lifecycle visible, adds no dependency, and provides enough
application code for deterministic protocol and orchestration tests without
claiming to be a production Redis client.

### Rejected: raw socket calls only inside the Docker test

This is shorter, but it produces a test-shaped snippet rather than an
independently runnable example. It also leaves no deterministic application
boundary for timeout, protocol, and lifecycle orchestration tests.

### Rejected: add `redis-py`

This would provide a production-grade client, but the new dependency and client
configuration would obscure the ecosystem wrapper contract. It would also make
the workshop look like a production cache/provider recommendation, which is an
explicit non-goal.

## Package Layout

```text
examples/redis_test_server/
├── __init__.py
├── __main__.py
├── application.py
├── probe.py
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
    ├── test_probe.py
    └── test_redis_integration.py
```

`probe.py` is deliberately local to the example. It is not exported as a
general Redis client and supports no arbitrary command surface.

## Contracts

### `RedisProbeResult`

An immutable, slotted, keyword-only dataclass records only the fixed workshop
scenario and safe observable state:

- normalized `order_id`;
- expected `status`;
- `ping_succeeded`;
- `write_succeeded`; and
- `read_succeeded`.

It never records connection details, container identifiers, raw protocol data,
or credentials.

### `RedisOrderStatusProbe`

The constructor requires exact `RedisConnectionDetails` and a finite positive
`command_timeout` (default 2 seconds). An injectable socket factory is a
deterministic-test seam only; production composition uses
`socket.create_connection`. The implementation fixes maximum UTF-8
command-part length at 64 bytes, order-ID length at 48 bytes so the fixed key
also fits that part bound, status length at 64 bytes, response-line length at
128 bytes, and bulk response length at 64 bytes; callers cannot weaken these
teaching-scenario bounds. The public `verify(order_id, status)` method:

1. normalizes and validates the two application values;
2. sends `PING` and requires `PONG`;
3. writes key `workshop:order:{order_id}` with the expected status and requires
   `OK`;
4. reads the same key and requires the exact expected bytes; and
5. returns `RedisProbeResult`.

`read_status(order_id=...)` performs only the same fixed-key `GET` and returns a
normalized status or `None`. It exists so a fresh-server integration test can
prove that the prior container's state was released; it is not an arbitrary
command or production provider surface. `verify()` uses this method for its
read-back step.

The private protocol surface accepts only command tuples selected by the
probe, rejects blank application values and values above the 64-byte encoded
bound, and prevents command injection by encoding each value as one length-
delimited RESP part. It uses UTF-8 byte lengths and
`socket.create_connection((details.host, details.port), timeout=...)`, applies
the timeout to the connected socket, and closes it via a context manager.

It parses only the simple-string and bulk-string responses needed by this
scenario. Missing, malformed, truncated, oversized, negative-length other than
`-1`, Redis error, or unexpected response types raise `RedisProbeError`.
Socket and Unicode failures are preserved as the exception cause of a safe
`RedisProbeError`; protocol payload content is not included in public messages.

### `run_workshop()`

`run_workshop(*, server, probe_factory=RedisOrderStatusProbe)` owns this order:

1. enter `server` so startup and readiness complete;
2. obtain `server.details` exactly once;
3. construct the application probe from those details;
4. execute the fixed order-status round trip; and
5. leave the context on success or any body exception.

The function does not catch body exceptions. The wrapper therefore preserves
the primary application failure while attempting cleanup according to its
public context-manager contract.

## CLI Contract

`python -m examples.redis_test_server` is intentionally Docker-backed.
`main(*, server_factory=RedisServer, workshop_runner=run_workshop) -> int` creates
`RedisServer(startup_timeout=30.0)`, runs the fixed `ORD-1001` / `accepted`
scenario, and emits one compact JSON success event containing only the safe
`RedisProbeResult` fields. The module entry point exits with `main()`'s status;
the injectable factory and runner are deterministic-test seams, not public
image-selection or protocol-extension surfaces.

If startup fails, it emits one compact JSON failure event with
`error_code=testcontainer_start_failed` and the stable failure `kind`, then
returns exit status 1. If the application probe fails, it emits
`error_code=redis_probe_failed` and returns exit status 1. Neither failure path
emits raw provider messages, addresses, container IDs, request values, protocol
payloads, exception text, or tracebacks. Direct `run_workshop()` callers still
receive `RedisProbeError` with its causal exception for local diagnosis.

## Test Strategy

### Deterministic lane

`uv run --locked pytest -m "not testcontainers"` must not access Docker.

- construct `RedisServer` and prove unstarted details are unavailable;
- reject unsafe image and timeout configuration through public wrapper APIs;
- use scripted fake sockets to prove exact `PING` / `SET` / `GET` requests and
  successful result fields;
- prove socket timeout, malformed response, oversized response, missing key,
  and value mismatch errors retain safe causal context where applicable;
- use a fake context-managed server and probe factory to prove details are read
  only after entry and cleanup runs on success and body failure;
- prove CLI success plus stable startup- and probe-failure JSON without Docker;
  assert stderr stays empty; and
- enforce bilingual token parity, exact commands, source references, and all
  four diagram assets.

### Docker lane

Run only this focused command, serially:

```bash
uv run --locked pytest -m testcontainers \
  examples/redis_test_server/tests/test_redis_integration.py -q
```

The integration test uses the default wrapper and public application API to
prove dynamic connection details, `PING` / `SET` / `GET`, state closure after
success, and state closure after an injected application-body failure. It then
starts a fresh server and proves the previous key is absent. No Docker-backed
test runs concurrently. The runner records the label-filtered container list
before and after the command; the post-run list must equal the pre-run list.

## Documentation and Diagrams

Both README files contain reciprocal locale navigation, scenario, non-goals,
package/API inventory, prerequisites, deterministic command, Docker command,
CLI command, expected JSON, cleanup inspection/removal commands, startup
failure categories, timeout ownership, single-use lifecycle, trusted image
policy, troubleshooting, and unsupported production use. Cleanup guidance uses
`docker ps -a --filter label=com.bluetape.testcontainers.redis=true` for
inspection and permits `docker rm -f <confirmed-container-id>` only after the
reader confirms that the labeled container belongs to this workshop run.

The Architecture diagram maps CLI/application ownership, `RedisServer`, Docker,
`RedisConnectionDetails`, and the bounded probe. The Sequence diagram includes
success plus application-failure cleanup branches. Assets are generated only
after source behavior exists and are tested against source filenames.

## Acceptance Mapping

| Issue acceptance criterion | Design proof |
|---|---|
| Started/unstarted lifecycle explicit | Public wrapper checks, `run_workshop()` order, lifecycle docs/tests |
| Readiness bounded and causal failure retained | `startup_timeout`, stable failure kind, safe CLI event, causal probe errors |
| Wrapper-owned connection details | Probe accepts exact `RedisConnectionDetails`; no endpoint reconstruction |
| Sequential Docker tests and cleanup | Explicit marker command, context ownership, success/failure/fresh-state integration proof |
| Deterministic configuration/lifecycle tests | Default marker exclusion, fake socket/server tests, public unstarted/config checks |
| Equivalent bilingual docs and root navigation | README parity tests, root links, shared Architecture/Sequence PNG+SVG assets |

## Risks and Rollback

- A RESP parser can accidentally become an incomplete client. Keep its command
  surface private, fixed to this scenario, and capped at 48-byte order IDs,
  64-byte command parts/statuses/bulk responses, and 128-byte lines.
- Three short-lived connections add round trips. This is accepted for a
  one-shot teaching probe because it makes ownership and failure isolation
  obvious; production pooling and pipelining remain out of scope.
- A Docker test can leave a container after process termination. Inspect the
  Bluetape label before and after the serial run and document confirmed removal.
- Pull latency can exceed local expectations. Keep the wrapper's 30-second
  operation bound visible and distinguish image acquisition from application
  command timeout.
- Changing pytest selection can hide tests. Register the marker, make default
  exclusion explicit, and run both selection commands during final validation.

Rollback is deletion of the additive example, marker registration, README
navigation, WIP entry, and related documentation. No library API, package lock,
schema, persisted data, or production deployment is migrated.

## Stop Condition

Stop before merge after the exact PR head passes deterministic CI, the focused
serial Docker test, diagram/document checks, final six-perspective review, and
live review/thread verification with P0=0 and P1=0. Merge requires fresh user
approval and auto-merge remains forbidden.
