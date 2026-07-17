import importlib
import logging
from types import ModuleType

import pytest

pytest.importorskip("fastapi", reason="requires the fastapi-order-api extra")

from bluetape.logging import ContextLogFilter, get_log_context, log_context
from starlette.datastructures import Headers


def _load_context() -> ModuleType:
    try:
        return importlib.import_module("examples.fastapi_order_api.context")
    except ModuleNotFoundError as error:
        pytest.fail(f"FastAPI order request context is missing: {error}")


def _headers(*values: str) -> Headers:
    return Headers(raw=[(b"x-request-id", value.encode("utf-8")) for value in values])


class CaptureHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__(logging.INFO)
        self.records: list[logging.LogRecord] = []
        self.addFilter(ContextLogFilter())

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


def test_request_id_is_trimmed_after_exactly_one_header() -> None:
    context = _load_context()

    assert context.parse_request_id(_headers("  req-1001  ")) == "req-1001"


@pytest.mark.parametrize(
    ("headers", "reason"),
    [
        (_headers(), "missing"),
        (_headers("req-1", "req-2"), "duplicate"),
    ],
)
def test_missing_or_duplicate_request_id_is_rejected(headers: Headers, reason: str) -> None:
    context = _load_context()

    with pytest.raises(context.InvalidRequestId) as raised:
        context.parse_request_id(headers)

    assert raised.value.reason == reason
    assert str(raised.value) == reason


@pytest.mark.parametrize(
    "value",
    ["", " ", "bad request", "bad/request", "req\x00id", "요청-1", "x" * 129],
)
def test_invalid_request_id_never_leaks_the_raw_value(value: str) -> None:
    context = _load_context()

    with pytest.raises(context.InvalidRequestId) as raised:
        context.parse_request_id(_headers(value))

    assert raised.value.reason == "invalid"
    assert str(raised.value) == "invalid"
    if value:
        assert value not in repr(raised.value)
    assert context.INVALID_REQUEST_ID == "<invalid>"


@pytest.mark.parametrize("raise_inside", [False, True])
def test_request_context_restores_outer_log_context(raise_inside: bool) -> None:
    context = _load_context()
    logger = logging.Logger("fastapi-order-context-test", level=logging.INFO)
    logger.propagate = False
    handler = CaptureHandler()
    logger.addHandler(handler)

    try:
        with log_context(request_id="outer"):
            logger.info("before")
            if raise_inside:
                with pytest.raises(RuntimeError, match="boom"):
                    with context.request_context("inner"):
                        logger.info("inside")
                        raise RuntimeError("boom")
            else:
                with context.request_context("inner"):
                    logger.info("inside")
            logger.info("after")
    finally:
        logger.removeHandler(handler)
        handler.close()

    assert [record.request_id for record in handler.records] == ["outer", "inner", "outer"]
    assert get_log_context() == {}
