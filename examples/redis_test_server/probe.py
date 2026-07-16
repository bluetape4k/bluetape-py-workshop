from __future__ import annotations

import math
import socket
from collections.abc import Callable
from dataclasses import dataclass

from bluetape.testcontainers import RedisConnectionDetails

_MAX_PART_BYTES = 64
_MAX_ORDER_ID_BYTES = 48
_MAX_STATUS_BYTES = 64
_MAX_LINE_BYTES = 128
_MAX_BULK_BYTES = 64

SocketFactory = Callable[[tuple[str, int], float], socket.socket]


class RedisProbeError(RuntimeError):
    """A safe application-level Redis probe failure."""


@dataclass(frozen=True, slots=True, kw_only=True)
class RedisProbeResult:
    order_id: str
    status: str
    ping_succeeded: bool
    write_succeeded: bool
    read_succeeded: bool


class RedisOrderStatusProbe:
    def __init__(
        self,
        *,
        details: RedisConnectionDetails,
        command_timeout: float = 2.0,
        socket_factory: SocketFactory = socket.create_connection,
    ) -> None:
        if not isinstance(details, RedisConnectionDetails):
            raise TypeError("details must be RedisConnectionDetails")
        if isinstance(command_timeout, bool) or not isinstance(command_timeout, int | float):
            raise TypeError("command_timeout must be a finite positive number")
        timeout = float(command_timeout)
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("command_timeout must be a finite positive number")
        if not callable(socket_factory):
            raise TypeError("socket_factory must be callable")
        self._details = details
        self._command_timeout = timeout
        self._socket_factory = socket_factory

    def verify(self, *, order_id: str, status: str) -> RedisProbeResult:
        normalized_order_id = _token(
            order_id,
            field="order_id",
            uppercase=True,
            max_bytes=_MAX_ORDER_ID_BYTES,
        )
        normalized_status = _token(
            status,
            field="status",
            uppercase=False,
            max_bytes=_MAX_STATUS_BYTES,
        )
        key = _key(normalized_order_id)
        if self._command("PING") != b"PONG":
            raise RedisProbeError("Redis ping returned an unexpected response")
        if self._command("SET", key, normalized_status) != b"OK":
            raise RedisProbeError("Redis write returned an unexpected response")
        if self.read_status(order_id=normalized_order_id) != normalized_status:
            raise RedisProbeError("Redis read returned an unexpected response")
        return RedisProbeResult(
            order_id=normalized_order_id,
            status=normalized_status,
            ping_succeeded=True,
            write_succeeded=True,
            read_succeeded=True,
        )

    def read_status(self, *, order_id: str) -> str | None:
        normalized_order_id = _token(
            order_id,
            field="order_id",
            uppercase=True,
            max_bytes=_MAX_ORDER_ID_BYTES,
        )
        response = self._command("GET", _key(normalized_order_id))
        if response is None:
            return None
        try:
            return response.decode("utf-8")
        except UnicodeError as error:
            raise RedisProbeError("Redis status was not valid UTF-8") from error

    def _command(self, *parts: str) -> bytes | None:
        try:
            request = _request(parts)
            with self._socket_factory(
                (self._details.host, self._details.port), self._command_timeout
            ) as stream:
                stream.settimeout(self._command_timeout)
                stream.sendall(request)
                return _response(stream)
        except RedisProbeError:
            raise
        except (OSError, UnicodeError) as error:
            raise RedisProbeError("Redis command failed") from error


def _token(value: str, *, field: str, uppercase: bool, max_bytes: int) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field} must be non-blank")
    if not normalized.isascii() or any(
        not (character.isalnum() or character in "_-") for character in normalized
    ):
        raise ValueError(f"{field} must use ASCII letters, digits, '_' or '-'")
    normalized = normalized.upper() if uppercase else normalized.lower()
    if len(normalized.encode()) > max_bytes:
        raise ValueError(f"{field} exceeds {max_bytes} UTF-8 bytes")
    return normalized


def _key(order_id: str) -> str:
    return f"workshop:order:{order_id}"


def _request(parts: tuple[str, ...]) -> bytes:
    encoded = [part.encode("utf-8") for part in parts]
    if any(len(part) > _MAX_PART_BYTES for part in encoded):
        raise RedisProbeError("Redis command part exceeded the limit")
    request = [f"*{len(encoded)}\r\n".encode()]
    for part in encoded:
        request.extend((f"${len(part)}\r\n".encode(), part, b"\r\n"))
    return b"".join(request)


def _response(stream: socket.socket) -> bytes | None:
    prefix = _read_exact(stream, 1)
    line = _read_line(stream)
    if prefix == b"+":
        return line
    if prefix == b"-":
        raise RedisProbeError("Redis returned an error response")
    if prefix != b"$":
        raise RedisProbeError("Redis returned an unsupported response type")
    try:
        size = int(line)
    except ValueError:
        raise RedisProbeError("Redis returned an invalid bulk length") from None
    if size == -1:
        return None
    if size < 0 or size > _MAX_BULK_BYTES:
        raise RedisProbeError("Redis returned an invalid bulk length")
    payload = _read_exact(stream, size)
    if _read_exact(stream, 2) != b"\r\n":
        raise RedisProbeError("Redis returned an invalid bulk trailer")
    return payload


def _read_line(stream: socket.socket) -> bytes:
    data = bytearray()
    while not data.endswith(b"\r\n"):
        if len(data) >= _MAX_LINE_BYTES + 2:
            raise RedisProbeError("Redis response line exceeded the limit")
        data.extend(_read_exact(stream, 1))
    return bytes(data[:-2])


def _read_exact(stream: socket.socket, size: int) -> bytes:
    data = bytearray()
    while len(data) < size:
        chunk = stream.recv(size - len(data))
        if not chunk:
            raise RedisProbeError("Redis closed the connection unexpectedly")
        data.extend(chunk)
    return bytes(data)
