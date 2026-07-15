# Issue #3 Validated Order Intake Design

Status: approved design captured for written review

Issue: [#3](https://github.com/bluetape4k/bluetape-py-workshop/issues/3)

Work type: Type A — Full Feature

## Problem

The workshop foundation is reproducible, but readers do not yet have an
application-shaped example showing how the focused `bluetape-py` foundation
packages work together. The first example must accept a partner order command,
validate it without mutating caller-owned values, scope request context to
application-owned logs, and return an immutable accepted result.

The example must remain framework-neutral. It teaches application boundaries,
not HTTP routing, persistence, cache integration, or background execution.

## Current Evidence

The workshop resolves all focused packages from bluetape-py commit
`4b7458f22cea0a9e757b5fbf7f5ff4bc8c23cb9a`.

The design uses only APIs present at that exact source:

- `bluetape.core.require_instance`
- `bluetape.core.require_not_blank`
- `bluetape.logging.log_context`
- `bluetape.logging.get_log_context`
- `bluetape.logging.ContextLogFilter`
- `bluetape.testing.eventually`

`require_not_blank` returns the original string rather than a stripped copy.
The example therefore validates caller values without silently normalizing
them. `log_context` resets its `ContextVar` token in `finally`, and
`ContextLogFilter` attaches the current context only to records processed by an
application-owned handler. Because standard logging handler emission is
synchronous here, ordinary log assertions inspect captured records directly.
One explicitly labelled API-demonstration test uses `eventually` with the
smallest practical timeout to teach its bounded probe contract without implying
that this example needs synchronization.

The application-shaped layout and explicit production boundaries borrow from
`bluetape-go-workshop` examples. The bilingual navigation and source-backed
SVG/PNG visual contract follow the established workshop documentation rules
used in `bluetape4k-workshop`.

## Design Alternatives

### A. Small application package — selected

Create one importable example package under `examples/order_intake` with
separate models, errors, service, and runnable entrypoint modules.

Benefits:

- each responsibility is independently readable and testable;
- the package runs with `python -m` from the repository root;
- issue #8 can later compose the public service contract;
- the example stays small without collapsing every concern into one file.

Cost: a few more files than a script-only example.

### B. Single teaching script — rejected

A single `main.py` would minimize navigation, but validation, error mapping,
logging ownership, runnable output, and test seams would become entangled. It
would also provide a poor contract for the integrated backend in issue #8.

### C. Domain/application/adapter layers — rejected

Three explicit layers would anticipate future framework integration, but issue
#3 has no external adapter. Creating those boundaries now would add ceremony
without a second implementation behind any interface.

## Package Layout

```text
examples/
└── order_intake/
    ├── __init__.py
    ├── __main__.py
    ├── errors.py
    ├── models.py
    ├── service.py
    ├── README.md
    ├── README.ko.md
    ├── docs/images/
    │   ├── architecture.svg
    │   ├── architecture.png
    │   ├── sequence.svg
    │   └── sequence.png
    └── tests/
        ├── test_application.py
        ├── test_documentation.py
        └── test_service.py
```

The example remains part of the root non-package `uv` project. No new runtime
dependency or lockfile change is expected. Root pytest discovery will include
the `examples` tree so the full CI lane runs the example tests.

## Public Contracts

### PartnerOrderCommand

`PartnerOrderCommand` is a frozen dataclass with:

- `request_id: str`
- `partner_id: str`
- `order_id: str`
- `sku: str`
- `quantity: int`

Frozen input makes the ownership boundary visible, but the service must still
avoid replacing, trimming, or otherwise normalizing accepted caller values.

### AcceptedOrder

`AcceptedOrder` is a frozen dataclass containing the validated command fields
and `status: Literal["accepted"]`. The result does not retain a mutable
reference to caller-owned state.

### InvalidOrderCommand

`InvalidOrderCommand` is the public application exception. It records a stable
field name and safe reason while chaining the underlying `ValueError` or
`TypeError`. Raw command contents are not included in the public message.

`map_order_error` converts the exception into an immutable
`OrderIntakeProblem` containing a stable code, field, and safe message. This is
an application mapping, not an HTTP response contract.

### OrderIntakeService

`OrderIntakeService` receives a caller-owned `logging.Logger` and validates that
constructor argument with `require_instance`. It does not call `basicConfig`,
fetch or mutate the root logger, register a global handler, or own process-wide
logging policy.

`accept(command)`:

1. establishes safe request context for `request_id`, `partner_id`, and
   `order_id`; context extraction performs only `isinstance(value, str)` and
   otherwise substitutes `<invalid>` without calling `str`, `repr`,
   serialization, truncation, or any user-defined conversion;
2. validates the command object, then `request_id`, `partner_id`, `order_id`,
   and `sku` in that deterministic order using `bluetape-core` runtime type and
   non-blank checks;
3. rejects `bool`, non-`int`, zero, and negative quantities explicitly;
4. returns an immutable `AcceptedOrder` preserving accepted caller values;
5. logs one success or one rejection event while context is active;
6. lets `log_context` reset state after both success and failure.

The service catches and maps only validation failures. Logger/handler failures
remain application failures and are not misreported as invalid commands; the
context manager still resets its token. The service never logs the full
command. `sku` and quantity stay out of log context to keep the example's
telemetry boundary small.

The three identifiers are treated as non-secret operational correlation IDs.
The example documents that callers must not place credentials or sensitive
payloads in them and should hash or replace identifiers when their own data
classification requires it.

## Application-Owned Logging

The runnable entrypoint creates a dedicated `logging.Logger` directly rather
than using the global registry. It sets the logger and handler to `INFO`, sets
`propagate = False`, attaches a stream handler with `ContextLogFilter`, invokes
the service with a deterministic sample command, and prints the accepted result
as JSON using only the standard library. Logs go to stderr and JSON goes to
stdout so the machine-readable result remains deterministic.

Tests construct their own direct logger and capture handler with explicit
levels and propagation disabled. Handler attachment and removal are bounded by
test-owned setup/cleanup. Ordinary service tests assert captured records
directly. One separate `eventually` API-demonstration test probes for a matching
record or `None` with the minimum bounded timeout; it is not used to hide a
race or introduce an artificial delay.

## Data Flow

### Success

1. Partner caller creates an immutable command.
2. Service opens the logging context.
3. `bluetape-core` validates identifiers and values.
4. Service creates an immutable accepted result.
5. Application-owned handler captures a contextual success record.
6. Context resets before control returns to the caller.

### Failure

1. Service opens safe logging context before field validation.
2. A core or quantity check fails.
3. Service translates the cause into `InvalidOrderCommand`.
4. Application-owned handler captures a contextual rejection record without
   raw command data.
5. Context resets before the exception reaches the caller.
6. `map_order_error` can create the documented application problem shape.

## Test Contract

Tests must prove:

- a valid command returns the exact immutable accepted projection;
- accepted strings retain caller whitespace because validation does not
  normalize values;
- every required string field rejects blank and non-string values;
- quantity rejects `bool`, non-integer, zero, and negative values;
- invalid input raises `InvalidOrderCommand` with a chained cause and stable
  error mapping;
- the caller command remains equal to its pre-call value;
- accepted results and commands reject mutation;
- success and failure records contain request context;
- full command values do not appear in log messages;
- `get_log_context()` is empty after success and failure;
- invalid non-string identifiers are never coerced with `str`, `repr`, or
  serialization while safe context is prepared;
- log capture uses an application-owned logger and leaves root/global logger
  state unchanged;
- ordinary synchronous log assertions do not poll, while one isolated test
  demonstrates the bounded `eventually` probe contract;
- the runnable module exits successfully with deterministic JSON output;
- English and Korean documents expose equivalent commands, APIs, assets, and
  source links.

Async cancellation and timeout tests are N/A because this example creates no
task, awaitable, timer, subprocess, socket, or external resource.

## Documentation and Visuals

Both example README files use reciprocal `English | 한국어` navigation and
contain:

- Scenario and explicit non-goals;
- Architecture and ownership explanation;
- Sequence Diagram covering success and validation failure;
- exact package/API inventory;
- root-relative setup, run, targeted test, and full validation commands;
- deterministic expected output;
- cleanup and troubleshooting boundaries;
- source links to the example and pinned bluetape-py APIs.

The Architecture diagram is a static responsibility view of Partner Caller,
Order Intake Service, bluetape-core validation, bluetape-logging context, the
application-owned handler, and the accepted result/error mapping.

The Sequence Diagram shows the time-ordered `accept` path with an `alt` frame
for valid and invalid commands, visible context reset, numbered messages, and
application-owned log capture.

Each diagram is authored as SVG, rendered to PNG with CairoSVG at scale 2,
audited with the bluetape diagram scripts, opened at full size, and embedded by
both locales using shared English labels.

## Failure Modes and Guards

1. **Context leaks after validation failure.** Guard with success and failure
   reset assertions using `get_log_context()`.
2. **Tests mutate global logging state.** Guard with direct `logging.Logger`
   instances and before/after root logger snapshots.
3. **Validation silently normalizes caller values.** Guard with whitespace and
   caller-preservation tests.
4. **Python treats `bool` as `int`.** Reject boolean quantities before the
   integer check and cover the boundary explicitly.
5. **Logs expose the complete partner command.** Emit stable event names and
   selected identifier context only; assert sensitive/sample payload values are
   absent from messages.
6. **Diagrams drift from source.** Create assets after implementation and map
   every participant/message to a concrete module or call.
7. **Root pytest misses example tests.** Extend configured discovery and prove
   both the targeted example path and the full suite.
8. **Direct logger defaults suppress success events or propagate globally.**
   Set explicit INFO levels, disable propagation, and assert both properties.
9. **Invalid objects execute expensive or hostile string conversion.** Safe
   context performs a string type check only and otherwise emits `<invalid>`.

## Compatibility and Migration

- Python remains 3.13+ with reference interpreter 3.13.14.
- uv remains pinned to 0.11.28.
- The existing bluetape-py source commit remains unchanged.
- No new dependency, extra, provider, or Docker capability is introduced.
- Existing bootstrap commands remain valid; the full pytest count increases.
- Issue #8 may import the example's public models, error mapping, and service,
  but issue #3 does not introduce abstractions solely for that future use.

## Acceptance Mapping

| Issue acceptance criterion | Design proof |
|---|---|
| Immutable accepted result without caller mutation | Frozen models plus preservation and mutation tests |
| Explicit failure and application error mapping | `InvalidOrderCommand`, chained causes, `OrderIntakeProblem` |
| Context present and reset after success/failure | `log_context`, filtered handler, reset assertions |
| Capture logs without global changes | Direct application-owned logger and handler cleanup |
| Success, invalid, empty/boundary, reset, log, preservation tests | Parametrized service and logging test matrix |
| Equivalent README locales, navigation, runnable command | Per-example docs contract and root navigation update |

## Non-Goals

- ASGI, FastAPI, HTTP status mapping, or request parsing
- persistence, idempotency storage, cache, Redis, or Testcontainers
- async execution, cancellation, retry, or timeout policy
- package publication, release, tag, or milestone closure
- reusable workshop utility layers

## Delivery Boundary

The approved delivery target is:

- repository: `bluetape4k/bluetape-py-workshop`
- base: `develop`
- head: `feat/issue-3-validated-order-intake`
- issue: #3, milestone `0.1.0`, assignee `debop`

PR creation is in scope after spec, plan, implementation, documentation,
diagram, review, and validation gates pass. Merge remains a separate fresh
approval after the exact PR head is reported merge-ready. Auto-merge is
forbidden.

## Design DoD

- Exact pinned APIs and ownership boundaries are named.
- Alternatives and rejection reasons are explicit.
- Public models, exceptions, error mapping, logging, and lifecycle behavior are
  unambiguous.
- Success and failure flows map to tests and diagrams.
- At least three concrete failure modes have guards.
- Bilingual documentation and visual validation contracts are pinned.
- No dependency, release, or production-provider side effect is implied.
