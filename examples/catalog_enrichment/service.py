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
from .models import (
    CatalogRecord,
    EnrichedProduct,
    EnrichmentWarning,
    RecommendationRecord,
    WarningCode,
)
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


_WARNING_MESSAGES: dict[WarningCode, str] = {
    "optional_provider_failed": "recommendation provider is unavailable",
    "optional_record_missing": "recommendation is unavailable",
    "optional_record_invalid": "recommendation record is invalid",
    "optional_response_invalid": "recommendation response is invalid",
}


def _normalize_product_ids(product_ids: Iterable[str]) -> list[str]:
    normalized: list[str] = []
    for index, value in enumerate(product_ids):
        if index == MAX_PRODUCT_IDENTIFIERS:
            raise TooManyProductIdentifiers(MAX_PRODUCT_IDENTIFIERS)
        field = f"product_ids[{index}]"
        try:
            trimmed = require_not_blank(require_instance(value, str, field), field).strip()
        except (TypeError, ValueError) as error:
            raise InvalidProductIdentifier(index, "must be a non-blank string") from error
        if not trimmed.isascii():
            raise InvalidProductIdentifier(index, "must use ASCII SKU characters")
        if len(trimmed) > MAX_PRODUCT_ID_LENGTH:
            raise InvalidProductIdentifier(
                index,
                f"must contain at most {MAX_PRODUCT_ID_LENGTH} characters",
            )
        product_id = trimmed.upper()
        if _PRODUCT_ID.fullmatch(product_id) is None:
            raise InvalidProductIdentifier(index, "must use ASCII SKU characters")
        normalized.append(product_id)
    return normalized


def _warning(product_id: str, code: WarningCode) -> EnrichmentWarning:
    return EnrichmentWarning(
        product_id=product_id,
        provider="recommendations",
        code=code,
        message=_WARNING_MESSAGES[code],
    )


def _valid_catalog_record(product_id: str, value: object) -> bool:
    return (
        isinstance(value, CatalogRecord)
        and value.product_id == product_id
        and isinstance(value.name, str)
        and bool(value.name.strip())
        and isinstance(value.price_cents, int)
        and not isinstance(value.price_cents, bool)
        and value.price_cents >= 0
    )


def _valid_recommendation_record(product_id: str, value: object) -> bool:
    return (
        isinstance(value, RecommendationRecord)
        and value.product_id == product_id
        and isinstance(value.recommendation, str)
        and bool(value.recommendation.strip())
    )


def _exception_leaves(group: ExceptionGroup[Exception]) -> list[Exception]:
    leaves: list[Exception] = []
    for error in group.exceptions:
        if isinstance(error, ExceptionGroup):
            leaves.extend(_exception_leaves(error))
        else:
            leaves.append(error)
    return leaves


class CatalogEnrichmentService:
    def __init__(
        self,
        catalog_provider: RequiredCatalogProvider,
        recommendation_provider: OptionalRecommendationProvider,
    ) -> None:
        if not callable(getattr(catalog_provider, "fetch", None)):
            raise TypeError("catalog_provider must define an async fetch method")
        if not callable(getattr(recommendation_provider, "fetch", None)):
            raise TypeError("recommendation_provider must define an async fetch method")
        self._catalog_provider = catalog_provider
        self._recommendation_provider = recommendation_provider

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

        catalog = {record.product_id: record for outcome in outcomes for record in outcome.catalog}
        recommendations = {
            record.product_id: record for outcome in outcomes for record in outcome.recommendations
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

    async def _run_job(self, job: _ProviderJob) -> _JobOutcome:
        if job.kind == "catalog":
            return await self._run_catalog_job(job)
        return await self._run_recommendation_job(job)

    async def _run_catalog_job(self, job: _ProviderJob) -> _JobOutcome:
        try:
            response = await self._catalog_provider.fetch(job.product_ids)
        except ProviderUnavailable as error:
            raise RequiredProviderFailure(job.batch_index, "provider_unavailable") from error
        if not isinstance(response, Mapping) or set(response) != set(job.product_ids):
            raise RequiredProviderFailure(job.batch_index, "response_invalid")
        records: list[CatalogRecord] = []
        for product_id in job.product_ids:
            value = response[product_id]
            if not _valid_catalog_record(product_id, value):
                raise RequiredProviderFailure(job.batch_index, "response_invalid")
            records.append(cast(CatalogRecord, value))
        return _JobOutcome(catalog=tuple(records))

    async def _run_recommendation_job(self, job: _ProviderJob) -> _JobOutcome:
        try:
            response = await self._recommendation_provider.fetch(job.product_ids)
        except ProviderUnavailable:
            return _JobOutcome(
                warnings=tuple(
                    _warning(product_id, "optional_provider_failed")
                    for product_id in job.product_ids
                )
            )
        if not isinstance(response, Mapping) or any(
            product_id not in job.product_ids for product_id in response
        ):
            return _JobOutcome(
                warnings=tuple(
                    _warning(product_id, "optional_response_invalid")
                    for product_id in job.product_ids
                )
            )
        records: list[RecommendationRecord] = []
        warnings: list[EnrichmentWarning] = []
        for product_id in job.product_ids:
            if product_id not in response:
                warnings.append(_warning(product_id, "optional_record_missing"))
                continue
            value = response[product_id]
            if not _valid_recommendation_record(product_id, value):
                warnings.append(_warning(product_id, "optional_record_invalid"))
                continue
            records.append(cast(RecommendationRecord, value))
        return _JobOutcome(recommendations=tuple(records), warnings=tuple(warnings))
