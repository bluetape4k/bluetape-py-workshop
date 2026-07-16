from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

from bluetape.cache.redis import (
    AsyncRedisProvider,
    RedisCommandPolicy,
    RedisCoordinationSnapshot,
    RedisProviderError,
)


@dataclass(slots=True)
class SharedRedisBackend:
    values: dict[str, bytes] = field(default_factory=dict)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


class FakeAsyncRedisProvider(AsyncRedisProvider):
    def __init__(self, backend: SharedRedisBackend) -> None:
        self.backend = backend
        self.policy = RedisCommandPolicy(connect_timeout=0.01, socket_timeout=0.01)
        self.calls: list[str] = []
        self.snapshot_called = asyncio.Event()
        self.snapshot_plan: list[RedisCoordinationSnapshot] = []
        self.failure: RedisProviderError | None = None
        self.publish_result = True
        self.cleanup_error: BaseException | None = None

    @property
    def command_policy(self) -> RedisCommandPolicy:
        return self.policy

    def _raise_failure(self) -> None:
        if self.failure is not None:
            raise self.failure

    async def set_if_absent(self, key: str, value: bytes, *, ttl: float) -> bool:
        del ttl
        self.calls.append("set_if_absent")
        self._raise_failure()
        async with self.backend.lock:
            if key in self.backend.values:
                return False
            self.backend.values[key] = value
            return True

    async def coordination_snapshot(
        self,
        marker_key: str,
        result_key: str,
        *,
        max_marker_size: int = 138,
        max_result_size: int,
    ) -> RedisCoordinationSnapshot:
        self.calls.append("coordination_snapshot")
        self._raise_failure()
        self.snapshot_called.set()
        if self.snapshot_plan:
            return self.snapshot_plan.pop(0)
        async with self.backend.lock:
            marker = self.backend.values.get(marker_key)
            result = self.backend.values.get(result_key)
        return RedisCoordinationSnapshot(
            marker=None if marker is not None and len(marker) > max_marker_size else marker,
            result=None if result is not None and len(result) > max_result_size else result,
            marker_oversized=marker is not None and len(marker) > max_marker_size,
            result_oversized=result is not None and len(result) > max_result_size,
        )

    async def publish_if_value(
        self,
        condition_key: str,
        expected_value: bytes,
        *,
        result_key: str,
        result_value: bytes,
        completion_value: bytes,
        ttl: float,
    ) -> bool:
        del ttl
        self.calls.append("publish_if_value")
        self._raise_failure()
        if not self.publish_result:
            return False
        async with self.backend.lock:
            if self.backend.values.get(condition_key) != expected_value:
                return False
            self.backend.values[result_key] = result_value
            self.backend.values[condition_key] = completion_value
            return True

    async def delete_if_value(self, key: str, expected_value: bytes) -> bool:
        self.calls.append("delete_if_value")
        if self.cleanup_error is not None:
            raise self.cleanup_error
        async with self.backend.lock:
            if self.backend.values.get(key) != expected_value:
                return False
            del self.backend.values[key]
            return True
