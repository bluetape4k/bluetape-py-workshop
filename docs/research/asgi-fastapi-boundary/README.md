# ASGI and FastAPI Workshop Boundary

English | [한국어](README.ko.md)

This research decision defines the boundary for the first HTTP example in
`bluetape-py-workshop`. It does not add FastAPI, an ASGI adapter, or a new
`bluetape-py` package. The current framework-neutral
`OrderBackendApplication` remains the business and request-lifecycle core.

Decision date: **2026-07-16**.

## Decision in One Minute

Use **Direct FastAPI** for the first HTTP example: a workshop-owned
`POST /orders` transport delegates to the existing integrated order backend.
Keep FastAPI request models, request parsing, dependency injection,
request-context reset, public exception mapping, response shaping, client
disconnect policy, timeout mapping, and lifespan wiring in the example.

Do not begin with **Raw ASGI**. It would teach routing, body assembly,
validation, and response framing before it teaches the `bluetape-py` boundary.
Do not claim **Future `bluetape-fastapi`** support until upstream research and
implementation pass the adoption gate below.

## Recommended Scenario

A partner sends `POST /orders` with the same aggregate used by the
[integrated order backend](../../../examples/integrated_order_backend/README.md).
The HTTP layer validates the transport shape and creates an
`OrderBackendCommand`. `OrderBackendApplication` then owns the overall request
deadline, task observation, business processing, and retryable finite close.

The first HTTP example should prove:

- one application instance is created during FastAPI lifespan startup;
- one HTTP request delegates to `OrderBackendApplication.process()`;
- validation and domain failures become stable public responses without
  exposing provider messages or encoded artifacts;
- timeout and caller-cancellation policies remain explicit;
- request context is always reset in `finally`;
- lifespan shutdown awaits `OrderBackendApplication.aclose()`.

Authentication, persistence, production deployment, automatic disconnect
cancellation, and reusable framework middleware are non-goals for that example.

## Architecture

![ASGI and FastAPI ownership architecture](images/architecture.png)

[Open the Architecture SVG source](images/architecture.svg).

The diagram is a responsibility map, not an ordered request trace. The workshop
owns the FastAPI transport while the existing backend owns business and task
lifecycle. The dashed future path is unavailable until both upstream gates are
satisfied.

## Sequence Diagram

![First HTTP order sequence](images/sequence.png)

[Open the Sequence Diagram SVG source](images/sequence.svg).

The ASGI server may send `http.disconnect`, but the specification does not
promise that application work is automatically cancelled. The adapter must
observe the signal when its policy requires it, cancel only work it owns, and
still reset context. A response send may also fail after disconnect, so public
error mapping must not depend on being able to write a response.

## Alternatives

| Alternative | Pros | Cons | Decision |
|---|---|---|---|
| Direct FastAPI | Realistic learner API; native DTO validation, DI, error handlers, and lifespan; smallest transport around the existing backend | Framework concepts remain workshop-owned; a later upstream adapter may change the boundary | **Use first** |
| Raw ASGI | Makes protocol events and disconnect behavior fully visible; no framework dependency | Duplicates routing, body buffering, validation, error, and response glue; distracts from `bluetape-py` | Keep as an advanced protocol exercise, not the first HTTP example |
| Future `bluetape-fastapi` | Could standardize Problem Details, request context, middleware composition, and conformance behavior | The package and contract do not exist; premature use would create a workshop-owned de facto API | Adopt only after the exact gate below |

Direct FastAPI is the most realistic first lesson because students see the
boundary they are likely to use in a service. Raw ASGI remains valuable when
the learning objective is the protocol itself. A future adapter becomes useful
only after upstream owns and tests the reusable policy.

## Ownership Matrix

| Concern | Workshop FastAPI transport | Existing backend | Future upstream adapter |
|---|---|---|---|
| request parsing | Pydantic/FastAPI DTO and bounded conversion to `OrderBackendCommand` | Reject invalid domain aggregate | May provide generic helpers, never the domain DTO |
| dependency injection | Wire backend through FastAPI dependencies/app state | Accept explicit collaborators | May standardize framework hooks |
| request-context reset | Open correlation/request context and reset in `finally` | Preserve service-level context contracts | May provide reusable context middleware after conformance tests |
| public exception mapping | Map known exceptions to stable status/body; redact internals | Raise typed domain/lifecycle exceptions | May provide RFC 7807 primitives and handlers |
| response shaping | Build the public allowlist; omit encoded artifact data and provider details | Return domain result and safe metadata | May provide generic Problem Details serialization |
| client disconnect | Observe `http.disconnect` when chosen; define whether owned request work is cancelled | React correctly to caller cancellation; observe late terminal failures | May provide tested disconnect/cancellation middleware |
| timeout | Choose HTTP-facing budget and map native `TimeoutError` | Enforce overall backend deadline and cancel owned task | May compose generic timeout hooks without replacing domain budgets |
| lifespan and cleanup | Create one backend on startup; call `aclose()` on shutdown | Own request/close tasks and retryable finite shutdown | May provide framework registration helpers, not application resource policy |

## Boundary Rules

1. Transport validation and domain validation are separate. FastAPI rejects an
   invalid JSON shape; the backend still validates the complete order before
   provider I/O.
2. Dependency injection wires application-owned resources. It must not hide a
   global backend or create a backend per request.
3. Request context uses a token/context-manager boundary and is reset in
   `finally` on success, error, timeout, or cancellation.
4. Public exception mapping is an explicit allowlist. Unknown failures become a
   generic server problem and are logged without exposing request secrets.
5. Client disconnect is a signal, not an automatic-cancellation guarantee.
   Cancellation policy must name the task owner and preserve cleanup.
6. The outer HTTP timeout must not detach backend work. The existing backend
   deadline remains the authoritative task-lifecycle boundary.
7. FastAPI lifespan owns construction and shutdown. Requests start only after
   startup completes, and shutdown waits for the backend close contract.

## Adoption Gate for `bluetape-fastapi`

Framework-specific adoption requires all of the following:

1. [bluetape-py #21](https://github.com/bluetape4k/bluetape-py/issues/21) is
   accepted with a package and ownership decision;
2. [bluetape-py #22](https://github.com/bluetape4k/bluetape-py/issues/22) ships
   conformance-tested ASGI/FastAPI behavior;
3. the workshop pins an **exact stable release tag or commit** containing that
   implementation—an open issue, branch name, or moving `develop` head is not
   sufficient;
4. the adapter preserves the ownership matrix above and does not pull optional
   web dependencies into the thin default `bluetape-py` install;
5. the HTTP example is updated in one reviewed change with bilingual docs,
   Architecture, Sequence Diagram, tests, and migration notes.

Until then, FastAPI stays workshop-only and no reusable adapter is copied into
this repository.

## Focused Prerequisites

- [Validated order intake](../../../examples/order_intake/README.md) for domain
  normalization and validation.
- [Integrated order backend](../../../examples/integrated_order_backend/README.md)
  for request deadlines, task observation, shared cache composition, bounded
  JSON, and shutdown.
- ASGI lifespan and HTTP/disconnect semantics from the primary specifications.
- FastAPI lifespan, dependencies, and exception handlers as transport tools,
  not business abstractions.

## Primary Sources

All sources were retrieved on **2026-07-16**.

- [ASGI Lifespan](https://asgi.readthedocs.io/en/latest/specs/lifespan.html)
- [ASGI HTTP and WebSocket](https://asgi.readthedocs.io/en/latest/specs/www.html)
- [Starlette Lifespan](https://www.starlette.io/lifespan/)
- [Starlette Requests](https://www.starlette.io/requests/)
- [FastAPI Lifespan Events](https://fastapi.tiangolo.com/advanced/events/)
- [FastAPI Dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [FastAPI Error Handling](https://fastapi.tiangolo.com/tutorial/handling-errors/)
- [Workshop Issue #9](https://github.com/bluetape4k/bluetape-py-workshop/issues/9)

## Scope Result

This issue records a boundary decision only. It changes no Python source,
dependency, lockfile, runtime, package, release, or milestone state. The first
HTTP example must be tracked by a separate implementation issue after this
decision is accepted.
