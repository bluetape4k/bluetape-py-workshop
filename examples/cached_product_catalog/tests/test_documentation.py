from pathlib import Path

EXAMPLE = Path("examples/cached_product_catalog")
ENGLISH = (EXAMPLE / "README.md").read_text(encoding="utf-8")
KOREAN = (EXAMPLE / "README.ko.md").read_text(encoding="utf-8")

EXPECTED_TOKENS = (
    "## Scenario",
    "## Architecture",
    "## Sequence Diagram",
    "python -m examples.cached_product_catalog",
    "pytest examples/cached_product_catalog/tests -q",
    "bluetape.cache.TTLCache",
    "bluetape.cache.AsyncTTLCache",
    "bluetape.cache.CacheStats",
    "bluetape.core.require_instance",
    "bluetape.core.require_not_blank",
    "bluetape.testing.eventually_async",
    "hit",
    "miss",
    "expiry",
    "eviction",
    "CancelledError",
    "event loop",
    "entry count",
    "architecture.svg",
    "architecture.png",
    "sequence.svg",
    "sequence.png",
)


def test_locale_navigation_and_contract_tokens_are_aligned() -> None:
    assert "English | [한국어](README.ko.md)" in ENGLISH
    assert "[English](README.md) | 한국어" in KOREAN
    for token in EXPECTED_TOKENS:
        assert token in ENGLISH
        assert token in KOREAN


def test_diagram_assets_and_source_links_exist() -> None:
    for name in ("architecture.svg", "architecture.png", "sequence.svg", "sequence.png"):
        assert (EXAMPLE / "docs" / "images" / name).is_file()
    for source in ("models.py", "providers.py", "service.py", "__main__.py", "tests"):
        assert source in ENGLISH
        assert source in KOREAN
