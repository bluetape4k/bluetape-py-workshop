import asyncio
import importlib
from collections.abc import Mapping
from dataclasses import FrozenInstanceError
from types import ModuleType

import pytest

from examples.catalog_enrichment import (
    CatalogEnrichmentFailed,
    CatalogEnrichmentService,
    CatalogRecord,
    InvalidProductIdentifier,
    ProviderUnavailable,
    RecommendationRecord,
    RequiredProviderFailure,
    TooManyProductIdentifiers,
)


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


class GatedCatalogProvider:
    def __init__(self, gate: ConcurrencyGate) -> None:
        self.gate = gate

    async def fetch(self, product_ids: tuple[str, ...]) -> object:
        await self.gate.enter()
        return {
            product_id: CatalogRecord(
                product_id=product_id,
                name=f"Product {product_id}",
                price_cents=1000,
            )
            for product_id in product_ids
        }


class GatedRecommendationProvider:
    def __init__(self, gate: ConcurrencyGate) -> None:
        self.gate = gate

    async def fetch(self, product_ids: tuple[str, ...]) -> object:
        await self.gate.enter()
        return {
            product_id: RecommendationRecord(
                product_id=product_id,
                recommendation=f"PAIR-{product_id}",
            )
            for product_id in product_ids
        }


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


class CatalogProvider:
    def __init__(self, records: Mapping[str, CatalogRecord]) -> None:
        self.records = dict(records)
        self.calls: list[tuple[str, ...]] = []
        self.error: BaseException | None = None
        self.response_override: object | None = None

    async def fetch(self, product_ids: tuple[str, ...]) -> object:
        self.calls.append(product_ids)
        if self.error is not None:
            raise self.error
        if self.response_override is not None:
            return self.response_override
        return {product_id: self.records[product_id] for product_id in product_ids}


class RecommendationProvider:
    def __init__(self, records: Mapping[str, RecommendationRecord]) -> None:
        self.records = dict(records)
        self.calls: list[tuple[str, ...]] = []
        self.error: BaseException | None = None
        self.response_override: object | None = None

    async def fetch(self, product_ids: tuple[str, ...]) -> object:
        self.calls.append(product_ids)
        if self.error is not None:
            raise self.error
        if self.response_override is not None:
            return self.response_override
        return {
            product_id: self.records[product_id]
            for product_id in product_ids
            if product_id in self.records
        }


@pytest.fixture
def providers() -> tuple[CatalogProvider, RecommendationProvider]:
    catalog = CatalogProvider(
        {
            "SKU-1": CatalogRecord(product_id="SKU-1", name="Desk", price_cents=12000),
            "SKU-2": CatalogRecord(product_id="SKU-2", name="Chair", price_cents=8000),
            "SKU-3": CatalogRecord(product_id="SKU-3", name="Lamp", price_cents=4500),
        }
    )
    recommendations = RecommendationProvider(
        {
            "SKU-1": RecommendationRecord(
                product_id="SKU-1",
                recommendation="PAIR-SKU-9",
            ),
            "SKU-2": RecommendationRecord(
                product_id="SKU-2",
                recommendation="PAIR-SKU-8",
            ),
        }
    )
    return catalog, recommendations


async def test_duplicate_work_is_deduplicated_and_results_are_restored(providers) -> None:
    catalog, recommendations = providers
    source = [" sku-2 ", "sku-1", "SKU-2", "sku-3"]
    api = _load_api()
    service = api.CatalogEnrichmentService(catalog, recommendations)

    result = await service.enrich(source, batch_size=2, concurrency_limit=2, timeout=1.0)

    assert source == [" sku-2 ", "sku-1", "SKU-2", "sku-3"]
    assert [item.product_id for item in result] == ["SKU-2", "SKU-1", "SKU-2", "SKU-3"]
    assert catalog.calls == [("SKU-2", "SKU-1"), ("SKU-3",)]
    assert recommendations.calls == [("SKU-2", "SKU-1"), ("SKU-3",)]
    assert result[2] == result[0]
    assert result[3].warnings[0].code == "optional_record_missing"


async def test_empty_input_calls_no_provider_and_still_validates_configuration(providers) -> None:
    catalog, recommendations = providers
    service = _load_api().CatalogEnrichmentService(catalog, recommendations)

    assert await service.enrich([], batch_size=2, concurrency_limit=1, timeout=None) == []
    assert catalog.calls == []
    assert recommendations.calls == []
    with pytest.raises(ValueError, match="limit must be greater than 0"):
        await service.enrich([], batch_size=2, concurrency_limit=0, timeout=None)


@pytest.mark.parametrize("value", ["", "   ", "SKU/1", "ß", "a" * 65, 7, None])
async def test_invalid_identifier_fails_before_provider_calls(providers, value: object) -> None:
    catalog, recommendations = providers
    service = _load_api().CatalogEnrichmentService(catalog, recommendations)

    with pytest.raises(InvalidProductIdentifier):
        await service.enrich(  # type: ignore[list-item]
            [value],
            batch_size=2,
            concurrency_limit=1,
            timeout=None,
        )
    assert catalog.calls == []
    assert recommendations.calls == []


async def test_occurrence_and_batch_limits_fail_before_provider_calls(providers) -> None:
    catalog, recommendations = providers
    service = _load_api().CatalogEnrichmentService(catalog, recommendations)

    with pytest.raises(TooManyProductIdentifiers) as captured:
        await service.enrich(
            ("SKU-1" for _ in range(1001)),
            batch_size=2,
            concurrency_limit=1,
            timeout=None,
        )
    assert captured.value.limit == 1000
    with pytest.raises(ValueError, match="batch_size must be less than or equal to 100"):
        await service.enrich(["SKU-1"], batch_size=101, concurrency_limit=1, timeout=None)
    assert catalog.calls == []
    assert recommendations.calls == []


async def test_required_operational_failure_becomes_safe_request_failure(providers) -> None:
    catalog, recommendations = providers
    catalog.error = ProviderUnavailable()
    catalog.error.__cause__ = RuntimeError("secret-provider-detail")
    service = _load_api().CatalogEnrichmentService(catalog, recommendations)

    with pytest.raises(CatalogEnrichmentFailed) as captured:
        await service.enrich(["SKU-1"], batch_size=1, concurrency_limit=1, timeout=None)
    assert captured.value.failures[0].code == "provider_unavailable"
    assert "secret-provider-detail" not in str(captured.value)


async def test_optional_operational_failure_becomes_warning(providers) -> None:
    catalog, recommendations = providers
    recommendations.error = ProviderUnavailable()
    service = _load_api().CatalogEnrichmentService(catalog, recommendations)

    result = await service.enrich(
        ["SKU-1"],
        batch_size=1,
        concurrency_limit=2,
        timeout=None,
    )

    assert result[0].warnings[0].code == "optional_provider_failed"
    assert result[0].recommendation is None


async def test_unexpected_optional_defect_propagates(providers) -> None:
    catalog, recommendations = providers
    recommendations.error = AssertionError("programming defect")
    service = _load_api().CatalogEnrichmentService(catalog, recommendations)

    with pytest.raises(ExceptionGroup) as captured:
        await service.enrich(["SKU-1"], batch_size=1, concurrency_limit=2, timeout=None)
    assert any(isinstance(error, AssertionError) for error in captured.value.exceptions)


@pytest.mark.parametrize(
    "response",
    [
        {},
        {
            "SKU-1": CatalogRecord(product_id="SKU-1", name="Desk", price_cents=12000),
            "SKU-X": CatalogRecord(product_id="SKU-X", name="Other", price_cents=1),
        },
        {"SKU-1": CatalogRecord(product_id="SKU-2", name="Desk", price_cents=12000)},
        {"SKU-1": CatalogRecord(product_id="SKU-1", name=" ", price_cents=12000)},
        {"SKU-1": CatalogRecord(product_id="SKU-1", name="Desk", price_cents=True)},
        {"SKU-1": CatalogRecord(product_id="SKU-1", name="Desk", price_cents=-1)},
    ],
)
async def test_invalid_required_response_fails_closed(providers, response: object) -> None:
    catalog, recommendations = providers
    catalog.response_override = response
    service = _load_api().CatalogEnrichmentService(catalog, recommendations)

    with pytest.raises(CatalogEnrichmentFailed) as captured:
        await service.enrich(["SKU-1"], batch_size=1, concurrency_limit=1, timeout=None)
    assert captured.value.failures[0].code == "response_invalid"
    assert "Other" not in str(captured.value)


@pytest.mark.parametrize(
    ("response", "code"),
    [
        ({}, "optional_record_missing"),
        (
            {"SKU-1": RecommendationRecord(product_id="SKU-2", recommendation="PAIR")},
            "optional_record_invalid",
        ),
        (
            {"SKU-1": RecommendationRecord(product_id="SKU-1", recommendation=" ")},
            "optional_record_invalid",
        ),
    ],
)
async def test_optional_response_problem_becomes_warning(providers, response, code: str) -> None:
    catalog, recommendations = providers
    recommendations.response_override = response
    service = _load_api().CatalogEnrichmentService(catalog, recommendations)

    result = await service.enrich(["SKU-1"], batch_size=1, concurrency_limit=2, timeout=None)

    assert result[0].warnings[0].code == code
    assert result[0].recommendation is None


async def test_optional_extra_key_discards_the_batch(providers) -> None:
    catalog, recommendations = providers
    recommendations.response_override = {
        "SKU-1": RecommendationRecord(product_id="SKU-1", recommendation="PAIR-1"),
        "SKU-2": RecommendationRecord(product_id="SKU-2", recommendation="PAIR-2"),
        "SKU-X": RecommendationRecord(product_id="SKU-X", recommendation="secret-extra"),
    }
    service = _load_api().CatalogEnrichmentService(catalog, recommendations)

    result = await service.enrich(
        ["SKU-1", "SKU-2"],
        batch_size=2,
        concurrency_limit=2,
        timeout=None,
    )

    assert [item.recommendation for item in result] == [None, None]
    assert [item.warnings[0].code for item in result] == [
        "optional_response_invalid",
        "optional_response_invalid",
    ]
    assert "secret-extra" not in str(result)


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
    service = CatalogEnrichmentService(
        GatedCatalogProvider(gate),
        GatedRecommendationProvider(gate),
    )

    with pytest.raises(TimeoutError):
        await service.enrich(["SKU-1"], batch_size=1, concurrency_limit=2, timeout=0.01)
    assert gate.active == 0
    assert gate.cleaned == 2
    _assert_no_helper_tasks()


async def test_caller_cancellation_remains_native_and_cleans_siblings() -> None:
    release = asyncio.Event()
    gate = ConcurrencyGate(release)
    service = CatalogEnrichmentService(
        GatedCatalogProvider(gate),
        GatedRecommendationProvider(gate),
    )
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


async def test_required_outage_cleans_optional_sibling() -> None:
    sibling_entered = asyncio.Event()
    sibling_cleaned = 0

    class OutageCatalogProvider:
        async def fetch(self, product_ids: tuple[str, ...]) -> object:
            await sibling_entered.wait()
            raise ProviderUnavailable()

    class WaitingRecommendationProvider:
        async def fetch(self, product_ids: tuple[str, ...]) -> object:
            nonlocal sibling_cleaned
            sibling_entered.set()
            try:
                await asyncio.Event().wait()
            finally:
                sibling_cleaned += 1

    service = CatalogEnrichmentService(OutageCatalogProvider(), WaitingRecommendationProvider())

    with pytest.raises(CatalogEnrichmentFailed):
        await service.enrich(["SKU-1"], batch_size=1, concurrency_limit=2, timeout=None)
    assert sibling_cleaned == 1
    _assert_no_helper_tasks()


async def test_mixed_operational_outage_and_defect_propagates_exception_group() -> None:
    both_entered = asyncio.Event()
    release = asyncio.Event()
    entered = 0

    async def rendezvous() -> None:
        nonlocal entered
        entered += 1
        if entered == 2:
            both_entered.set()
        await release.wait()

    class OutageCatalogProvider:
        async def fetch(self, product_ids: tuple[str, ...]) -> object:
            await rendezvous()
            raise ProviderUnavailable()

    class DefectiveRecommendationProvider:
        async def fetch(self, product_ids: tuple[str, ...]) -> object:
            await rendezvous()
            raise AssertionError("programming defect")

    service = CatalogEnrichmentService(
        OutageCatalogProvider(),
        DefectiveRecommendationProvider(),
    )
    task = asyncio.create_task(
        service.enrich(["SKU-1"], batch_size=1, concurrency_limit=2, timeout=None)
    )
    await asyncio.wait_for(both_entered.wait(), timeout=1.0)
    release.set()

    with pytest.raises(ExceptionGroup) as captured:
        await task
    leaves = captured.value.exceptions
    assert any(isinstance(error, AssertionError) for error in leaves)
    assert any(isinstance(error, RequiredProviderFailure) for error in leaves)
    _assert_no_helper_tasks()
