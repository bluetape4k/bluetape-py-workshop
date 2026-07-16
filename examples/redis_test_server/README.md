# Redis Test Server Workshop

English | [한국어](README.ko.md)

A Docker-backed integration-test example that keeps container lifecycle in the
ecosystem-owned `RedisServer` while the application owns only one fixed,
bounded order-status probe.

## Scenario

An order service needs a real Redis process during integration testing. The
test must wait for readiness, discover the mapped endpoint, prove a minimal
application round trip, and release the container even when application code
fails.

This example performs `PING`, `SET`, and `GET` for `ORD-1001`. It is deliberately
not a production Redis client:

- `RedisServer` owns `redis:8`, image acquisition, container startup,
  `redis-cli ping` readiness, dynamic port mapping, and cleanup.
- `run_workshop()` owns one server context and reads `RedisConnectionDetails`
  only after the server is running.
- `RedisOrderStatusProbe` owns a private RESP subset with a 2-second socket
  timeout and fixed byte limits.
- No `redis-py`, direct `GenericContainer`, fixed host port, shared global
  fixture, retry loop, or production Redis cache/provider is introduced.

## Architecture

[![Redis test server workshop architecture](docs/images/architecture.png)](docs/images/architecture.svg)

The wrapper and application have different responsibilities. The application
never reconstructs a Redis URL or container configuration; it consumes the
immutable details returned by the running wrapper. The probe cannot select an
image or send an arbitrary command.

## Sequence Diagram

[![Redis test server workshop sequence](docs/images/sequence.png)](docs/images/sequence.svg)

Construction is deterministic and Docker-free. Entering the context starts the
bounded lifecycle. Both the successful and failing body paths call `close()`;
the wrapper preserves the primary body failure if cleanup also fails and keeps
the container reference so a caller can retry `close()`.

## Ownership and limits

| Owner | Contract |
| --- | --- |
| Caller / test | Creates one single-use server and chooses trusted `startup_timeout` configuration. |
| `RedisServer` | Owns image, Docker start, bounded readiness, mapped details, stable failure kind, and cleanup. |
| `run_workshop()` | Enters and exits exactly one server context on success or failure. |
| `RedisOrderStatusProbe` | Accepts exact `RedisConnectionDetails`; allows only fixed order-key `PING` / `SET` / `GET`. |
| Docker lane | Runs sequentially; no parallel container launch or shared server owner. |

The default `startup_timeout` used by this CLI is 30 seconds. Each application
command uses a 2-second socket timeout. Order IDs are limited to 48 ASCII bytes,
status values and RESP command parts/bulk responses to 64 bytes, and response
lines to 128 bytes.

## Prerequisites and setup

- CPython 3.13.14
- uv 0.11.28
- Docker-compatible runtime for the explicit Docker commands only
- Access to the trusted `redis:8` image

From the repository root:

```bash
uv sync --locked --python 3.13.14
```

Do not take an image override from a request, pull request payload, or other
untrusted input. Image references are executable test infrastructure.

## Run deterministic tests without Docker

The default lane excludes the registered `testcontainers` marker:

```bash
uv run --locked pytest -m "not testcontainers" \
  examples/redis_test_server/tests -q
```

These tests cover unstarted and terminal lifecycle behavior, trusted
configuration, protocol bounds, timeout/error context, redacted CLI failures,
and success/failure context ownership with scripted sockets and servers.

## Run the Docker integration test

Run Docker-backed work sequentially:

```bash
uv run --locked pytest -m testcontainers \
  examples/redis_test_server/tests/test_redis_integration.py -q
```

The test proves real readiness, dynamic `RedisConnectionDetails`, `PING` / `SET`
/ `GET`, cleanup after success, cleanup after an application body failure, and
fresh state in a new server.

## Run the example

```bash
uv run --locked python -m examples.redis_test_server
```

Expected output:

```json
{"event":"redis_workshop_succeeded","order_id":"ORD-1001","ping_succeeded":true,"read_succeeded":true,"status":"accepted","write_succeeded":true}
```

The success event contains no address or container identifier. Startup and
probe failures produce redacted JSON and exit status 1.

## Failure and cleanup

`TestcontainerStartError.kind` exposes one stable `StartFailureKind` without
raw daemon or registry diagnostics:

- `runtime-unavailable`
- `image-pull`
- `readiness-timeout`
- `wrapper-failure`

Check runtime health separately with `docker info`. When a Python process exits
abnormally, inspect Bluetape-labeled resources before removing anything:

```bash
docker ps -a --filter label=com.bluetape.testcontainers.redis=true
```

Remove only an ID you have confirmed belongs to this workshop run:

```bash
docker rm -f <confirmed-container-id>
```

If normal termination reports cleanup failure, keep the original exception,
call `close()` again on the same `RedisServer`, and use the label inspection as
operational evidence. Never remove an unrelated container based only on its
image name.

## Source map

- [`probe.py`](probe.py) — immutable result, safe failure, and bounded fixed RESP flow.
- [`application.py`](application.py) — the single server context owner.
- [`__main__.py`](__main__.py) — Docker-backed composition and redacted JSON.
- [`test_application.py`](tests/test_application.py) — deterministic lifecycle and CLI contracts.
- [`test_probe.py`](tests/test_probe.py) — protocol, limit, and causal error tests.
- [`test_redis_integration.py`](tests/test_redis_integration.py) — sequential real Redis proof.

## Non-goals

This workshop does not provide production Redis authentication, TLS, pooling,
pipelining, retries, cluster/sentinel discovery, distributed coordination,
cache semantics, or a generic command API. Use a supported production Redis
client and application-specific security policy for those concerns.
