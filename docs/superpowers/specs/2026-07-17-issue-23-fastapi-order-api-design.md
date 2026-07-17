# Issue #23 Direct FastAPI Order API Design

**Status:** Approved after Step 2-R review repair
**Issue:** [#23](https://github.com/bluetape4k/bluetape-py-workshop/issues/23)  
**Milestone:** `0.2.0`  
**Branch:** `feat/fastapi-order-api`  
**Base:** `develop` at `a750245`

## Outcome

Add an independently runnable, workshop-owned Direct FastAPI example that
accepts `POST /orders`, converts a bounded decoded order model into the existing
framework-neutral `OrderBackendCommand`, and returns an allowlisted order
summary. One FastAPI lifespan owns one `OrderBackendApplication`; the existing
backend remains the authority for request deadlines, task observation,
cancellation, cache behavior, and finite shutdown.

The example teaches a realistic service boundary without inventing or copying
a future `bluetape-fastapi` contract. Upstream
[bluetape-py #21](https://github.com/bluetape4k/bluetape-py/issues/21) and
[#22](https://github.com/bluetape4k/bluetape-py/issues/22) remain open gates for
reusable framework integration.

## Evidence and Constraints

- Workshop issue #9 already selected Direct FastAPI over Raw ASGI and a future
  adapter for the first HTTP lesson.
- FastAPI documents `FastAPI(lifespan=...)` with an async context manager as the
  recommended shared-resource startup/shutdown boundary. The code before
  `yield` runs before requests; cleanup after `yield` runs at shutdown.
- FastAPI supports custom `RequestValidationError` and application exception
  handlers, allowing a stable redacted public error contract.
- FastAPI's async-test guidance states that HTTPX `AsyncClient` with
  `ASGITransport` does not trigger lifespan by itself. This example therefore
  uses `TestClient` as a context manager for HTTP/lifespan proof instead of
  adding `asgi-lifespan`.
- Starlette exposes `request.app`, `request.state`, and
  `request.is_disconnected()`. Automatic disconnect cancellation is explicitly
  outside issue #23, so the endpoint creates no watcher or detached task.
- The root default environment must remain free of FastAPI, Starlette, Pydantic,
  HTTPX, and Uvicorn.
- Each example README locale must embed source-backed Architecture and Sequence
  Diagram PNGs and link the SVG sources.

Primary references:

- [FastAPI Lifespan Events](https://fastapi.tiangolo.com/advanced/events/)
- [FastAPI Handling Errors](https://fastapi.tiangolo.com/tutorial/handling-errors/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [FastAPI Async Tests](https://fastapi.tiangolo.com/advanced/async-tests/)
- [Starlette Requests](https://www.starlette.io/requests/)
- [Workshop ASGI/FastAPI boundary](../../research/asgi-fastapi-boundary/README.md)

## Alternatives

| Alternative | Advantages | Costs and risks | Decision |
|---|---|---|---|
| Direct FastAPI | Realistic learner API; native DTO validation, handlers, app state, lifespan, and OpenAPI; smallest transport around the existing backend | Framework policy remains example-owned; a later upstream adapter may change wiring | **Selected** |
| Raw ASGI | Makes receive/send/disconnect semantics fully visible; no framework dependency | Duplicates routing, body assembly, validation, and response framing; obscures the `bluetape-py` lesson | Reject for the first HTTP example |
| Future `bluetape-fastapi` | Could standardize request context and Problem Details | No accepted package or conformance implementation exists; copying it here would create a de facto API | Gated on upstream #21/#22 and an exact released source |

## Source Layout

```text
examples/fastapi_order_api/
├── __init__.py                 public app factory and transport models
├── __main__.py                 loopback-only development server entry point
├── application.py              FastAPI factory, lifespan, route, handlers
├── context.py                  bounded request-id validation and context scope
├── models.py                   strict HTTP request/response/problem DTOs
├── providers.py                deterministic workshop catalog/recommendation data
├── README.md                   English learner guide
├── README.ko.md                Korean learner guide
├── docs/images/
│   ├── architecture.svg
│   ├── architecture.png
│   ├── sequence.svg
│   └── sequence.png
└── tests/
    ├── test_application.py     route, mapping, context, lifespan, cancellation
    ├── test_dependencies.py    optional/default environment isolation
    └── test_documentation.py   locale, commands, sources, diagrams

tests/test_dependency_baseline.py   default web-distribution absence
tests/test_documentation_contract.py root locale/navigation/diagram registration
README.md / README.ko.md             root example navigation
WIP.md                               exact issue/branch/checkpoint state
```

The names above are example-local. No reusable middleware, adapter, or helper is
added outside `examples/fastapi_order_api`.

## Architecture and Ownership

```text
Partner HTTP client
        |
        v
FastAPI transport (workshop-owned)
  request-id + strict DTO + stable problem mapping + response allowlist
        |
        v
OrderBackendApplication (existing framework-neutral boundary)
  deadline + owned request task + observation + finite close
        |
        v
OrderBackendService and existing bluetape-py-backed example services
  intake + bounded enrichment + shared cache + bounded payload encoding
```

FastAPI lifespan constructs the backend through an injected factory and stores
it on `app.state`. The default factory uses deterministic workshop catalog and
recommendation providers. The endpoint retrieves the backend from app state;
it does not create a backend per request or use a module-global backend.

The app factory accepts a typed backend factory seam. Tests use it to inject an
instrumented backend with public `process()` and `aclose()` methods. The default
path still builds the exact existing `OrderBackendApplication` through
`build_application()`.

## HTTP Contract

### Request

`POST /orders` requires `Content-Type: application/json` and an
`X-Request-ID` header. The request ID is ASCII text after surrounding whitespace
is removed, between 1 and 128 characters, and contains only letters, digits,
`.`, `_`, `:`, or `-`. Invalid or duplicated request-id headers are rejected;
the server does not echo an unsafe value.

The request ID is correlation metadata only. It is not an idempotency key, and
the example does not deduplicate or replay requests. Clients must not
automatically retry a `POST` merely because the same request ID can be reused.

The JSON body is strict and forbids unknown fields. `partner_id`, `order_id`,
and each `sku` accept 1 through 128 characters; `lines` accepts 1 through 100
items; and `quantity` is a strict integer from 1 through 1,000,000:

```json
{
  "partner_id": "partner-7",
  "order_id": "order-9001",
  "lines": [
    {"sku": "SKU-1", "quantity": 2},
    {"sku": "SKU-2", "quantity": 1}
  ]
}
```

Transport bounds reject non-string identifiers, non-integer or boolean
quantities, out-of-range quantities, more than 100 lines, empty lists, and
oversized identifier strings before domain work. A whitespace-only identifier
can satisfy the transport length constraint but is rejected by the existing
backend. This keeps complete domain validation after conversion to immutable
dataclasses instead of duplicating its normalization policy in Pydantic.

### Success

Success returns `200 OK` with this allowlisted shape. The example processes an
order command but does not create an addressable persisted HTTP resource, so it
does not use `201 Created` or invent a `Location` header:

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

The response never includes encoded artifact bytes or metadata, provider
messages, recommendation payloads, cache internals, exception text, or stack
traces.

### Stable problem responses

Every public problem has required `code`, `message`, and `request_id` fields.
Optional `field` and `line_index` fields appear only for the safe
invalid-request and invalid-order cases. Raw Pydantic messages, raw input, and
`repr(input)` are never returned.

| Condition | Status | Code | Public detail |
|---|---:|---|---|
| Missing/invalid request ID or malformed/invalid transport DTO | 422 | `invalid_request` | Generic bounded message; safe field location only |
| `InvalidOrderBackendCommand` / `InvalidOrderLine` | 422 | `invalid_order` | Safe domain field and reason |
| `CatalogEnrichmentFailed` | 503 | `catalog_unavailable` | Generic retryable message |
| `OrderBackendClosedError` | 503 | `backend_unavailable` | Generic retryable message |
| Backend `TimeoutError` | 504 | `order_timeout` | Generic deadline message |
| Payload limit, compression, or serialization failure | 500 | `order_processing_failed` | Generic internal processing message |
| Any other `Exception` | 500 | `internal_error` | Generic internal error message |

`asyncio.CancelledError` is not mapped to an HTTP problem. It remains caller
cancellation, propagates through the endpoint, and relies on the existing
backend to cancel and observe its owned request task.

## Request Context

The transport creates a small example-local context scope around conversion,
backend invocation, response shaping, and every mapped failure. It delegates to
`bluetape.logging.log_context(request_id=...)` and always exits through
`finally`/context-manager cleanup.

The request validation handler establishes the same scope from the raw header
before returning `invalid_request`. If the header itself is unsafe, logs and the
problem body use the fixed sentinel `<invalid>` rather than the raw value.
Tests seed an outer context and prove it is restored after success, validation,
domain failure, timeout, unknown failure, and cancellation.

## Lifespan, Timeout, Cancellation, and Shutdown

The FastAPI lifespan performs these steps:

1. construct exactly one backend before accepting requests;
2. store it in `app.state.order_backend`;
3. yield to serve any number of requests;
4. await `backend.aclose()` exactly once during shutdown;
5. remove the state reference only after successful close.

If close fails, the state reference remains available for shutdown diagnostics
and deterministic tests, while the original exception propagates. The lifespan
does not silently retry because the process owner must decide whether another
finite close attempt is safe.

The HTTP layer adds no second request timeout. The existing backend's 2-second
deadline is authoritative. This prevents nested timeout ambiguity and detached
work. A backend timeout is only translated after `OrderBackendApplication` has
cancelled and retained observation of its task.

Client disconnect detection and automatic work cancellation are non-goals. The
example neither polls `request.is_disconnected()` nor creates an unbounded
watcher. ASGI/server cancellation that reaches the endpoint propagates as
`CancelledError`; the transport resets context and the backend performs its
existing cancellation policy.

If backend shutdown raises `OrderBackendShutdownError`, lifespan shutdown fails
visibly. It is not swallowed or converted to an HTTP response because request
serving has already ended.

## Dependency and Execution Boundary

Add one optional extra named `fastapi-order-api` containing FastAPI, HTTPX, and
Uvicorn. `uv` selects compatible Python 3.13 versions and locks their complete
transitive graph. Default `uv sync --locked` must continue to omit FastAPI,
Starlette, Pydantic, HTTPX, Uvicorn, and their CLI/server dependencies.

The runnable command uses the optional environment and starts a single
loopback-only development process:

```bash
UV_PROJECT_ENVIRONMENT=.venv-fastapi uv sync --locked \
  --extra fastapi-order-api --python 3.13.14
UV_PROJECT_ENVIRONMENT=.venv-fastapi uv run --locked \
  --extra fastapi-order-api python -m examples.fastapi_order_api --port 8000
```

The entry point accepts only `--port` in the range 1 through 65535, binds fixed
host `127.0.0.1`, uses one process, and is for workshop use only. The CLI test
reserves a loopback port and passes it explicitly. Worker topology, TLS, proxy
headers, deployment, persistence, auth, and production tuning are explicitly
unsupported.

The Pydantic model bounds the decoded transport shape, not the number of raw
HTTP bytes consumed before validation. FastAPI/Uvicorn does not make a raw body
limit part of this example. README security guidance must name this limitation
and require an upstream server or gateway body limit before production use;
the example must not claim denial-of-service-safe request buffering.

## Test Strategy

Implementation follows test-driven development.

1. **Dependency isolation:** default metadata/import probes prove all web
   distributions absent; optional-extra probes prove exact imports and lock
   membership without weakening existing Fory or Redis isolation.
2. **Transport contract:** `TestClient` context proves 200 success, strict JSON
   validation, forbidden fields, request-id validation, 100-line bound, and
   allowlisted output.
3. **Failure mapping:** inject one typed failure at a time and assert exact
   status/body, no raw exception/provider/artifact/secret text, and safe logs.
4. **Context:** seed outer log context and prove restoration on success,
   validation, domain failure, timeout, unknown exception, and cancellation.
5. **Lifespan:** assert one construction, shared instance across requests,
   exactly one `aclose()`, shutdown failure visibility, and no request before
   startup or after shutdown.
6. **Cancellation:** call the async route function with a constructed Starlette
   request and a real `OrderBackendApplication` whose injected provider is held
   by events, using no real sleeps; cancel the endpoint task, assert native
   `CancelledError`, release backend cleanup, and prove no named request task
   remains terminally unobserved.
7. **CLI:** start the module on a test-selected loopback port, wait with a
   bounded readiness probe, submit one order, inspect the response, and stop
   cleanly without a child-process leak.
8. **Documentation:** both locale files share facts, commands, links, failure
   policy, and all four diagram assets.

Focused tests run only in `.venv-fastapi`; the default full suite continues to
collect without importing the optional example. Optional test modules use an
explicit module-level `pytest.importorskip()` with a stable reason, while root
dependency tests separately prove the packages are absent. This makes the
default skip visible instead of turning a collection failure into accidental
evidence.

## README and Diagram Contract

`README.md` starts with `English | [한국어](README.ko.md)` and
`README.ko.md` starts with `[English](README.md) | 한국어`. Both explain the
business scenario, ownership boundary, exact setup/run/curl/test/stop commands,
expected response, error table, security/redaction policy, cancellation,
shutdown, troubleshooting, unsupported production use, and upstream gate.
The guide lists the deterministic demo SKUs, states that request IDs provide
correlation rather than idempotency, and warns against automatic POST retries.

The Architecture diagram is a static ownership map with separate cards for the
partner, FastAPI transport, lifespan/app state, existing
`OrderBackendApplication`, backend services, and bluetape-py packages. The
Sequence Diagram shows startup, one successful `POST /orders`, a validation or
timeout alternative, context reset, and shutdown.

Diagram assets are authored only after source behavior exists. Both SVGs use
explicit markers whose rendered arrowhead width and height are part of layout
math. Card gaps exceed the marker projection plus stroke and safety margin;
terminal connector segments remain long enough that arrowheads do not overlap
cards, labels, bends, or endpoints. Tests parse the marker/viewBox/refX values
and connector/card coordinates so this rule cannot regress.

Completion requires XML parsing, CairoSVG 2x PNG render, connector audit,
geometry audit, endpoint audit, mixed-corner audit, sequence-style audit where
applicable, full-size PNG inspection, and README link/locale parity.

## Security and Trust Boundaries

- Accept only JSON and bounded model shapes; forbid unknown fields.
- Describe the decoded-model bound honestly; production deployments require a
  separate raw request-body byte limit before FastAPI parsing.
- Never log or return request bodies, raw Pydantic input, provider errors,
  exception text, artifact bytes, stack traces, or secrets.
- Treat request IDs as untrusted input; validate before logging or echoing.
- Use explicit response models and an allowlist rather than serializing domain
  dataclasses directly.
- Do not enable permissive CORS, proxy trust, debug trace responses, auth
  placeholders, or production deployment defaults.
- Keep optional web dependencies out of the default install and import graph.

## Compatibility, Migration, and Rollback

This issue adds only an optional example and root documentation/navigation.
Existing examples, public imports, default runtime, pinned bluetape-py commit,
and CI commands remain compatible. No `OrderBackendApplication` change is
planned.

A future upstream adapter migration requires an accepted implementation from
bluetape-py #21/#22, an exact stable tag or commit, conformance evidence, and a
separate reviewed issue. The Direct FastAPI example remains the behavioral
comparison baseline.

Rollback removes the optional extra, lock entries, example directory, root
navigation/WIP entries, and issue-specific spec/review/lesson artifacts in one
revert. No data migration or external service cleanup exists.

## Delivery and Stop Boundary

The implementation updates issue #23, Epic #1, root bilingual navigation, and
`WIP.md`; adds design/plan/review/lesson evidence; runs focused optional and
full default validation; converges independent review to P0=0 and P1=0; then
creates a PR from `feat/fastapi-order-api` to `develop` with `Closes #23`.

After exact-head CI, current reviews/threads, dependency isolation, tests, and
diagram evidence pass, report the PR as merge-ready and stop for a fresh
explicit merge approval. Auto-merge is forbidden.

## Acceptance Mapping

| Issue requirement | Design proof |
|---|---|
| Independently runnable/testable Direct FastAPI example | Optional environment, loopback CLI, focused tests |
| One lifespan-owned backend | App-state ownership and construction/close assertions |
| Transport/domain validation separation | Strict Pydantic DTO followed by existing domain validation |
| Context reset on every path | Scoped context plus success/error/timeout/cancellation restoration tests |
| Stable redacted failures | Exact status/code table and leak-negative assertions |
| Backend deadline remains authoritative | No outer HTTP timeout or detached watcher |
| Default dependency isolation | Default absence and optional lock/import probes |
| Bilingual guides and diagrams | Reciprocal locale, four assets, source-backed geometry audits |
| Arrowhead-aware geometry | Marker/card/terminal-segment regression test |
| Root/Epic/WIP state | Delivery checklist and exact checkpoint updates |
| P0=0/P1=0 | Required design, plan, implementation, and final review gates |

## Definition of Done

- The approved design and implementation plan are committed with Lore messages.
- Optional dependency isolation and lockfile contracts pass in default and
  `.venv-fastapi` environments.
- Focused HTTP/lifespan/context/cancellation/CLI tests pass without real sleeps
  or leaked tasks/processes.
- Both README locales embed readable Architecture and Sequence Diagram PNGs and
  link their audited SVG sources.
- Ruff, full default pytest, actionlint, diagram checks, link/locale checks, and
  `git diff --check` pass at the exact PR head.
- Review evidence records P0=0 and P1=0, and the Type A lesson gate is satisfied.
- PR head/base/CI/review/thread evidence is current; merge waits for fresh user
  approval.
