import logging
import math

from bluetape.cache import CacheStats
from bluetape.logging import log_context
from bluetape.serde import JsonValue

from examples.bounded_payload_processing import JsonPayloadService
from examples.cached_product_catalog import AsyncProductCatalogService
from examples.catalog_enrichment import MAX_BATCH_SIZE, CatalogEnrichmentService
from examples.order_intake import (
    AcceptedOrder,
    InvalidOrderCommand,
    OrderIntakeService,
    PartnerOrderCommand,
)

from .errors import InvalidOrderBackendCommand, InvalidOrderLine
from .models import (
    OrderBackendCommand,
    OrderLineCommand,
    ProcessedOrder,
    ProcessedOrderLine,
)


def _positive_exact_int(name: str, value: object) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact int")
    if value <= 0:
        raise ValueError(f"{name} must be positive")
    return value


def _positive_timeout(name: str, value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise TypeError(f"{name} must be a finite positive number")
    timeout = float(value)
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError(f"{name} must be a finite positive number")
    return timeout


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
            "concurrency_limit",
            concurrency_limit,
        )
        self._provider_timeout = _positive_timeout(
            "provider_timeout",
            provider_timeout,
        )

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

    async def cache_stats(self) -> CacheStats:
        return await self._catalog.stats()
