import re
import xml.etree.ElementTree as ET
from itertools import pairwise
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


def test_architecture_card_gaps_leave_room_for_arrowheads() -> None:
    root = ET.parse(EXAMPLE / "docs" / "images" / "architecture.svg").getroot()
    namespace = {"svg": "http://www.w3.org/2000/svg"}

    markers = root.findall(".//svg:marker", namespace)
    assert markers
    assert {
        (float(marker.attrib["markerWidth"]), float(marker.attrib["markerHeight"]))
        for marker in markers
    } == {(14.0, 14.0)}

    cards = [
        rect
        for rect in root.findall(".//svg:rect", namespace)
        if rect.attrib.get("class") == "card"
    ]
    stacks = {
        x: sorted(
            (
                (float(card.attrib["y"]), float(card.attrib["height"]))
                for card in cards
                if float(card.attrib["x"]) == x
            ),
            key=lambda dimensions: dimensions[0],
        )
        for x in (405.0, 775.0)
    }
    for stack in stacks.values():
        assert len(stack) == 3
        gaps = [next_y - (y + height) for (y, height), (next_y, _) in pairwise(stack)]
        assert min(gaps) >= 55.0

    redis = next(card for card in cards if card.attrib.get("stroke") == "#d65a4a")
    redis_top = float(redis.attrib["y"])
    for stack in stacks.values():
        provider_y, provider_height = stack[-1]
        assert redis_top - (provider_y + provider_height) >= 70.0

    redis_entry_paths = [
        path.attrib["d"]
        for path in root.findall(".//svg:path", namespace)
        if path.attrib.get("class") == "coord" and "Q" in path.attrib.get("d", "")
    ]
    assert len(redis_entry_paths) == 2
    for path in redis_entry_paths:
        terminal = re.search(r"Q\d+ \d+ \d+ (?P<exit_y>\d+) V(?P<target_y>\d+)$", path)
        assert terminal is not None
        assert float(terminal["target_y"]) - float(terminal["exit_y"]) >= 28.0
