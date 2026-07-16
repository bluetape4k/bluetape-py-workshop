from __future__ import annotations

import asyncio
import logging
import math

from bluetape.cache import CacheStats
from bluetape.compression import CompressionError
from bluetape.serde import SerdeError

from examples.bounded_payload_processing import TransportLimitError
from examples.catalog_enrichment import CatalogEnrichmentFailed

from .errors import (
    InvalidOrderBackendCommand,
    InvalidOrderLine,
    OrderBackendClosedError,
    OrderBackendShutdownError,
)
from .models import OrderBackendCommand, ProcessedOrder
from .service import OrderBackendService


def _positive_timeout(name: str, value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise TypeError(f"{name} must be a finite positive number")
    timeout = float(value)
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError(f"{name} must be a finite positive number")
    return timeout


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


def _error_kind(error: Exception) -> str:
    if isinstance(error, InvalidOrderBackendCommand | InvalidOrderLine):
        return "invalid_order"
    if isinstance(error, CatalogEnrichmentFailed):
        return "catalog_enrichment_failed"
    if isinstance(error, TransportLimitError | CompressionError | SerdeError):
        return "payload_rejected"
    return "unexpected_error"


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
        self._request_timeout = _positive_timeout(
            "request_timeout",
            request_timeout,
        )
        self._shutdown_grace_timeout = _positive_timeout(
            "shutdown_grace_timeout",
            shutdown_grace_timeout,
        )
        self._shutdown_cancel_timeout = _positive_timeout(
            "shutdown_cancel_timeout",
            shutdown_cancel_timeout,
        )
        self._loop: asyncio.AbstractEventLoop | None = None
        self._state = "OPEN"
        self._requests: set[asyncio.Task[ProcessedOrder]] = set()
        self._close_task: asyncio.Task[None] | None = None
        self._request_sequence = 0

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

    async def __aexit__(self, exc_type, exc, traceback) -> bool:
        try:
            await self.aclose()
        except OrderBackendShutdownError:
            if exc is None:
                raise
            exc.add_note("order backend cleanup did not reach terminal state")
        return False
