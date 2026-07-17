import asyncio
import importlib
import logging
from collections.abc import Mapping
from types import ModuleType, SimpleNamespace

import pytest

pytest.importorskip("fastapi", reason="requires the fastapi-order-api extra")

from bluetape.logging import ContextLogFilter, get_log_context, log_context
from bluetape.testing import eventually_async
from fastapi import Request
from fastapi.testclient import TestClient

from examples.bounded_payload_processing import TransportLimitError
from examples.cached_product_catalog import ProductSummary
from examples.catalog_enrichment import ProviderUnavailable
from examples.catalog_enrichment.errors import (
    CatalogEnrichmentFailed,
    RequiredProviderFailure,
)
from examples.catalog_enrichment.models import RecommendationRecord
from examples.integrated_order_backend import build_application
from examples.integrated_order_backend.errors import (
    InvalidOrderBackendCommand,
    InvalidOrderLine,
    OrderBackendClosedError,
    OrderBackendShutdownError,
)


def _load_application() -> ModuleType:
    try:
        return importlib.import_module("examples.fastapi_order_api.application")
    except ModuleNotFoundError as error:
        pytest.fail(f"FastAPI order application is missing: {error}")


class InstrumentedBackend:
    def __init__(self, *, fail_close: bool = False, result=None, failure=None) -> None:
        self.close_calls = 0
        self.fail_close = fail_close
        self.result = result
        self.failure = failure
        self.commands = []

    async def process(self, command):
        self.commands.append(command)
        if self.failure is not None:
            raise self.failure
        if self.result is None:
            raise AssertionError(f"unexpected process call: {command!r}")
        return self.result

    async def aclose(self) -> None:
        self.close_calls += 1
        if self.fail_close:
            raise OrderBackendShutdownError(1)


class BackendFactory:
    def __init__(self, backend: InstrumentedBackend) -> None:
        self.backend = backend
        self.calls = 0

    def __call__(self) -> InstrumentedBackend:
        self.calls += 1
        return self.backend


class CaptureHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__(logging.INFO)
        self.records: list[logging.LogRecord] = []
        self.addFilter(ContextLogFilter())

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


def _transport_logger() -> tuple[logging.Logger, CaptureHandler]:
    logger = logging.Logger("fastapi-order-transport-test", level=logging.INFO)
    logger.propagate = False
    handler = CaptureHandler()
    logger.addHandler(handler)
    return logger, handler


def _result():
    return SimpleNamespace(
        request_id="req-1001",
        partner_id="partner-7",
        order_id="order-9001",
        lines=(
            SimpleNamespace(warnings=(), recommendation="PAIR-SKU-9"),
            SimpleNamespace(warnings=(), recommendation=None),
        ),
        total_cents=32_900,
        artifact=SimpleNamespace(data=b"secret-artifact"),
    )


def _body() -> dict[str, object]:
    return {
        "partner_id": "partner-7",
        "order_id": "order-9001",
        "lines": [
            {"sku": "SKU-1", "quantity": 2},
            {"sku": "SKU-2", "quantity": 1},
        ],
    }


def _client(*, backend: InstrumentedBackend, raise_server_exceptions: bool = True):
    application = _load_application()
    logger, handler = _transport_logger()
    app = application.create_app(
        backend_factory=BackendFactory(backend),
        transport_logger=logger,
    )
    return TestClient(app, raise_server_exceptions=raise_server_exceptions), logger, handler


def _add_backend_identity_route(app) -> None:
    async def backend_identity(request: Request) -> dict[str, int]:
        return {"backend_id": id(request.app.state.order_backend)}

    app.add_api_route("/_backend-id", backend_identity, methods=["GET"])


def test_lifespan_constructs_one_shared_backend_and_closes_it_once() -> None:
    application = _load_application()
    backend = InstrumentedBackend()
    factory = BackendFactory(backend)
    app = application.create_app(backend_factory=factory)
    _add_backend_identity_route(app)

    with TestClient(app) as client:
        first = client.get("/_backend-id")
        second = client.get("/_backend-id")

        assert factory.calls == 1
        assert first.json() == second.json() == {"backend_id": id(backend)}
        assert app.state.order_backend is backend

    assert backend.close_calls == 1
    assert not hasattr(app.state, "order_backend")


def test_lifespan_retains_backend_state_when_close_fails() -> None:
    application = _load_application()
    backend = InstrumentedBackend(fail_close=True)
    factory = BackendFactory(backend)
    app = application.create_app(backend_factory=factory)

    with pytest.raises(OrderBackendShutdownError) as raised:
        with TestClient(app):
            assert app.state.order_backend is backend

    assert raised.value.pending_count == 1
    assert factory.calls == 1
    assert backend.close_calls == 1
    assert app.state.order_backend is backend


async def test_demo_catalog_maps_unknown_sku_to_safe_provider_signal() -> None:
    providers = importlib.import_module("examples.fastapi_order_api.providers")

    product = await providers.demo_catalog_loader("SKU-1")

    assert (product.product_id, product.name, product.price_cents) == (
        "SKU-1",
        "Mechanical Keyboard",
        12_500,
    )
    with pytest.raises(ProviderUnavailable):
        await providers.demo_catalog_loader("SECRET-SKU")


def test_post_orders_returns_only_the_allowlisted_success_shape() -> None:
    backend = InstrumentedBackend(result=_result())
    client, logger, handler = _client(backend=backend)

    with log_context(request_id="outer"), client:
        response = client.post(
            "/orders",
            headers={"X-Request-ID": " req-1001 "},
            json=_body(),
        )
        logger.info("after")
        assert get_log_context()["request_id"] == "outer"

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.json() == {
        "request_id": "req-1001",
        "partner_id": "partner-7",
        "order_id": "order-9001",
        "line_count": 2,
        "total_cents": 32_900,
        "warning_count": 0,
    }
    assert "artifact" not in response.text
    assert "recommendation" not in response.text
    assert backend.commands[0].request_id == "req-1001"
    assert [record.getMessage() for record in handler.records[-2:]] == [
        "order_api.request_succeeded",
        "after",
    ]
    assert [record.request_id for record in handler.records[-2:]] == ["req-1001", "outer"]


@pytest.mark.parametrize(
    ("body", "headers"),
    [
        ({**_body(), "secret": "raw-input"}, {"X-Request-ID": "req-1001"}),
        ({**_body(), "lines": []}, {"X-Request-ID": "req-1001"}),
        (_body(), {}),
    ],
)
def test_invalid_requests_use_the_stable_redacted_problem(body, headers) -> None:
    backend = InstrumentedBackend(result=_result())
    client, _, _ = _client(backend=backend)

    with client:
        response = client.post("/orders", headers=headers, json=body)

    assert response.status_code == 422
    assert response.json()["code"] in {"invalid_request", "invalid_order"}
    assert set(response.json()) <= {"code", "message", "request_id", "field", "line_index"}
    assert "raw-input" not in response.text


def test_whitespace_only_identifier_reaches_backend_domain_rejection() -> None:
    backend = InstrumentedBackend(
        failure=InvalidOrderLine(index=0, field="partner_id", reason="must not be blank")
    )
    client, _, _ = _client(backend=backend)
    body = {**_body(), "partner_id": "   "}

    with client:
        response = client.post(
            "/orders",
            headers={"X-Request-ID": "req-1001"},
            json=body,
        )

    assert response.status_code == 422
    assert response.json() == {
        "code": "invalid_order",
        "message": "must not be blank",
        "request_id": "req-1001",
        "field": "partner_id",
        "line_index": 0,
    }
    assert backend.commands[0].partner_id == "   "


def test_duplicate_request_id_and_non_json_content_are_rejected_as_422() -> None:
    backend = InstrumentedBackend(result=_result())
    client, _, _ = _client(backend=backend)

    with client:
        duplicate = client.post(
            "/orders",
            headers=[
                ("X-Request-ID", "req-1"),
                ("X-Request-ID", "req-2"),
                ("Content-Type", "application/json"),
            ],
            content='{"partner_id":"partner-7","order_id":"order-1","lines":[]}',
        )
        non_json = client.post(
            "/orders",
            headers={"X-Request-ID": "req-1", "Content-Type": "text/plain"},
            content="raw-input",
        )

    assert duplicate.status_code == 422
    assert duplicate.json()["request_id"] == "<invalid>"
    assert non_json.status_code == 422
    assert non_json.json()["code"] == "invalid_request"
    assert "raw-input" not in non_json.text


@pytest.mark.parametrize(
    ("failure", "status", "code", "event"),
    [
        (
            InvalidOrderBackendCommand("lines", "bad"),
            422,
            "invalid_order",
            "order_api.request_rejected",
        ),
        (
            InvalidOrderLine(index=0, field="sku", reason="bad"),
            422,
            "invalid_order",
            "order_api.request_rejected",
        ),
        (
            CatalogEnrichmentFailed((RequiredProviderFailure(0, "provider_unavailable"),)),
            503,
            "catalog_unavailable",
            "order_api.request_failed",
        ),
        (OrderBackendClosedError(), 503, "backend_unavailable", "order_api.request_failed"),
        (TimeoutError(), 504, "order_timeout", "order_api.request_timed_out"),
        (
            TransportLimitError(stage="encoded", actual_size=2, limit=1),
            500,
            "order_processing_failed",
            "order_api.request_failed",
        ),
        (RuntimeError("provider-secret"), 500, "internal_error", "order_api.request_failed"),
    ],
)
def test_backend_failures_map_to_stable_redacted_problems(failure, status, code, event) -> None:
    backend = InstrumentedBackend(failure=failure)
    client, _, handler = _client(backend=backend, raise_server_exceptions=False)

    with client:
        response = client.post(
            "/orders",
            headers={"X-Request-ID": "req-1001"},
            json=_body(),
        )

    assert response.status_code == status
    assert response.json()["code"] == code
    assert response.json()["request_id"] == "req-1001"
    assert "provider-secret" not in response.text
    assert "secret-artifact" not in response.text
    record = handler.records[-1]
    assert record.getMessage() == event
    assert record.request_id == "req-1001"
    assert record.status == status
    assert set(record.__dict__) >= {"error_kind"}
    assert "provider-secret" not in record.getMessage()


def test_openapi_documents_the_explicit_success_and_problem_contracts() -> None:
    backend = InstrumentedBackend(result=_result())
    client, _, _ = _client(backend=backend)

    with client:
        schema = client.get("/openapi.json").json()

    responses = schema["paths"]["/orders"]["post"]["responses"]
    assert set(responses) >= {"200", "422", "503", "504", "500"}
    assert responses["200"]["content"]["application/json"]["schema"]["$ref"].endswith(
        "/OrderResponse"
    )
    serialized = str(schema)
    assert "OrderProblem" in serialized
    assert "ProcessedOrder" not in serialized
    assert "EncodedPayload" not in serialized


def test_default_backend_processes_the_documented_order_without_warnings() -> None:
    application = _load_application()

    with TestClient(application.create_app()) as client:
        response = client.post(
            "/orders",
            headers={"X-Request-ID": "req-1001"},
            json=_body(),
        )

    assert response.status_code == 200
    assert response.json() == {
        "request_id": "req-1001",
        "partner_id": "partner-7",
        "order_id": "order-9001",
        "line_count": 2,
        "total_cents": 32_900,
        "warning_count": 0,
    }


class NoRecommendations:
    async def fetch(
        self,
        product_ids: tuple[str, ...],
    ) -> Mapping[str, RecommendationRecord]:
        return {}


def _direct_request(app) -> Request:
    return Request(
        {
            "type": "http",
            "http_version": "1.1",
            "method": "POST",
            "scheme": "http",
            "path": "/orders",
            "raw_path": b"/orders",
            "query_string": b"",
            "headers": [
                (b"x-request-id", b"req-1001"),
                (b"content-type", b"application/json"),
            ],
            "client": ("127.0.0.1", 12345),
            "server": ("127.0.0.1", 8000),
            "app": app,
        }
    )


async def test_real_backend_cancellation_propagates_and_leaves_no_request_task() -> None:
    application = _load_application()
    entered = asyncio.Event()
    release = asyncio.Event()

    async def blocking_loader(product_id: str) -> ProductSummary:
        entered.set()
        await release.wait()
        return ProductSummary(product_id=product_id, name="Product", price_cents=1_000)

    logger, handler = _transport_logger()
    backend = build_application(
        logger=logger,
        catalog_loader=blocking_loader,
        recommendation_provider=NoRecommendations(),
    )
    app = application.create_app(backend_factory=lambda: backend, transport_logger=logger)
    app.state.order_backend = backend
    order = importlib.import_module(
        "examples.fastapi_order_api.models"
    ).OrderRequest.model_validate(_body())

    with log_context(request_id="outer"):
        task = asyncio.create_task(application.submit_order(_direct_request(app), order))
        await entered.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        release.set()
        logger.info("after-cancellation")
        assert get_log_context()["request_id"] == "outer"

    async def no_backend_request_task() -> bool:
        current = asyncio.current_task()
        return not any(
            task is not current and task.get_name().startswith("integrated-order-backend-request-")
            for task in asyncio.all_tasks()
        )

    await eventually_async(no_backend_request_task, timeout=1.0, interval=0.01)
    await backend.aclose()

    after = next(
        record for record in handler.records if record.getMessage() == "after-cancellation"
    )
    assert after.request_id == "outer"
