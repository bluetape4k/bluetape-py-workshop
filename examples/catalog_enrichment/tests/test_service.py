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
