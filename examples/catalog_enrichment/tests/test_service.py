import importlib
from collections.abc import Mapping
from dataclasses import FrozenInstanceError
from types import ModuleType

import pytest

from examples.catalog_enrichment import (
    CatalogEnrichmentFailed,
    CatalogRecord,
    InvalidProductIdentifier,
    ProviderUnavailable,
    RecommendationRecord,
    TooManyProductIdentifiers,
)


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
