from pathlib import Path

EXAMPLE = Path("examples/catalog_enrichment")
ENGLISH = (EXAMPLE / "README.md").read_text(encoding="utf-8")
KOREAN = (EXAMPLE / "README.ko.md").read_text(encoding="utf-8")

EXPECTED_TOKENS = (
    "python -m examples.catalog_enrichment",
    "pytest examples/catalog_enrichment/tests -q",
    "bluetape.collections.distinct",
    "bluetape.collections.chunked",
    "bluetape.asyncio.map_bounded",
    "optional_provider_failed",
    "TimeoutError",
    "CancelledError",
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


def test_diagram_assets_exist_and_link_to_source() -> None:
    for name in ("architecture.svg", "architecture.png", "sequence.svg", "sequence.png"):
        assert (EXAMPLE / "docs" / "images" / name).is_file()
    for source in ("models.py", "providers.py", "service.py", "__main__.py"):
        assert source in ENGLISH
        assert source in KOREAN
