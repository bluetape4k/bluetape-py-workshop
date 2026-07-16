from pathlib import Path

EXAMPLE = Path("examples/integrated_order_backend")
ENGLISH = (EXAMPLE / "README.md").read_text(encoding="utf-8")
KOREAN = (EXAMPLE / "README.ko.md").read_text(encoding="utf-8")

SHARED_TOKENS = (
    "## Scenario",
    "## Architecture",
    "## Sequence Diagram",
    "## Packages and APIs",
    "## Aggregate Invariants",
    "## Failure, Timeout, Cancellation, and Shutdown",
    "## Security and Production Boundaries",
    "## Tests",
    "## Cleanup and Troubleshooting",
    "python -m examples.integrated_order_backend",
    "pytest examples/integrated_order_backend/tests -q",
    "OrderBackendApplication",
    "OrderBackendService",
    "OrderIntakeService",
    "CatalogEnrichmentService",
    "CachedCatalogProvider",
    "AsyncProductCatalogService",
    "AsyncTTLCache",
    "JsonPayloadService",
    "build_application()",
    "Fory",
    "untrusted",
    "TimeoutError",
    "CancelledError",
    "OrderBackendShutdownError",
    "best-effort",
    "architecture.svg",
    "architecture.png",
    "sequence.svg",
    "sequence.png",
    "models.py",
    "errors.py",
    "composition.py",
    "service.py",
    "application.py",
    "__main__.py",
)


def test_locale_navigation_and_contract_tokens_are_aligned() -> None:
    assert "English | [한국어](README.ko.md)" in ENGLISH
    assert "[English](README.md) | 한국어" in KOREAN
    for token in SHARED_TOKENS:
        assert token in ENGLISH
        assert token in KOREAN


def test_both_locales_embed_pngs_and_link_svg_sources_directly() -> None:
    for document in (ENGLISH, KOREAN):
        assert "](docs/images/architecture.png)" in document
        assert "](docs/images/architecture.svg)" in document
        assert "](docs/images/sequence.png)" in document
        assert "](docs/images/sequence.svg)" in document


def test_diagram_assets_and_documented_sources_exist() -> None:
    for name in ("architecture.svg", "architecture.png", "sequence.svg", "sequence.png"):
        asset = EXAMPLE / "docs" / "images" / name
        assert asset.is_file()
        assert asset.stat().st_size > 0
    for name in (
        "models.py",
        "errors.py",
        "composition.py",
        "service.py",
        "application.py",
        "__main__.py",
    ):
        assert (EXAMPLE / name).is_file()
