from pathlib import Path

WORKFLOW = Path(".github/workflows/ci.yml")


def test_ci_has_safe_events_permissions_and_exact_head_checkout() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "pull_request_target" not in text
    assert "secrets:" not in text
    assert "pull_request:" in text
    assert "branches: [develop]" in text
    assert "permissions:\n  contents: read" in text
    assert "github.event.pull_request.head.sha" in text
    assert "git rev-parse HEAD" in text
    assert "persist-credentials: false" in text
    assert "timeout-minutes: 15" in text
    assert "cancel-in-progress: true" in text


def test_ci_pins_tools_cache_inputs_and_locked_commands() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "actions/checkout@93cb6efe18208431cddfb8368fd83d5badbf9bfd" in text
    assert "astral-sh/setup-uv@11f9893b081a58869d3b5fccaea48c9e9e46f990" in text
    assert "actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1" in text
    assert 'version: "0.11.28"' in text
    assert 'python-version: "3.13.14"' in text
    assert "cache-dependency-glob: |" in text
    assert "pyproject.toml" in text
    assert "uv.lock" in text
    assert "uv sync --locked --python 3.13.14" in text
    assert "uv run --locked ruff check ." in text
    assert "uv run --locked ruff format --check ." in text
    assert "uv run --locked pytest" in text
