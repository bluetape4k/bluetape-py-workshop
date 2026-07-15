# Issue #4 Bounded Catalog Enrichment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a runnable, framework-neutral catalog enrichment example that deterministically normalizes, deduplicates, batches, and restores product identifiers while executing required and optional provider calls under one bounded structured-concurrency budget.

**Architecture:** `examples/catalog_enrichment` is one importable application package. Frozen public records and explicit provider protocols surround a `CatalogEnrichmentService` that validates bounded SKU input, creates required/optional batch jobs, delegates task ownership to `bluetape.asyncio.map_bounded`, validates provider responses, and restores one immutable result per normalized input occurrence. A standard-library entrypoint supplies deterministic in-memory providers and emits JSON without network or global telemetry state.

**Tech Stack:** Python 3.13.14, uv 0.11.28, pinned bluetape-py commit `4b7458f22cea0a9e757b5fbf7f5ff4bc8c23cb9a`, `bluetape-core`, `bluetape-collections`, `bluetape-async`, pytest/pytest-asyncio, Ruff, stdlib `asyncio`/`dataclasses`/`json`/`re`, CairoSVG, bluetape diagram audit scripts.

---

## Scope and file ownership

| File | Responsibility | Write task |
|---|---|---:|
| `examples/catalog_enrichment/__init__.py` | Stable public example surface | 1, 2 |
| `examples/catalog_enrichment/models.py` | Frozen provider records, warnings, and enriched results | 1 |
| `examples/catalog_enrichment/errors.py` | Input, provider, and request failure contracts | 1 |
| `examples/catalog_enrichment/providers.py` | Required and optional async provider protocols | 1 |
| `examples/catalog_enrichment/service.py` | Bounded normalization, jobs, provider validation, aggregation | 2 |
| `examples/catalog_enrichment/tests/test_service.py` | Model, input, provider, ordering, failure, timeout, cancellation, cleanup tests | 1–3 |
| `examples/catalog_enrichment/__main__.py` | Deterministic in-memory runnable scenario | 3 |
| `examples/catalog_enrichment/tests/test_application.py` | CLI JSON and network-free execution contract | 3 |
| `examples/catalog_enrichment/README.md` | English scenario, architecture, sequence, APIs, commands, policy | 4 |
| `examples/catalog_enrichment/README.ko.md` | Natural Korean equivalent | 4 |
| `examples/catalog_enrichment/tests/test_documentation.py` | Locale, command, link, policy, and asset parity | 4 |
| `examples/catalog_enrichment/docs/images/architecture.svg` | Source-backed responsibility diagram | 4 |
| `examples/catalog_enrichment/docs/images/architecture.png` | Rendered architecture asset | 4 |
| `examples/catalog_enrichment/docs/images/sequence.svg` | Source-backed async lifecycle diagram | 4 |
| `examples/catalog_enrichment/docs/images/sequence.png` | Rendered sequence asset | 4 |
| `README.md`, `README.ko.md` | Root learning-path navigation and current status | 4 |
| `tests/test_documentation_contract.py` | Root bilingual navigation and WIP contract | 4 |
| `WIP.md` | Resume checkpoint, validation, PR boundary, next issue | 4, 5 |
| `docs/superpowers/reviews/2026-07-15-issue-4-implementation-review.md` | Final six-lens implementation review | 5 |
| `docs/superpowers/lessons/2026-07-15-issue-4-catalog-enrichment.md` | Reusable bounded-fan-out lesson | 5 |

Tasks are sequential. Models and protocols precede the service; service behavior
precedes the CLI; diagrams and documentation are created only from implemented
source. No task changes `pyproject.toml`, `uv.lock`, dependencies, CI workflow,
Docker state, release metadata, or global logging configuration.

## Acceptance mapping

| Spec/issue criterion | Implementing task | Proof command |
|---|---:|---|
| Deterministic empty/boundary/duplicate transforms | 1, 2 | `uv run --locked pytest examples/catalog_enrichment/tests/test_service.py -q` |
| One result per normalized input occurrence | 2 | `test_duplicate_work_is_deduplicated_and_results_are_restored` |
| Global provider concurrency never exceeds limit | 3 | `test_provider_calls_share_one_global_concurrency_limit` |
| Required failures fail without partial result | 2, 3 | required outage/response/mixed-group tests |
| Optional failures become explicit safe warnings | 2 | optional outage/missing/invalid/extra tests |
| Timeout differs from caller cancellation | 3 | exact `TimeoutError` and `CancelledError` tests |
| All owned tasks complete or cancel | 3 | named helper-task assertions on every exit path |
| Input/provider trust boundaries are bounded | 2 | invalid SKU, 1,001-item, response-validation tests |
| Runnable deterministic JSON example | 3 | `uv run --locked python -m examples.catalog_enrichment` |
| Equivalent bilingual docs and root navigation | 4 | documentation tests plus source/asset audits |
| Full repository quality gates | 5 | locked Ruff, full pytest, actionlint, diff check |
| Exact-head PR delivery | 5 | matching remote SHA, live PR metadata/body, CI/review evidence |

## Conditional scope decisions

- Packaging/lock build: `N/A`; this is a root non-package example using already
  pinned dependencies. `pyproject.toml` and `uv.lock` must remain byte-identical.
- HTTP/client resource ownership: `N/A`; provider protocols are injected and
  the service creates no socket/session/client. README assigns provider resource
  cleanup to the adapter that constructs the provider.
- Testcontainers/real backend: `N/A`; all providers are in-memory and issue #7
  owns Docker-backed teaching.
- Retry/circuit breaker: `N/A`; issue #4 explicitly waits for the upstream
  resilience package and must not grow a local substitute.
- Benchmark: `N/A`; fixed request caps make local transforms bounded, and the
  acceptance metric is a measured concurrency ceiling rather than throughput.
- Release/tag/milestone closure: `N/A`; delivery is one issue PR only.
- Cleanup/deslop: conditional; run only if implementation duplicates provider
  validation or introduces generated verbosity after tests are green.
- Repository hazards for module/BOM/Kover/Nightly registration: `N/A`; no
  publishable module or workflow/catalog surface changes.

## Risk prediction

Step 3-P is required because this change owns async cancellation, total timeout,
provider trust, eager collection bounds, and generated visuals.

| Risk | Early signal | Mitigation | Rollback/rerun point |
|---|---|---|---|
| Bounded tasks hide unbounded eager input | iterable consumes beyond 1,001 or job list grows without cap | fixed occurrence, identifier, and batch caps before job creation | revert normalization helper; rerun Task 2 input tests |
| Unicode normalization collapses identifiers | non-ASCII input becomes an accepted ASCII SKU | reject raw non-ASCII before uppercase | rerun invalid identifier matrix |
| Optional handling swallows a programming defect | `KeyError`/`AssertionError` becomes a warning | catch only `ProviderUnavailable`; propagate all other exceptions/groups | rerun Task 2 mixed failure tests |
| Required failure leaks partial results | service returns after one required batch fails | raise inside mapper; translate all-required group only after sibling cleanup | rerun Task 3 required failure/cleanup tests |
| Timeout is relabelled as cancellation or provider outage | wrong exception type reaches caller | never catch `TimeoutError`/`CancelledError` in service provider policy | rerun Task 3 exact-type tests |
| Global limit becomes per-provider limit | active required + optional calls exceed configured value | one ordered job list and one `map_bounded` call | rerun global active-counter test |
| Cross-batch provider data contaminates results | unexpected mapping key appears in output | exact required key match; discard optional batch on extra key | rerun provider contract matrix |
| Warning/error output leaks raw provider details | secret marker appears in `str(error)` or JSON | stable code/message literals; keep raw causes chained and unserialized | rerun safe-output tests |
| Diagram drifts from task ownership | participant/message has no source anchor | create assets after code and maintain a source-to-node/message ledger | regenerate one asset and rerun audits |

### Task 1: Add immutable public values, errors, and provider protocols with TDD

**Complexity:** Medium  
**Dependencies:** Approved spec and approved implementation plan  
**Required skills:** `test-driven-development`, `bluetape-py-patterns`  
**Files:**
- Create: `examples/catalog_enrichment/__init__.py`
- Create: `examples/catalog_enrichment/models.py`
- Create: `examples/catalog_enrichment/errors.py`
- Create: `examples/catalog_enrichment/providers.py`
- Create: `examples/catalog_enrichment/tests/test_service.py`

- [ ] **Step 1: Write the failing public-contract tests**

Create `examples/catalog_enrichment/tests/test_service.py`:

```python
import importlib
from dataclasses import FrozenInstanceError
from types import ModuleType

import pytest


def _load_api() -> ModuleType:
    try:
        return importlib.import_module("examples.catalog_enrichment")
    except ModuleNotFoundError as error:
        pytest.fail(f"catalog enrichment API is missing: {error}")


def test_public_values_are_immutable_and_keyword_only() -> None:
    api = _load_api()
    catalog = api.CatalogRecord(product_id="SKU-1", name="Desk", price_cents=12000)
    warning = api.EnrichmentWarning(
        product_id="SKU-1",
        provider="recommendations",
        code="optional_record_missing",
        message="recommendation is unavailable",
    )
    result = api.EnrichedProduct(
        product_id="SKU-1",
        name="Desk",
        price_cents=12000,
        recommendation=None,
        warnings=(warning,),
    )

    with pytest.raises(FrozenInstanceError):
        catalog.name = "Chair"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.warnings = ()  # type: ignore[misc]


def test_public_errors_expose_safe_bounded_metadata() -> None:
    api = _load_api()
    invalid = api.InvalidProductIdentifier(2, "must use ASCII SKU characters")
    required = api.RequiredProviderFailure(1, "provider_unavailable")
    failed = api.CatalogEnrichmentFailed((required,))

    assert invalid.index == 2
    assert "secret-provider-detail" not in str(invalid)
    assert failed.failures == (required,)
    assert str(failed) == "catalog enrichment failed for required batch 1"
```

- [ ] **Step 2: Run the focused test and observe RED**

Run:

```bash
uv run --locked pytest examples/catalog_enrichment/tests/test_service.py -q
```

Expected: both tests fail through `_load_api` with the explicit assertion
`catalog enrichment API is missing`; pytest collection succeeds.

- [ ] **Step 3: Implement frozen public records**

Create `models.py`:

```python
from dataclasses import dataclass
from typing import Literal

WarningCode = Literal[
    "optional_provider_failed",
    "optional_record_missing",
    "optional_record_invalid",
    "optional_response_invalid",
]


@dataclass(frozen=True, slots=True, kw_only=True)
class CatalogRecord:
    product_id: str
    name: str
    price_cents: int


@dataclass(frozen=True, slots=True, kw_only=True)
class RecommendationRecord:
    product_id: str
    recommendation: str


@dataclass(frozen=True, slots=True, kw_only=True)
class EnrichmentWarning:
    product_id: str
    provider: Literal["recommendations"]
    code: WarningCode
    message: str


@dataclass(frozen=True, slots=True, kw_only=True)
class EnrichedProduct:
    product_id: str
    name: str
    price_cents: int
    recommendation: str | None
    warnings: tuple[EnrichmentWarning, ...] = ()
```

- [ ] **Step 4: Implement safe errors and provider protocols**

Create `errors.py`:

```python
from typing import Literal

RequiredFailureCode = Literal["provider_unavailable", "response_invalid"]


class InvalidProductIdentifier(ValueError):  # noqa: N818 - domain name
    def __init__(self, index: int, reason: str) -> None:
        self.index = index
        self.reason = reason
        super().__init__(f"product_ids[{index}]: {reason}")


class TooManyProductIdentifiers(ValueError):  # noqa: N818 - domain name
    def __init__(self, limit: int) -> None:
        self.limit = limit
        super().__init__(f"product_ids must contain at most {limit} values")


class ProviderUnavailable(RuntimeError):  # noqa: N818 - provider signal
    def __init__(self) -> None:
        super().__init__("provider unavailable")


class RequiredProviderFailure(RuntimeError):  # noqa: N818 - domain name
    def __init__(self, batch_index: int, code: RequiredFailureCode) -> None:
        self.batch_index = batch_index
        self.code = code
        super().__init__(f"required provider failed for batch {batch_index}: {code}")


class CatalogEnrichmentFailed(RuntimeError):  # noqa: N818 - domain name
    def __init__(self, failures: tuple[RequiredProviderFailure, ...]) -> None:
        self.failures = failures
        batches = ", ".join(str(failure.batch_index) for failure in failures)
        super().__init__(f"catalog enrichment failed for required batch {batches}")
```

Create `providers.py`:

```python
from collections.abc import Mapping
from typing import Protocol

from .models import CatalogRecord, RecommendationRecord


class RequiredCatalogProvider(Protocol):
    async def fetch(self, product_ids: tuple[str, ...]) -> Mapping[str, CatalogRecord]: ...


class OptionalRecommendationProvider(Protocol):
    async def fetch(
        self,
        product_ids: tuple[str, ...],
    ) -> Mapping[str, RecommendationRecord]: ...
```

Create `__init__.py` exporting the four models, five errors, two protocols, and
the two type aliases through an explicit alphabetized `__all__`.

- [ ] **Step 5: Run focused tests and Ruff and observe GREEN**

```bash
uv run --locked pytest examples/catalog_enrichment/tests/test_service.py -q
uv run --locked ruff check examples/catalog_enrichment
uv run --locked ruff format --check examples/catalog_enrichment
```

Expected: 2 tests pass; Ruff reports no findings or formatting changes.

- [ ] **Step 6: Commit the public boundary**

Commit only Task 1 files with Lore intent
`Make catalog enrichment failures safe before provider work starts`.
`Tested:` records the three Task 1 commands; `Not-tested:` names async service
behavior as the next task.

### Task 2: Implement deterministic normalization, batching, provider policy, and aggregation with TDD

**Complexity:** High  
**Dependencies:** Task 1 GREEN  
**Required skills:** `test-driven-development`, `bluetape-py-patterns`  
**Files:**
- Modify: `examples/catalog_enrichment/tests/test_service.py`
- Create: `examples/catalog_enrichment/service.py`
- Modify: `examples/catalog_enrichment/__init__.py`

- [ ] **Step 1: Add failing transform and provider-policy tests**

Extend `test_service.py` with deterministic in-memory providers and tests that
assert these exact values:

```python
from collections.abc import Mapping

from examples.catalog_enrichment import (
    CatalogEnrichmentFailed,
    CatalogEnrichmentService,
    CatalogRecord,
    EnrichedProduct,
    InvalidProductIdentifier,
    ProviderUnavailable,
    RecommendationRecord,
    TooManyProductIdentifiers,
)


class CatalogProvider:
    def __init__(self, records: Mapping[str, CatalogRecord]) -> None:
        self.records = dict(records)
        self.calls: list[tuple[str, ...]] = []
        self.error: BaseException | None = None

    async def fetch(self, product_ids: tuple[str, ...]):
        self.calls.append(product_ids)
        if self.error is not None:
            raise self.error
        return {product_id: self.records[product_id] for product_id in product_ids}


class RecommendationProvider:
    def __init__(self, records: Mapping[str, RecommendationRecord]) -> None:
        self.records = dict(records)
        self.calls: list[tuple[str, ...]] = []
        self.error: BaseException | None = None

    async def fetch(self, product_ids: tuple[str, ...]):
        self.calls.append(product_ids)
        if self.error is not None:
            raise self.error
        return {
            product_id: self.records[product_id]
            for product_id in product_ids
            if product_id in self.records
        }


@pytest.fixture
def providers():
    catalog = CatalogProvider(
        {
            "SKU-1": CatalogRecord(product_id="SKU-1", name="Desk", price_cents=12000),
            "SKU-2": CatalogRecord(product_id="SKU-2", name="Chair", price_cents=8000),
            "SKU-3": CatalogRecord(product_id="SKU-3", name="Lamp", price_cents=4500),
        }
    )
    recommendations = RecommendationProvider(
        {
            "SKU-1": RecommendationRecord(product_id="SKU-1", recommendation="PAIR-SKU-9"),
            "SKU-2": RecommendationRecord(product_id="SKU-2", recommendation="PAIR-SKU-8"),
        }
    )
    return catalog, recommendations


async def test_duplicate_work_is_deduplicated_and_results_are_restored(providers) -> None:
    catalog, recommendations = providers
    source = [" sku-2 ", "sku-1", "SKU-2", "sku-3"]
    service = CatalogEnrichmentService(catalog, recommendations)

    result = await service.enrich(source, batch_size=2, concurrency_limit=2, timeout=1.0)

    assert source == [" sku-2 ", "sku-1", "SKU-2", "sku-3"]
    assert [item.product_id for item in result] == ["SKU-2", "SKU-1", "SKU-2", "SKU-3"]
    assert catalog.calls == [("SKU-2", "SKU-1"), ("SKU-3",)]
    assert recommendations.calls == [("SKU-2", "SKU-1"), ("SKU-3",)]
    assert result[2] == result[0]
    assert result[3].warnings[0].code == "optional_record_missing"


async def test_empty_input_calls_no_provider_and_still_validates_configuration(providers) -> None:
    catalog, recommendations = providers
    service = CatalogEnrichmentService(catalog, recommendations)

    assert await service.enrich([], batch_size=2, concurrency_limit=1, timeout=None) == []
    assert catalog.calls == []
    assert recommendations.calls == []
    with pytest.raises(ValueError, match="limit must be greater than 0"):
        await service.enrich([], batch_size=2, concurrency_limit=0, timeout=None)


@pytest.mark.parametrize("value", ["", "   ", "SKU/1", "ß", "a" * 65, 7, None])
async def test_invalid_identifier_fails_before_provider_calls(providers, value: object) -> None:
    catalog, recommendations = providers
    service = CatalogEnrichmentService(catalog, recommendations)

    with pytest.raises(InvalidProductIdentifier):
        await service.enrich([value], batch_size=2, concurrency_limit=1, timeout=None)  # type: ignore[list-item]
    assert catalog.calls == []
    assert recommendations.calls == []


async def test_occurrence_limit_stops_a_large_iterable(providers) -> None:
    catalog, recommendations = providers
    service = CatalogEnrichmentService(catalog, recommendations)

    with pytest.raises(TooManyProductIdentifiers) as captured:
        await service.enrich(("SKU-1" for _ in range(1001)), batch_size=2, concurrency_limit=1, timeout=None)
    assert captured.value.limit == 1000
    assert catalog.calls == []
```

Add required/optional provider contract tests with exact assertions:

```python
async def test_required_operational_failure_becomes_safe_request_failure(providers) -> None:
    catalog, recommendations = providers
    secret = RuntimeError("secret-provider-detail")
    catalog.error = ProviderUnavailable()
    catalog.error.__cause__ = secret
    service = CatalogEnrichmentService(catalog, recommendations)

    with pytest.raises(CatalogEnrichmentFailed) as captured:
        await service.enrich(["SKU-1"], batch_size=1, concurrency_limit=1, timeout=None)
    assert captured.value.failures[0].code == "provider_unavailable"
    assert "secret-provider-detail" not in str(captured.value)


async def test_optional_operational_failure_becomes_warning(providers) -> None:
    catalog, recommendations = providers
    recommendations.error = ProviderUnavailable()
    service = CatalogEnrichmentService(catalog, recommendations)

    result = await service.enrich(["SKU-1"], batch_size=1, concurrency_limit=2, timeout=None)

    assert result[0].warnings[0].code == "optional_provider_failed"
    assert result[0].recommendation is None


async def test_unexpected_optional_defect_propagates(providers) -> None:
    catalog, recommendations = providers
    recommendations.error = AssertionError("programming defect")
    service = CatalogEnrichmentService(catalog, recommendations)

    with pytest.raises(ExceptionGroup) as captured:
        await service.enrich(["SKU-1"], batch_size=1, concurrency_limit=2, timeout=None)
    assert any(isinstance(error, AssertionError) for error in captured.value.exceptions)
```

Use parametrized provider mappings to prove required missing/extra/mismatched or
invalid records fail with `response_invalid`, and optional missing/mismatched
records produce `optional_record_missing`/`optional_record_invalid`. An optional
extra key must discard the whole optional batch and produce
`optional_response_invalid` for every requested identifier.

The parametrized matrix is exact:

| Provider | Batch | Response mutation | Expected proof |
|---|---|---|---|
| required | `("SKU-1",)` | `{}` | `CatalogEnrichmentFailed.failures[0].code == "response_invalid"` |
| required | `("SKU-1",)` | adds `SKU-X` | same required failure; `SKU-X` absent from output |
| required | `("SKU-1",)` | record `product_id="SKU-2"` | same required failure |
| required | `("SKU-1",)` | blank name, boolean price, negative price | same required failure for every case |
| optional | `("SKU-1",)` | `{}` | one `optional_record_missing` warning |
| optional | `("SKU-1",)` | record `product_id="SKU-2"` or blank recommendation | one `optional_record_invalid` warning |
| optional | `("SKU-1", "SKU-2")` | adds `SKU-X` | discard all optional records; two `optional_response_invalid` warnings |

Every case also asserts caller mappings and records remain unchanged and that
raw provider payload values do not appear in exception or warning messages.

- [ ] **Step 2: Run Task 2 tests and observe RED**

```bash
uv run --locked pytest examples/catalog_enrichment/tests/test_service.py -q
```

Expected: Task 1 remains green; new tests fail because
`CatalogEnrichmentService` is not exported.

- [ ] **Step 3: Implement the minimal service**

Create `service.py` with these exact public limits and internal job shapes:

```python
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Literal, cast

from bluetape.asyncio import map_bounded
from bluetape.collections import chunked, distinct
from bluetape.core import require_instance, require_not_blank

from .errors import (
    CatalogEnrichmentFailed,
    InvalidProductIdentifier,
    ProviderUnavailable,
    RequiredProviderFailure,
    TooManyProductIdentifiers,
)
from .models import CatalogRecord, EnrichedProduct, EnrichmentWarning, RecommendationRecord
from .providers import OptionalRecommendationProvider, RequiredCatalogProvider

MAX_PRODUCT_IDENTIFIERS = 1000
MAX_PRODUCT_ID_LENGTH = 64
MAX_BATCH_SIZE = 100
_PRODUCT_ID = re.compile(r"[A-Z0-9][A-Z0-9._-]*\Z")


@dataclass(frozen=True, slots=True)
class _ProviderJob:
    batch_index: int
    kind: Literal["catalog", "recommendations"]
    product_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class _JobOutcome:
    catalog: tuple[CatalogRecord, ...] = ()
    recommendations: tuple[RecommendationRecord, ...] = ()
    warnings: tuple[EnrichmentWarning, ...] = ()
```

Implement helpers with the following contracts:

- `_normalize_product_ids` stops before appending occurrence 1,001; maps core
  type/blank failures to `InvalidProductIdentifier`; checks raw trimmed ASCII
  and length before uppercase; applies `_PRODUCT_ID.fullmatch` after uppercase.
- `_warning(product_id, code)` returns provider `recommendations` and only these
  safe messages: `recommendation provider is unavailable`, `recommendation is
  unavailable`, `recommendation record is invalid`, or `recommendation response
  is invalid`.
- `_valid_catalog_record` rejects wrong type, mismatched ID, blank/non-string
  name, boolean price, non-integer price, and negative price.
- `_valid_recommendation_record` rejects wrong type, mismatched ID, and
  blank/non-string recommendation.
- `_exception_leaves` recursively flattens nested `ExceptionGroup` values but
  never catches `BaseExceptionGroup` cancellation branches.

Implement `CatalogEnrichmentService` so constructor `fetch` validation uses
`getattr(..., "fetch", None)` plus `callable`, and `enrich` performs:

```python
async def enrich(
    self,
    product_ids: Iterable[str],
    *,
    batch_size: int,
    concurrency_limit: int,
    timeout: float | None,
) -> list[EnrichedProduct]:
    chunked((), batch_size)
    if batch_size > MAX_BATCH_SIZE:
        raise ValueError(f"batch_size must be less than or equal to {MAX_BATCH_SIZE}")
    normalized = _normalize_product_ids(product_ids)
    batches = [tuple(batch) for batch in chunked(distinct(normalized), batch_size)]
    jobs = [
        _ProviderJob(batch_index, kind, batch)
        for batch_index, batch in enumerate(batches)
        for kind in ("catalog", "recommendations")
    ]

    try:
        outcomes = await map_bounded(
            jobs,
            self._run_job,
            limit=concurrency_limit,
            timeout=timeout,
        )
    except ExceptionGroup as group:
        leaves = _exception_leaves(group)
        if leaves and all(isinstance(error, RequiredProviderFailure) for error in leaves):
            failures = tuple(
                sorted(
                    cast(list[RequiredProviderFailure], leaves),
                    key=lambda error: (error.batch_index, error.code),
                )
            )
            raise CatalogEnrichmentFailed(failures) from group
        raise

    catalog = {
        record.product_id: record
        for outcome in outcomes
        for record in outcome.catalog
    }
    recommendations = {
        record.product_id: record
        for outcome in outcomes
        for record in outcome.recommendations
    }
    warnings: dict[str, list[EnrichmentWarning]] = {}
    for outcome in outcomes:
        for warning in outcome.warnings:
            warnings.setdefault(warning.product_id, []).append(warning)

    return [
        EnrichedProduct(
            product_id=product_id,
            name=catalog[product_id].name,
            price_cents=catalog[product_id].price_cents,
            recommendation=(
                recommendations[product_id].recommendation
                if product_id in recommendations
                else None
            ),
            warnings=tuple(warnings.get(product_id, ())),
        )
        for product_id in normalized
    ]
```

`_run_job` catches only `ProviderUnavailable`. Required operational failure is
raised as `RequiredProviderFailure(batch_index, "provider_unavailable")` from
the provider signal. Required mapping/type/key/record validation raises
`RequiredProviderFailure(batch_index, "response_invalid")`. Optional operational
failure returns one warning per batch ID. Optional mapping validation follows
the exact discard/missing/invalid policy from the spec and never serializes a
provider exception.

Export `CatalogEnrichmentService` and the three public limits from `__init__.py`.

- [ ] **Step 4: Run focused tests and Ruff and observe GREEN**

```bash
uv run --locked pytest examples/catalog_enrichment/tests/test_service.py -q
uv run --locked ruff check examples/catalog_enrichment
uv run --locked ruff format --check examples/catalog_enrichment
```

Expected: all Task 1–2 tests pass; Ruff is clean.

- [ ] **Step 5: Commit deterministic provider policy**

Commit Task 2 files with Lore intent
`Keep catalog provider work bounded without changing caller order`.
`Directive:` states that only `ProviderUnavailable` is an optional outage and
that duplicate provider work must remain deduplicated.

### Task 3: Prove concurrency, timeout, cancellation, cleanup, and runnable output

**Complexity:** High  
**Dependencies:** Task 2 GREEN  
**Required skills:** `test-driven-development`, `bluetape-py-patterns`  
**Files:**
- Modify: `examples/catalog_enrichment/tests/test_service.py`
- Create: `examples/catalog_enrichment/__main__.py`
- Create: `examples/catalog_enrichment/tests/test_application.py`

- [ ] **Step 1: Add event-driven failing lifecycle tests**

Add this shared assertion and provider gate to `test_service.py`:

```python
import asyncio


def _assert_no_helper_tasks() -> None:
    assert not [
        task
        for task in asyncio.all_tasks()
        if task is not asyncio.current_task()
        and task.get_name().startswith("bluetape.map_bounded.")
    ]


class ConcurrencyGate:
    def __init__(self, release: asyncio.Event) -> None:
        self.release = release
        self.active = 0
        self.maximum = 0
        self.admitted = asyncio.Event()
        self.cleaned = 0

    async def enter(self) -> None:
        self.active += 1
        self.maximum = max(self.maximum, self.active)
        if self.maximum >= 2:
            self.admitted.set()
        try:
            await self.release.wait()
        finally:
            self.active -= 1
            self.cleaned += 1
```

Add exact tests:

```python
async def test_provider_calls_share_one_global_concurrency_limit() -> None:
    release = asyncio.Event()
    gate = ConcurrencyGate(release)
    catalog = GatedCatalogProvider(gate)
    recommendations = GatedRecommendationProvider(gate)
    service = CatalogEnrichmentService(catalog, recommendations)

    task = asyncio.create_task(
        service.enrich(
            ["SKU-1", "SKU-2", "SKU-3"],
            batch_size=1,
            concurrency_limit=2,
            timeout=None,
        )
    )
    await asyncio.wait_for(gate.admitted.wait(), timeout=1.0)
    assert gate.active == 2
    assert gate.maximum == 2
    release.set()
    await asyncio.wait_for(task, timeout=1.0)
    assert gate.maximum == 2
    _assert_no_helper_tasks()


async def test_total_timeout_waits_for_mapper_cleanup() -> None:
    release = asyncio.Event()
    gate = ConcurrencyGate(release)
    service = CatalogEnrichmentService(GatedCatalogProvider(gate), GatedRecommendationProvider(gate))

    with pytest.raises(TimeoutError):
        await service.enrich(["SKU-1"], batch_size=1, concurrency_limit=2, timeout=0.01)
    assert gate.active == 0
    assert gate.cleaned == 2
    _assert_no_helper_tasks()


async def test_caller_cancellation_remains_native_and_cleans_siblings() -> None:
    release = asyncio.Event()
    gate = ConcurrencyGate(release)
    service = CatalogEnrichmentService(GatedCatalogProvider(gate), GatedRecommendationProvider(gate))
    task = asyncio.create_task(
        service.enrich(["SKU-1"], batch_size=1, concurrency_limit=2, timeout=None)
    )
    await asyncio.wait_for(gate.admitted.wait(), timeout=1.0)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert gate.active == 0
    assert gate.cleaned == 2
    _assert_no_helper_tasks()
```

Add an event-controlled required provider that raises `ProviderUnavailable`
after the optional sibling enters `finally`; assert `CatalogEnrichmentFailed`,
the optional cleanup counter, and no helper tasks. Add a mixed required outage
plus unexpected provider defect race; assert the original `ExceptionGroup`
propagates rather than `CatalogEnrichmentFailed`. Use `asyncio.Event` and
`asyncio.wait_for(..., timeout=1.0)` only; no sleep longer than the library
timeout probe of `0.01` seconds.

- [ ] **Step 2: Run lifecycle tests and observe RED where gated providers and CLI are missing**

```bash
uv run --locked pytest examples/catalog_enrichment/tests/test_service.py -q
```

Expected: existing transform tests stay green; new lifecycle tests fail on the
missing test-provider implementations or violated cleanup behavior.

- [ ] **Step 3: Complete minimal gated test providers and keep production code unchanged unless RED proves a defect**

Implement `GatedCatalogProvider` and `GatedRecommendationProvider` inside the
test file. Each calls `await gate.enter()` and then returns exact records for its
batch. Do not add sleeps, production semaphores, task registries, or service
cleanup code: `map_bounded` remains the sole task owner.

- [ ] **Step 4: Write the failing CLI contract**

Create `test_application.py`:

```python
import json
import socket
import subprocess
import sys

import pytest

from examples.catalog_enrichment.__main__ import main


def test_runnable_example_is_deterministic() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "examples.catalog_enrichment"],
        check=True,
        capture_output=True,
        text=True,
        timeout=2,
    )
    payload = json.loads(completed.stdout)
    assert completed.stderr == ""
    assert [item["product_id"] for item in payload] == ["SKU-2", "SKU-1", "SKU-2"]
    assert payload[0] == payload[2]
    assert payload[1]["warnings"] == [
        {
            "code": "optional_record_missing",
            "message": "recommendation is unavailable",
            "product_id": "SKU-1",
            "provider": "recommendations",
        }
    ]


async def test_main_uses_no_network(monkeypatch, capsys) -> None:
    def deny_socket(*args, **kwargs):
        raise AssertionError("the in-memory example must not open a socket")

    monkeypatch.setattr(socket, "socket", deny_socket)
    await main()
    assert json.loads(capsys.readouterr().out)
```

Run it and expect RED because `examples.catalog_enrichment.__main__` is absent.

- [ ] **Step 5: Implement the deterministic entrypoint**

Create `__main__.py` with two private in-memory providers. They use immutable
module-level mappings, `async def fetch`, and no sleep, socket, environment,
random, clock, logger, thread, or process access. `main()` calls:

```python
results = await service.enrich(
    [" sku-2 ", "sku-1", "SKU-2"],
    batch_size=2,
    concurrency_limit=2,
    timeout=1.0,
)
print(json.dumps([asdict(result) for result in results], sort_keys=True))
```

The recommendation mapping intentionally omits `SKU-1` so the observable JSON
demonstrates an optional warning without failing required data. Module execution
uses `asyncio.run(main())`.

- [ ] **Step 6: Run lifecycle, CLI, Ruff, and full tests**

```bash
uv run --locked pytest examples/catalog_enrichment/tests/test_service.py -q
uv run --locked pytest examples/catalog_enrichment/tests/test_application.py -q
uv run --locked python -m examples.catalog_enrichment
uv run --locked ruff check examples/catalog_enrichment
uv run --locked ruff format --check examples/catalog_enrichment
uv run --locked pytest -q
```

Expected: all focused/full tests pass, CLI emits one deterministic JSON line,
and Ruff is clean.

- [ ] **Step 7: Commit structured concurrency and runnable output**

Commit Task 3 files with Lore intent
`Make catalog fan-out cancellation visible without owning provider clients`.
`Tested:` records focused lifecycle, application, CLI, Ruff, and full pytest.

### Task 4: Add aligned bilingual guidance and source-backed diagrams

**Complexity:** High  
**Dependencies:** Task 3 implementation and CLI GREEN  
**Required skills:** `bluetape-writer`, `bluetape-diagram`  
**Files:**
- Create: `examples/catalog_enrichment/README.md`
- Create: `examples/catalog_enrichment/README.ko.md`
- Create: `examples/catalog_enrichment/tests/test_documentation.py`
- Create: `examples/catalog_enrichment/docs/images/architecture.svg`
- Create: `examples/catalog_enrichment/docs/images/architecture.png`
- Create: `examples/catalog_enrichment/docs/images/sequence.svg`
- Create: `examples/catalog_enrichment/docs/images/sequence.png`
- Modify: `README.md`
- Modify: `README.ko.md`
- Modify: `tests/test_documentation_contract.py`
- Modify: `WIP.md`

- [ ] **Step 1: Write failing bilingual documentation-contract tests**

Create `test_documentation.py` that reads both locale files and asserts:

```python
EXPECTED_TOKENS = (
    "python -m examples.catalog_enrichment",
    "pytest examples/catalog_enrichment/tests -q",
    "bluetape.collections.distinct",
    "bluetape.collections.chunked",
    "bluetape.asyncio.map_bounded",
    "optional_provider_failed",
    "TimeoutError",
    "CancelledError",
    "architecture.svg",
    "architecture.png",
    "sequence.svg",
    "sequence.png",
)


def test_locale_navigation_and_contract_tokens_are_aligned() -> None:
    assert "English | [한국어](README.ko.md)" in ENGLISH
    assert "[English](README.md) | 한국어" in KOREAN
    for token in EXPECTED_TOKENS:
        assert token in ENGLISH
        assert token in KOREAN


def test_diagram_assets_exist_and_link_to_source() -> None:
    for name in ("architecture.svg", "architecture.png", "sequence.svg", "sequence.png"):
        assert (EXAMPLE / "docs" / "images" / name).is_file()
    for source in ("models.py", "providers.py", "service.py", "__main__.py"):
        assert source in ENGLISH
        assert source in KOREAN
```

Extend the root documentation contract to require both root README files link
to their matching catalog-enrichment locale and WIP marks #3 completed and #4
as the current target. Run both documentation test files and observe RED.

- [ ] **Step 2: Write the aligned README pair from implemented source**

Both files must contain the same section sequence and exact commands:

1. reciprocal `English | 한국어` navigation;
2. Scenario with duplicate SKUs, required catalog, optional recommendations;
3. Architecture image plus ownership table;
4. Sequence Diagram plus success/warning/failure/timeout/cancellation policy;
5. exact pinned distributions and API links;
6. limits: 1,000 occurrences, 64 ASCII characters, batch size 1–100,
   concurrency 1–1,024, one total cooperative timeout;
7. root working directory setup, run, focused test, full test commands;
8. deterministic expected JSON semantics;
9. provider trust/resource boundary and caller-owned telemetry;
10. troubleshooting and non-goals including no retry/HTTP/cache/Docker.

English uses precise technical prose. Korean is a natural translation but keeps
commands, exception names, warning codes, package names, paths, and numeric
limits byte-identical.

- [ ] **Step 3: Create source-backed Architecture and Sequence assets**

Read `bluetape-diagram` fresh. Architecture participants map exactly to Caller,
`CatalogEnrichmentService`, `distinct`/`chunked`, the one `map_bounded` task
group, required provider, optional provider, response validation/aggregation,
and immutable results. Sequence messages map exactly to service steps and use
an `alt` frame for success/optional warning, required failure, total timeout,
and caller cancellation. Both SVG files include accessible titles/descriptions,
English labels, no speculative HTTP/cache/retry nodes, and source-path notes.

Render PNG at scale 2 from the final SVG only. Run the skill's SVG text, bounds,
overlap, clipping, arrow, PNG parity, and full-size inspection gates. If a PNG
fails visual inspection, edit the SVG, rerender, and rerun every affected audit.

- [ ] **Step 4: Update root navigation and WIP**

Root English/Korean README current-status paragraphs link to the matching locale
example. Keep the milestone table unchanged except that #4 becomes runnable.
WIP records the branch and exact-head reporting policy, focused commands, validation
counts, current gate, PR boundary, and #5 as the next dependency-ready issue;
never predict a commit hash before it exists.

- [ ] **Step 5: Run documentation and visual proof**

```bash
uv run --locked pytest examples/catalog_enrichment/tests/test_documentation.py -q
uv run --locked pytest tests/test_documentation_contract.py -q
uv run --locked ruff check .
uv run --locked ruff format --check .
git diff --check
```

Expected: tests and Ruff pass; diff check is empty; every diagram audit and
full-size PNG inspection is recorded in the implementation review artifact.

- [ ] **Step 6: Commit reader guidance and visuals**

Commit Task 4 files with Lore intent
`Explain bounded catalog fan-out from input order through cleanup`.
`Tested:` includes documentation tests, diagram audits, PNG inspection, Ruff,
and diff check.

### Task 5: Converge validation, review, lesson, and exact-head PR delivery

**Complexity:** High  
**Dependencies:** Tasks 1–4 GREEN  
**Required skills:** `verification-before-completion`, `requesting-code-review`, `bluetape-py-patterns`, `bluetape-writer`, `bluetape-diagram`  
**Files:**
- Modify: `WIP.md`
- Create: `docs/superpowers/reviews/2026-07-15-issue-4-implementation-review.md`
- Create: `docs/superpowers/lessons/2026-07-15-issue-4-catalog-enrichment.md`

- [ ] **Step 1: Prove the exact implementation against spec and plan**

Run and read every result sequentially:

```bash
uv sync --locked --python 3.13.14
uv run --locked python -m examples.catalog_enrichment
uv run --locked pytest examples/catalog_enrichment/tests -q
uv run --locked pytest tests/test_dependency_baseline.py -q
uv run --locked ruff format --check .
uv run --locked ruff check .
uv run --locked pytest
GOTOOLCHAIN=go1.26.1 go run github.com/rhysd/actionlint/cmd/actionlint@v1.7.12 \
  .github/workflows/ci.yml
git diff --check
```

Also record SHA-256 of `pyproject.toml` and `uv.lock` against `develop`; both must
be unchanged. Docker/Testcontainers commands are N/A because the example never
imports or constructs those providers.

- [ ] **Step 2: Run performance/stability and six-lens implementation review**

Review the exact branch diff through performance, stability, security,
operator/Ops, developer/API, and user/caller lenses plus main integration.
Native lanes are read-only with zero heavy commands and a bounded response
window; any delayed lane is interrupted and immediately rerun in the main
session. Record file:line evidence, fixes, rerun commands, and final
`P0=0/P1=0` in the implementation review.

- [ ] **Step 3: Commit the required durable lesson**

The lesson records context, decision, any RED/failure surprise, outcome, exact
verification, review misses, and future guard. It must explain why one global
`map_bounded` call plus an explicit operational provider error preserves the
distinction among optional outages, defects, timeout, and cancellation. Commit
the lesson before PR creation using Lore intent
`Preserve the failure distinctions learned from bounded fan-out`.

- [ ] **Step 4: Finalize WIP and commit the exact pre-PR checkpoint**

WIP records the real validation counts and current local head policy, then the
checkpoint commit records why the branch is ready to publish. Rerun the full
Step 1 ladder on this exact head and verify `git status --short` is empty.

- [ ] **Step 5: Publish and create the authorized PR**

Push `feat/issue-4-bounded-catalog-enrichment` without force and verify local and
remote head SHAs match. Create the PR in
`bluetape4k/bluetape-py-workshop` targeting `develop`, assign `debop`, apply
milestone `0.1.0` and issue labels `enhancement`, `type:feature`, `area:async`,
and close #4. The English body explains why/what, validation, risk boundaries,
diagram review, lesson, and ends with final heading `## DoD Status`.

- [ ] **Step 6: Pass exact-head CI and post-PR review**

Wait for required checks on the exact remote SHA. Reread PR metadata, body,
reviews, and unresolved threads after CI succeeds. Rerun affected verification
after any correction commit and refresh the PR DoD body.

- [ ] **Step 7: Stop at the merge-ready boundary**

Report exact PR URL/number/head, successful CI, current reviews/threads,
diagram inspection, lesson, changed files, residual risks, and reconciled
Required/N/A/Blocked counts. Keep CG-16 through CG-18 pending and request a
fresh merge approval. Never enable auto-merge.

- [ ] **Step 8: Merge only after fresh exact-head approval**

After approval issued in response to the merge-ready report, rebase-merge the
exact PR, verify the live merge SHA and issue closure, sync local `develop`, and
remove only the merged issue #4 worktree and local branch. Remote branch
deletion remains outside cleanup unless separately requested.

## Pre-implementation approval gate

No example source, test, README, or diagram file may be created until:

1. this plan and its six-lens review converge at P0=0/P1=0;
2. the user explicitly approves the converged written plan;
3. the plan, review, and WIP checkpoint are committed;
4. machine workflow checks record `design_review` and `plan_review` PASS;
5. `test-driven-development` and `executing-plans` are read fresh.

Rollback before implementation is deleting the isolated feature worktree and
local branch; no external branch or PR exists at this gate.
