English | [한국어](README.ko.md)

# Direct FastAPI Order API

This runnable example places a Direct FastAPI transport in front of the existing
framework-neutral `OrderBackendApplication`. It teaches the boundary between
HTTP validation and domain validation, lifespan-owned backend state, stable
problem responses, and request-context cleanup in one application-shaped flow.

## Scenario

A partner sends an order to `POST /orders`. `X-Request-ID` is correlation
metadata, not an idempotency key. Reusing the same request ID does not suppress
duplicate work, so a client must not automatically retry an order based only on
that value.

FastAPI validates a bounded JSON DTO and converts it to an immutable
`OrderBackendCommand`. One lifespan-owned `OrderBackendApplication` performs
order intake, catalog enrichment, `AsyncTTLCache`, and `JsonPayloadService`
work. The HTTP response contains only an allowlist, never provider output or an
encoded artifact.

The deterministic demo catalog supports three SKUs:

- `SKU-1`: Mechanical Keyboard, 12,500 cents
- `SKU-2`: Vertical Mouse, 7,900 cents
- `SKU-3`: USB-C Dock, 15,900 cents

## Architecture

[![Direct FastAPI order API architecture](docs/images/architecture.png)](docs/images/architecture.svg)

[Architecture SVG source](docs/images/architecture.svg) · [Architecture PNG](docs/images/architecture.png)

The three cards on the left define the Partner, FastAPI transport, and
lifespan/app-state boundary. The three cards on the right show the
framework-neutral backend, reusable services, and bluetape-py packages. Card
gaps exceed the rendered 14px arrowhead projection plus stroke and safety
margin, and no connector crosses a card interior.

## Sequence Diagram

[![Direct FastAPI order API sequence](docs/images/sequence.png)](docs/images/sequence.svg)

[Sequence SVG source](docs/images/sequence.svg) · [Sequence PNG](docs/images/sequence.png)

The Sequence Diagram combines lifespan startup, `POST /orders`, context
open/reset, the backend deadline, `422`/`504` branches, and shutdown ordering.
`CancelledError` is propagated instead of being converted into an HTTP problem.

## Prerequisites and Setup

Run from the repository root with Python 3.13.14 and `uv`. FastAPI, HTTPX, and
Uvicorn belong to an optional extra and remain outside the default install. The
following command creates a separate `.venv-fastapi` without changing the Redis
or Apache Fory optional lanes.

```bash
UV_PROJECT_ENVIRONMENT=.venv-fastapi uv sync --locked --extra fastapi-order-api --python 3.13.14
```

The workshop consumes a pinned bluetape-py source commit. Reusable upstream
adapter research remains gated by [bluetape-py/issues/21](https://github.com/bluetape4k/bluetape-py/issues/21)
and [bluetape-py/issues/22](https://github.com/bluetape4k/bluetape-py/issues/22).
This example does not imitate a future `bluetape-fastapi` API.

## Run

Start the loopback-only development server. The CLI does not expose host,
worker-count, reload, or proxy-trust configuration.

```bash
UV_PROJECT_ENVIRONMENT=.venv-fastapi uv run --locked --extra fastapi-order-api python -m examples.fastapi_order_api --port 8000
```

Send exactly one order from another terminal:

```bash
curl --fail-with-body \
  -X POST http://127.0.0.1:8000/orders \
  -H 'Content-Type: application/json' \
  -H 'X-Request-ID: req-1001' \
  -d '{
    "partner_id": "partner-7",
    "order_id": "order-9001",
    "lines": [
      {"sku": "SKU-1", "quantity": 2},
      {"sku": "SKU-2", "quantity": 1}
    ]
  }'
```

Success is `200 OK` with this exact allowlisted shape:

```json
{
  "request_id": "req-1001",
  "partner_id": "partner-7",
  "order_id": "order-9001",
  "line_count": 2,
  "total_cents": 32900,
  "warning_count": 0
}
```

## Ownership and Lifecycle

- The `create_app()` lifespan invokes the backend factory exactly once.
- Every request borrows the same `app.state.order_backend` instance.
- The FastAPI transport owns HTTP DTOs, status codes, public messages, and
  redacted transport logs.
- `OrderBackendApplication` owns the two-second overall deadline and request
  task cleanup.
- Shutdown deletes state only after `await backend.aclose()` succeeds.
- `OrderBackendShutdownError` remains visible and preserves state for diagnosis.

The endpoint adds no second timeout or client-disconnect watcher. Caller
cancellation propagates as `CancelledError`; the backend cancels and observes
its owned task.

## Validation and Failure Contract

The endpoint accepts `Content-Type: application/json` with an optional charset.
After trimming, `X-Request-ID` must contain 1..128 ASCII characters from
`[A-Za-z0-9._:-]`; duplicate headers are rejected. The body forbids unknown
fields, bounds identifiers to 1..128 characters and lines to 1..100 entries,
and accepts only strict integer quantities from 1 through 1,000,000.

A whitespace-only identifier passes the transport length check and is then
rejected by the domain as `invalid_order`. This preserves complete domain
validation instead of duplicating it in Pydantic.

| HTTP | code | Meaning |
| ---: | --- | --- |
| 422 | `invalid_request` | Header, JSON, or DTO validation failed |
| 422 | `invalid_order` | Complete domain validation failed |
| 503 | `catalog_unavailable` | Required catalog provider unavailable |
| 503 | `backend_unavailable` | Backend already closed |
| 504 | `order_timeout` | Backend overall deadline expired |
| 500 | `order_processing_failed` | Payload, compression, or serde processing failed |
| 500 | `internal_error` | Unexpected internal failure |

Every problem includes `code`, `message`, and `request_id`; only safe cases add
`field` or `line_index`. Raw input, Pydantic messages, provider exception text,
artifact bytes, and stack traces never enter the response or transport log.

## Security and Production Boundaries

This is a workshop loopback server. It does not provide authentication,
authorization, persistence, TLS, rate limiting, or a production worker
topology. With `proxy_headers=False`, it does not trust forwarded identity from
a reverse proxy.

Pydantic bounds the decoded model, not the raw HTTP body bytes consumed before
validation. This example deliberately installs no Uvicorn body limit. Before
production use, enforce a strict request body limit, authentication,
authorization, and rate limit at a gateway or reverse proxy.

`X-Request-ID` is correlation metadata, not idempotency, and must not contain a
secret. Automatic retry after a `503` or `504` can process an order twice.

## Packages and APIs

- FastAPI: lifespan, `RequestValidationError`, explicit response models
- Uvicorn: fixed `127.0.0.1`, one worker, reload and proxy trust disabled
- `bluetape.logging`: `log_context`, `ContextLogFilter`
- `bluetape.cache`: `AsyncTTLCache`
- `bluetape.compression` / `bluetape.serde`: bounded payload pipeline
- `bluetape.testing`: event-driven `eventually_async` cancellation proof

## Tests

Run all example tests in the optional environment:

```bash
UV_PROJECT_ENVIRONMENT=.venv-fastapi uv run --locked --extra fastapi-order-api pytest examples/fastapi_order_api/tests -q
```

The default full collection explicitly skips the FastAPI test modules, while a
separate dependency baseline proves the web packages are absent:

```bash
uv run --locked pytest -q
uv run --locked pytest tests/test_dependency_baseline.py -q
```

## Cleanup and Troubleshooting

- Stop the server with `Ctrl+C` in its terminal.
- For `address already in use`, select a free port such as `--port 18080`.
- For `ModuleNotFoundError: fastapi`, rerun the `.venv-fastapi` setup command.
- For `422 invalid_request`, check `Content-Type: application/json`, one
  `X-Request-ID`, and the strict JSON fields.
- For `422 invalid_order`, check whitespace identifiers and full domain rules.
- For `503 catalog_unavailable`, use `SKU-1`, `SKU-2`, or `SKU-3`.
- Remove the optional environment with `rm -rf .venv-fastapi`.

This example is not a production deployment recipe, reusable FastAPI adapter,
database API, authentication/authorization service, or exactly-once retry
protocol.
