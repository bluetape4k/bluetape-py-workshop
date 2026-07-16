import json

from bluetape.testcontainers import RedisServer

from .application import run_workshop


def main() -> None:
    result = run_workshop(server=RedisServer())
    print(
        json.dumps(
            {
                "product_id": result.owner_value.product_id,
                "loader_calls": result.loader_calls,
                "owner_outcome": result.owner_events[-1].outcome.value,
                "follower_outcome": result.follower_events[-1].outcome.value,
                "follower_local_hits": result.follower_stats.hits,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
