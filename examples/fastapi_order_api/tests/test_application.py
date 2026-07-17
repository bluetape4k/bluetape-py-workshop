import importlib
from types import ModuleType

import pytest

pytest.importorskip("fastapi", reason="requires the fastapi-order-api extra")

from fastapi import Request
from fastapi.testclient import TestClient

from examples.catalog_enrichment import ProviderUnavailable
from examples.integrated_order_backend.errors import OrderBackendShutdownError


def _load_application() -> ModuleType:
    try:
        return importlib.import_module("examples.fastapi_order_api.application")
    except ModuleNotFoundError as error:
        pytest.fail(f"FastAPI order application is missing: {error}")


class InstrumentedBackend:
    def __init__(self, *, fail_close: bool = False) -> None:
        self.close_calls = 0
        self.fail_close = fail_close

    async def process(self, command):  # pragma: no cover - Task 4 owns route behavior
        raise AssertionError(f"unexpected process call: {command!r}")

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
