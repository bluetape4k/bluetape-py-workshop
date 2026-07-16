from pathlib import Path

EXAMPLE = Path("examples/bounded_payload_processing")
ENGLISH = (EXAMPLE / "README.md").read_text(encoding="utf-8")
KOREAN = (EXAMPLE / "README.ko.md").read_text(encoding="utf-8")

EXPECTED_TOKENS = (
    "## Scenario",
    "## Architecture",
    "## Sequence Diagram",
    "TrustProfile.UNTRUSTED",
    "TrustProfile.TRUSTED_INTERNAL",
    "JsonPayloadService",
    "ForyPayloadService",
    "base64url",
    "gzip",
    "max_encoded_size",
    "max_compressed_size",
    "DecompressionLimitError",
    "CPython 3.13",
    "pyfory==1.3.0",
    "uv run --locked python -m examples.bounded_payload_processing",
    "UV_PROJECT_ENVIRONMENT=.venv-fory uv sync --locked --extra fory --python 3.13.14",
    "python -m examples.bounded_payload_processing.fory_demo",
    "pytest examples/bounded_payload_processing/tests/test_fory_service.py -q",
    "rm -rf .venv-fory",
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


def test_readmes_warn_against_automatic_format_selection() -> None:
    for readme in (ENGLISH, KOREAN):
        assert "automatic" in readme
        assert "metadata" in readme
        assert "authenticated" in readme
        assert "default" in readme
        assert "optional" in readme


def test_diagram_assets_and_source_links_exist() -> None:
    for name in ("architecture.svg", "architecture.png", "sequence.svg", "sequence.png"):
        assert (EXAMPLE / "docs" / "images" / name).is_file()
    for source in (
        "models.py",
        "errors.py",
        "service.py",
        "fory_service.py",
        "__main__.py",
        "fory_demo.py",
        "tests",
    ):
        assert source in ENGLISH
        assert source in KOREAN
