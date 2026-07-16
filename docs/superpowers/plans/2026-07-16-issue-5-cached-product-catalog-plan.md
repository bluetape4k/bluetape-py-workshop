# Cached Product Catalog Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> `subagent-driven-development` (recommended) or `executing-plans` to implement
> this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build independently runnable sync and async product-catalog services
that demonstrate the pinned `bluetape-cache` hit, miss, expiry, LRU capacity,
loader failure, coalescing, and cancellation contracts.

**Architecture:** `SyncProductCatalogService` and
`AsyncProductCatalogService` share immutable models and key normalization but
use the exact matching `TTLCache` and `AsyncTTLCache` APIs. The composition root
owns caches, clocks, loaders, and the event loop; the services delegate through
public cache methods without a workshop cache abstraction or global state.

**Tech Stack:** Python 3.13.14, uv 0.11.28, `bluetape-core`,
`bluetape-cache`, `bluetape-testing`, pytest 8.4.2, pytest-asyncio 1.4.0,
Ruff 0.12.12, SVG/CairoSVG diagram workflow.

---

## Execution Contract

- Repository: `bluetape4k/bluetape-py-workshop`
- Base: `develop`
- Head: `feat/issue-5-cached-product-catalog`
- Worktree:
  `/Users/debop/work/bluetape4k/bluetape-py-workshop/.worktrees/feat-issue-5-cached-product-catalog`
- Issue: <https://github.com/bluetape4k/bluetape-py-workshop/issues/5>
- Approved spec:
  `docs/superpowers/specs/2026-07-16-issue-5-cached-product-catalog-design.md`
- Spec review:
  `docs/superpowers/reviews/2026-07-16-issue-5-design-review.md`
- Workflow type: Type A
- Heavy-command limit: one repository-wide pytest or actionlint process at a
  time; Docker and Testcontainers are not triggered.
- Side effects authorized by plan approval: local edits, Lore commits, push of
  the exact head branch, and PR creation into `develop` with issue #5 metadata.
- Side effects not authorized: merge, auto-merge, remote branch deletion, tag,
  release, publish, workflow dispatch, milestone closure, or dependency update.
- Stop boundary: report the exact PR head as merge-ready after CI and current
  review; wait for fresh explicit merge approval.

## File Map

| Path | Responsibility |
|---|---|
| `examples/cached_product_catalog/models.py` | Immutable `ProductSummary` |
| `examples/cached_product_catalog/providers.py` | Sync and async callable loader protocols |
| `examples/cached_product_catalog/service.py` | Key normalization and separate sync/async application services |
| `examples/cached_product_catalog/__init__.py` | Deliberate public example exports |
| `examples/cached_product_catalog/__main__.py` | Deterministic sync/async JSON scenario |
| `examples/cached_product_catalog/tests/test_service.py` | Validation, cache behavior, stats, concurrency, cancellation, cleanup |
| `examples/cached_product_catalog/tests/test_application.py` | Module entry-point JSON contract |
| `examples/cached_product_catalog/tests/test_documentation.py` | Locale, commands, source, and diagram contract |
| `examples/cached_product_catalog/README.md` | English reader path |
| `examples/cached_product_catalog/README.ko.md` | Equivalent Korean reader path |
| `examples/cached_product_catalog/docs/images/architecture.svg` | Source-backed ownership/component view |
| `examples/cached_product_catalog/docs/images/architecture.png` | Authoritative rendered Architecture image |
| `examples/cached_product_catalog/docs/images/sequence.svg` | Source-backed sync/async lifecycle view |
| `examples/cached_product_catalog/docs/images/sequence.png` | Authoritative rendered Sequence image |
| `tests/test_documentation_contract.py` | Root auto-discovery and navigation contract |
| `README.md`, `README.ko.md` | Bilingual workshop navigation and current status |
| `WIP.md` | Issue #5 checkpoint, evidence, and next action |
| `docs/superpowers/reviews/2026-07-16-issue-5-implementation-review.md` | Final six-lens review evidence |
| `docs/superpowers/lessons/2026-07-16-issue-5-local-cache-ownership.md` | Required Type A reusable lesson |

No dependency, lockfile, workflow, package, or existing example source file is
modified.

## Acceptance Traceability

| Spec requirement | Plan tasks | Proof |
|---|---|---|
| Separate injected sync/async services | 1, 2, 3 | public-shape and service tests |
| Immutable normalized product values | 1 | model/validation tests |
| Hit, miss, expiry, LRU, failure recovery, caller value preservation | 2, 3 | exact stats and identity assertions |
| Async shared loading and partial waiter cancellation | 3 | event-driven two-caller tests |
| Last-waiter cancellation and terminal task cleanup | 4 | events, gauges, named-task scan |
| Deterministic runnable CLI | 5 | subprocess JSON test and direct run |
| Bilingual README and mandatory diagrams | 6 | documentation tests and diagram audit ledger |
| Root navigation and WIP checkpoint | 7 | root documentation contract |
| Full validation, P0/P1 convergence, lesson, PR, CI | 8 | exact commands, review artifact, live PR evidence |

## Task 1: Lock Public Contracts and Key Validation

**Complexity:** Medium

**Depends on:** approved spec commit `eecd73b`

**Files:**

- Create: `examples/cached_product_catalog/__init__.py`
- Create: `examples/cached_product_catalog/models.py`
- Create: `examples/cached_product_catalog/providers.py`
- Create: `examples/cached_product_catalog/service.py`
- Create: `examples/cached_product_catalog/tests/__init__.py`
- Create: `examples/cached_product_catalog/tests/test_service.py`

**Patterns:** `test-driven-development`, `bluetape-py-patterns`

- [ ] **Step 1.1: Create the test package and write failing public-shape tests**

Create `examples/cached_product_catalog/tests/__init__.py` as an empty package
marker, then add these initial contracts to `test_service.py`:

```python
from dataclasses import FrozenInstanceError

import pytest

from examples.cached_product_catalog import (
    AsyncProductCatalogService,
    ProductSummary,
    SyncProductCatalogService,
)


def test_product_summary_is_keyword_only_frozen_and_slotted() -> None:
    product = ProductSummary(product_id="SKU-1", name="Keyboard", price_cents=12_500)
    assert product.product_id == "SKU-1"
    assert not hasattr(product, "__dict__")
    with pytest.raises(FrozenInstanceError):
        product.name = "changed"  # type: ignore[misc]
    with pytest.raises(TypeError):
        ProductSummary("SKU-1", "Keyboard", 12_500)  # type: ignore[misc]


def test_services_expose_only_the_approved_application_methods() -> None:
    assert {
        name for name in vars(SyncProductCatalogService) if not name.startswith("_")
    } == {"get_product", "stats"}
    assert {
        name for name in vars(AsyncProductCatalogService) if not name.startswith("_")
    } == {"get_product", "stats"}
```

- [ ] **Step 1.2: Run the public-shape tests and observe RED**

Run:

```bash
uv run --locked pytest \
  examples/cached_product_catalog/tests/test_service.py \
  -q
```

Expected: collection fails because `examples.cached_product_catalog` and its
exports do not exist.

- [ ] **Step 1.3: Implement the immutable model, loader protocols, and exports**

Create `models.py`:

```python
from dataclasses import dataclass


@dataclass(frozen=True, slots=True, kw_only=True)
class ProductSummary:
    product_id: str
    name: str
    price_cents: int
```

Create `providers.py`:

```python
from typing import Protocol

from .models import ProductSummary


class SyncProductLoader(Protocol):
    def __call__(self, product_id: str) -> ProductSummary: ...


class AsyncProductLoader(Protocol):
    async def __call__(self, product_id: str) -> ProductSummary: ...
```

Create skeletal services with the exact approved constructors and methods.
Use `TTLCache[str, ProductSummary]`, `AsyncTTLCache[str, ProductSummary]`, and
`CacheStats` directly. Do not create a cache protocol.

Create `__init__.py` with only these exports:

```python
from .models import ProductSummary
from .providers import AsyncProductLoader, SyncProductLoader
from .service import AsyncProductCatalogService, SyncProductCatalogService

__all__ = [
    "ProductSummary",
    "SyncProductLoader",
    "AsyncProductLoader",
    "SyncProductCatalogService",
    "AsyncProductCatalogService",
]
```

- [ ] **Step 1.4: Run the public-shape tests and observe GREEN**

Run the Step 1.2 command.

Expected: public-shape tests pass; behavior tests do not exist yet.

- [ ] **Step 1.5: Write failing key-normalization tests**

Add a `ManualClock` and recording sync/async loaders. Parametrize:

- `" sku-1 " -> "SKU-1"`;
- non-string input;
- `""` and whitespace;
- 65 characters;
- non-ASCII text; and
- grammar-invalid `/` or whitespace inside the ID.

For every invalid value, assert the loader call count remains zero and cache
stats remain at zero hits, misses, and loads. Apply the same cases to both
services.

- [ ] **Step 1.6: Run normalization tests and observe RED**

Run:

```bash
uv run --locked pytest \
  examples/cached_product_catalog/tests/test_service.py \
  -q -k 'normaliz or invalid or blank'
```

Expected: FAIL because normalization and validation are not implemented.

- [ ] **Step 1.7: Implement `_normalize_product_id` and minimal delegation**

In `service.py`, use the current workshop boundary:

```python
import re

from bluetape.core import require_instance, require_not_blank

MAX_PRODUCT_ID_LENGTH = 64
_PRODUCT_ID = re.compile(r"[A-Z0-9][A-Z0-9._-]*\Z")


def _normalize_product_id(value: object) -> str:
    product_id = require_not_blank(
        require_instance(value, str, "product_id"),
        "product_id",
    ).strip().upper()
    if len(product_id) > MAX_PRODUCT_ID_LENGTH:
        raise ValueError(
            f"product_id must contain at most {MAX_PRODUCT_ID_LENGTH} characters"
        )
    if not product_id.isascii() or _PRODUCT_ID.fullmatch(product_id) is None:
        raise ValueError("product_id must use ASCII SKU characters")
    return product_id
```

`SyncProductCatalogService.get_product` calls
`cache.get_or_load(normalized, loader)` exactly once. The async service awaits
the matching public call exactly once. Stats delegate to the public cache
snapshot methods.

- [ ] **Step 1.8: Run the complete Task 1 tests and observe GREEN**

Run:

```bash
uv run --locked pytest examples/cached_product_catalog/tests/test_service.py -q
uv run --locked ruff check examples/cached_product_catalog
```

Expected: all Task 1 tests pass; Ruff reports no findings.

- [ ] **Step 1.9: Commit the public contracts**

Use a Lore commit whose intent records why sync and async remain separate.
Stage only Task 1 files. `Tested:` names the exact focused pytest and Ruff
commands. `Not-tested:` states that cache lifecycle cases are assigned to
Tasks 2–4.

## Task 2: Prove Synchronous Cache Lifecycle

**Complexity:** Medium

**Depends on:** Task 1

**Files:**

- Modify: `examples/cached_product_catalog/tests/test_service.py`
- Modify only if the RED test requires it:
  `examples/cached_product_catalog/service.py`

**Patterns:** `test-driven-development`, `bluetape-py-patterns`

- [ ] **Step 2.1: Write failing sync miss/hit and identity tests**

Construct `TTLCache(default_ttl=10, max_size=2, clock=manual_clock)`. Assert:

1. first `get_product("sku-1")` invokes the loader once;
2. second call does not invoke it again;
3. both results are the exact same `ProductSummary` object; and
4. stats equal `misses=1`, `loads=1`, `hits=1`, with zero failures,
   evictions, and expirations.

- [ ] **Step 2.2: Run the new sync test and observe RED or exact GREEN**

Run:

```bash
uv run --locked pytest \
  examples/cached_product_catalog/tests/test_service.py::test_sync_miss_then_hit_preserves_identity_and_stats \
  -q
```

Expected: RED if Task 1 delegation is incomplete. If it is already GREEN, read
the assertion output and record that Task 1's minimal implementation already
satisfies the behavior; do not add duplicate code.

- [ ] **Step 2.3: Add the exact TTL-boundary RED test**

Load with a 10ns TTL using `ttl=10e-9` on the cache or a 10ns default TTL.
Assert a hit at 9ns and a reload at 10ns. Verify identity changes only after
expiry and stats equal one expiration, two loads, two misses, and one hit.

- [ ] **Step 2.4: Run the TTL test and observe GREEN from the public cache**

Run the exact TTL test node. Expected: PASS without service changes. A failure
means the plan or pinned dependency contract must be reopened; do not emulate
TTL behavior in the service.

- [ ] **Step 2.5: Add LRU eviction, failure recovery, and caller-set tests**

Add three focused tests:

- load A and B, hit A, then load C; assert B is the evicted key and the next B
  call reloads;
- loader raises a sentinel `LookupError` once, then returns a product; assert
  original exception identity, `load_failures=1`, and later success;
- call `cache.set("SKU-1", caller_value)`, then use the service; assert exact
  caller object identity and zero loader calls.

- [ ] **Step 2.6: Run all synchronous behavior tests**

Run:

```bash
uv run --locked pytest \
  examples/cached_product_catalog/tests/test_service.py \
  -q -k 'sync and not async'
```

Expected: PASS. If a public cache contract fails, stop and record an upstream
source mismatch rather than adding a workshop cache shim.

- [ ] **Step 2.7: Commit the sync lifecycle proof**

Stage only `test_service.py` and any strictly required service correction.
The Lore commit records that the service delegates rather than reproducing
cache behavior.

## Task 3: Prove Async Loading, Coalescing, and Partial Cancellation

**Complexity:** High

**Depends on:** Task 1

**Files:**

- Modify: `examples/cached_product_catalog/tests/test_service.py`
- Modify only on service-contract failure:
  `examples/cached_product_catalog/service.py`

**Patterns:** `test-driven-development`, `bluetape-py-patterns`

- [ ] **Step 3.1: Write async miss/hit, identity, expiry, eviction, failure, and caller-set tests**

Mirror Task 2 through public async methods. Keep one `AsyncTTLCache` inside one
pytest event loop. Await `stats()` and `size()` where required. Use the same
9ns/10ns TTL boundary and exact counter assertions.

- [ ] **Step 3.2: Run the basic async tests**

Run:

```bash
uv run --locked pytest \
  examples/cached_product_catalog/tests/test_service.py \
  -q -k 'async and not coalesc and not cancel'
```

Expected: PASS through the pinned public cache. Any event-loop reuse failure is
a test-fixture defect; create each cache inside its test's running loop.

- [ ] **Step 3.3: Write an event-driven shared-success RED test**

Use `loader_started` and `release_loader` events. Start two tasks for the same
normalized key before releasing the loader. Assert:

- one loader call;
- both callers receive the same object;
- `loads=1`, `coalesced_waiters=1`, `misses=2`; and
- `inflight_loads=0` after terminal completion.

- [ ] **Step 3.4: Run the shared-success test**

Expected: PASS through `AsyncTTLCache`. Do not add coalescing to the service.

- [ ] **Step 3.5: Write shared-failure and one-waiter-cancelled tests**

For shared failure, both same-key callers receive the same sentinel exception
object, one loader runs, and `load_failures=1`. A later call with a recovered
loader succeeds.

For partial cancellation, start two same-key callers, cancel one after the
loader starts, assert that caller receives `CancelledError`, release the
loader, and assert the surviving caller receives the product. Confirm the
loader was not cancelled and no named `bluetape-cache-*` task remains after
terminal completion.

- [ ] **Step 3.6: Run all async coalescing tests**

Run:

```bash
uv run --locked pytest \
  examples/cached_product_catalog/tests/test_service.py \
  -q -k 'coalesc or shared or surviving'
```

Expected: PASS with no long sleep. All coordination is event-driven and every
created caller task is awaited in `finally` cleanup.

- [ ] **Step 3.7: Commit the async shared-loading proof**

Stage the focused tests and any exact service correction. Lore trailers name
event-driven proof and the remaining last-waiter cancellation task.

## Task 4: Prove Last-Waiter Cancellation and Terminal Cleanup

**Complexity:** High

**Depends on:** Task 3

**Files:**

- Modify: `examples/cached_product_catalog/tests/test_service.py`

**Patterns:** `test-driven-development`, `bluetape-py-patterns`

- [ ] **Step 4.1: Add a named cache-task scanner**

```python
def _cache_tasks() -> list[asyncio.Task[object]]:
    current = asyncio.current_task()
    return [
        task
        for task in asyncio.all_tasks()
        if task is not current and task.get_name().startswith("bluetape-cache-")
    ]
```

Use this only for terminal leak evidence. Do not inspect private cache fields.

- [ ] **Step 4.2: Write the last-waiter cancellation test**

The loader sets `started`, then awaits forever. On `CancelledError`, it sets
`cancellation_seen`, awaits `release_cleanup`, and re-raises. Test order:

1. start the service caller and await `started`;
2. cancel the caller and gather its `CancelledError`;
3. await `cancellation_seen`;
4. assert `inflight_loads=1` and `abandoned_loads=1` while cleanup is held;
5. set `release_cleanup`;
6. use `bluetape.testing.eventually_async` only for the bounded terminal stats
   probe;
7. assert both gauges are zero and `_cache_tasks()` is empty.

Use a one-second outer timeout only to fail a broken test; do not use timing as
the synchronization signal.

- [ ] **Step 4.3: Run the cancellation test and inspect RED/GREEN honestly**

Run:

```bash
uv run --locked pytest \
  examples/cached_product_catalog/tests/test_service.py::test_async_last_waiter_cancellation_exposes_then_cleans_abandoned_load \
  -q
```

Expected: PASS through the pinned cache. If it fails, inspect whether the test
incorrectly assumes immediate cleanup before changing service code.

- [ ] **Step 4.4: Run the entire service suite repeatedly**

Run the focused service suite three times sequentially, not in parallel:

```bash
for run in 1 2 3; do
  uv run --locked pytest examples/cached_product_catalog/tests/test_service.py -q
done
```

Expected: identical PASS counts and no pending-task warnings on every run.
Retry-only success is a stability finding and must be diagnosed.

- [ ] **Step 4.5: Run the performance/stability scan**

Load `bluetape-full-feature/references/performance-stability-scan.md`. Confirm:

- services add no lock, task, copy, retry, logging, or cache operation;
- all event-driven tasks are awaited;
- capacity and inflight bounds remain cache-owned;
- CLI uses no blocking call inside async code; and
- no benchmark is required because the implementation delegates once to the
  already-bounded package and introduces no hot-path loop.

Record exact P0/P1 counts.

- [ ] **Step 4.6: Commit the cancellation and stability proof**

The Lore intent records why caller return and loader terminal cleanup are
distinct. `Tested:` includes the three sequential focused runs.

## Task 5: Build the Deterministic Module Entry Point

**Complexity:** Medium

**Depends on:** Tasks 2–4

**Files:**

- Create: `examples/cached_product_catalog/__main__.py`
- Create: `examples/cached_product_catalog/tests/test_application.py`

**Patterns:** `test-driven-development`, `bluetape-py-patterns`

- [ ] **Step 5.1: Write a failing subprocess JSON contract test**

Run the module with the current interpreter from repository root. Parse every
non-empty stdout line as JSON. Assert a fixed ordered event list covering:

- `sync_miss`, `sync_hit`, `sync_expired_reload`, `sync_eviction`;
- `sync_loader_failed`, `sync_recovered`;
- `async_miss`, `async_hit`; and
- `sync_stats`, `async_stats`.

Value events contain `event`, `mode`, normalized `product_id`, `name`, and
`price_cents`. Failure output contains only `error_code="loader_unavailable"`.
Stats output uses public `CacheStats` field names. Assert stderr is empty.

- [ ] **Step 5.2: Run the application test and observe RED**

Run:

```bash
uv run --locked pytest \
  examples/cached_product_catalog/tests/test_application.py \
  -q
```

Expected: FAIL because `__main__.py` does not exist.

- [ ] **Step 5.3: Implement the deterministic scenario**

Create a private manual clock, immutable in-memory product mapping, recording
sync/async loaders, and one `main()` that runs the sync scenario then one
`asyncio.run(_run_async_scenario())`. Serialize dataclasses with an explicit
safe mapping; do not print reprs or raw exceptions.

Use a controlled loader-failure flag rather than retry logic. Advance only the
manual clock. Do not call `time.sleep`, `asyncio.sleep` for behavior, network,
Docker, or environment credentials.

- [ ] **Step 5.4: Run module and application tests**

```bash
uv run --locked python -m examples.cached_product_catalog
uv run --locked pytest examples/cached_product_catalog/tests/test_application.py -q
```

Expected: deterministic JSON and PASS.

- [ ] **Step 5.5: Commit the runnable scenario**

Stage only `__main__.py` and `test_application.py`. Lore trailers record the
safe output boundary and that cancellation remains a focused test/README path.

## Task 6: Create Bilingual README Files and Required Diagrams

**Complexity:** High

**Depends on:** source implementation and CLI from Tasks 1–5

**Files:**

- Create: `examples/cached_product_catalog/README.md`
- Create: `examples/cached_product_catalog/README.ko.md`
- Create: `examples/cached_product_catalog/docs/images/architecture.svg`
- Create: `examples/cached_product_catalog/docs/images/architecture.png`
- Create: `examples/cached_product_catalog/docs/images/sequence.svg`
- Create: `examples/cached_product_catalog/docs/images/sequence.png`
- Create: `examples/cached_product_catalog/tests/test_documentation.py`

**Patterns:** `bluetape-writer`, `bluetape-diagram`

- [ ] **Step 6.1: Write failing bilingual documentation tests**

Require reciprocal locale navigation, Scenario, Architecture, Sequence
Diagram, exact module/test commands, exact imports, source filenames, cache
lifecycle terms, loop binding, key sensitivity, stats semantics, and the four
diagram paths in both locales. Assert every asset exists.

- [ ] **Step 6.2: Run documentation tests and observe RED**

```bash
uv run --locked pytest \
  examples/cached_product_catalog/tests/test_documentation.py \
  -q
```

Expected: FAIL because the README and asset files do not exist.

- [ ] **Step 6.3: Draft aligned English and Korean README files**

Follow the established example structure:

1. locale navigation;
2. Scenario and explicit non-goals;
3. Architecture embed and ownership explanation;
4. Sequence embed and lifecycle explanation;
5. exact `bluetape-cache`, `bluetape-core`, and `bluetape-testing` APIs;
6. prerequisites and root working directory;
7. run command and representative deterministic JSON;
8. focused test command;
9. hit/miss/expiry/eviction/failure/cancellation interpretation;
10. entry-count, event-loop, key-context, value-identity, safe-logging, and
    unsupported Redis/distributed boundaries; and
11. no cleanup command beyond process exit because all state is local and
    caller-owned.

Use the same English-label images in both locales. Korean prose must be natural
engineer-to-engineer writing, not literal translation.

- [ ] **Step 6.4: Create and validate the Architecture asset**

Load `bluetape-diagram/references/common.md` and `architecture.md`. Model only
implemented source:

- caller/composition root;
- separate sync/async services;
- caller-owned sync/async caches;
- injected loaders and clock;
- immutable `ProductSummary`; and
- public `CacheStats` snapshots.

Edit one SVG, validate XML, render PNG with:

```bash
xmllint --noout examples/cached_product_catalog/docs/images/architecture.svg
cairosvg examples/cached_product_catalog/docs/images/architecture.svg \
  -o examples/cached_product_catalog/docs/images/architecture.png -s 2
```

Run connector, geometry, endpoint, and mixed-corner audits. Record markers,
connectors, cards, crossings, intrusions, bends, and failures. Open the final
PNG at full size. Any visual contradiction returns to the SVG edit.

- [ ] **Step 6.5: Create and validate the Sequence asset**

Load `common.md` and `sequence.md`. Use the approved local sequence family and
show numbered sync/async calls with chronological frames for:

- miss → loader → publish → return;
- hit;
- exact-boundary expiry/reload;
- loader failure then later recovery;
- one waiter cancellation with survivor; and
- last-waiter cancellation, abandoned cleanup, and terminal task removal.

Render with CairoSVG and run the common audits plus
`diagram-sequence-style-audit.py`. Record visible numbered messages, lifelines,
activations, frames, marker parity, and failures. Open the final PNG full size.

- [ ] **Step 6.6: Run documentation and diagram exposure proof**

```bash
uv run --locked pytest examples/cached_product_catalog/tests/test_documentation.py -q
rg -n 'architecture\.(png|svg)|sequence\.(png|svg)' \
  examples/cached_product_catalog/README.md \
  examples/cached_product_catalog/README.ko.md
git diff --check -- examples/cached_product_catalog
```

Expected: PASS; both locales embed PNGs and link SVGs.

- [ ] **Step 6.7: Commit bilingual documentation and diagrams**

Stage the README pair, tests, and exact SVG/PNG pairs. Lore `Tested:` includes
all diagram ledger counts and full-size inspection paths. Do not claim visual
PASS from SVG generation alone.

## Task 7: Register the Example and Update the Milestone Board

**Complexity:** Medium

**Depends on:** Tasks 5–6

**Files:**

- Modify: `README.md`
- Modify: `README.ko.md`
- Modify: `WIP.md`
- Modify: `tests/test_documentation_contract.py`

**Patterns:** `test-driven-development`, `bluetape-writer`

- [ ] **Step 7.1: Write failing root navigation assertions**

Extend the root contract to require:

- `examples/cached_product_catalog/README.md` in English root README;
- `examples/cached_product_catalog/README.ko.md` in Korean root README;
- issue #5 as the current WIP target;
- the focused module and pytest commands; and
- issue #6 as the next dependency-ready example after issue #5 merge.

The existing runnable-example auto-discovery test must pick up the new package
and enforce all four diagram links without special casing.

- [ ] **Step 7.2: Run the root contract and observe RED**

```bash
uv run --locked pytest tests/test_documentation_contract.py -q
```

Expected: new navigation/current-target assertions fail while the generic
diagram discovery may already pass.

- [ ] **Step 7.3: Update both root README locales and WIP**

Add cached product catalog to current status and navigation. Keep facts,
commands, issue links, and limits aligned. Update WIP with:

- active branch/base and issue #5;
- approved spec/plan paths and review state;
- current validation counts;
- PR stop boundary;
- diagrams as required artifacts; and
- issue #6 as next after merge.

Do not mark issue #5 completed before merge.

- [ ] **Step 7.4: Run locale/root contract GREEN**

```bash
uv run --locked pytest \
  tests/test_documentation_contract.py \
  examples/cached_product_catalog/tests/test_documentation.py \
  -q
git diff --check -- README.md README.ko.md WIP.md tests/test_documentation_contract.py
```

Expected: PASS with reciprocal locale and diagram-contract evidence.

- [ ] **Step 7.5: Commit registration and WIP checkpoint**

Stage only root documentation and its contract test. Lore intent records why a
runnable example is incomplete until navigation, WIP, both locales, and both
diagrams are registered.

## Task 8: Converge Validation, Review, Lesson, and PR Delivery

**Complexity:** High

**Depends on:** Tasks 1–7

**Files:**

- Create:
  `docs/superpowers/reviews/2026-07-16-issue-5-implementation-review.md`
- Create:
  `docs/superpowers/lessons/2026-07-16-issue-5-local-cache-ownership.md`
- Modify: `WIP.md` only for the final exact checkpoint before publication

**Patterns:** `verification-before-completion`, `bluetape-full-feature`,
`bluetape-py-patterns`, `bluetape-writer`, `bluetape-diagram`

- [ ] **Step 8.1: Verify exact spec and plan coverage**

Load `bluetape-full-feature/references/step-5-verifier-checklist.md`. Map every
spec acceptance criterion to current files and tests. A missing item returns to
its owning task; do not edit the approved spec to match incomplete code.

- [ ] **Step 8.2: Run the fresh local validation ladder**

Run sequentially:

```bash
uv sync --locked --python 3.13.14
uv run --locked python -m examples.cached_product_catalog
uv run --locked pytest examples/cached_product_catalog/tests -q
uv run --locked pytest tests/test_dependency_baseline.py -q
uv run --locked ruff format --check .
uv run --locked ruff check .
uv run --locked pytest
GOTOOLCHAIN=go1.26.1 go run \
  github.com/rhysd/actionlint/cmd/actionlint@v1.7.12 \
  .github/workflows/ci.yml
git diff --check origin/develop
```

Expected: every command exits zero. Record exact test counts. `pyproject.toml`
and `uv.lock` must remain byte-identical to `origin/develop`; verify SHA-256.

- [ ] **Step 8.3: Run six implementation-review perspectives**

Use performance, stability, security, operator/Ops, developer/API, and
user/caller read-only lanes plus main integration. Apply the active bounded
wait rule: interrupt any lane without material progress and complete that lens
in the main session. Review exact source, tests, CLI, docs, diagrams, and
validation evidence. Normalize to P0/P1/P2/P3.

Fix every P0/P1 and rerun affected tests/lenses. Fix in-scope P2/P3 or record a
durable follow-up with rationale. Write the final review artifact only after
P0=0/P1=0.

- [ ] **Step 8.4: Commit the required Type A lesson**

Record:

- why cache ownership stays in the composition root;
- why sync/async service separation is clearer than an adapter;
- the difference between caller cancellation and loader terminal cleanup;
- how stats distinguish lifetime counters from gauges;
- review misses and the future guard; and
- exact verification evidence.

Commit the lesson before PR creation.

- [ ] **Step 8.5: Commit the converged exact head and verify clean state**

Update WIP with the exact validation checkpoint, then commit any remaining
review/WIP changes. Rerun the entire Step 8.2 ladder on the new exact head.
Confirm:

```bash
git status --short
git rev-parse HEAD
git diff --check origin/develop
```

Expected: clean worktree and exact head recorded for publication.

- [ ] **Step 8.6: Push and create the authorized PR**

Push `feat/issue-5-cached-product-catalog` without force. Create a PR in
`bluetape4k/bluetape-py-workshop` with base `develop`, head
`feat/issue-5-cached-product-catalog`, assignee `debop`, milestone `0.1.0`, and
labels mirrored from issue #5: `enhancement`, `type:feature`, `area:cache`.

Use an English title and body with `Closes #5`. Explain why/what, exact
validation, cache/cancellation risk boundaries, diagram audit evidence,
lesson, and a final `## DoD Status` section.

- [ ] **Step 8.7: Wait for exact-head CI and current review**

Verify local, remote, and PR head SHAs match. Wait for required CI. After green,
re-read reviews, review decision, comments, and unresolved GraphQL review
threads. Refresh the PR DoD to the final state.

- [ ] **Step 8.8: Report merge readiness and stop**

Report:

- exact PR URL and head SHA;
- CI conclusion and current reviews/threads;
- focused and full test counts;
- Ruff/actionlint/diff/lock parity;
- P0=0/P1=0;
- Architecture and Sequence audit/inspection evidence;
- committed lesson;
- residual limits: local in-process cache only, entry-count sizing, no Redis,
  no persistence, no HTTP, no publish; and
- `CG-16` pending fresh explicit merge approval.

Do not merge, enable auto-merge, delete the remote branch, or start issue #6
until the user explicitly approves the exact merge-ready head.

## Rollback and Recovery

- Before PR: revert only the last scoped Lore commit or repair the owning task;
  never reset unrelated user work.
- Cache contract mismatch: stop implementation, preserve the failing public API
  test, and open/link an upstream issue rather than adding an adapter.
- Async flake: preserve raw output, identify missing event ownership, and rerun
  from Task 3 or 4; retry success alone is not evidence.
- Diagram defect: return one asset at a time to SVG edit → XML → CairoSVG →
  audits → full-size PNG inspection.
- CI failure: classify exact-head source/test failure versus hosted-runner setup
  failure before rerun; any code change requires a new exact-head validation.
- PR metadata/body drift: repair live metadata and reread it before reporting
  merge readiness.

## Plan Completion Gate

This plan is ready for implementation only when:

- every spec acceptance item maps to an ordered task and exact command;
- no task depends on a later artifact;
- six plan-review perspectives plus main integration converge at P0=0/P1=0;
- placeholder, type/signature, and path scans pass;
- the plan and review artifact are committed; and
- the user explicitly approves this written plan.
