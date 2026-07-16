from __future__ import annotations

import json
from collections.abc import Callable
from types import TracebackType

import pytest
from bluetape.testcontainers import (
    DEFAULT_REDIS_IMAGE,
    RedisConnectionDetails,
    RedisServer,
    StartFailureKind,
    TestcontainerStartError,
)

from examples.redis_test_server import RedisProbeError, RedisProbeResult, run_workshop
from examples.redis_test_server.__main__ import main


class ExpectedBodyError(RuntimeError):
    pass


class FakeServer:
    def __init__(self, events: list[str]) -> None:
        self._events = events
        self._entered = False
        self._details = RedisConnectionDetails(
            host="127.0.0.1",
            port=46379,
            url="redis://127.0.0.1:46379",
        )

    @property
    def details(self) -> RedisConnectionDetails:
        if not self._entered:
            raise AssertionError("details read before enter")
        self._events.append("details")
        return self._details

    def __enter__(self) -> FakeServer:
        self._events.append("enter")
        self._entered = True
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        del exc, traceback
        name = "none" if exc_type is None else exc_type.__name__
        self._events.append(f"exit:{name}")
        self._entered = False


class RecordingProbe:
    def __init__(
        self,
        *,
        events: list[str],
        failure: Exception | None = None,
    ) -> None:
        self._events = events
        self._failure = failure

    def verify(self, *, order_id: str, status: str) -> RedisProbeResult:
        self._events.append(f"verify:{order_id}:{status}")
        if self._failure is not None:
            raise self._failure
        return success_result()


def success_result() -> RedisProbeResult:
    return RedisProbeResult(
        order_id="ORD-1001",
        status="accepted",
        ping_succeeded=True,
        write_succeeded=True,
        read_succeeded=True,
    )


def probe_factory(
    events: list[str],
    *,
    failure: Exception | None = None,
) -> Callable[..., RecordingProbe]:
    def create(*, details: RedisConnectionDetails) -> RecordingProbe:
        assert details.url == "redis://127.0.0.1:46379"
        events.append("probe_factory")
        return RecordingProbe(events=events, failure=failure)

    return create


def test_run_workshop_owns_one_successful_context() -> None:
    events: list[str] = []

    result = run_workshop(
        server=FakeServer(events),  # type: ignore[arg-type]
        probe_factory=probe_factory(events),  # type: ignore[arg-type]
    )

    assert result == success_result()
    assert events == [
        "enter",
        "details",
        "probe_factory",
        "verify:ORD-1001:accepted",
        "exit:none",
    ]


def test_run_workshop_preserves_body_failure_and_exits_context() -> None:
    events: list[str] = []
    failure = ExpectedBodyError("body failure")

    with pytest.raises(ExpectedBodyError) as raised:
        run_workshop(
            server=FakeServer(events),  # type: ignore[arg-type]
            probe_factory=probe_factory(events, failure=failure),  # type: ignore[arg-type]
        )

    assert raised.value is failure
    assert events == [
        "enter",
        "details",
        "probe_factory",
        "verify:ORD-1001:accepted",
        "exit:ExpectedBodyError",
    ]


def test_public_wrapper_unstarted_and_terminal_close_contract_is_deterministic() -> None:
    server = RedisServer()

    assert DEFAULT_REDIS_IMAGE == "redis:8"
    assert server.running is False
    with pytest.raises(RuntimeError, match="not running"):
        _ = server.details
    server.close()
    server.close()
    with pytest.raises(RuntimeError, match="closed"):
        server.start()


@pytest.mark.parametrize("image", ["redis", "redis:latest", " redis:8"])
def test_public_wrapper_rejects_unsafe_image_without_docker(image: str) -> None:
    with pytest.raises(ValueError):
        RedisServer(image=image)


@pytest.mark.parametrize("timeout", [0, -1, float("inf")])
def test_public_wrapper_rejects_unsafe_timeout_without_docker(timeout: float) -> None:
    with pytest.raises(ValueError):
        RedisServer(startup_timeout=timeout)


def test_main_emits_safe_success_json(capsys: pytest.CaptureFixture[str]) -> None:
    expected_server = object()
    factory_calls: list[float] = []

    def server_factory(*, startup_timeout: float) -> object:
        factory_calls.append(startup_timeout)
        return expected_server

    def workshop_runner(*, server: object) -> RedisProbeResult:
        assert server is expected_server
        return success_result()

    assert main(server_factory=server_factory, workshop_runner=workshop_runner) == 0
    captured = capsys.readouterr()
    assert json.loads(captured.out) == {
        "event": "redis_workshop_succeeded",
        "order_id": "ORD-1001",
        "status": "accepted",
        "ping_succeeded": True,
        "write_succeeded": True,
        "read_succeeded": True,
    }
    assert captured.err == ""
    assert factory_calls == [30.0]


def test_main_redacts_stable_start_failure(capsys: pytest.CaptureFixture[str]) -> None:
    def workshop_runner(*, server: object) -> RedisProbeResult:
        del server
        raise TestcontainerStartError(StartFailureKind.READINESS_TIMEOUT, "redis:8")

    assert main(server_factory=lambda **kwargs: kwargs, workshop_runner=workshop_runner) == 1
    captured = capsys.readouterr()
    assert json.loads(captured.out) == {
        "error_code": "testcontainer_start_failed",
        "event": "redis_workshop_failed",
        "kind": "readiness-timeout",
    }
    assert captured.err == ""


def test_main_redacts_probe_failure(capsys: pytest.CaptureFixture[str]) -> None:
    def workshop_runner(*, server: object) -> RedisProbeResult:
        del server
        raise RedisProbeError("provider-secret 127.0.0.1:46379")

    assert main(server_factory=lambda **kwargs: kwargs, workshop_runner=workshop_runner) == 1
    captured = capsys.readouterr()
    assert json.loads(captured.out) == {
        "error_code": "redis_probe_failed",
        "event": "redis_workshop_failed",
    }
    assert "provider-secret" not in captured.out
    assert captured.err == ""
