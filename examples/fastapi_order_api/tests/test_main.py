import importlib
import signal
import socket
import subprocess
import sys
import time
from types import ModuleType

import pytest

pytest.importorskip("fastapi", reason="requires the fastapi-order-api extra")

import httpx


def _load_main() -> ModuleType:
    try:
        return importlib.import_module("examples.fastapi_order_api.__main__")
    except ModuleNotFoundError as error:
        pytest.fail(f"FastAPI order CLI is missing: {error}")


def test_parser_defaults_to_loopback_development_port() -> None:
    assert _load_main()._parser().parse_args([]).port == 8000


def test_parser_accepts_an_explicit_valid_port() -> None:
    assert _load_main()._parser().parse_args(["--port", "18080"]).port == 18080


@pytest.mark.parametrize("port", ["0", "65536", "not-a-port"])
def test_parser_rejects_invalid_ports(port: str) -> None:
    with pytest.raises(SystemExit):
        _load_main()._parser().parse_args(["--port", port])


@pytest.mark.parametrize("arguments", [["--host", "0.0.0.0"], ["--workers", "2"], ["--unknown"]])
def test_parser_cannot_select_host_workers_or_unknown_options(arguments: list[str]) -> None:
    with pytest.raises(SystemExit):
        _load_main()._parser().parse_args(arguments)


def test_main_starts_one_fixed_loopback_server(monkeypatch) -> None:
    main_module = _load_main()
    captured: dict[str, object] = {}

    def capture_run(app, **kwargs) -> None:
        captured.update({"app": app, **kwargs})

    monkeypatch.setattr(main_module.uvicorn, "run", capture_run)

    main_module.main(["--port", "18080"])

    assert captured["host"] == "127.0.0.1"
    assert captured["port"] == 18080
    assert captured["workers"] == 1
    assert captured["reload"] is False
    assert captured["proxy_headers"] is False
    assert captured["app"] is not None


def _reserve_loopback_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as reserved:
        reserved.bind(("127.0.0.1", 0))
        return int(reserved.getsockname()[1])


def _wait_for_tcp(port: int, *, timeout: float) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.1):
                return
        except OSError:
            time.sleep(0.01)
            continue
    raise AssertionError(f"server did not bind loopback port {port} within {timeout:g}s")


def test_module_serves_one_order_and_stops_without_a_process_leak() -> None:
    port = _reserve_loopback_port()
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "examples.fastapi_order_api",
            "--port",
            str(port),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    stderr = ""
    try:
        _wait_for_tcp(port, timeout=5.0)
        response = httpx.post(
            f"http://127.0.0.1:{port}/orders",
            headers={"X-Request-ID": "req-smoke-1"},
            json={
                "partner_id": "partner-7",
                "order_id": "order-smoke-1",
                "lines": [{"sku": "SKU-1", "quantity": 1}],
            },
            timeout=3.0,
        )
        assert response.status_code == 200
        assert response.json() == {
            "request_id": "req-smoke-1",
            "partner_id": "partner-7",
            "order_id": "order-smoke-1",
            "line_count": 1,
            "total_cents": 12_500,
            "warning_count": 0,
        }
    finally:
        process.terminate()
        try:
            _, stderr = process.communicate(timeout=5.0)
        except subprocess.TimeoutExpired:
            process.kill()
            _, stderr = process.communicate(timeout=2.0)

    assert process.poll() is not None, stderr[-4_000:]
    assert process.returncode in {0, -signal.SIGTERM}, stderr[-4_000:]
    assert "Application shutdown complete" in stderr
