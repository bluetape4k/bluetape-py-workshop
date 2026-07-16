from pathlib import Path

EXAMPLE = Path("examples/redis_test_server")


def read(path: str) -> str:
    return (EXAMPLE / path).read_text(encoding="utf-8")


def test_locale_navigation_and_reader_contract_are_aligned() -> None:
    english = read("README.md")
    korean = read("README.ko.md")
    assert "English | [한국어](README.ko.md)" in english
    assert "[English](README.md) | 한국어" in korean

    tokens = (
        "## Scenario",
        "## Architecture",
        "## Sequence Diagram",
        "RedisServer",
        "RedisConnectionDetails",
        "StartFailureKind",
        "startup_timeout",
        "redis:8",
        "redis-py",
        'uv run --locked pytest -m "not testcontainers"',
        "uv run --locked pytest -m testcontainers",
        "uv run --locked python -m examples.redis_test_server",
        "docker ps -a --filter label=com.bluetape.testcontainers.redis=true",
        "docker rm -f <confirmed-container-id>",
        "architecture.svg",
        "architecture.png",
        "sequence.svg",
        "sequence.png",
        "probe.py",
        "application.py",
        "__main__.py",
        "test_redis_integration.py",
    )
    for token in tokens:
        assert token in english
        assert token in korean


def test_readmes_explain_ownership_failure_and_non_goals() -> None:
    for readme in (read("README.md"), read("README.ko.md")):
        for token in (
            "single-use",
            "sequential",
            "runtime-unavailable",
            "image-pull",
            "readiness-timeout",
            "wrapper-failure",
            "close()",
            "GenericContainer",
            "production Redis",
            "PING",
            "SET",
            "GET",
        ):
            assert token in readme


def test_diagram_assets_exist_and_are_embedded() -> None:
    english = read("README.md")
    korean = read("README.ko.md")
    for name in ("architecture.svg", "architecture.png", "sequence.svg", "sequence.png"):
        asset = EXAMPLE / "docs" / "images" / name
        assert asset.is_file(), f"missing diagram asset: {asset}"
        link = f"docs/images/{name}"
        assert link in english
        assert link in korean
