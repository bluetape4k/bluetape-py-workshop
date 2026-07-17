from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from typing import Protocol

from fastapi import FastAPI

from examples.integrated_order_backend.models import OrderBackendCommand, ProcessedOrder

from .providers import build_default_backend


class OrderBackend(Protocol):
    async def process(self, command: OrderBackendCommand) -> ProcessedOrder: ...

    async def aclose(self) -> None: ...


type BackendFactory = Callable[[], OrderBackend]


def create_app(*, backend_factory: BackendFactory = build_default_backend) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        backend = backend_factory()
        app.state.order_backend = backend
        yield
        await backend.aclose()
        del app.state.order_backend

    return FastAPI(lifespan=lifespan)
