# Issue #23 Direct FastAPI Order API Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `executing-plans` to implement this plan task-by-task. The user requires main-session execution if native subagents stall, so this plan uses one write lane and explicit checkpoints. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an optional, independently runnable Direct FastAPI `POST /orders` example around the existing `OrderBackendApplication`, with stable redacted responses, authoritative backend cancellation/shutdown, bilingual learner guides, and arrowhead-aware diagrams.

**Architecture:** `create_app()` owns FastAPI transport policy and an async lifespan that constructs one injected backend and closes it before removing app state. Strict Pydantic DTOs convert into existing immutable backend commands; the route owns only request-id validation, context scope, exception mapping, and an allowlisted response. FastAPI, HTTPX, and Uvicorn remain in one optional extra so the default workshop import graph stays unchanged.

**Tech Stack:** Python 3.13.14, uv 0.11.28, FastAPI `>=0.139.2,<0.140`, Uvicorn `>=0.51.0,<0.52`, HTTPX `>=0.28.1,<0.29`, Pydantic v2 through FastAPI, pytest 8, pytest-asyncio, Ruff 0.12, existing bluetape-py commit `4b7458f22cea0a9e757b5fbf7f5ff4bc8c23cb9a`, CairoSVG diagram workflow.

---

## Execution Contract

- Work type: Type A full feature; issue #23; milestone `0.2.0`.
- Repository: `bluetape4k/bluetape-py-workshop`.
- Base/head: `develop` / `feat/fastapi-order-api`.
- Worktree: `.worktrees/feat-fastapi-order-api`.
- Write lanes: one. Root docs, `pyproject.toml`, `uv.lock`, optional tests, and diagrams are shared surfaces.
- Heavy-command limit: one uv sync, pytest, actionlint, server smoke, or diagram render/audit process at a time.
- Implementation skills at Task 1: `test-driven-development`, `bluetape-py-patterns`.
- Documentation skills at Task 6: `bluetape-writer`, `bluetape-diagram` plus `common.md`, `architecture.md`, and `sequence.md`.
- Verification skills at Task 8: `verification-before-completion` and the Type A verifier/review references.
- Stop condition: create and verify the authorized PR to `develop`, wait for exact-head CI/review/diagram evidence, report merge-ready, and stop for fresh merge approval. Auto-merge is forbidden.
- External side effects before merge-ready: issue/Epic updates and the approved PR only. No release, tag, workflow dispatch, production server, or upstream package change.

## File Map

| Path | Responsibility |
|---|---|
| `pyproject.toml` | Declare the isolated `fastapi-order-api` extra |
| `uv.lock` | Lock the complete optional web dependency graph |
| `tests/test_dependency_baseline.py` | Prove default absence and optional lock/source boundaries |
| `examples/fastapi_order_api/models.py` | Strict request, success, and problem DTOs |
| `examples/fastapi_order_api/context.py` | Validate one request ID and open/reset log context |
| `examples/fastapi_order_api/providers.py` | Deterministic demo catalog/recommendation providers |
| `examples/fastapi_order_api/application.py` | Backend protocol/factory, lifespan, handlers, `POST /orders` |
| `examples/fastapi_order_api/__init__.py` | Package marker with no optional imports, preserving default pytest collection |
| `examples/fastapi_order_api/__main__.py` | Fixed-loopback single-process Uvicorn CLI |
| `examples/fastapi_order_api/tests/test_models.py` | DTO strictness and conversion tests |
| `examples/fastapi_order_api/tests/test_context.py` | Header/context/reset tests |
| `examples/fastapi_order_api/tests/test_application.py` | HTTP, mapping, lifespan, cancellation tests |
| `examples/fastapi_order_api/tests/test_main.py` | CLI argument and loopback server smoke tests |
| `examples/fastapi_order_api/tests/test_documentation.py` | Locale, commands, sources, diagrams, geometry contract |
| `examples/fastapi_order_api/README.md` | English learner guide |
| `examples/fastapi_order_api/README.ko.md` | Korean learner guide |
| `examples/fastapi_order_api/docs/images/architecture.svg` | Architecture source with arrowhead-aware ownership geometry |
| `examples/fastapi_order_api/docs/images/architecture.png` | CairoSVG 2x Architecture render |
| `examples/fastapi_order_api/docs/images/sequence.svg` | Sequence source with lifecycle and failure branches |
| `examples/fastapi_order_api/docs/images/sequence.png` | CairoSVG 2x Sequence render |
| `README.md`, `README.ko.md` | Root example navigation and optional commands |
| `WIP.md` | Current issue/branch/validation/PR checkpoint |
| `tests/test_documentation_contract.py` | Root registration and bilingual diagram links |
| `docs/superpowers/reviews/*issue-23*` | Plan and implementation review evidence |
| `docs/superpowers/lessons/2026-07-17-issue-23-fastapi-order-api.md` | Required Type A durable lesson |

## Traceability

| Approved requirement | Task |
|---|---:|
| Optional dependency isolation | 1 |
| Strict transport/domain validation separation | 2, 4 |
| Safe request-id and context reset | 2, 4 |
| One lifespan-owned backend and finite close | 3 |
| Stable success/problem contract | 4 |
| Native cancellation and authoritative backend deadline | 4 |
| Independently runnable loopback server | 5 |
| README.md/README.ko.md parity | 6 |
| Architecture and Sequence Diagram assets | 6 |
| Arrowhead/card/terminal connector regression | 6 |
| Root navigation, WIP, Epic/issue state | 7, 9 |
| Full verification, P0=0/P1=0, lesson, PR | 8, 9 |

## Predicted Risks

| Risk | Signal | Mitigation and proof | Rollback/rerun point |
|---|---|---|---|
| Optional imports break default collection | FastAPI import error or web package present in `.venv` | Root absence probes plus module-level reasoned `importorskip`; run default suite before optional suite | Revert Task 1 metadata/lock and rerun default sync |
| Nested timeout or cancellation detaches backend work | transport creates timeout/watcher task; named backend task survives | No transport timeout/watcher; real backend cancellation test with events and terminal task scan | Return to Task 4 RED test |
| Shutdown deletes state before close succeeds | failed close leaves no inspectable backend | `await aclose()` before `del app.state`; failure test | Return to Task 3 lifespan test |
| Error handler leaks raw validation/provider data | response/log contains sentinels or exception message | Exact body allowlist and hostile-string negative assertions | Return to Task 4 mapping table |
| TestClient hides lifespan/loop differences | backend binds to a different loop or async client skips startup | Use `TestClient` context for HTTP/lifespan; direct async route test only for cancellation | Return to Task 3 lifecycle test |
| CLI smoke flakes or leaks a process | readiness timeout, occupied port, child remains alive | reserve loopback port, bounded probe, `terminate` then bounded `kill`, assert process exit | Return to Task 5 smoke harness |
| Diagram arrowheads overlap cards | marker projection exceeds terminal segment/card gap | parse marker geometry and coordinates; all audits plus full-size inspection | Return to Task 6 SVG source, rerender both assets |
| Raw body limit is misunderstood | README claims DoS-safe buffering | Explicit decoded-model limitation and gateway/server requirement | Return to Task 6 security prose |

## Task 1: Isolate and Lock the Optional Web Stack

**Complexity:** medium  
**Depends on:** approved spec and Step 2-R review  
**Patterns:** `test-driven-development`, `bluetape-py-patterns`  
**Files:** modify `tests/test_dependency_baseline.py`, `pyproject.toml`, `uv.lock`

- [ ] **Step 1.1: Write the failing default-isolation and metadata tests**

Extend `FORBIDDEN_DEFAULT_DISTRIBUTIONS` with `fastapi`, `starlette`,
`pydantic`, `pydantic-core`, `httpx`, `httpcore`, `uvicorn`, and `anyio`. Add an
exact optional-extra assertion:

```python
assert project["project"]["optional-dependencies"]["fastapi-order-api"] == [
    "fastapi>=0.139.2,<0.140",
    "httpx>=0.28.1,<0.29",
    "uvicorn>=0.51.0,<0.52",
]
```

Add lock assertions that these direct distributions exist only as optional
resolution members and that the workshop root does not require them by default.
Each optional example test module must call
`pytest.importorskip("fastapi", reason="requires the fastapi-order-api extra")`
before importing `application`, `models`, `context`, or `__main__`.

- [ ] **Step 1.2: Run the focused test and observe RED**

Run:

```bash
uv run --locked pytest tests/test_dependency_baseline.py -q
```

Expected: FAIL because `fastapi-order-api` and its lock entries do not exist.

- [ ] **Step 1.3: Add the optional extra and regenerate the lock**

Add to `pyproject.toml`:

```toml
fastapi-order-api = [
    "fastapi>=0.139.2,<0.140",
    "httpx>=0.28.1,<0.29",
    "uvicorn>=0.51.0,<0.52",
]
```

Run:

```bash
uv lock --python 3.13.14
uv sync --locked --python 3.13.14
```

Expected: lock succeeds; default sync installs no forbidden web distribution.

- [ ] **Step 1.4: Prove default and optional environments separately**

Run sequentially:

```bash
uv run --locked pytest tests/test_dependency_baseline.py -q
UV_PROJECT_ENVIRONMENT=.venv-fastapi uv sync --locked \
  --extra fastapi-order-api --python 3.13.14
UV_PROJECT_ENVIRONMENT=.venv-fastapi uv run --locked \
  --extra fastapi-order-api python -c \
  "import fastapi,httpx,uvicorn; print(fastapi.__version__,httpx.__version__,uvicorn.__version__)"
```

Expected: baseline PASS; optional probe prints versions in the approved ranges.

- [ ] **Step 1.5: Commit the dependency boundary**

Commit only the three Task 1 files with a Lore message whose `Tested:` trailer
records both default and optional commands. Rollback is a single revert of this
commit followed by `uv sync --locked --python 3.13.14`.

## Task 2: Define Strict DTO and Request-Context Contracts

**Complexity:** medium  
**Depends on:** Task 1 optional environment  
**Files:** create `models.py`, `context.py`, `tests/test_models.py`, `tests/test_context.py`

- [ ] **Step 2.1: Write RED tests for strict models and conversion**

Tests construct this valid body and assert conversion to exact immutable backend
dataclasses:

```python
payload = OrderRequest(
    partner_id="partner-7",
    order_id="order-9001",
    lines=[OrderLineRequest(sku="SKU-1", quantity=2)],
)
assert payload.to_command("req-1001") == OrderBackendCommand(
    request_id="req-1001",
    partner_id="partner-7",
    order_id="order-9001",
    lines=(OrderLineCommand(sku="SKU-1", quantity=2),),
)
```

Parameterize unknown fields, bool/float quantities, 0 and 1,000,001 quantities,
0 and 101 lines, and 129-character identifiers. Assert whitespace-only values
reach domain validation rather than being stripped by the DTO.

- [ ] **Step 2.2: Run model tests and observe RED**

```bash
UV_PROJECT_ENVIRONMENT=.venv-fastapi uv run --locked \
  --extra fastapi-order-api pytest examples/fastapi_order_api/tests/test_models.py -q
```

Expected: collection FAIL because the optional example does not exist.

- [ ] **Step 2.3: Implement strict Pydantic models**

Use `ConfigDict(extra="forbid", strict=True)`, `StringConstraints(min_length=1,
max_length=128)`, `conint(strict=True, ge=1, le=1_000_000)`, and
`conlist(..., min_length=1, max_length=100)`. Define:

```python
class OrderProblem(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    code: str
    message: str
    request_id: str
    field: str | None = None
    line_index: int | None = None
```

Keep output construction explicit; never call `model_validate` on a domain
dataclass or serialize `ProcessedOrder` wholesale.

- [ ] **Step 2.4: Write RED request-id and context restoration tests**

Test exactly one header, missing/duplicate headers, whitespace trim, invalid
ASCII/control/Unicode/129-character values, and the fixed `<invalid>` sentinel.
Capture a log record under an outer `log_context(request_id="outer")`; after
success and raised exception, assert the following record again contains
`request_id == "outer"`.

- [ ] **Step 2.5: Implement request-id parsing and context scope**

Define a compiled full-match allowlist and return a frozen result:

```python
REQUEST_ID_PATTERN = re.compile(r"[A-Za-z0-9._:-]{1,128}\Z", re.ASCII)

@contextmanager
def request_context(request_id: str) -> Iterator[None]:
    with log_context(request_id=request_id):
        yield
```

Read duplicate headers with `request.headers.getlist("x-request-id")`; never log
the raw invalid value. Use one stable `InvalidRequestId` exception carrying only
a fixed reason code.

- [ ] **Step 2.6: Run focused tests GREEN and commit**

Run both files under `.venv-fastapi`; expected all PASS and Ruff PASS. Commit
only Task 2 files with exact validation evidence.

## Task 3: Build the Lifespan-Owned Application Boundary

**Complexity:** high  
**Depends on:** Task 2  
**Files:** create `providers.py`, `application.py`, an import-safe empty
`__init__.py`; extend `test_application.py`

- [ ] **Step 3.1: Write RED lifespan ownership tests**

Create an instrumented backend and factory. Within one `TestClient(app)` context,
send two requests and assert `factory.calls == 1` and both backend identities are
the same. After exit, assert `close_calls == 1` and
`hasattr(app.state, "order_backend") is False`.

For failure, make `aclose()` raise `OrderBackendShutdownError(1)` and assert the
exception escapes context exit while `app.state.order_backend is backend`.

- [ ] **Step 3.2: Run lifespan tests RED**

Expected: FAIL because `create_app` and lifespan state do not exist.

- [ ] **Step 3.3: Implement typed backend and factory protocols**

Define structural protocols with only the used surface:

```python
class OrderBackend(Protocol):
    async def process(self, command: OrderBackendCommand) -> ProcessedOrder: ...
    async def aclose(self) -> None: ...

type BackendFactory = Callable[[], OrderBackend]
```

The default factory creates a logger and calls existing `build_application()`
with deterministic providers supporting `SKU-1`, `SKU-2`, and `SKU-3`. Unknown
demo SKUs raise the existing safe provider signal so the route maps them through
`CatalogEnrichmentFailed`, not a raw `KeyError`.

- [ ] **Step 3.4: Implement close-before-delete lifespan**

```python
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    backend = backend_factory()
    app.state.order_backend = backend
    yield
    await backend.aclose()
    del app.state.order_backend
```

Do not enter the backend as a second async context; lifespan owns the one close
call directly. Do not swallow close failure or delete state in a `finally`.

- [ ] **Step 3.5: Run lifecycle GREEN and commit**

Run focused application tests three sequential times to detect loop/lifecycle
drift, then Ruff. Expected three PASS runs, one clean commit.

## Task 4: Implement the HTTP Contract and Failure Mapping

**Complexity:** high  
**Depends on:** Task 3  
**Files:** modify `application.py`, `test_application.py`

- [ ] **Step 4.1: Write RED success and validation tests**

Use `TestClient` as a context manager. Assert exact `200` JSON, response
`content-type`, no artifact/provider/recommendation fields, exact request ID,
strict content type, duplicate header rejection, forbidden fields, line bounds,
and whitespace-only domain rejection.

Assert `/openapi.json` documents the 200 response model and every approved
422/503/504/500 problem response without exposing the domain artifact model.

- [ ] **Step 4.2: Write the failure-mapping matrix RED**

Parameterize injected failures and expected `(status, code)`:

```python
[
    (InvalidOrderBackendCommand("lines", "bad"), 422, "invalid_order"),
    (InvalidOrderLine(index=0, field="sku", reason="bad"), 422, "invalid_order"),
    (CatalogEnrichmentFailed((RequiredProviderFailure(0, "provider_unavailable"),)), 503, "catalog_unavailable"),
    (OrderBackendClosedError(), 503, "backend_unavailable"),
    (TimeoutError(), 504, "order_timeout"),
    (TransportLimitError(stage="encoded", actual_size=2, limit=1), 500, "order_processing_failed"),
    (RuntimeError("provider-secret"), 500, "internal_error"),
]
```

Use `raise_server_exceptions=False` for mapped unknown errors. Assert
`provider-secret`, raw input, artifact bytes, and exception strings are absent
from bodies and captured transport logs. Assert fixed low-cardinality transport
events: `order_api.request_rejected`, `order_api.request_timed_out`,
`order_api.request_failed`, and `order_api.request_succeeded`; logs carry only
safe request ID, status, and error kind.

- [ ] **Step 4.3: Implement one route-local mapping boundary**

Create the command, call `await backend.process(command)`, and construct
`OrderResponse` explicitly. Catch only the listed `Exception` subclasses;
leave `asyncio.CancelledError` uncaught. Use fixed messages and safe field/index
metadata. Unknown exceptions log only `error_kind="unexpected_error"` and return
the generic 500 response.

- [ ] **Step 4.4: Install the validation handler**

Register a `RequestValidationError` handler that revalidates only the raw
request-id header, chooses the first safe Pydantic location from `exc.errors()`
without including `msg`, `input`, or `ctx`, and returns `invalid_request`.
Map missing or non-JSON request bodies into the already approved 422
`invalid_request` contract; do not introduce an unapproved 415 code. Accept
`application/json` with an optional charset parameter.

- [ ] **Step 4.5: Write and pass context-path tests**

For success, request validation, domain failure, timeout, unknown failure, and
cancellation, capture a transport log inside the request and a second log after
the call. Assert the request log has the safe request ID and the later log has
the seeded outer value.

- [ ] **Step 4.6: Write and pass real-backend cancellation proof**

Construct a real backend whose loader blocks on `asyncio.Event`. Call the route
coroutine with a constructed Starlette request, wait for loader entry, cancel
the route task, assert exact `CancelledError`, release cleanup, then use
`eventually_async` with a finite timeout to assert no
`integrated-order-backend-request-*` task remains. No `sleep()` is permitted.

- [ ] **Step 4.7: Run the focused suite and commit**

Expected: all model/context/application tests PASS; Ruff PASS; no loop exception
records. Commit only Task 4 files.

## Task 5: Add the Loopback-Only Runnable Server

**Complexity:** medium  
**Depends on:** Task 4  
**Files:** create `__main__.py`, `tests/test_main.py`; modify `__init__.py`

- [ ] **Step 5.1: Write RED CLI parser tests**

Assert default `8000`, valid selected port, rejection of `0`, `65536`, unknown
arguments, and inability to select a non-loopback host.

- [ ] **Step 5.2: Implement the minimal entry point**

```python
def main(argv: Sequence[str] | None = None) -> None:
    args = _parser().parse_args(argv)
    uvicorn.run(
        create_app(),
        host="127.0.0.1",
        port=args.port,
        workers=1,
        reload=False,
        proxy_headers=False,
    )
```

Disable reload and do not enable forwarded/proxy header trust. Keep application
construction inside the process; backend construction still occurs in lifespan.

- [ ] **Step 5.3: Write RED/GREEN subprocess smoke test**

Reserve a loopback port, launch the documented module command, poll only TCP
connectivity under a finite deadline, send exactly one supported order with `X-Request-ID`,
assert 200, terminate, wait finitely, kill only on timeout, and assert no child
process remains. Capture bounded stderr only on failure.

- [ ] **Step 5.4: Run CLI tests and commit**

Run CLI unit and smoke tests sequentially under `.venv-fastapi`; expected PASS
and clean process table. Commit Task 5 files.

## Task 6: Write Bilingual Guides and Source-Backed Diagrams

**Complexity:** high  
**Depends on:** implemented Tasks 1-5  
**Skills:** `bluetape-writer`, `bluetape-diagram`  
**Files:** create both README files, four diagram assets, `test_documentation.py`

- [ ] **Step 6.1: Load documentation and diagram references fresh**

Read the writer skill plus diagram `common.md`, `architecture.md`, and
`sequence.md`. Use implemented source as the only behavior authority. Inspect
the final Redis coordination diagram geometry as a style and spacing reference,
not as a source to copy.

- [ ] **Step 6.2: Write RED documentation-contract tests**

Assert reciprocal locale navigation, exact setup/run/curl/test/stop commands,
200 and all problem codes, three demo SKUs, correlation-not-idempotency warning,
raw-body-limit limitation, upstream #21/#22 gate, and all four asset links.

- [ ] **Step 6.3: Write aligned README guides**

Both locales contain scenario, non-goals, prerequisites, optional setup,
loopback run command, exact curl request, expected response, Architecture,
Sequence Diagram, ownership, validation versus domain errors, timeout,
cancellation, shutdown, security/redaction, raw body limitation,
troubleshooting, tests, cleanup, and unsupported production use.

- [ ] **Step 6.4: Create the Architecture SVG from source ownership**

Use separate cards for Partner, FastAPI transport, lifespan/app state,
`OrderBackendApplication`, backend services, and bluetape-py packages. Keep
connector routes orthogonal. Define explicit marker dimensions and calculate:

```text
minimum_card_gap >= rendered_arrow_projection + stroke_width + 12px safety
minimum_terminal_segment >= rendered_arrow_projection + 16px safety
```

Place cards far enough apart before routing connectors; never hide an overlap by
shrinking the arrowhead.

- [ ] **Step 6.5: Create the Sequence SVG from implemented events**

Show lifespan startup, POST parsing/context, backend process, 200 response, an
`alt` validation/timeout branch, context reset, and close-before-state-delete
shutdown. Use continuous lifelines, numbered messages, readable activations,
and the same arrowhead clearance rule.

- [ ] **Step 6.6: Add geometry regression assertions**

Parse SVG marker `viewBox`, `markerWidth`, `refX`, stroke width, card rectangles,
and terminal path segments. Fail when either formula in Step 6.4 is violated.
Assert no connector endpoint lies inside an unrelated card.

- [ ] **Step 6.7: Render, audit, and inspect both diagrams**

Run CairoSVG at scale 2, XML parsing, connector, geometry, endpoint,
mixed-corner, and sequence-style audits. Open both PNGs at full size and inspect
labels, whitespace, arrowheads, bends, and card clearance. Rerender after every
SVG correction; never edit PNGs directly.

- [ ] **Step 6.8: Run docs tests and commit**

Expected: documentation tests and every diagram audit PASS; both PNG dimensions
are recorded; `git diff --check` PASS. Commit README and diagram assets together.

## Task 7: Register the Example and Refresh Live Work State

**Complexity:** medium  
**Depends on:** Task 6  
**Files:** modify root README pair, `WIP.md`, `tests/test_documentation_contract.py`

- [ ] **Step 7.1: Write RED root registration tests**

Require both locale links, optional setup/run/test commands, issue #23 current
target, completed #10/PR #22 state, blocked #20 state, and the four local diagram
assets discovered by the generic runnable-example contract.

- [ ] **Step 7.2: Update root README locales and WIP**

Keep facts aligned. WIP names branch `feat/fastapi-order-api`, base/head,
milestone, current validation counts, pending PR, exact stop boundary, and both
optional Redis/Fory/FastAPI environments without claiming PyPI support.

- [ ] **Step 7.3: Run root documentation tests and commit**

Run `tests/test_documentation_contract.py` plus the new example documentation
test. Expected PASS and locale parity. Commit only Task 7 surfaces.

## Task 8: Verify, Review, and Commit the Required Lesson

**Complexity:** high  
**Depends on:** Tasks 1-7  
**Files:** create implementation review and lesson; repair only in-scope files

- [ ] **Step 8.1: Run focused optional verification**

Run sequentially in `.venv-fastapi`: all example tests, the module smoke, Ruff
format/check, and three repetitions of lifecycle/cancellation tests. Expected
all PASS with no leaked task/process warnings.

- [ ] **Step 8.2: Re-prove default isolation and full default suite**

Run default `uv sync --locked --python 3.13.14`, dependency baseline, Ruff,
full pytest, actionlint, and `git diff --check`. Expected web distributions
absent, optional tests visibly skipped with reasons, and all existing examples
green.

- [ ] **Step 8.3: Run every diagram and documentation proof**

Rerun XML/render/audit/link/locale/geometry commands. Inspect both final PNGs at
full size after the last SVG commit. Record marker, connector, card, and image
dimension counts in the implementation review.

- [ ] **Step 8.4: Verify exact spec/plan coverage**

Load the Step 5 verifier checklist. Map every acceptance and DoD row to source,
test, docs, or command evidence. Any `NEEDS FIX` returns to the owning task and
reruns all affected downstream checks.

- [ ] **Step 8.5: Complete six-perspective main-session code review**

Review performance, stability, security, Ops, developer/API, and user/caller
against the complete branch diff. Repair all P0/P1 and rerun only affected
lenses plus integration. Store the final P0=0/P1=0 table under
`docs/superpowers/reviews/`.

- [ ] **Step 8.6: Commit the Type A lesson**

Create the required lesson with context, decisions, surprises/failures,
verification, review misses, and future guards. It must specifically capture
the raw-body versus decoded-model boundary, close-before-state-delete ordering,
and arrowhead-aware spacing regression. Commit before PR creation.

## Task 9: Deliver the Authorized Pull Request and Stop at Merge Approval

**Complexity:** medium  
**Depends on:** Task 8 and CG-01 through CG-10 PASS

- [ ] **Step 9.1: Refresh issue, Epic, and authority evidence**

Read live issue #23, Epic #1, branch status, remote base, workflow receipts, and
the approved plan. Update issue/Epic checklists with exact evidence but do not
close the issue manually; the PR uses `Closes #23`.

- [ ] **Step 9.2: Publish the exact head**

Push `feat/fastapi-order-api`, read back `origin/feat/fastapi-order-api`, and
assert it equals local HEAD. Do not force-push or enable auto-merge.

- [ ] **Step 9.3: Create and verify the PR**

Create the English PR to `develop`, assign `debop`, mirror milestone `0.2.0`
and relevant labels, include `Closes #23`, explain optional isolation and
production non-goals, list validation/diagram evidence, and finish with final
heading `## DoD Status`. Verify the live body and metadata with `gh pr view`.

- [ ] **Step 9.4: Pass exact-head CI and live review**

Wait for required checks, reread reviews and unresolved threads after green,
rerun the six perspectives against the PR diff, and repair/revalidate any P0/P1.
Refresh the PR body DoD when the head changes.

- [ ] **Step 9.5: Report merge-ready and stop**

Render the complete Type A/common-gate table, exact PR/head, test counts,
dependency isolation, lesson, diagram audit/full-size inspection, P0=0/P1=0,
and residual production limitation. Leave CG-16 through CG-18 PENDING and wait
for a fresh explicit merge approval.

## Plan Completion Gate

Before Task 1 begins:

- [ ] user approves this reviewed plan;
- [ ] Step 3-R plan review records P0=0 and P1=0;
- [ ] approved spec, design review, plan, and plan review are committed;
- [ ] workflow evidence marks spec and plan prerequisites complete;
- [ ] `repo-status` is clean and the worktree remains based on the approved
      `develop` ancestry.
