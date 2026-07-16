# Integrated Order Backend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> `subagent-driven-development` (recommended) or `executing-plans` to implement
> this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an independently runnable, framework-neutral multi-line order
backend that composes the existing intake, enrichment, async cache, and bounded
JSON payload examples behind explicit request and shutdown lifecycle ownership.

**Architecture:** `OrderBackendService` validates an immutable aggregate through
the existing intake service, enriches its occurrence-ordered lines through a
cache-backed required provider, calculates totals, and encodes an allowlisted
untrusted JSON document. `OrderBackendApplication` owns one tracked task per
request plus one shared close task, while the composition root owns the cache,
providers, fixed limits, and deterministic CLI scenario.

**Tech Stack:** Python 3.13.14, uv 0.11.28, asyncio, stdlib logging,
`bluetape-core`, `bluetape-logging`, `bluetape-async`, `bluetape-collections`,
`bluetape-cache`, `bluetape-codec`, `bluetape-compression`, `bluetape-serde`,
pytest 8.4, Ruff 0.12, SVG/CairoSVG.

---

## Execution Contract

- Repository: `bluetape4k/bluetape-py-workshop`
- Base: `develop@15bbe2efced086eb06ccf67aa03f4efb7633e7bb`
- Head: `feat/issue-8-integrated-order-backend`
- Worktree:
  `/Users/debop/work/bluetape4k/bluetape-py-workshop/.worktrees/issue-8-integrated-order-backend`
- Issue: <https://github.com/bluetape4k/bluetape-py-workshop/issues/8>
- Approved spec:
  `docs/superpowers/specs/2026-07-16-issue-8-integrated-order-backend-design.md`
- Spec review:
  `docs/superpowers/reviews/2026-07-16-issue-8-design-review.md`
- Workflow type: Type A; use `bluetape-py-patterns` and strict TDD for code,
  `bluetape-writer` for both README locales, and `bluetape-diagram` for visuals.
- Heavy-command limit: one pytest, actionlint, diagram-render, or full validation
  process at a time. This example has no Docker-backed lane.
- Side effects authorized when this plan is approved: local edits, Lore commits,
  push of the exact head branch, and PR creation in
  `bluetape4k/bluetape-py-workshop` from
  `feat/issue-8-integrated-order-backend` into `develop`.
- Side effects not authorized: merge, auto-merge, remote branch deletion, tag,
  release, publish, workflow dispatch, milestone closure, dependency or
  lockfile changes.
- Stop boundary: report the exact PR head as merge-ready after local validation,
  diagram inspection, hosted CI, and current review/thread verification; wait
  for fresh explicit merge approval.

## File Map

| Path | Responsibility |
|---|---|
| `examples/integrated_order_backend/models.py` | Immutable aggregate and processed result contracts |
| `examples/integrated_order_backend/errors.py` | Safe aggregate, line, closed, and shutdown errors |
| `examples/integrated_order_backend/composition.py` | Cache-backed provider adapter and composition root |
| `examples/integrated_order_backend/service.py` | Validate, enrich, total, allowlist, encode, and expose cache stats |
| `examples/integrated_order_backend/application.py` | Loop binding, request task tracking, deadlines, and bounded shared close |
| `examples/integrated_order_backend/__init__.py` | Deliberate example-local public exports |
| `examples/integrated_order_backend/__main__.py` | Two-order shared-cache CLI and safe JSON events |
| `examples/integrated_order_backend/tests/test_models.py` | Exact model/error/public shape |
| `examples/integrated_order_backend/tests/test_composition.py` | Sequential cache adapter and root ownership |
| `examples/integrated_order_backend/tests/test_service.py` | Validation-before-I/O, ordering, warnings, failures, totals, payload, logging |
| `examples/integrated_order_backend/tests/test_application.py` | Timeout, cancellation, races, close ownership, retry, loop binding |
| `examples/integrated_order_backend/tests/test_cli.py` | Exact ordered events and cache miss/hit scenario |
| `examples/integrated_order_backend/tests/test_documentation.py` | Locale, command, source, and diagram contract |
| `examples/integrated_order_backend/README.md` | English learner scenario and limits |
| `examples/integrated_order_backend/README.ko.md` | Meaning-equivalent Korean learner scenario and limits |
| `examples/integrated_order_backend/docs/images/architecture.{svg,png}` | Source-backed responsibility/ownership view |
| `examples/integrated_order_backend/docs/images/sequence.{svg,png}` | Source-backed success/failure/cancellation/shutdown sequence |
| `README.md`, `README.ko.md` | Root discovery, learning path, and run/test commands |
| `tests/test_documentation_contract.py` | Automatic new-example README and asset discovery |
| `WIP.md` | Issue #8 branch, artifacts, validation, PR, and next gate |
| `docs/superpowers/risks/2026-07-16-issue-8-integrated-order-backend-risk.md` | Triggered concurrency/cache/trust risk controls |
| `docs/superpowers/reviews/2026-07-16-issue-8-implementation-review.md` | Final six-perspective evidence |
| `docs/superpowers/lessons/2026-07-16-issue-8-composition-lifecycle.md` | Required reusable Type A lesson |

`pyproject.toml`, `uv.lock`, `.github/workflows/ci.yml`, and every existing
example implementation must remain byte-identical to `origin/develop`.

## Acceptance Traceability

| Acceptance criterion | Tasks | Proof |
|---|---|---|
| Compose the four focused example boundaries | 1-5 | public-shape, adapter, service, root, and CLI tests |
| Stable occurrence order and caller-owned immutable input | 1, 3 | exact tuple/model tests and duplicate-line result assertions |
| Reject invalid aggregate/line before provider, cache, or payload | 1, 3 | call spies remain empty for every invalid path |
| Required failure propagates; optional failure becomes warnings | 2, 3 | exact existing exception/warning contracts |
| Overall timeout and caller cancellation do not detach work | 4 | shielded task and cancellation-resistant event tests |
| Cache miss/hit, deduplication, failure recovery | 2, 3, 5 | loader calls, public `CacheStats`, two-order CLI |
| Allowlisted untrusted JSON and all limits | 1, 3 | decoded document equality and focused limit exceptions |
| Bounded, concurrent-safe, retryable shutdown | 4 | shared close, grace/cancel, pending error, retry tests |
| Bilingual learner guidance with direct diagrams | 6, 7 | reciprocal locale and four-asset documentation tests |
| Type A validation, lesson, exact-head PR/CI gate | 8 | validation ladder, six-lens review, lesson, live PR evidence |

## Task 1: Define the Aggregate, Result, Error, and Export Contracts

**Complexity:** Medium. **Depends on:** approved spec only. **Write scope:** new
package models/errors/exports and model tests.

**Files:**

- Create: `examples/integrated_order_backend/__init__.py`
- Create: `examples/integrated_order_backend/models.py`
- Create: `examples/integrated_order_backend/errors.py`
- Create: `examples/integrated_order_backend/tests/__init__.py`
- Create: `examples/integrated_order_backend/tests/test_models.py`

- [x] **Step 1.1: Write failing exact public-shape tests**

Require imports, keyword-only construction, slots, frozen mutation failure,
exact tuple preservation, and exact error metadata:

```python
line = OrderLineCommand(sku=" sku-1 ", quantity=2)
command = OrderBackendCommand(
    request_id="req-1001",
    partner_id="partner-7",
    order_id="order-9001",
    lines=(line,),
)
assert command.lines is not None
assert command.lines[0] is line
assert not hasattr(command, "__dict__")
with pytest.raises(FrozenInstanceError):
    line.quantity = 3  # type: ignore[misc]
with pytest.raises(TypeError):
    OrderLineCommand("SKU-1", 2)  # type: ignore[misc]

cause = InvalidOrderCommand("sku", "must not be blank")
error = InvalidOrderLine(index=3, field=cause.field, reason=cause.reason)
error.__cause__ = cause
assert (error.index, error.field, error.reason) == (3, "sku", "must not be blank")
assert str(error) == "lines[3].sku: must not be blank"
assert OrderBackendShutdownError(2).pending_count == 2
```

- [x] **Step 1.2: Observe RED**

Run:

```bash
uv run --locked pytest examples/integrated_order_backend/tests/test_models.py -q
```

Expected: collection fails because the new package contracts do not exist.

- [x] **Step 1.3: Implement the exact immutable contracts**

Use these complete model fields:

```python
from dataclasses import dataclass

from examples.bounded_payload_processing import EncodedPayload
from examples.catalog_enrichment import EnrichmentWarning


@dataclass(frozen=True, slots=True, kw_only=True)
class OrderLineCommand:
    sku: str
    quantity: int


@dataclass(frozen=True, slots=True, kw_only=True)
class OrderBackendCommand:
    request_id: str
    partner_id: str
    order_id: str
    lines: tuple[OrderLineCommand, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class ProcessedOrderLine:
    line_index: int
    sku: str
    quantity: int
    name: str
    unit_price_cents: int
    line_total_cents: int
    recommendation: str | None
    warnings: tuple[EnrichmentWarning, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class ProcessedOrder:
    request_id: str
    partner_id: str
    order_id: str
    lines: tuple[ProcessedOrderLine, ...]
    total_cents: int
    artifact: EncodedPayload
```

Implement safe errors with exact fields and messages:

```python
class InvalidOrderBackendCommand(ValueError):
    def __init__(self, field: str, reason: str) -> None:
        self.field = field
        self.reason = reason
        super().__init__(f"{field}: {reason}")


class InvalidOrderLine(ValueError):
    def __init__(self, *, index: int, field: str, reason: str) -> None:
        self.index = index
        self.field = field
        self.reason = reason
        super().__init__(f"lines[{index}].{field}: {reason}")


class OrderBackendClosedError(RuntimeError):
    def __init__(self) -> None:
        super().__init__("order backend is closed")


class OrderBackendShutdownError(RuntimeError):
    def __init__(self, pending_count: int) -> None:
        self.pending_count = pending_count
        super().__init__(f"order backend shutdown left {pending_count} pending requests")
```

Export only the planned public models, errors, services, adapter, application,
and `build_application`; temporarily export the Task 1 symbols and extend the
same explicit `__all__` as later tasks land.

- [x] **Step 1.4: Observe GREEN and commit**

Run the Step 1.2 command, Ruff on the new files, and `git diff --check`.
Expected: all pass. Commit with a Lore message whose directive preserves exact
keyword-only aggregate and safe error metadata.

## Task 2: Compose the Async Catalog Cache Behind the Existing Provider Protocol

**Complexity:** Medium. **Depends on:** Task 1 exports. **Write scope:** adapter
and adapter tests only. **Pattern:** `bluetape-py-patterns`, async TDD.

**Files:**

- Create: `examples/integrated_order_backend/composition.py`
- Create: `examples/integrated_order_backend/tests/test_composition.py`
- Modify: `examples/integrated_order_backend/__init__.py`

- [x] **Step 2.1: Write failing adapter success/failure tests**

Construct a real `AsyncTTLCache` and existing catalog service around an
event-aware loader. Assert sequential normalized calls, exact mapping, public
stats, failure identity, and recovery:

```python
attempts: dict[str, int] = {}

async def loader(product_id: str) -> ProductSummary:
    attempts[product_id] = attempts.get(product_id, 0) + 1
    if product_id == "FAIL" and attempts[product_id] == 1:
        raise ProviderUnavailable()
    return ProductSummary(
        product_id=product_id,
        name=f"Product {product_id}",
        price_cents=1_000,
    )

catalog = AsyncProductCatalogService(
    cache=AsyncTTLCache(default_ttl=60, max_size=16),
    loader=loader,
)
provider = CachedCatalogProvider(catalog=catalog)
assert await provider.fetch(("SKU-1", "SKU-2")) == {
    "SKU-1": CatalogRecord(product_id="SKU-1", name="Product SKU-1", price_cents=1_000),
    "SKU-2": CatalogRecord(product_id="SKU-2", name="Product SKU-2", price_cents=1_000),
}
with pytest.raises(ProviderUnavailable):
    await provider.fetch(("FAIL",))
assert (await provider.fetch(("FAIL",)))["FAIL"].product_id == "FAIL"
stats = await catalog.stats()
assert (stats.misses, stats.loads, stats.load_failures) == (4, 4, 1)
```

- [x] **Step 2.2: Observe RED**

Run the focused composition test. Expected: import fails for
`CachedCatalogProvider`.

- [x] **Step 2.3: Implement the minimal sequential adapter**

```python
class CachedCatalogProvider:
    def __init__(self, *, catalog: AsyncProductCatalogService) -> None:
        if type(catalog) is not AsyncProductCatalogService:
            raise TypeError("catalog must be an exact AsyncProductCatalogService")
        self._catalog = catalog

    async def fetch(self, product_ids: tuple[str, ...]) -> Mapping[str, CatalogRecord]:
        records: dict[str, CatalogRecord] = {}
        for product_id in product_ids:
            value = await self._catalog.get_product(product_id)
            records[product_id] = CatalogRecord(
                product_id=value.product_id,
                name=value.name,
                price_cents=value.price_cents,
            )
        return records
```

Do not catch loader exceptions, create tasks, expose cache mutation, or add a
new provider abstraction. The outer enrichment service remains the only
provider-job concurrency owner.

- [x] **Step 2.4: Observe GREEN, verify no nested tasks, and commit**

Run focused tests and assert no new task name appears during adapter calls.
Expected: success/failure/recovery pass and `uv.lock` is unchanged. Commit with
a Lore message recording the deliberate sequential teaching trade-off.

## Task 3: Implement Validation-First Aggregate Processing with TDD

**Complexity:** High. **Depends on:** Tasks 1-2. **Write scope:** service and
service tests. **Pattern:** `bluetape-py-patterns`, TDD, existing service reuse.

**Files:**

- Create: `examples/integrated_order_backend/service.py`
- Create: `examples/integrated_order_backend/tests/test_service.py`
- Modify: `examples/integrated_order_backend/__init__.py`

- [x] **Step 3.1: Write failing constructor and aggregate-boundary tests**

Create spies for intake, enrichment, catalog stats, and payload encoding. Assert
constructor rejection of invalid `batch_size`, `concurrency_limit`, and
non-finite/non-positive `provider_timeout`. Parameterize exact command type,
exact tuple, 0/101 lines, and wrong line type. For every invalid shape assert:

```python
with pytest.raises(InvalidOrderBackendCommand):
    await service.process(raw_command)  # type: ignore[arg-type]
assert intake.calls == []
assert enrichment.calls == []
assert payloads.calls == []
```

- [x] **Step 3.2: Observe RED, then implement constructor-owned validation**

Run the focused service tests and expect import failure. Implement exact-int
batch/concurrency checks, `1 <= batch_size <= 100`, and finite positive numeric
provider timeout before storing dependencies. Use this exact constructor and
validation; concrete annotations explain composition while method-callable
checks keep test doubles possible without adding a public protocol:

```python
def _positive_exact_int(name: str, value: object) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact int")
    if value <= 0:
        raise ValueError(f"{name} must be positive")
    return value


def _positive_timeout(name: str, value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a finite positive number")
    timeout = float(value)
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError(f"{name} must be a finite positive number")
    return timeout


class OrderBackendService:
    def __init__(
        self,
        *,
        intake: OrderIntakeService,
        enrichment: CatalogEnrichmentService,
        catalog: AsyncProductCatalogService,
        payloads: JsonPayloadService,
        logger: logging.Logger,
        batch_size: int,
        concurrency_limit: int,
        provider_timeout: float,
    ) -> None:
        required = {
            "intake": (intake, "accept"),
            "enrichment": (enrichment, "enrich"),
            "catalog": (catalog, "stats"),
            "payloads": (payloads, "encode"),
        }
        for name, (dependency, method) in required.items():
            if not callable(getattr(dependency, method, None)):
                raise TypeError(f"{name} must define {method}()")
        if not isinstance(logger, logging.Logger):
            raise TypeError("logger must be a logging.Logger")
        checked_batch_size = _positive_exact_int("batch_size", batch_size)
        if checked_batch_size > MAX_BATCH_SIZE:
            raise ValueError(f"batch_size must be at most {MAX_BATCH_SIZE}")
        self._intake = intake
        self._enrichment = enrichment
        self._catalog = catalog
        self._payloads = payloads
        self._logger = logger
        self._batch_size = checked_batch_size
        self._concurrency_limit = _positive_exact_int(
            "concurrency_limit", concurrency_limit
        )
        self._provider_timeout = _positive_timeout(
            "provider_timeout", provider_timeout
        )
```

Require callable `accept`, `enrich`, `stats`, and `encode` methods and an exact
stdlib `logging.Logger`; reject missing methods at construction. Validate
aggregate shape with `type(command) is OrderBackendCommand`,
`type(command.lines) is tuple`, 1-100 occurrences, and
`type(line) is OrderLineCommand` using this helper:

```python
def _validated_command(command: object) -> OrderBackendCommand:
    if type(command) is not OrderBackendCommand:
        raise InvalidOrderBackendCommand("command", "must be OrderBackendCommand")
    if type(command.lines) is not tuple:
        raise InvalidOrderBackendCommand("lines", "must be an exact tuple")
    if not 1 <= len(command.lines) <= 100:
        raise InvalidOrderBackendCommand("lines", "must contain between 1 and 100 lines")
    for index, line in enumerate(command.lines):
        if type(line) is not OrderLineCommand:
            raise InvalidOrderBackendCommand(
                f"lines[{index}]",
                "must be OrderLineCommand",
            )
    return command
```

- [x] **Step 3.3: Write failing delegated line-validation tests**

Use a real `OrderIntakeService` with a capture logger. Parameterize invalid
header, SKU, and quantity values at indices 0 and 2. Require exact wrapping and
cause while provider/payload spies remain empty:

```python
with pytest.raises(InvalidOrderLine) as captured:
    await service.process(command)
assert captured.value.index == 2
assert captured.value.field == "quantity"
assert isinstance(captured.value.__cause__, InvalidOrderCommand)
assert enrichment.calls == []
assert payloads.calls == []
```

- [x] **Step 3.4: Implement the complete validation-before-I/O phase**

Map every occurrence to `PartnerOrderCommand` with the shared aggregate header,
call `intake.accept()` in order, and store all `AcceptedOrder` values before the
first enrichment call. Wrap only `InvalidOrderCommand` as
`InvalidOrderLine` with the current index, field, and reason, using
`raise mapped from error`; do not catch
`BaseException`, `CancelledError`, or logging-handler failures.

- [x] **Step 3.5: Write failing success, duplicate, failure, and cache tests**

Use real focused services and the Task 2 adapter. Assert:

```python
result = await service.process(
    OrderBackendCommand(
        request_id="req-1001",
        partner_id="partner-7",
        order_id="order-9001",
        lines=(
            OrderLineCommand(sku=" sku-2 ", quantity=2),
            OrderLineCommand(sku="SKU-1", quantity=1),
            OrderLineCommand(sku="sku-2", quantity=3),
        ),
    )
)
assert [line.sku for line in result.lines] == ["SKU-2", "SKU-1", "SKU-2"]
assert [line.line_index for line in result.lines] == [0, 1, 2]
assert result.total_cents == sum(line.line_total_cents for line in result.lines)
assert result.request_id == "req-1001"
assert loader_calls == ["SKU-2", "SKU-1"]
```

Add exact required `CatalogEnrichmentFailed` propagation, optional
`optional_provider_failed` warning preservation, cross-request cache hit,
loader failure not cached and later recovery, and caller input identity/equality
assertions.

- [x] **Step 3.6: Implement enrichment, totals, and explicit document allowlist**

After all intake calls pass, enter aggregate `log_context`, call existing
enrichment with fixed settings, zip accepted/enriched occurrences exactly, and
build `ProcessedOrderLine` values. Encode this exact document shape, never the
result object:

```python
def _document(
    header: AcceptedOrder,
    lines: tuple[ProcessedOrderLine, ...],
    total_cents: int,
) -> JsonValue:
    return {
        "request_id": header.request_id,
        "partner_id": header.partner_id,
        "order_id": header.order_id,
        "lines": [
            {
                "line_index": line.line_index,
                "sku": line.sku,
                "quantity": line.quantity,
                "name": line.name,
                "unit_price_cents": line.unit_price_cents,
                "line_total_cents": line.line_total_cents,
                "recommendation": line.recommendation,
                "warnings": [
                    {
                        "provider": warning.provider,
                        "code": warning.code,
                        "message": warning.message,
                    }
                    for warning in line.warnings
                ],
            }
            for line in lines
        ],
        "total_cents": total_cents,
    }


async def process(self, command: OrderBackendCommand) -> ProcessedOrder:
    typed = _validated_command(command)
    accepted: list[AcceptedOrder] = []
    for index, line in enumerate(typed.lines):
        try:
            accepted.append(
                self._intake.accept(
                    PartnerOrderCommand(
                        request_id=typed.request_id,
                        partner_id=typed.partner_id,
                        order_id=typed.order_id,
                        sku=line.sku,
                        quantity=line.quantity,
                    )
                )
            )
        except InvalidOrderCommand as error:
            raise InvalidOrderLine(
                index=index,
                field=error.field,
                reason=error.reason,
            ) from error

    header = accepted[0]
    with log_context(
        request_id=header.request_id,
        partner_id=header.partner_id,
        order_id=header.order_id,
    ):
        enriched = await self._enrichment.enrich(
            [line.sku for line in accepted],
            batch_size=self._batch_size,
            concurrency_limit=self._concurrency_limit,
            timeout=self._provider_timeout,
        )
        lines = tuple(
            ProcessedOrderLine(
                line_index=index,
                sku=product.product_id,
                quantity=accepted_line.quantity,
                name=product.name,
                unit_price_cents=product.price_cents,
                line_total_cents=product.price_cents * accepted_line.quantity,
                recommendation=product.recommendation,
                warnings=product.warnings,
            )
            for index, (accepted_line, product) in enumerate(
                zip(accepted, enriched, strict=True)
            )
        )
        total_cents = sum(line.line_total_cents for line in lines)
        artifact = self._payloads.encode(_document(header, lines, total_cents))
        return ProcessedOrder(
            request_id=header.request_id,
            partner_id=header.partner_id,
            order_id=header.order_id,
            lines=lines,
            total_cents=total_cents,
            artifact=artifact,
        )
```

Encode the allowlisted document first, then return `ProcessedOrder` with the
validated header, processed line tuple, total, and encoded artifact. Implement
`cache_stats()` only as this delegation; do not expose the cache itself:

```python
async def cache_stats(self) -> CacheStats:
    return await self._catalog.stats()
```

- [x] **Step 3.7: Prove payload limits and logging cleanup**

With the real `JsonPayloadService`, assert decoded equality, fixed untrusted
JSON metadata, serialized/compressed/encoded/nesting failures, and no artifact
field. Test success, invalid line, required failure, payload failure, timeout,
and cancellation context reset with `get_log_context() == {}`. Assert log
records never contain recommendation, product-name, artifact, or provider-cause
text.

- [x] **Step 3.8: Observe GREEN, run the triggered performance/stability scan, and commit**

Run all Task 3 tests, Ruff, and diff check. Inspect 100-line allocation,
duplicate-provider calls, nested tasks, exception catches, and payload creation.
Expected: stable order, one load per distinct SKU per cache lifetime, no
unbounded task creation, and all configured limits fail safely. Commit with a
Lore message preserving validation-before-I/O and explicit document shape.

## Task 4: Implement Deadline-Safe Request and Shared Shutdown Ownership

**Complexity:** High. **Depends on:** Task 3. **Write scope:** application and
lifecycle tests. **Pattern:** asyncio structured ownership and event-driven TDD.

**Files:**

- Create: `examples/integrated_order_backend/application.py`
- Create: `examples/integrated_order_backend/tests/test_application.py`
- Modify: `examples/integrated_order_backend/__init__.py`

- [x] **Step 4.1: Write failing constructor, success, and closed-state tests**

Use an event-driven fake processor with `async process(command)`. Require exact
finite positive `request_timeout`, `shutdown_grace_timeout`, and
`shutdown_cancel_timeout`, one named request task, terminal removal, idempotent
close, delegated public `cache_stats()`, and `OrderBackendClosedError` after
shutdown begins. Implement this exact constructor:

```python
def _positive_timeout(name: str, value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a finite positive number")
    timeout = float(value)
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError(f"{name} must be a finite positive number")
    return timeout


class OrderBackendApplication:
    def __init__(
        self,
        *,
        service: OrderBackendService,
        logger: logging.Logger,
        request_timeout: float,
        shutdown_grace_timeout: float,
        shutdown_cancel_timeout: float,
    ) -> None:
        if not callable(getattr(service, "process", None)):
            raise TypeError("service must define process()")
        if not callable(getattr(service, "cache_stats", None)):
            raise TypeError("service must define cache_stats()")
        if not isinstance(logger, logging.Logger):
            raise TypeError("logger must be a logging.Logger")
        self._service = service
        self._logger = logger
        self._request_timeout = _positive_timeout("request_timeout", request_timeout)
        self._shutdown_grace_timeout = _positive_timeout(
            "shutdown_grace_timeout", shutdown_grace_timeout
        )
        self._shutdown_cancel_timeout = _positive_timeout(
            "shutdown_cancel_timeout", shutdown_cancel_timeout
        )
        self._loop: asyncio.AbstractEventLoop | None = None
        self._state = "OPEN"
        self._requests: set[asyncio.Task[ProcessedOrder]] = set()
        self._close_task: asyncio.Task[None] | None = None
        self._request_sequence = 0
```

Runtime-check only callable `process` and `cache_stats` methods so event-driven
application test doubles remain possible; this is a private testing seam, not a
new exported protocol.

- [x] **Step 4.2: Observe RED, then implement loop binding and no-await admission**

Bind on first `process()`, `aclose()`, or `__aenter__` with
`asyncio.get_running_loop()`. Reject a different loop with stable `RuntimeError`
before state mutation. In one section containing no `await`: require `OPEN`,
create a named request task, register it, and attach a done callback that removes
only terminal tasks and calls `task.exception()` for non-cancelled completion.

- [x] **Step 4.3: Write failing timeout and caller-cancellation tests**

Use this cancellation-resistant processor shape without sleeps:

```python
class ResistantProcessor:
    def __init__(self) -> None:
        self.started = asyncio.Event()
        self.cancelled = asyncio.Event()
        self.release = asyncio.Event()

    async def process(self, command: OrderBackendCommand) -> ProcessedOrder:
        self.started.set()
        while not self.release.is_set():
            try:
                await self.release.wait()
            except asyncio.CancelledError:
                self.cancelled.set()
        raise RuntimeError("late provider failure")
```

Wrap awaits with a one-second test guard, not a real sleep. Assert overall
timeout/caller cancellation returns promptly, the owned task receives cancel,
`aclose()` still reports it pending until release, release produces no event-loop
"Task exception was never retrieved" record, and later close reaches terminal.
Add one real-service cooperative path with an event-gated async catalog loader:
after overall timeout, its `finally` event must fire, cache stats must report
`inflight_loads == abandoned_loads == 0`, and no `bluetape-cache-` task may
remain.

- [x] **Step 4.4: Implement shielded request waiting**

Await the owned task through `asyncio.shield()` inside `asyncio.timeout()`.
On `TimeoutError`, cancel and re-raise without awaiting an unbounded terminal
state. On caller `CancelledError`, cancel and promptly re-raise. Emit fixed
`order_backend.request_started`, `order_backend.request_succeeded`,
`order_backend.request_failed`, `order_backend.request_timed_out`, and
`order_backend.request_cancelled` events. Map failures only to
`catalog_enrichment_failed`, `payload_rejected`, or `unexpected_error`; never
include raw exception text or task representation. Emit matching fixed
`order_backend.shutdown_started`, `order_backend.shutdown_completed`, and
`order_backend.shutdown_failed` events; only the failure event may add numeric
`pending_count`. Lifecycle correctness must not depend on a logging handler, so
all application-level events use this best-effort boundary and tests require a
failing handler not to change request or close outcomes:

```python
def _emit(
    logger: logging.Logger,
    level: int,
    event: str,
    **extra: object,
) -> None:
    try:
        logger.log(level, event, extra=extra)
    except Exception:
        return
```

This containment applies only to application lifecycle telemetry. Existing
intake logging behavior remains unchanged inside the owned request task.

- [x] **Step 4.5: Write failing shutdown race, shared-close, and retry tests**

Cover:

1. a request reaches the processor gate before `aclose()` snapshots and close
   cannot return until that request completes or is cancelled;
2. two concurrent close callers receive the same close outcome and only one
   cancellation reaches the processor;
3. cancelling one close waiter does not cancel the close task or request;
4. grace expiry cancels cooperative work and returns;
5. cancellation-resistant work raises
   `OrderBackendShutdownError(pending_count=1)`;
6. releasing that work then retrying close reaches `CLOSED`;
7. context-body failure remains primary when cleanup also fails; successful body
   exposes cleanup failure directly; and
8. first-loop use followed by second-loop use fails before starting work;
9. a failing application logger cannot detach a request or prevent close; and
10. unexpected close-task failure/cancellation moves to `CLOSE_FAILED` and a
    later call can retry.

- [x] **Step 4.6: Implement the one-owner close state machine**

Use private states `OPEN`, `CLOSING`, `CLOSE_FAILED`, and `CLOSED`. The first
close caller flips state and snapshots admission in a no-`await` section,
creates one named close task, and all concurrent callers await it through
`shield`. `_close_once()` uses `asyncio.wait(snapshot, timeout=grace)`, cancels
pending tasks, then uses `asyncio.wait(pending, timeout=cancel_timeout)`.
Terminal success sets `CLOSED`; remaining tasks set `CLOSE_FAILED` and raise the
exact pending count while retaining references. A later call creates one retry
task. Observe the close task's exception even when all current waiters cancel.

Implement these complete lifecycle methods around the constructor from Step
4.1. Begin `application.py` with `from __future__ import annotations`, and
import `CompressionError`, `SerdeError`, `TransportLimitError`, the aggregate
errors/models, `CatalogEnrichmentFailed`, `CacheStats`, asyncio, logging, math,
and the exact service type used below:

```python
def _error_kind(error: Exception) -> str:
    if isinstance(error, (InvalidOrderBackendCommand, InvalidOrderLine)):
        return "invalid_order"
    if isinstance(error, CatalogEnrichmentFailed):
        return "catalog_enrichment_failed"
    if isinstance(error, (TransportLimitError, CompressionError, SerdeError)):
        return "payload_rejected"
    return "unexpected_error"


def _bind_loop(self) -> None:
    loop = asyncio.get_running_loop()
    if self._loop is None:
        self._loop = loop
    elif self._loop is not loop:
        raise RuntimeError("order backend is bound to another event loop")


def _observe_request(self, task: asyncio.Task[ProcessedOrder]) -> None:
    self._requests.discard(task)
    if not task.cancelled():
        task.exception()


def _observe_close(self, task: asyncio.Task[None]) -> None:
    if task.cancelled():
        if self._state == "CLOSING":
            self._state = "CLOSE_FAILED"
        return
    error = task.exception()
    if error is not None and self._state == "CLOSING":
        self._state = "CLOSE_FAILED"


async def process(self, command: OrderBackendCommand) -> ProcessedOrder:
    self._bind_loop()
    if self._state != "OPEN":
        raise OrderBackendClosedError()
    self._request_sequence += 1
    task = asyncio.create_task(
        self._service.process(command),
        name=f"integrated-order-backend-request-{self._request_sequence}",
    )
    self._requests.add(task)
    task.add_done_callback(self._observe_request)
    _emit(self._logger, logging.INFO, "order_backend.request_started")
    try:
        async with asyncio.timeout(self._request_timeout):
            result = await asyncio.shield(task)
    except TimeoutError:
        task.cancel()
        _emit(self._logger, logging.WARNING, "order_backend.request_timed_out")
        raise
    except asyncio.CancelledError:
        task.cancel()
        _emit(self._logger, logging.INFO, "order_backend.request_cancelled")
        raise
    except Exception as error:
        _emit(
            self._logger,
            logging.WARNING,
            "order_backend.request_failed",
            error_kind=_error_kind(error),
        )
        raise
    _emit(self._logger, logging.INFO, "order_backend.request_succeeded")
    return result


async def cache_stats(self) -> CacheStats:
    self._bind_loop()
    return await self._service.cache_stats()


async def _close_once(
    self,
    snapshot: tuple[asyncio.Task[ProcessedOrder], ...],
) -> None:
    _emit(self._logger, logging.INFO, "order_backend.shutdown_started")
    pending: set[asyncio.Task[ProcessedOrder]] = set(snapshot)
    if pending:
        _, pending = await asyncio.wait(
            pending,
            timeout=self._shutdown_grace_timeout,
        )
    for task in pending:
        task.cancel()
    if pending:
        _, pending = await asyncio.wait(
            pending,
            timeout=self._shutdown_cancel_timeout,
        )
    if pending:
        self._state = "CLOSE_FAILED"
        _emit(
            self._logger,
            logging.WARNING,
            "order_backend.shutdown_failed",
            pending_count=len(pending),
        )
        raise OrderBackendShutdownError(len(pending))
    self._state = "CLOSED"
    _emit(self._logger, logging.INFO, "order_backend.shutdown_completed")


async def aclose(self) -> None:
    self._bind_loop()
    if self._state == "CLOSED":
        return
    if self._state != "CLOSING":
        self._state = "CLOSING"
        snapshot = tuple(self._requests)
        self._close_task = asyncio.create_task(
            self._close_once(snapshot),
            name="integrated-order-backend-close",
        )
        self._close_task.add_done_callback(self._observe_close)
    close_task = self._close_task
    if close_task is None:
        raise RuntimeError("order backend close task was not created")
    await asyncio.shield(close_task)


async def __aenter__(self) -> OrderBackendApplication:
    self._bind_loop()
    if self._state != "OPEN":
        raise OrderBackendClosedError()
    return self
```

Implement context-manager precedence exactly:

```python
async def __aexit__(self, exc_type, exc, traceback) -> bool:
    try:
        await self.aclose()
    except OrderBackendShutdownError:
        if exc is None:
            raise
        exc.add_note("order backend cleanup did not reach terminal state")
    return False
```

- [x] **Step 4.7: Observe GREEN, scan lifecycle stability, and commit**

Run the lifecycle tests repeatedly in one pytest process, then the whole new
example test directory. Expected: no polling loop, real sleep, leaked request,
un-retrieved exception, or cross-loop mutation. Commit with a Lore directive
preserving shielded request/close ownership and finite waits.

## Task 5: Build the Shared-Cache Composition Root and Two-Order CLI

**Complexity:** Medium. **Depends on:** Tasks 2-4. **Write scope:** composition
root, CLI, and their tests.

**Files:**

- Modify: `examples/integrated_order_backend/composition.py`
- Create: `examples/integrated_order_backend/__main__.py`
- Extend: `examples/integrated_order_backend/tests/test_composition.py`
- Create: `examples/integrated_order_backend/tests/test_cli.py`
- Modify: `examples/integrated_order_backend/__init__.py`

- [x] **Step 5.1: Write failing composition-ownership tests**

Require `build_application` with keyword-only `logger`, `catalog_loader`, and
`recommendation_provider` to create one `AsyncTTLCache`, one existing async
catalog service, one adapter, one enrichment service, one JSON payload service,
one aggregate service, and one application. Use this exact root signature:

```python
def build_application(
    *,
    logger: logging.Logger,
    catalog_loader: AsyncProductLoader,
    recommendation_provider: OptionalRecommendationProvider,
) -> OrderBackendApplication:
    if not callable(catalog_loader):
        raise TypeError("catalog_loader must be async-callable")
    cache: AsyncTTLCache[str, ProductSummary] = AsyncTTLCache(
        default_ttl=60,
        max_size=128,
    )
    catalog = AsyncProductCatalogService(cache=cache, loader=catalog_loader)
    enrichment = CatalogEnrichmentService(
        CachedCatalogProvider(catalog=catalog),
        recommendation_provider,
    )
    payloads = JsonPayloadService(
        compressor=GzipCompressor(max_output_size=64 * 1024),
        max_encoded_size=128 * 1024,
        max_compressed_size=64 * 1024,
        max_serialized_size=64 * 1024,
        max_nesting_depth=16,
    )
    service = OrderBackendService(
        intake=OrderIntakeService(logger),
        enrichment=enrichment,
        catalog=catalog,
        payloads=payloads,
        logger=logger,
        batch_size=50,
        concurrency_limit=4,
        provider_timeout=1.0,
    )
    return OrderBackendApplication(
        service=service,
        logger=logger,
        request_timeout=2.0,
        shutdown_grace_timeout=1.0,
        shutdown_cancel_timeout=1.0,
    )
```

Do not expose configuration overrides or inspect cache private fields; each
owning constructor validates the root's fixed values. Prove sharing by processing
two commands and observing `await application.cache_stats()`.

- [x] **Step 5.2: Implement the exact fixed root**

Use `AsyncTTLCache(default_ttl=60, max_size=128)`, aggregate batch size `50`,
provider concurrency `4`, provider timeout `1.0`, request timeout `2.0`, grace
timeout `1.0`, cancellation timeout `1.0`, and
`GzipCompressor(max_output_size=64 * 1024)` with encoded `128 * 1024`, compressed
`64 * 1024`, serialized `64 * 1024`, and nesting depth `16`. Keep overrides
keyword-only and test-only where injection is required. No global cache or app.

- [x] **Step 5.3: Write failing exact CLI event tests**

Capture stdout and require exactly five compact, sorted JSON lines in this
order:

```python
assert [event["event"] for event in events] == [
    "backend_started",
    "order_processed",
    "order_processed",
    "cache_stats",
    "backend_stopped",
]
assert events[1]["line_count"] == 3
assert events[2]["line_count"] == 2
assert events[1]["total_cents"] == 45_400
assert events[2]["total_cents"] == 31_700
assert events[1]["warning_count"] == events[2]["warning_count"] == 1
assert {
    "event",
    "order_id",
    "line_count",
    "total_cents",
    "warning_count",
    "artifact_format",
    "trust_profile",
    "compression",
    "encoding",
    "encoded_size",
} == set(events[1]) == set(events[2])
assert events[3] == {
    "event": "cache_stats",
    "hits": 1,
    "misses": 3,
    "loads": 3,
    "load_failures": 0,
    "inflight_loads": 0,
    "abandoned_loads": 0,
}
assert all("data" not in event and "recommendation" not in event for event in events)
```

- [x] **Step 5.4: Implement the realistic two-order scenario**

The first order has `SKU-1 x2`, `SKU-2 x1`, and duplicate `SKU-1 x1`; the
second has cached `SKU-2 x2` and new `SKU-3 x1`. Use fixed in-memory product and
recommendation providers. Fix prices at `SKU-1=12_500`, `SKU-2=7_900`, and
`SKU-3=15_900`, and provide optional recommendations for `SKU-1` and `SKU-3`
only, producing one missing-record warning per order. Emit order ID, line count,
total, warning count,
artifact format/trust/compression/encoding, and encoded size, but never artifact
data, product names, recommendations, or provider exception text. Enter one
application context, process both orders sequentially, emit public stats, exit,
then emit `backend_stopped`. Keep the runnable surface exact:

```python
_PRODUCTS = {
    "SKU-1": ("Mechanical Keyboard", 12_500),
    "SKU-2": ("Vertical Mouse", 7_900),
    "SKU-3": ("USB-C Dock", 15_900),
}
_RECOMMENDATIONS = {
    "SKU-1": "PAIR-SKU-9",
    "SKU-3": "PAIR-SKU-8",
}


async def _catalog_loader(product_id: str) -> ProductSummary:
    name, price_cents = _PRODUCTS[product_id]
    return ProductSummary(
        product_id=product_id,
        name=name,
        price_cents=price_cents,
    )


class _RecommendationProvider:
    async def fetch(
        self,
        product_ids: tuple[str, ...],
    ) -> Mapping[str, RecommendationRecord]:
        return {
            product_id: RecommendationRecord(
                product_id=product_id,
                recommendation=_RECOMMENDATIONS[product_id],
            )
            for product_id in product_ids
            if product_id in _RECOMMENDATIONS
        }


def _emit(event: dict[str, object]) -> None:
    print(json.dumps(event, sort_keys=True, separators=(",", ":")))


def _order_event(order: ProcessedOrder) -> dict[str, object]:
    return {
        "event": "order_processed",
        "order_id": order.order_id,
        "line_count": len(order.lines),
        "total_cents": order.total_cents,
        "warning_count": sum(len(line.warnings) for line in order.lines),
        "artifact_format": order.artifact.metadata.format,
        "trust_profile": order.artifact.metadata.trust_profile.value,
        "compression": order.artifact.compression,
        "encoding": order.artifact.encoding,
        "encoded_size": len(order.artifact.data),
    }


async def _run_scenario() -> None:
    logger = logging.Logger("integrated-order-backend", level=logging.CRITICAL)
    application = build_application(
        logger=logger,
        catalog_loader=_catalog_loader,
        recommendation_provider=_RecommendationProvider(),
    )
    first = OrderBackendCommand(
        request_id="req-1001",
        partner_id="partner-7",
        order_id="order-9001",
        lines=(
            OrderLineCommand(sku="SKU-1", quantity=2),
            OrderLineCommand(sku="SKU-2", quantity=1),
            OrderLineCommand(sku="SKU-1", quantity=1),
        ),
    )
    second = OrderBackendCommand(
        request_id="req-1002",
        partner_id="partner-7",
        order_id="order-9002",
        lines=(
            OrderLineCommand(sku="SKU-2", quantity=2),
            OrderLineCommand(sku="SKU-3", quantity=1),
        ),
    )
    _emit({"event": "backend_started"})
    async with application:
        _emit(_order_event(await application.process(first)))
        _emit(_order_event(await application.process(second)))
        stats = await application.cache_stats()
        _emit(
            {
                "event": "cache_stats",
                "hits": stats.hits,
                "misses": stats.misses,
                "loads": stats.loads,
                "load_failures": stats.load_failures,
                "inflight_loads": stats.inflight_loads,
                "abandoned_loads": stats.abandoned_loads,
            }
        )
    _emit({"event": "backend_stopped"})


def main() -> None:
    asyncio.run(_run_scenario())


if __name__ == "__main__":
    main()
```

- [x] **Step 5.5: Observe GREEN, run the CLI, and commit**

Run:

```bash
uv run --locked pytest examples/integrated_order_backend/tests/test_composition.py \
  examples/integrated_order_backend/tests/test_cli.py -q
uv run --locked python -m examples.integrated_order_backend
```

Expected: exact five events, miss then hit, clean shutdown, and no stderr.
Commit with a Lore message preserving one application/cache lifetime across the
scenario.

## Task 6: Write the Bilingual Example Guide and Source-Backed Diagrams

**Complexity:** High documentation/visual proof. **Depends on:** implemented
Tasks 1-5. **Write scope:** example README pair, assets, and doc tests.

**Files:**

- Create: `examples/integrated_order_backend/README.md`
- Create: `examples/integrated_order_backend/README.ko.md`
- Create: `examples/integrated_order_backend/tests/test_documentation.py`
- Create: `examples/integrated_order_backend/docs/images/architecture.svg`
- Create: `examples/integrated_order_backend/docs/images/architecture.png`
- Create: `examples/integrated_order_backend/docs/images/sequence.svg`
- Create: `examples/integrated_order_backend/docs/images/sequence.png`

- [x] **Step 6.1: Load `bluetape-writer` and `bluetape-diagram` before edits**

Follow reciprocal locale navigation, meaning parity, source-backed labels,
scale-2 rendering, geometry audits, and full-size visual inspection. Create
assets only from the implemented source; both locales share English-label
assets.

- [x] **Step 6.2: Write failing documentation tests**

Require exact locale headers, Scenario, Architecture, Sequence Diagram,
aggregate invariants, existing service links, cache ownership, duplicate order,
optional warnings, untrusted JSON, timeout/cancellation/shared shutdown,
identifier privacy/retention, sequential-read performance caveat, Fory as a
separate trusted-internal example, exact run/test commands, troubleshooting,
production non-goals, best-effort application lifecycle telemetry, source
paths, direct PNG embeds, SVG links, and all four asset files.

- [x] **Step 6.3: Observe RED and write both README files together**

Run the focused documentation test and expect missing files. Add equivalent
English/Korean sections with exact setup, working directory, CLI output schema,
targeted tests, no cleanup requirement, provider/cache/payload ownership,
deadline and close behavior, unsupported HTTP/auth/persistence/retry/telemetry,
and production adapter obligations for identifier bounds/privacy/authorization.

- [x] **Step 6.4: Create Architecture SVG from implemented ownership**

Show CLI/caller, `OrderBackendApplication`, `OrderBackendService`,
`OrderIntakeService`, `CatalogEnrichmentService`, `CachedCatalogProvider`,
`AsyncProductCatalogService`, caller-owned `AsyncTTLCache`, required/optional
providers, and `JsonPayloadService`. Distinguish ownership from call/data arrows
and label the untrusted JSON boundary.

- [x] **Step 6.5: Create Sequence SVG from implemented behavior**

Show one multi-line success with validation-before-I/O, distinct-SKU cache
loads, occurrence restoration, warnings, totals, and encoding. Include clearly
separated alternate branches for invalid input, optional provider warning,
overall timeout/caller cancellation, and stop/grace/cancel/shutdown failure.

- [x] **Step 6.6: Render, audit, inspect, and observe GREEN**

For each SVG run `xmllint --noout`, CairoSVG scale-2 rendering, connector,
geometry, endpoint, mixed-corner, and sequence-style audits from the installed
diagram skill. Inspect both full-size PNGs for clipping, overlap, unreadable
labels, and branch ambiguity. Run documentation tests and require PASS.

- [x] **Step 6.7: Commit aligned docs and visuals**

Run focused docs tests, Ruff, and `git diff --check`; commit with a Lore
directive that every example README locale must continue to embed both diagrams
and link their SVG sources.

## Task 7: Register Root Discovery and the Live Issue Checkpoint

**Complexity:** Medium docs. **Depends on:** Task 6. **Write scope:** root
README pair, discovery test, and WIP.

**Files:**

- Modify: `README.md`
- Modify: `README.ko.md`
- Modify: `tests/test_documentation_contract.py`
- Modify: `WIP.md`

- [x] **Step 7.1: Write failing root discovery assertions**

Require both root locales to link `examples/integrated_order_backend`, preserve
the existing five examples, name the integrated CLI and targeted test commands,
and automatically require the new README pair plus four diagram assets.

- [x] **Step 7.2: Observe RED and update both root README files together**

Add Issue #8 as the composed milestone outcome, explain that Redis/Fory remain
separate optional examples, and include:

```bash
uv run --locked python -m examples.integrated_order_backend
uv run --locked pytest examples/integrated_order_backend/tests -q
```

- [x] **Step 7.3: Update WIP to the Issue #8 implementation gate**

Replace stale Issue #7 status with exact Issue #8 branch/base, approved spec,
design review, plan/risk/review paths, focused commands, current validation
counts, exclusions, and next gate. Record PR as `Not created` until live and do
not claim CI/merge evidence early.

- [x] **Step 7.4: Observe GREEN and commit**

Run root/example documentation tests and diff check. Expected: bilingual root
discovery and mandatory diagram contract pass. Commit with a Lore message
preserving the milestone learning path.

## Task 8: Verify, Review, Capture the Lesson, and Deliver the Exact PR Head

**Complexity:** High verification/delivery. **Depends on:** Tasks 1-7. **Write
scope:** review, lesson, final WIP/plan checkboxes, PR metadata only.

**Files:**

- Create: `docs/superpowers/reviews/2026-07-16-issue-8-implementation-review.md`
- Create: `docs/superpowers/lessons/2026-07-16-issue-8-composition-lifecycle.md`
- Modify: `docs/superpowers/plans/2026-07-16-issue-8-integrated-order-backend-plan.md`
- Modify: `WIP.md`

- [x] **Step 8.1: Run focused then full deterministic validation**

Run sequentially:

```bash
uv --version
uv sync --locked --python 3.13.14
uv run --locked pytest examples/integrated_order_backend/tests -q
uv run --locked pytest tests/test_dependency_baseline.py -q
uv run --locked ruff format --check .
uv run --locked ruff check .
uv run --locked pytest -m "not testcontainers"
GOTOOLCHAIN=go1.26.1 go run github.com/rhysd/actionlint/cmd/actionlint@v1.7.12 \
  .github/workflows/ci.yml
git diff --check
```

Expected: uv 0.11.28, Python 3.13.14 environment, focused/full tests pass with
only the existing optional Fory skip/deselection behavior, Ruff/actionlint/diff
pass, and no Docker contact.

- [x] **Step 8.2: Prove dependency, scope, task, and payload invariants**

Run:

```bash
git diff --exit-code origin/develop -- pyproject.toml uv.lock .github/workflows/ci.yml
git diff --name-only origin/develop
rg -n "create_task|asyncio\.wait|asyncio\.shield|asyncio\.timeout|except BaseException|sleep\(" \
  examples/integrated_order_backend
uv run --locked python -m examples.integrated_order_backend
```

Expected: authority files unchanged; only planned files differ; task creation is
confined to request/close ownership; no `BaseException` catch or real sleep;
five safe CLI events with cache `hits=1`, `misses=3`, `loads=3`.

- [x] **Step 8.3: Run diagram and performance/stability verification**

Repeat XML/render/audit/full-size inspection on both final source-backed assets.
Read the Type A performance/stability checklist and verify 100-line bounds,
distinct-SKU provider work, fixed task cardinality, finite waits, late exception
observation, cache cleanup, payload limits, and no blocking call on the event
loop. Fix P0/P1 and rerun affected tests. Record benchmark execution as N/A with
evidence: the example makes no throughput/latency claim, caps each order at 100
lines, and deliberately documents sequential cache-backed reads rather than
optimizing them.

- [x] **Step 8.4: Run final six-perspective implementation review**

Review the exact branch diff independently for performance, stability,
security, operator/Ops, developer/API, and user/caller. Reclaim delayed agents
immediately and complete missing lenses in the main session. Integrate findings
in the review artifact; fix and rerun affected proof until P0=0/P1=0. Resolve or
file every P2/P3.

- [x] **Step 8.5: Verify exact spec/plan coverage and capture the lesson**

Load `verification-before-completion` and the Type A verifier checklist. Map
every acceptance row to fresh output and require PASS. Record the reusable
lesson: application-level composition should preserve focused service contracts
while one outer lifecycle owns deadlines, task observation, and shutdown. Include
the admission race and cancellation-resistant cleanup surprise plus its future
guard.

- [x] **Step 8.6: Commit the final local evidence and rerun at exact head**

Update checkboxes and WIP only from observed evidence. Commit review, lesson,
and checkpoint with a Lore message, then rerun the focused tests, full
deterministic lane, Ruff, actionlint, diagram checks, and diff check at resulting
HEAD.

- [x] **Step 8.7: Push and create the approved PR**

Push `feat/issue-8-integrated-order-backend` and create an English PR into
`develop`, assigned to `debop`, with milestone `0.1.0`, relevant labels,
`Closes #8`, validation/diagram evidence, production non-goals, and final
`## DoD Status`. Do not enable auto-merge.

- [ ] **Step 8.8: Verify exact-head CI and current review state**

Pin the live PR head SHA; verify remote SHA equality, required CI success,
mergeability, current reviews, unresolved threads, and human-inspection evidence
for both PNGs. Any head change invalidates prior hosted evidence and requires
proportional local revalidation plus refreshed PR DoD.

- [ ] **Step 8.9: Stop for fresh merge approval**

Report PR URL, exact head, commits, changed files, test counts, diagram audit and
inspection, CI/review state, lesson, residual risks, and P0=0/P1=0. Leave merge,
auto-merge, milestone closure, and remote branch deletion untouched until a new
explicit approval.

## Triggered Risk Prediction

This plan triggers Step 3-P because it introduces async task ownership,
cancellation-resistant work, cache sharing, provider failures, serialization,
and lifecycle state. The detailed risk record is
`docs/superpowers/risks/2026-07-16-issue-8-integrated-order-backend-risk.md`.
Tasks 3, 4, 5, 6, and 8 contain the corresponding signals, mitigations, and
rerun points. No database, migration, dependency, Docker, native/JNI, module,
publish, or production deployment hazard is triggered.

## Rollback

Before PR creation, revert only the current task's commit and retain/rewrite its
failing test while repairing a boundary. After PR creation, use additive repair
commits. Full rollback removes the additive integrated example, root navigation,
WIP checkpoint, diagrams, tests, review/risk/lesson artifacts, and nothing else:
no dependency, lockfile, existing example, library API, persisted schema,
external service, release, or deployment is migrated.
