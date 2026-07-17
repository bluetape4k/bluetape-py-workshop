import logging
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from typing import Protocol

from bluetape.compression import CompressionError
from bluetape.serde import SerdeError
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from examples.bounded_payload_processing import TransportLimitError
from examples.catalog_enrichment import CatalogEnrichmentFailed
from examples.integrated_order_backend.errors import (
    InvalidOrderBackendCommand,
    InvalidOrderLine,
    OrderBackendClosedError,
)
from examples.integrated_order_backend.models import OrderBackendCommand, ProcessedOrder

from .context import INVALID_REQUEST_ID, InvalidRequestId, parse_request_id, request_context
from .models import OrderProblem, OrderRequest, OrderResponse
from .providers import build_default_backend


class OrderBackend(Protocol):
    async def process(self, command: OrderBackendCommand) -> ProcessedOrder: ...

    async def aclose(self) -> None: ...


type BackendFactory = Callable[[], OrderBackend]


def _emit(
    logger: logging.Logger,
    level: int,
    event: str,
    *,
    status: int,
    error_kind: str,
) -> None:
    try:
        logger.log(
            level,
            event,
            extra={"status": status, "error_kind": error_kind},
        )
    except Exception:
        return


def _problem(
    *,
    status: int,
    code: str,
    message: str,
    request_id: str,
    field: str | None = None,
    line_index: int | None = None,
) -> JSONResponse:
    body = OrderProblem(
        code=code,
        message=message,
        request_id=request_id,
        field=field,
        line_index=line_index,
    )
    return JSONResponse(
        status_code=status,
        content=body.model_dump(exclude_none=True),
    )


def _request_id_or_sentinel(request: Request) -> str:
    try:
        return parse_request_id(request.headers)
    except InvalidRequestId:
        return INVALID_REQUEST_ID


def _is_json_request(request: Request) -> bool:
    media_type = request.headers.get("content-type", "").split(";", 1)[0]
    return media_type.strip().lower() == "application/json"


def _safe_validation_field(error: RequestValidationError) -> str | None:
    errors = error.errors()
    if not errors:
        return None
    parts = errors[0].get("loc", ())
    safe: list[str] = []
    for part in parts:
        if isinstance(part, int):
            safe.append(f"[{part}]")
        elif isinstance(part, str) and part.isidentifier():
            safe.append(("." if safe else "") + part)
    field = "".join(safe)
    return field[:128] or None


async def validation_exception_handler(
    request: Request,
    error: RequestValidationError,
) -> JSONResponse:
    request_id = _request_id_or_sentinel(request)
    logger: logging.Logger = request.app.state.transport_logger
    with request_context(request_id):
        _emit(
            logger,
            logging.WARNING,
            "order_api.request_rejected",
            status=422,
            error_kind="invalid_request",
        )
        return _problem(
            status=422,
            code="invalid_request",
            message="Request validation failed.",
            request_id=request_id,
            field=_safe_validation_field(error),
        )


async def submit_order(request: Request, order: OrderRequest):
    request_id = _request_id_or_sentinel(request)
    logger: logging.Logger = request.app.state.transport_logger
    with request_context(request_id):
        if request_id == INVALID_REQUEST_ID or not _is_json_request(request):
            _emit(
                logger,
                logging.WARNING,
                "order_api.request_rejected",
                status=422,
                error_kind="invalid_request",
            )
            return _problem(
                status=422,
                code="invalid_request",
                message="Request validation failed.",
                request_id=request_id,
            )

        backend: OrderBackend = request.app.state.order_backend
        try:
            result = await backend.process(order.to_command(request_id))
        except InvalidOrderBackendCommand as error:
            _emit(
                logger,
                logging.WARNING,
                "order_api.request_rejected",
                status=422,
                error_kind="invalid_order",
            )
            return _problem(
                status=422,
                code="invalid_order",
                message=error.reason,
                request_id=request_id,
                field=error.field,
            )
        except InvalidOrderLine as error:
            _emit(
                logger,
                logging.WARNING,
                "order_api.request_rejected",
                status=422,
                error_kind="invalid_order",
            )
            return _problem(
                status=422,
                code="invalid_order",
                message=error.reason,
                request_id=request_id,
                field=error.field,
                line_index=error.index,
            )
        except CatalogEnrichmentFailed:
            _emit(
                logger,
                logging.WARNING,
                "order_api.request_failed",
                status=503,
                error_kind="catalog_unavailable",
            )
            return _problem(
                status=503,
                code="catalog_unavailable",
                message="Catalog is temporarily unavailable.",
                request_id=request_id,
            )
        except OrderBackendClosedError:
            _emit(
                logger,
                logging.WARNING,
                "order_api.request_failed",
                status=503,
                error_kind="backend_unavailable",
            )
            return _problem(
                status=503,
                code="backend_unavailable",
                message="Order backend is temporarily unavailable.",
                request_id=request_id,
            )
        except TimeoutError:
            _emit(
                logger,
                logging.WARNING,
                "order_api.request_timed_out",
                status=504,
                error_kind="order_timeout",
            )
            return _problem(
                status=504,
                code="order_timeout",
                message="Order processing timed out.",
                request_id=request_id,
            )
        except (TransportLimitError, CompressionError, SerdeError):
            _emit(
                logger,
                logging.ERROR,
                "order_api.request_failed",
                status=500,
                error_kind="order_processing_failed",
            )
            return _problem(
                status=500,
                code="order_processing_failed",
                message="Order processing failed.",
                request_id=request_id,
            )
        except Exception:
            _emit(
                logger,
                logging.ERROR,
                "order_api.request_failed",
                status=500,
                error_kind="unexpected_error",
            )
            return _problem(
                status=500,
                code="internal_error",
                message="Internal server error.",
                request_id=request_id,
            )

        response = OrderResponse(
            request_id=result.request_id,
            partner_id=result.partner_id,
            order_id=result.order_id,
            line_count=len(result.lines),
            total_cents=result.total_cents,
            warning_count=sum(len(line.warnings) for line in result.lines),
        )
        _emit(
            logger,
            logging.INFO,
            "order_api.request_succeeded",
            status=200,
            error_kind="none",
        )
        return response


def create_app(
    *,
    backend_factory: BackendFactory = build_default_backend,
    transport_logger: logging.Logger | None = None,
) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        backend = backend_factory()
        app.state.order_backend = backend
        yield
        await backend.aclose()
        del app.state.order_backend

    app = FastAPI(lifespan=lifespan)
    app.state.transport_logger = transport_logger or logging.getLogger(
        "examples.fastapi_order_api.transport"
    )
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_api_route(
        "/orders",
        submit_order,
        methods=["POST"],
        response_model=OrderResponse,
        responses={
            422: {"model": OrderProblem},
            503: {"model": OrderProblem},
            504: {"model": OrderProblem},
            500: {"model": OrderProblem},
        },
    )
    return app
