import json
from collections.abc import Callable
from dataclasses import asdict

from bluetape.testcontainers import RedisServer, TestcontainerStartError

from .application import run_workshop
from .probe import RedisProbeError, RedisProbeResult

ServerFactory = Callable[..., RedisServer]
WorkshopRunner = Callable[..., RedisProbeResult]


def _emit(payload: dict[str, object]) -> None:
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))


def main(
    *,
    server_factory: ServerFactory = RedisServer,
    workshop_runner: WorkshopRunner = run_workshop,
) -> int:
    try:
        result = workshop_runner(server=server_factory(startup_timeout=30.0))
    except TestcontainerStartError as error:
        _emit(
            {
                "error_code": "testcontainer_start_failed",
                "event": "redis_workshop_failed",
                "kind": error.kind.value,
            }
        )
        return 1
    except RedisProbeError:
        _emit(
            {
                "error_code": "redis_probe_failed",
                "event": "redis_workshop_failed",
            }
        )
        return 1
    _emit({"event": "redis_workshop_succeeded", **asdict(result)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
