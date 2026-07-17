import re
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Literal

from bluetape.logging import log_context
from starlette.datastructures import Headers

INVALID_REQUEST_ID = "<invalid>"
REQUEST_ID_PATTERN = re.compile(r"[A-Za-z0-9._:-]{1,128}\Z", re.ASCII)
InvalidRequestIdReason = Literal["missing", "duplicate", "invalid"]


class InvalidRequestId(ValueError):  # noqa: N818 - domain contract uses an Invalid* name
    def __init__(self, reason: InvalidRequestIdReason) -> None:
        self.reason = reason
        super().__init__(reason)


def parse_request_id(headers: Headers) -> str:
    values = headers.getlist("x-request-id")
    if not values:
        raise InvalidRequestId("missing")
    if len(values) != 1:
        raise InvalidRequestId("duplicate")

    request_id = values[0].strip()
    if REQUEST_ID_PATTERN.fullmatch(request_id) is None:
        raise InvalidRequestId("invalid")
    return request_id


@contextmanager
def request_context(request_id: str) -> Iterator[None]:
    with log_context(request_id=request_id):
        yield
