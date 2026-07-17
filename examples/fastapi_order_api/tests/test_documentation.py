import re
import xml.etree.ElementTree as ET
from itertools import pairwise
from pathlib import Path

EXAMPLE = Path("examples/fastapi_order_api")
IMAGES = EXAMPLE / "docs" / "images"


def read(path: str) -> str:
    return (EXAMPLE / path).read_text(encoding="utf-8")


def test_locale_navigation_scenario_commands_and_contracts_are_aligned() -> None:
    english = read("README.md")
    korean = read("README.ko.md")
    assert "English | [한국어](README.ko.md)" in english
    assert "[English](README.md) | 한국어" in korean

    shared = (
        "## Scenario",
        "## Architecture",
        "## Sequence Diagram",
        "## Ownership and Lifecycle",
        "## Validation and Failure Contract",
        "## Security and Production Boundaries",
        "## Tests",
        "## Cleanup and Troubleshooting",
        "Direct FastAPI",
        "POST /orders",
        "X-Request-ID",
        "correlation",
        "idempotency",
        "OrderBackendApplication",
        "AsyncTTLCache",
        "JsonPayloadService",
        "SKU-1",
        "SKU-2",
        "SKU-3",
        "200 OK",
        "invalid_request",
        "invalid_order",
        "catalog_unavailable",
        "backend_unavailable",
        "order_timeout",
        "order_processing_failed",
        "internal_error",
        "CancelledError",
        "OrderBackendShutdownError",
        "raw HTTP body",
        "127.0.0.1",
        "Ctrl+C",
        "UV_PROJECT_ENVIRONMENT=.venv-fastapi",
        "uv sync --locked --extra fastapi-order-api --python 3.13.14",
        "python -m examples.fastapi_order_api --port 8000",
        "pytest examples/fastapi_order_api/tests -q",
        "bluetape-py/issues/21",
        "bluetape-py/issues/22",
        "architecture.svg",
        "architecture.png",
        "sequence.svg",
        "sequence.png",
    )
    for token in shared:
        assert token in english
        assert token in korean


def test_guides_document_exact_request_response_and_non_goals() -> None:
    for guide in (read("README.md"), read("README.ko.md")):
        for token in (
            '"partner_id": "partner-7"',
            '"order_id": "order-9001"',
            '"sku": "SKU-1"',
            '"quantity": 2',
            '"request_id": "req-1001"',
            '"total_cents": 32900',
            '"warning_count": 0',
            "Content-Type: application/json",
            "authentication",
            "authorization",
            "persistence",
            "proxy",
            "body limit",
            "provider",
            "artifact",
            "retry",
        ):
            assert token in guide


def test_diagram_assets_exist_and_are_embedded() -> None:
    english = read("README.md")
    korean = read("README.ko.md")
    for name in ("architecture.svg", "architecture.png", "sequence.svg", "sequence.png"):
        asset = IMAGES / name
        assert asset.is_file(), f"missing diagram asset: {asset}"
        assert asset.stat().st_size > 0
        link = f"docs/images/{name}"
        assert link in english
        assert link in korean


def _marker_projection(marker: ET.Element) -> float:
    view_box = [float(value) for value in marker.attrib["viewBox"].split()]
    return float(marker.attrib["markerWidth"]) * float(marker.attrib["refX"]) / view_box[2]


def test_architecture_card_gaps_and_terminal_segments_clear_arrowheads() -> None:
    root = ET.parse(IMAGES / "architecture.svg").getroot()
    namespace = {"svg": "http://www.w3.org/2000/svg"}
    markers = root.findall(".//svg:marker", namespace)
    assert markers
    assert {marker.attrib["markerUnits"] for marker in markers} == {"userSpaceOnUse"}
    assert {
        (float(marker.attrib["markerWidth"]), float(marker.attrib["markerHeight"]))
        for marker in markers
    } == {(14.0, 14.0)}

    projection = max(_marker_projection(marker) for marker in markers)
    cards = sorted(
        (
            float(rect.attrib["x"]),
            float(rect.attrib["width"]),
        )
        for rect in root.findall(".//svg:rect", namespace)
        if rect.attrib.get("class") == "card"
    )
    assert len(cards) == 6
    gaps = [next_x - (x + width) for (x, width), (next_x, _) in pairwise(cards)]
    assert min(gaps) >= projection + 4.0 + 12.0

    connectors = [
        path.attrib["d"]
        for path in root.findall(".//svg:path", namespace)
        if "connector" in path.attrib.get("class", "").split()
    ]
    assert len(connectors) == 5
    for path in connectors:
        match = re.fullmatch(r"M(?P<start>\d+) (?P<y>\d+) H(?P<end>\d+)", path)
        assert match is not None
        assert float(match["end"]) - float(match["start"]) >= projection + 16.0


def test_sequence_has_visible_numbered_messages_and_arrowhead_clearance() -> None:
    root = ET.parse(IMAGES / "sequence.svg").getroot()
    namespace = {"svg": "http://www.w3.org/2000/svg"}
    markers = root.findall(".//svg:marker", namespace)
    assert markers
    assert {
        (float(marker.attrib["markerWidth"]), float(marker.attrib["markerHeight"]))
        for marker in markers
    } == {(16.0, 16.0)}
    projection = max(_marker_projection(marker) for marker in markers)

    messages = [
        path.attrib["d"]
        for path in root.findall(".//svg:path", namespace)
        if "message" in path.attrib.get("class", "").split()
    ]
    numbers = [
        text.text
        for text in root.findall(".//svg:text", namespace)
        if text.attrib.get("class") == "num"
    ]
    assert len(messages) == len(numbers) == 15
    assert numbers == [str(number) for number in range(1, 16)]
    for path in messages:
        match = re.fullmatch(r"M(?P<start>\d+) (?P<y>\d+) H(?P<end>\d+)", path)
        assert match is not None
        assert abs(float(match["end"]) - float(match["start"])) >= projection + 16.0

    assert len(root.findall(".//svg:path[@class='lifeline']", namespace)) == 5
    assert len(root.findall(".//svg:rect[@class='activation']", namespace)) >= 3
    branch = root.find(".//svg:rect[@class='alt']", namespace)
    assert branch is not None
    assert branch.attrib.get("fill") == "none"
