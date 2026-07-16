from bluetape.cache.redis import RedisCoordinationEvent


class CoordinationEventRecorder:
    """Record only bounded terminal events emitted by the coordinator."""

    def __init__(self) -> None:
        self._events: list[RedisCoordinationEvent] = []

    def on_event(self, event: RedisCoordinationEvent) -> None:
        if type(event) is not RedisCoordinationEvent:
            raise TypeError("event must be an exact RedisCoordinationEvent")
        self._events.append(event)

    def snapshot(self) -> tuple[RedisCoordinationEvent, ...]:
        return tuple(self._events)
