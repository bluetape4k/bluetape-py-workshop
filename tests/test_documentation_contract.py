from pathlib import Path

ENGLISH = Path("README.md").read_text(encoding="utf-8")
KOREAN = Path("README.ko.md").read_text(encoding="utf-8")
WIP = Path("WIP.md").read_text(encoding="utf-8")
AGENTS = Path("AGENTS.md").read_text(encoding="utf-8")

COMMON_FACTS = (
    "Python 3.13.14",
    "uv 0.11.28",
    "4b7458f22cea0a9e757b5fbf7f5ff4bc8c23cb9a",
    "uv sync --locked --python 3.13.14",
    "uv run --locked ruff check .",
    "uv run --locked ruff format --check .",
    "uv run --locked pytest",
    "WIP.md",
)


def test_readme_locale_navigation_is_reciprocal() -> None:
    assert "English | [한국어](README.ko.md)" in ENGLISH
    assert "[English](README.md) | 한국어" in KOREAN


def test_readme_pair_shares_setup_status_and_validation_facts() -> None:
    for fact in COMMON_FACTS:
        assert fact in ENGLISH
        assert fact in KOREAN
    assert "PyPI" in ENGLISH and "HOLD" in ENGLISH
    assert "PyPI" in KOREAN and "HOLD" in KOREAN
    assert "Architecture" in ENGLISH and "Sequence Diagram" in ENGLISH
    assert "Architecture" in KOREAN and "Sequence Diagram" in KOREAN


def test_wip_keeps_the_dependency_order_and_current_issue() -> None:
    positions = [
        WIP.index(f"| {order} | [#{issue}]") for order, issue in enumerate(range(2, 9), start=1)
    ]
    assert positions == sorted(positions)
    assert "Issue [#3]" in WIP
    assert "Validated order intake service" in WIP


def test_readme_pair_links_the_first_runnable_example() -> None:
    assert "examples/order_intake/README.md" in ENGLISH
    assert "examples/order_intake/README.ko.md" in KOREAN


def test_agents_keeps_authoritative_commands_and_rules() -> None:
    for command in COMMON_FACTS[3:7]:
        assert command in AGENTS
    assert "Keep each example independently runnable and testable." in AGENTS
    assert "Keep `README.md` and `README.ko.md` aligned" in AGENTS
    assert "Docker-backed examples sequentially" in AGENTS
