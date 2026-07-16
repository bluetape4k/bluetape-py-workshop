from pathlib import Path

EXAMPLE = Path("examples/redis_load_coordination")


def read(path: str) -> str:
    return (EXAMPLE / path).read_text(encoding="utf-8")


def test_locale_navigation_scenario_and_commands_are_aligned() -> None:
    english = read("README.md")
    korean = read("README.ko.md")
    assert "English | [한국어](README.ko.md)" in english
    assert "[English](README.md) | 한국어" in korean

    shared = (
        "## Scenario",
        "## Architecture",
        "## Sequence Diagram",
        "AsyncTTLCache",
        "AsyncRedisProvider",
        "AsyncRedisLoadCoordinator",
        "RedisLoadOptions",
        "ResultEnvelopeCodec",
        "ProductSummaryCodec",
        "CoordinationEventRecorder",
        "4b7458f22cea0a9e757b5fbf7f5ff4bc8c23cb9a",
        "bluetape-cache-redis==0.1.0",
        "redis-coordination",
        "UV_PROJECT_ENVIRONMENT=.venv-redis",
        "python -m examples.redis_load_coordination",
        'pytest -m "not testcontainers"',
        "pytest -m testcontainers",
        "test_redis_integration.py",
        "loader_calls",
        "result-reused",
        "follower_local_hits",
        "architecture.svg",
        "architecture.png",
        "sequence.svg",
        "sequence.png",
        "bluetape-py/issues/54",
        "bluetape-py/issues/55",
        "bluetape-py/issues/56",
        "redis/redis-py/issues/3916",
        "#20",
    )
    for token in shared:
        assert token in english
        assert token in korean


def test_readmes_explain_failure_security_cleanup_and_non_goals() -> None:
    for guide in (read("README.md"), read("README.ko.md")):
        for token in (
            "local hit",
            "LOADED",
            "RESULT_REUSED",
            "LEASE_LOST",
            "CancelledError",
            "no fallback",
            "rediss://",
            "ACL",
            "hostname",
            "plaintext",
            "pseudonym",
            "AsyncExitStack",
            "RedisServer",
            "sequential",
            "near-cache invalidation",
            "L2 cache",
            "fencing",
            "exactly-once",
            "Docker",
        ):
            assert token in guide


def test_diagram_assets_exist_and_are_embedded() -> None:
    english = read("README.md")
    korean = read("README.ko.md")
    for name in ("architecture.svg", "architecture.png", "sequence.svg", "sequence.png"):
        asset = EXAMPLE / "docs" / "images" / name
        assert asset.is_file(), f"missing diagram asset: {asset}"
        link = f"docs/images/{name}"
        assert link in english
        assert link in korean
