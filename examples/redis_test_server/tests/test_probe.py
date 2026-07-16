from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest
from bluetape.testcontainers import RedisConnectionDetails

from examples.redis_test_server import RedisOrderStatusProbe, RedisProbeError, RedisProbeResult


class ScriptedSocket:
    def __init__(self, response: bytes) -> None:
        self._response = bytearray(response)
        self.sent = b""
        self.timeout: float | None = None
        self.closed = False

    def __enter__(self) -> ScriptedSocket:
        return self

    def __exit__(self, *args: object) -> None:
        self.closed = True

    def settimeout(self, timeout: float) -> None:
        self.timeout = timeout

    def sendall(self, data: bytes) -> None:
        self.sent += data

    def recv(self, size: int) -> bytes:
        if not self._response:
            return b""
        chunk = bytes(self._response[:size])
        del self._response[:size]
        return chunk


class ScriptedSocketFactory:
    def __init__(self, *responses: bytes) -> None:
        self._responses = list(responses)
        self.calls: list[tuple[tuple[str, int], float, ScriptedSocket]] = []

    def __call__(self, address: tuple[str, int], timeout: float) -> ScriptedSocket:
        stream = ScriptedSocket(self._responses.pop(0))
        self.calls.append((address, timeout, stream))
        return stream


def connection_details() -> RedisConnectionDetails:
    return RedisConnectionDetails(
        host="127.0.0.1",
        port=46379,
        url="redis://127.0.0.1:46379",
    )


def test_probe_result_is_keyword_only_frozen_and_slotted() -> None:
    result = RedisProbeResult(
        order_id="ORD-1001",
        status="accepted",
        ping_succeeded=True,
        write_succeeded=True,
        read_succeeded=True,
    )

    assert not hasattr(result, "__dict__")
    with pytest.raises(FrozenInstanceError):
        result.status = "changed"  # type: ignore[misc]
    with pytest.raises(TypeError):
        RedisProbeResult("ORD-1001", "accepted", True, True, True)  # type: ignore[misc]


def test_verify_uses_wrapper_details_and_exact_bounded_commands() -> None:
    factory = ScriptedSocketFactory(b"+PONG\r\n", b"+OK\r\n", b"$8\r\naccepted\r\n")
    probe = RedisOrderStatusProbe(details=connection_details(), socket_factory=factory)

    result = probe.verify(order_id=" ord-1001 ", status=" Accepted ")

    assert result == RedisProbeResult(
        order_id="ORD-1001",
        status="accepted",
        ping_succeeded=True,
        write_succeeded=True,
        read_succeeded=True,
    )
    assert [(address, timeout) for address, timeout, _ in factory.calls] == [
        (("127.0.0.1", 46379), 2.0),
        (("127.0.0.1", 46379), 2.0),
        (("127.0.0.1", 46379), 2.0),
    ]
    assert [stream.sent for _, _, stream in factory.calls] == [
        b"*1\r\n$4\r\nPING\r\n",
        b"*3\r\n$3\r\nSET\r\n$23\r\nworkshop:order:ORD-1001\r\n$8\r\naccepted\r\n",
        b"*2\r\n$3\r\nGET\r\n$23\r\nworkshop:order:ORD-1001\r\n",
    ]
    assert all(stream.timeout == 2.0 for _, _, stream in factory.calls)
    assert all(stream.closed for _, _, stream in factory.calls)


def test_read_status_returns_none_for_missing_fixed_order_key() -> None:
    factory = ScriptedSocketFactory(b"$-1\r\n")
    probe = RedisOrderStatusProbe(details=connection_details(), socket_factory=factory)

    assert probe.read_status(order_id="ord-1001") is None
    assert factory.calls[0][2].sent == (b"*2\r\n$3\r\nGET\r\n$23\r\nworkshop:order:ORD-1001\r\n")


@pytest.mark.parametrize("details", [None, object()])
def test_probe_requires_wrapper_connection_details(details: object) -> None:
    with pytest.raises(TypeError, match="RedisConnectionDetails"):
        RedisOrderStatusProbe(details=details)  # type: ignore[arg-type]


@pytest.mark.parametrize("timeout", [True, "2"])
def test_probe_rejects_non_numeric_command_timeout(timeout: object) -> None:
    with pytest.raises(TypeError, match="finite positive"):
        RedisOrderStatusProbe(
            details=connection_details(),
            command_timeout=timeout,  # type: ignore[arg-type]
        )


@pytest.mark.parametrize("timeout", [0, -1, float("inf"), float("nan")])
def test_probe_rejects_non_positive_or_non_finite_command_timeout(timeout: float) -> None:
    with pytest.raises(ValueError, match="finite positive"):
        RedisOrderStatusProbe(details=connection_details(), command_timeout=timeout)


def test_probe_requires_callable_socket_factory() -> None:
    with pytest.raises(TypeError, match="callable"):
        RedisOrderStatusProbe(
            details=connection_details(),
            socket_factory=object(),  # type: ignore[arg-type]
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("order_id", None),
        ("order_id", ""),
        ("order_id", " "),
        ("order_id", "ord 1001"),
        ("order_id", "주문-1001"),
        ("order_id", "A" * 49),
        ("status", None),
        ("status", ""),
        ("status", "accepted now"),
        ("status", "승인"),
        ("status", "a" * 65),
    ],
)
def test_probe_rejects_invalid_application_tokens_before_socket_access(
    field: str,
    value: object,
) -> None:
    factory = ScriptedSocketFactory()
    probe = RedisOrderStatusProbe(details=connection_details(), socket_factory=factory)
    kwargs: dict[str, object] = {"order_id": "ORD-1001", "status": "accepted"}
    kwargs[field] = value

    with pytest.raises((TypeError, ValueError)):
        probe.verify(**kwargs)  # type: ignore[arg-type]

    assert factory.calls == []


@pytest.mark.parametrize(
    ("responses", "message"),
    [
        ((b"+NOPE\r\n",), "ping"),
        ((b"+PONG\r\n", b"+NOPE\r\n"), "write"),
        ((b"+PONG\r\n", b"+OK\r\n", b"$-1\r\n"), "read"),
        ((b"+PONG\r\n", b"+OK\r\n", b"$5\r\nother\r\n"), "read"),
    ],
)
def test_verify_rejects_unexpected_command_results(
    responses: tuple[bytes, ...],
    message: str,
) -> None:
    factory = ScriptedSocketFactory(*responses)
    probe = RedisOrderStatusProbe(details=connection_details(), socket_factory=factory)

    with pytest.raises(RedisProbeError, match=message):
        probe.verify(order_id="ORD-1001", status="accepted")


@pytest.mark.parametrize(
    ("response", "message"),
    [
        (b"", "closed"),
        (b"+" + b"x" * 131, "line exceeded"),
        (b":1\r\n", "unsupported"),
        (b"-provider-secret\r\n", "error response"),
        (b"$invalid-secret\r\n", "invalid bulk length"),
        (b"$-2\r\n", "invalid bulk length"),
        (b"$65\r\n", "invalid bulk length"),
        (b"$8\r\nshort", "closed"),
        (b"$3\r\nabcXX", "invalid bulk trailer"),
    ],
)
def test_read_status_rejects_malformed_or_oversized_protocol(
    response: bytes,
    message: str,
) -> None:
    factory = ScriptedSocketFactory(response)
    probe = RedisOrderStatusProbe(details=connection_details(), socket_factory=factory)

    with pytest.raises(RedisProbeError, match=message) as raised:
        probe.read_status(order_id="ORD-1001")

    assert "provider-secret" not in str(raised.value)
    assert "invalid-secret" not in str(raised.value)
    assert factory.calls[0][2].closed is True


def test_read_status_rejects_invalid_utf8_with_safe_context() -> None:
    factory = ScriptedSocketFactory(b"$1\r\n\xff\r\n")
    probe = RedisOrderStatusProbe(details=connection_details(), socket_factory=factory)

    with pytest.raises(RedisProbeError, match="valid UTF-8") as raised:
        probe.read_status(order_id="ORD-1001")

    assert isinstance(raised.value.__cause__, UnicodeError)
    assert "\\xff" not in str(raised.value)
    assert factory.calls[0][2].closed is True


def test_socket_failure_retains_cause_but_redacts_public_message() -> None:
    def failing_factory(address: tuple[str, int], timeout: float) -> ScriptedSocket:
        raise TimeoutError(f"provider-secret {address} {timeout}")

    probe = RedisOrderStatusProbe(
        details=connection_details(),
        socket_factory=failing_factory,
    )

    with pytest.raises(RedisProbeError, match="Redis command failed") as raised:
        probe.read_status(order_id="ORD-1001")

    assert isinstance(raised.value.__cause__, TimeoutError)
    assert "provider-secret" not in str(raised.value)
