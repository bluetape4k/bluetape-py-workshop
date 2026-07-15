from pathlib import Path

import pytest

EXAMPLE = Path(__file__).resolve().parents[1]

COMMON = (
    "Scenario",
    "Architecture",
    "Sequence Diagram",
    "bluetape-core",
    "bluetape-logging",
    "bluetape-testing",
    "python -m examples.order_intake",
    "pytest examples/order_intake/tests -q",
    "architecture.png",
    "architecture.svg",
    "sequence.png",
    "sequence.svg",
    "service.py",
)


def _read(name: str) -> str:
    try:
        return (EXAMPLE / name).read_text(encoding="utf-8")
    except FileNotFoundError:
        pytest.fail(f"missing example documentation: {name}")


def test_locale_navigation_and_shared_contract() -> None:
    english = _read("README.md")
    korean = _read("README.ko.md")
    assert "English | [한국어](README.ko.md)" in english
    assert "[English](README.md) | 한국어" in korean
    for token in COMMON:
        assert token in english
        assert token in korean


def test_diagram_sources_and_renders_exist() -> None:
    for name in ("architecture.svg", "architecture.png", "sequence.svg", "sequence.png"):
        assert (EXAMPLE / "docs" / "images" / name).is_file()
