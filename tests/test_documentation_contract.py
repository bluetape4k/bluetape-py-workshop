from pathlib import Path

ENGLISH = Path("README.md").read_text(encoding="utf-8")
KOREAN = Path("README.ko.md").read_text(encoding="utf-8")
WIP = Path("WIP.md").read_text(encoding="utf-8")
AGENTS = Path("AGENTS.md").read_text(encoding="utf-8")
WEB_RESEARCH = Path("docs/research/asgi-fastapi-boundary")

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
    assert "Issue [#10]" in WIP
    assert "Redis load coordination" in WIP
    assert "feat/issue-10-redis-load-coordination" in WIP
    assert "PR #19" in WIP
    assert "836ff2090eb6a998b7247e9bf89ea3d77065c29d" in WIP
    assert "Issue [#20]" in WIP and "blocked:upstream" in WIP
    assert "uv run --locked python -m examples.integrated_order_backend" in WIP
    assert 'pytest -m "not testcontainers"' in WIP
    assert (
        "pytest -m testcontainers examples/redis_test_server/tests/test_redis_integration.py -q"
        in WIP
    )


def test_readme_pair_links_every_runnable_example() -> None:
    assert "examples/order_intake/README.md" in ENGLISH
    assert "examples/order_intake/README.ko.md" in KOREAN
    assert "examples/catalog_enrichment/README.md" in ENGLISH
    assert "examples/catalog_enrichment/README.ko.md" in KOREAN
    assert "examples/cached_product_catalog/README.md" in ENGLISH
    assert "examples/cached_product_catalog/README.ko.md" in KOREAN
    assert "examples/bounded_payload_processing/README.md" in ENGLISH
    assert "examples/bounded_payload_processing/README.ko.md" in KOREAN
    assert "examples/redis_test_server/README.md" in ENGLISH
    assert "examples/redis_test_server/README.ko.md" in KOREAN
    assert "examples/integrated_order_backend/README.md" in ENGLISH
    assert "examples/integrated_order_backend/README.ko.md" in KOREAN
    assert "examples/redis_load_coordination/README.md" in ENGLISH
    assert "examples/redis_load_coordination/README.ko.md" in KOREAN


def test_readme_pair_documents_deterministic_and_docker_redis_lanes() -> None:
    commands = (
        'uv run --locked pytest -m "not testcontainers"',
        "uv run --locked pytest -m testcontainers "
        "examples/redis_test_server/tests/test_redis_integration.py -q",
        "uv run --locked python -m examples.redis_test_server",
        "uv run --locked python -m examples.integrated_order_backend",
        "uv run --locked pytest examples/integrated_order_backend/tests -q",
        "UV_PROJECT_ENVIRONMENT=.venv-redis uv sync --locked "
        "--extra redis-coordination --python 3.13.14",
        "--extra redis-coordination python -m examples.redis_load_coordination",
        "examples/redis_load_coordination/tests/test_redis_integration.py -q",
    )

    for command in commands:
        assert command in ENGLISH
        assert command in KOREAN


def test_agents_keeps_authoritative_commands_and_rules() -> None:
    for command in COMMON_FACTS[3:7]:
        assert command in AGENTS
    assert "Keep each example independently runnable and testable." in AGENTS
    assert "Keep `README.md` and `README.ko.md` aligned" in AGENTS
    assert "Every example README pair must embed" in AGENTS
    assert "Docker-backed examples sequentially" in AGENTS


def test_every_runnable_example_embeds_required_diagrams_in_both_locales() -> None:
    examples = sorted(path.parent for path in Path("examples").glob("*/__main__.py"))
    assert examples

    for example in examples:
        english = (example / "README.md").read_text(encoding="utf-8")
        korean = (example / "README.ko.md").read_text(encoding="utf-8")

        for name in ("architecture.png", "architecture.svg", "sequence.png", "sequence.svg"):
            asset = example / "docs" / "images" / name
            assert asset.is_file(), f"missing required diagram asset: {asset}"
            link = f"docs/images/{name}"
            assert link in english, f"{example}/README.md must link {link}"
            assert link in korean, f"{example}/README.ko.md must link {link}"


def test_asgi_fastapi_boundary_research_is_bilingual_and_source_backed() -> None:
    english = (WEB_RESEARCH / "README.md").read_text(encoding="utf-8")
    korean = (WEB_RESEARCH / "README.ko.md").read_text(encoding="utf-8")

    assert "English | [한국어](README.ko.md)" in english
    assert "[English](README.md) | 한국어" in korean

    shared_facts = (
        "Direct FastAPI",
        "Raw ASGI",
        "Future `bluetape-fastapi`",
        "POST /orders",
        "request parsing",
        "dependency injection",
        "request-context reset",
        "public exception mapping",
        "client disconnect",
        "timeout",
        "lifespan",
        "bluetape-py/issues/21",
        "bluetape-py/issues/22",
        "exact stable release tag or commit",
        "2026-07-16",
    )
    for fact in shared_facts:
        assert fact in english
        assert fact in korean

    official_sources = (
        "asgi.readthedocs.io/en/latest/specs/lifespan.html",
        "asgi.readthedocs.io/en/latest/specs/www.html",
        "starlette.io/lifespan/",
        "starlette.io/requests/",
        "fastapi.tiangolo.com/advanced/events/",
        "fastapi.tiangolo.com/tutorial/dependencies/",
        "fastapi.tiangolo.com/tutorial/handling-errors/",
    )
    for source in official_sources:
        assert source in english
        assert source in korean


def test_asgi_fastapi_boundary_research_embeds_required_diagrams() -> None:
    english = (WEB_RESEARCH / "README.md").read_text(encoding="utf-8")
    korean = (WEB_RESEARCH / "README.ko.md").read_text(encoding="utf-8")

    for name in ("architecture.png", "architecture.svg", "sequence.png", "sequence.svg"):
        asset = WEB_RESEARCH / "images" / name
        assert asset.is_file(), f"missing research diagram asset: {asset}"
        link = f"images/{name}"
        assert link in english
        assert link in korean


def test_root_roadmap_exposes_current_milestone_boundaries() -> None:
    assert "docs/research/asgi-fastapi-boundary/README.md" in ENGLISH
    assert "docs/research/asgi-fastapi-boundary/README.ko.md" in KOREAN
    assert "Issue [#10]" in WIP
    assert "feat/issue-10-redis-load-coordination" in WIP
    assert "0.2.0" in WIP
    assert "Issue #9 completed" in WIP
    assert "Issue [#20]" in WIP and "blocked:upstream" in WIP
