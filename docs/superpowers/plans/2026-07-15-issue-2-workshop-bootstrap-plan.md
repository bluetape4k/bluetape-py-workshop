# Issue #2 Workshop Bootstrap Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the reproducible Python 3.13 workshop foundation required by milestone `0.1.0` without adding a domain example or Docker-backed execution.

**Architecture:** A non-package root `uv` project installs ten focused `bluetape-py` distributions from one full Git commit and commits the resolved lockfile. Three contract-test files independently prove dependency provenance/provider isolation, CI trust boundaries, and bilingual documentation parity; a single pinned GitHub Actions job runs the same locked validation as local development.

**Tech Stack:** Python 3.13.14, uv/uv-build 0.11.28, pytest, pytest-asyncio, Ruff, GitHub Actions, actionlint 1.7.12 with Go 1.26.1.

---

## Scope and file ownership

| File | Responsibility | Write task |
|---|---|---:|
| `pyproject.toml` | Root project, focused dependencies, exact Git sources, uv/Ruff/pytest policy | 1 |
| `uv.lock` | Machine-resolved exact dependency and Git provenance | 1 |
| `tests/test_dependency_baseline.py` | Project/source/lock/import/provider/Docker-side-effect contract | 1 |
| `.github/workflows/ci.yml` | Exact-head, least-privilege locked validation | 2 |
| `tests/test_ci_contract.py` | Workflow event/ref/action/permission/command drift guard | 2 |
| `README.md` | English reader setup, learning path, source-only status, validation | 3 |
| `README.ko.md` | Korean parity version of the English reader contract | 3 |
| `AGENTS.md` | Thin authoritative commands and workshop-specific contributor rules | 3 |
| `WIP.md` | Current milestone/checkpoint/validation/next-action state | 3 and 5 |
| `tests/test_documentation_contract.py` | Locale links, shared facts, queue order, AGENTS commands | 3 |
| `docs/superpowers/risks/2026-07-15-issue-2-bootstrap-risk.md` | Triggered dependency/CI/cache/trust-boundary risk record | 4 |
| `docs/superpowers/reviews/2026-07-15-issue-2-implementation-review.md` | Six-lens implemented-diff findings and rerun evidence | 4 |
| `docs/superpowers/lessons/2026-07-15-issue-2-bootstrap.md` | Type A reusable lessons | 4 |

Tasks are sequential because `pyproject.toml`, `uv.lock`, root documentation, and
the final checkpoint are shared authority surfaces. No Docker-backed command is
part of this plan.

## Acceptance mapping

| Spec/issue criterion | Implementing task | Proof command |
|---|---:|---|
| Exact Git source commit and subdirectories | 1 | `uv run --locked pytest tests/test_dependency_baseline.py -q` |
| `uv sync --locked` succeeds | 1 | `uv sync --locked --python 3.13.14` |
| Fory/native providers absent | 1 | dependency baseline test |
| Testcontainers import has no runtime side effect | 1 | dependency baseline isolated subprocess test |
| Exact-head, least-privilege CI | 2 | CI contract test plus actionlint |
| Ruff and pytest gates | 1, 2 | locked Ruff/pytest commands |
| Equivalent English/Korean setup and status | 3 | documentation contract test plus writer review |
| Thin repo-local contributor commands | 3 | documentation contract test |
| WIP resumability | 3, 5 | WIP assertions and final checkpoint review |
| Spec, plan, risk, review, lesson artifacts | 4 | file presence, diff review, Lore commits |
| Exact-head PR merge-ready handoff | 5 | `gh pr checks`, live review/thread check, fresh head comparison |

## Conditional scope decisions

- Performance hot path/benchmark: `N/A`; the diff adds project metadata, tests,
  CI, and documentation but no application execution path.
- Coroutine cancellation/concurrency: `N/A`; no async API or task ownership is
  introduced.
- Database/backend capability: Docker absence and provider isolation are covered
  explicitly, while real Redis/Testcontainers execution is deferred to issue #7.
- Public Python API/KDoc and migration: `N/A`; no workshop package or reusable
  helper is created.
- New module registration, BOM, coverage aggregation, Spring Boot, Exposed, and
  release notes/CHANGELOG: `N/A`; this is a non-publishable Python root project
  and the repository has no release artifact or existing changelog to update.
- Cross-module duplication: one root contract is intentional; future examples
  must declare allowed distribution boundaries without copying workshop helpers.

## Risk prediction

Step 3-P is triggered by source-only dependencies, CI security boundaries, cache
behavior, and Testcontainers runtime ownership.

| Risk | Early signal | Mitigation in task | Rollback/rerun point |
|---|---|---|---|
| Git source resolves a different commit/subdirectory | lock provenance assertion fails | one shared full commit plus parsed source checks in Task 1 | restore previous `pyproject.toml`/`uv.lock`; rerun Task 1 from lock generation |
| PyPI or optional provider silently enters default lane | forbidden package appears in lock or metadata | negative lock and installed-distribution assertions in Task 1 | remove source/extra drift, regenerate lock, rerun fresh sync |
| Import contacts Docker or creates lifecycle work | patched constructor/process/thread call fails | isolated import test in Task 1; no Docker daemon command | stop implementation and re-evaluate upstream commit; do not weaken the test |
| Untrusted PR receives credentials or tests merge ref instead of head | CI contract test fails | explicit head ref, read-only permissions, non-persisted credentials, no secrets in Task 2 | revert workflow change and rerun Task 2/actionlint |
| Hosted runner/network/cache is transiently unavailable | same exact head fails only setup/fetch | bounded timeout, diagnostics, exact tool versions, cache key in Task 2 | rerun only the unchanged exact head; code/test failures require a new commit |
| README locales drift | common fact/link/command assertion fails | one task owns both locale files and writer review | revert both locale files together; never merge a one-locale repair |

### Task 1: Establish the locked dependency baseline with TDD

**Complexity:** High
**Dependencies:** Approved spec and reviewed upstream commit
**Required skills:** `bluetape-py-patterns`, `test-driven-development`
**Files:**
- Create: `tests/test_dependency_baseline.py`
- Create: `pyproject.toml`
- Create: `uv.lock`

- [ ] **Step 1: Write the failing dependency contract test**

Create `tests/test_dependency_baseline.py` with these authorities and assertions:

```python
from __future__ import annotations

import importlib
import importlib.metadata
import subprocess
import sys
import tomllib
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM_REPOSITORY = "https://github.com/bluetape4k/bluetape-py.git"
UPSTREAM_COMMIT = "4b7458f22cea0a9e757b5fbf7f5ff4bc8c23cb9a"
PACKAGES = {
    "bluetape-async": ("packages/bluetape-async", "bluetape.asyncio"),
    "bluetape-cache": ("packages/bluetape-cache", "bluetape.cache"),
    "bluetape-codec": ("packages/bluetape-codec", "bluetape.codec"),
    "bluetape-collections": ("packages/bluetape-collections", "bluetape.collections"),
    "bluetape-compression": ("packages/bluetape-compression", "bluetape.compression"),
    "bluetape-core": ("packages/bluetape-core", "bluetape.core"),
    "bluetape-logging": ("packages/bluetape-logging", "bluetape.logging"),
    "bluetape-serde": ("packages/bluetape-serde", "bluetape.serde"),
    "bluetape-testcontainers": (
        "packages/bluetape-testcontainers",
        "bluetape.testcontainers",
    ),
    "bluetape-testing": ("packages/bluetape-testing", "bluetape.testing"),
}
FORBIDDEN_DISTRIBUTIONS = {"cramjam", "lz4", "pyfory", "zstandard"}


def _load_toml(path: str) -> dict[str, object]:
    return tomllib.loads((ROOT / path).read_text(encoding="utf-8"))


def test_project_declares_the_approved_root_contract() -> None:
    project = _load_toml("pyproject.toml")
    metadata = project["project"]
    uv = project["tool"]["uv"]

    assert metadata["requires-python"] == ">=3.13"
    assert set(metadata["dependencies"]) == {f"{name}==0.1.0" for name in PACKAGES}
    assert uv["package"] is False
    assert uv["required-version"] == "==0.11.28"
    assert uv["build-constraint-dependencies"] == ["uv-build==0.11.28"]


def test_every_source_uses_one_repository_commit_and_subdirectory() -> None:
    sources = _load_toml("pyproject.toml")["tool"]["uv"]["sources"]

    assert set(sources) == set(PACKAGES)
    for name, (subdirectory, _) in PACKAGES.items():
        assert sources[name] == {
            "git": UPSTREAM_REPOSITORY,
            "rev": UPSTREAM_COMMIT,
            "subdirectory": subdirectory,
        }


def test_lock_resolves_every_bluetape_distribution_to_the_full_commit() -> None:
    locked = {item["name"]: item for item in _load_toml("uv.lock")["package"]}

    for name, (subdirectory, _) in PACKAGES.items():
        source_url = locked[name]["source"]["git"]
        parsed = urlsplit(source_url)
        query = parse_qs(parsed.query)
        assert f"{parsed.scheme}://{parsed.netloc}{parsed.path}" == UPSTREAM_REPOSITORY
        assert parsed.fragment == UPSTREAM_COMMIT
        assert query["subdirectory"] == [subdirectory]
    assert FORBIDDEN_DISTRIBUTIONS.isdisjoint(locked)


@pytest.mark.parametrize(("distribution", "module"), PACKAGES.items())
def test_required_distribution_is_installed_and_importable(
    distribution: str,
    module: tuple[str, str],
) -> None:
    _, import_name = module
    assert importlib.metadata.version(distribution) == "0.1.0"
    importlib.import_module(import_name)


@pytest.mark.parametrize("distribution", sorted(FORBIDDEN_DISTRIBUTIONS))
def test_optional_provider_is_not_installed(distribution: str) -> None:
    with pytest.raises(importlib.metadata.PackageNotFoundError):
        importlib.metadata.version(distribution)


def test_testcontainers_import_has_no_runtime_side_effect() -> None:
    probe = """
import importlib
import subprocess
import threading
from unittest.mock import patch
from testcontainers.core.docker_client import DockerClient

threads_before = tuple(threading.enumerate())
with (
    patch.object(DockerClient, "__init__", side_effect=AssertionError("Docker client created")),
    patch.object(subprocess, "Popen", side_effect=AssertionError("process started")),
    patch.object(threading.Thread, "start", side_effect=AssertionError("thread started")),
):
    importlib.import_module("bluetape.testcontainers")
assert tuple(threading.enumerate()) == threads_before
"""
    completed = subprocess.run(
        [sys.executable, "-I", "-c", probe],
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert completed.returncode == 0, completed.stderr
```

- [ ] **Step 2: Run the isolated test and observe RED**

Run:

```bash
uvx --from pytest==8.4.2 pytest tests/test_dependency_baseline.py -q
```

Expected: FAIL because `pyproject.toml` and `uv.lock` do not exist.

- [ ] **Step 3: Add the minimal root project configuration**

Create `pyproject.toml`:

```toml
[project]
name = "bluetape-py-workshop"
version = "0.1.0"
description = "Runnable backend service examples using bluetape-py."
readme = "README.md"
requires-python = ">=3.13"
dependencies = [
    "bluetape-async==0.1.0",
    "bluetape-cache==0.1.0",
    "bluetape-codec==0.1.0",
    "bluetape-collections==0.1.0",
    "bluetape-compression==0.1.0",
    "bluetape-core==0.1.0",
    "bluetape-logging==0.1.0",
    "bluetape-serde==0.1.0",
    "bluetape-testcontainers==0.1.0",
    "bluetape-testing==0.1.0",
]

[dependency-groups]
dev = [
    "pytest>=8.4.0,<9",
    "pytest-asyncio>=1.1.0,<2",
    "ruff>=0.12.0,<0.13",
]

[tool.uv]
package = false
required-version = "==0.11.28"
build-constraint-dependencies = ["uv-build==0.11.28"]

[tool.uv.sources]
bluetape-async = { git = "https://github.com/bluetape4k/bluetape-py.git", rev = "4b7458f22cea0a9e757b5fbf7f5ff4bc8c23cb9a", subdirectory = "packages/bluetape-async" }
bluetape-cache = { git = "https://github.com/bluetape4k/bluetape-py.git", rev = "4b7458f22cea0a9e757b5fbf7f5ff4bc8c23cb9a", subdirectory = "packages/bluetape-cache" }
bluetape-codec = { git = "https://github.com/bluetape4k/bluetape-py.git", rev = "4b7458f22cea0a9e757b5fbf7f5ff4bc8c23cb9a", subdirectory = "packages/bluetape-codec" }
bluetape-collections = { git = "https://github.com/bluetape4k/bluetape-py.git", rev = "4b7458f22cea0a9e757b5fbf7f5ff4bc8c23cb9a", subdirectory = "packages/bluetape-collections" }
bluetape-compression = { git = "https://github.com/bluetape4k/bluetape-py.git", rev = "4b7458f22cea0a9e757b5fbf7f5ff4bc8c23cb9a", subdirectory = "packages/bluetape-compression" }
bluetape-core = { git = "https://github.com/bluetape4k/bluetape-py.git", rev = "4b7458f22cea0a9e757b5fbf7f5ff4bc8c23cb9a", subdirectory = "packages/bluetape-core" }
bluetape-logging = { git = "https://github.com/bluetape4k/bluetape-py.git", rev = "4b7458f22cea0a9e757b5fbf7f5ff4bc8c23cb9a", subdirectory = "packages/bluetape-logging" }
bluetape-serde = { git = "https://github.com/bluetape4k/bluetape-py.git", rev = "4b7458f22cea0a9e757b5fbf7f5ff4bc8c23cb9a", subdirectory = "packages/bluetape-serde" }
bluetape-testcontainers = { git = "https://github.com/bluetape4k/bluetape-py.git", rev = "4b7458f22cea0a9e757b5fbf7f5ff4bc8c23cb9a", subdirectory = "packages/bluetape-testcontainers" }
bluetape-testing = { git = "https://github.com/bluetape4k/bluetape-py.git", rev = "4b7458f22cea0a9e757b5fbf7f5ff4bc8c23cb9a", subdirectory = "packages/bluetape-testing" }

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-ra"
asyncio_mode = "auto"

[tool.ruff]
target-version = "py313"
line-length = 100

[tool.ruff.lint]
select = ["A", "B", "C4", "E", "F", "I", "N", "RUF", "UP", "W"]
```

- [ ] **Step 4: Generate the lock and synchronize from a clean default lane**

Run:

```bash
test "$(uv --version)" = "uv 0.11.28"
uv lock --python 3.13.14
rm -rf .venv
uv sync --locked --python 3.13.14
```

Expected: `uv.lock` is created, all ten `bluetape-*` packages resolve to the
approved Git commit, and no Docker daemon is contacted. Removing `.venv` is
allowed only inside this isolated issue worktree.

- [ ] **Step 5: Run the dependency contract and observe GREEN**

Run:

```bash
uv run --locked pytest tests/test_dependency_baseline.py -q
uv run --locked ruff check tests/test_dependency_baseline.py
uv run --locked ruff format --check tests/test_dependency_baseline.py
```

Expected: all dependency/provider/import tests PASS; Ruff reports no errors or
format changes.

- [ ] **Step 6: Commit the foundation with Lore evidence**

```bash
git add pyproject.toml uv.lock tests/test_dependency_baseline.py
git commit -m "Make every workshop run resolve the same source baseline" \
  -m "Constraint: PyPI publication is on hold, so focused distributions use one full Git commit." \
  -m "Rejected: Moving future packages out of the root baseline | milestone-wide drift detection is intentional" \
  -m "Confidence: high" \
  -m "Scope-risk: moderate" \
  -m "Directive: Regenerate metadata and lock atomically whenever the upstream commit changes." \
  -m "Tested: locked sync; dependency baseline pytest; targeted Ruff" \
  -m "Not-tested: Docker-backed execution is outside issue #2."
```

### Task 2: Add exact-head least-privilege CI with TDD

**Complexity:** Medium
**Dependencies:** Task 1 green lock and tests
**Required skills:** `bluetape-py-patterns`, `test-driven-development`
**Files:**
- Create: `tests/test_ci_contract.py`
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: Write the failing CI contract test**

Create `tests/test_ci_contract.py`:

```python
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
```

- [ ] **Step 2: Run the CI test and observe RED**

Run:

```bash
uv run --locked pytest tests/test_ci_contract.py -q
```

Expected: FAIL with `FileNotFoundError` for `.github/workflows/ci.yml`.

- [ ] **Step 3: Create the minimum workflow that satisfies the contract**

Before writing YAML, verify that each pinned action commit exists in its
canonical repository:

```bash
gh api repos/actions/checkout/commits/93cb6efe18208431cddfb8368fd83d5badbf9bfd --jq .sha
gh api repos/astral-sh/setup-uv/commits/11f9893b081a58869d3b5fccaea48c9e9e46f990 --jq .sha
gh api repos/actions/setup-python/commits/ece7cb06caefa5fff74198d8649806c4678c61a1 --jq .sha
```

Expected: each command prints the requested full SHA. A mismatch or missing
commit stops Task 2 until the workflow pin is re-reviewed.

Create `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  pull_request:
    branches: [develop]
  push:
    branches: [develop]

permissions:
  contents: read

concurrency:
  group: ${{ github.workflow }}-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: true

jobs:
  test:
    runs-on: ubuntu-24.04
    timeout-minutes: 15
    steps:
      - name: Checkout exact source head
        uses: actions/checkout@93cb6efe18208431cddfb8368fd83d5badbf9bfd
        with:
          ref: ${{ github.event_name == 'pull_request' && github.event.pull_request.head.sha || github.sha }}
          persist-credentials: false

      - name: Set up uv
        uses: astral-sh/setup-uv@11f9893b081a58869d3b5fccaea48c9e9e46f990
        with:
          version: "0.11.28"
          enable-cache: true
          cache-dependency-glob: |
            pyproject.toml
            uv.lock
          prune-cache: true

      - name: Set up Python
        uses: actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1
        with:
          python-version: "3.13.14"

      - name: Report exact toolchain and head
        run: |
          git rev-parse HEAD
          test "$(uv --version)" = "uv 0.11.28"
          test "$(python --version)" = "Python 3.13.14"

      - name: Synchronize locked environment
        run: uv sync --locked --python 3.13.14

      - name: Verify dependency and provider boundary
        run: uv run --locked pytest tests/test_dependency_baseline.py -q

      - name: Check Ruff lint
        run: uv run --locked ruff check .

      - name: Check Ruff formatting
        run: uv run --locked ruff format --check .

      - name: Run tests
        run: uv run --locked pytest
```

- [ ] **Step 4: Validate the workflow and observe GREEN**

Run:

```bash
uv run --locked pytest tests/test_ci_contract.py -q
GOTOOLCHAIN=go1.26.1 go run github.com/rhysd/actionlint/cmd/actionlint@v1.7.12 \
  .github/workflows/ci.yml
```

Expected: CI contract PASS and actionlint exits 0 with no output.

- [ ] **Step 5: Commit the CI boundary**

```bash
git add .github/workflows/ci.yml tests/test_ci_contract.py
git commit -m "Make pull request evidence represent the exact unprivileged head" \
  -m "Constraint: Source builds execute untrusted pull request code without repository secrets." \
  -m "Confidence: high" \
  -m "Scope-risk: narrow" \
  -m "Directive: Keep action SHAs, uv version, permissions, and exact-head checkout under contract tests." \
  -m "Tested: CI contract pytest; actionlint 1.7.12 with Go 1.26.1" \
  -m "Not-tested: Hosted GitHub runner execution begins after PR push."
```

### Task 3: Replace roadmap-only docs with the bilingual foundation guide

**Complexity:** Medium
**Dependencies:** Tasks 1 and 2 establish commands and workflow facts
**Required skills:** `bluetape-writer`, `test-driven-development`
**Files:**
- Create: `tests/test_documentation_contract.py`
- Modify: `README.md`
- Modify: `README.ko.md`
- Modify: `AGENTS.md`
- Modify: `WIP.md`

- [ ] **Step 1: Write the failing documentation contract**

Create `tests/test_documentation_contract.py`:

```python
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
    positions = [WIP.index(f"#{issue}") for issue in range(2, 9)]
    assert positions == sorted(positions)
    assert "Issue #2" in WIP
    assert "In progress" in WIP


def test_agents_keeps_authoritative_commands_and_rules() -> None:
    for command in COMMON_FACTS[3:7]:
        assert command in AGENTS
    assert "Keep each example independently runnable and testable." in AGENTS
    assert "Keep `README.md` and `README.ko.md` aligned" in AGENTS
    assert "Docker-backed examples sequentially" in AGENTS
```

- [ ] **Step 2: Run the documentation test and observe RED**

Run:

```bash
uv run --locked pytest tests/test_documentation_contract.py -q
```

Expected: FAIL because the roadmap-only README pair lacks setup, validation,
package status, and future diagram contracts.

- [ ] **Step 3: Write the aligned reader journey in both locales**

Replace the README pair with equivalent sections in this exact order:

```text
1. locale switch
2. repository purpose and current foundation-only status
3. milestone 0.1.0 learning path table for issues #2-#8
4. requirements: Python 3.13.14 and uv 0.11.28
5. setup: uv sync --locked --python 3.13.14
6. source baseline: repository, full commit, v0.1.0 tag distinction, PyPI HOLD
7. validation: locked Ruff and pytest commands
8. example documentation contract: Scenario, Architecture, Sequence Diagram,
   exact APIs, run/result/test/cleanup/troubleshooting
9. current limitations and WIP.md navigation
```

Use these identical command blocks in both files:

```bash
uv sync --locked --python 3.13.14
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked pytest
```

State plainly in English and natural Korean that `v0.1.0` points to
`596e4898c915b55339521814ae7303953b50f4d2`, while the supported workshop source
is the later commit `4b7458f22cea0a9e757b5fbf7f5ff4bc8c23cb9a`; focused packages are not a
supported PyPI installation path. Do not add an architecture or sequence image
because issue #2 has no runtime behavior.

- [ ] **Step 4: Make AGENTS and WIP match the executable commands**

Add an `## Commands` section to `AGENTS.md` containing the four locked commands
from Step 3 plus the pinned actionlint command. Keep the existing workshop rules,
and state that `uv 0.11.28` is required while Python remains `>=3.13` with
`3.13.14` as the reference interpreter.

Update `WIP.md` so:

- Issue #2 remains `In progress` until merge;
- the planned validation label becomes authoritative validation;
- `Runnable now` says the repository foundation is runnable but domain examples
  begin at #3;
- blocker says `none` after local verification;
- next action is implemented-diff review and PR creation;
- the last validated head remains the latest actually verified content commit.

- [ ] **Step 5: Run the documentation checks and writer parity review**

Run:

```bash
uv run --locked pytest tests/test_documentation_contract.py -q
uv run --locked ruff check tests/test_documentation_contract.py
uv run --locked ruff format --check tests/test_documentation_contract.py
git diff --check
```

Expected: all tests and Ruff checks PASS; `git diff --check` prints nothing.
Then compare the two README files section-by-section and record that commands,
versions, commits, links, issue order, package status, and scope are identical.

- [ ] **Step 6: Commit the aligned public contract**

```bash
git add README.md README.ko.md AGENTS.md WIP.md tests/test_documentation_contract.py
git commit -m "Let readers reproduce the workshop foundation before examples arrive" \
  -m "Constraint: Public setup and package-status facts must remain equivalent in English and Korean." \
  -m "Confidence: high" \
  -m "Scope-risk: narrow" \
  -m "Directive: Update both README locales and the structural contract test in every user-facing change." \
  -m "Tested: documentation contract pytest; targeted Ruff; git diff --check" \
  -m "Not-tested: Example diagrams begin only after issue #3 source exists."
```

### Task 4: Prove the integrated branch and record Type A evidence

**Complexity:** High
**Dependencies:** Tasks 1-3 green and committed
**Required skills:** `verification-before-completion`, `requesting-code-review`, `bluetape-writer`
**Files:**
- Create: `docs/superpowers/risks/2026-07-15-issue-2-bootstrap-risk.md`
- Create: `docs/superpowers/reviews/2026-07-15-issue-2-implementation-review.md`
- Create: `docs/superpowers/lessons/2026-07-15-issue-2-bootstrap.md`

- [ ] **Step 1: Run the full fresh validation ladder**

Run sequentially:

```bash
rm -rf .venv
test "$(uv --version)" = "uv 0.11.28"
uv sync --locked --python 3.13.14
uv run --locked pytest tests/test_dependency_baseline.py -q
uv run --locked pytest tests/test_ci_contract.py -q
uv run --locked pytest tests/test_documentation_contract.py -q
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked pytest
GOTOOLCHAIN=go1.26.1 go run github.com/rhysd/actionlint/cmd/actionlint@v1.7.12 \
  .github/workflows/ci.yml
git diff --check
```

Expected: every command exits 0; provider and Docker-side-effect tests run
without contacting Docker; actionlint and diff check print no findings.

- [ ] **Step 2: Record the triggered risk evidence**

Create the risk record with the four concrete categories from this plan's risk
table: Git provenance, provider/runtime isolation, exact-head CI security, and
hosted-runner/cache recovery. For each category record the signal, the exact test
or workflow mitigation, and the rollback/rerun boundary. Explicitly mark
database, coroutine cancellation, API migration, and benchmark risk `N/A`
because issue #2 adds no runtime service or public Python API.

- [ ] **Step 3: Run six independent implemented-diff reviews**

Review `origin/develop...HEAD` independently from performance, stability,
security, operator/Ops, developer/API, and user/caller perspectives. Each lane
returns P0-P3 with file/line evidence. Integrate in the main session, repair all
P0/P1, resolve or explicitly defer P2/P3, and rerun affected lanes until the
latest integrated result is P0=0 and P1=0.

Create the implementation review record with:

- exact base and reviewed head;
- six perspective count table;
- every P0/P1 repair and rerun result;
- P2/P3 disposition;
- README locale parity result;
- full validation command/result summary.

- [ ] **Step 4: Record the mandatory Type A lesson**

Create the lesson artifact with these reusable findings:

1. `apply_patch` resolves paths from the primary checkout tool context, so
   worktree edits must use worktree-qualified paths and the main checkout must be
   rechecked immediately;
2. a committed WIP document cannot self-reference its own commit hash, so a
   resume checkpoint records the last validated content head;
3. a GitHub Release tag and a later source-only commit are separate provenance
   facts and must not be presented as equivalent;
4. installing Testcontainers libraries is distinct from contacting Docker, so
   deterministic lanes need an import-side-effect test rather than an absence
   claim for the wrapper itself.

- [ ] **Step 5: Commit risk, review, and lesson evidence**

```bash
git add docs/superpowers/risks docs/superpowers/reviews docs/superpowers/lessons
git commit -m "Preserve the evidence needed to trust the workshop bootstrap" \
  -m "Constraint: Type A completion requires reusable lessons and six-perspective implemented-diff review." \
  -m "Confidence: high" \
  -m "Scope-risk: narrow" \
  -m "Directive: Do not create the PR until the recorded head has P0=0 P1=0 and fresh validation." \
  -m "Tested: full locked validation ladder; actionlint; six-perspective review" \
  -m "Not-tested: GitHub-hosted CI starts only after push."
```

### Task 5: Create the issue-linked PR and stop at the merge gate

**Complexity:** Medium
**Dependencies:** Task 4 evidence commit; exact local head remains clean
**Required skills:** `bluetape-workflow`, `verification-before-completion`
**Files:**
- Modify: `WIP.md` with actual PR/checkpoint state
- Create then remove after PR creation: `.omx/pr/issue-2-body.md`

- [ ] **Step 1: Push the approved branch and create the scoped PR**

Target is fixed by the approved workflow scope:

```text
repository: bluetape4k/bluetape-py-workshop
base: develop
head: chore/issue-2-workshop-bootstrap
issue: #2
```

Create `.omx/pr/issue-2-body.md` with this complete body, replacing only the
reviewed head with the output of `git rev-parse HEAD`:

```markdown
Closes #2

## Scenario

Establish the reproducible Python 3.13 workshop foundation required before the
application-shaped examples in issues #3-#8.

## Scope

- non-package uv root with a committed lockfile
- ten focused bluetape-py distributions pinned to one source commit
- provider/Docker import-side-effect contract tests
- exact-head, least-privilege GitHub Actions CI
- aligned English and Korean setup documentation

## Source status

- Workshop source commit: `4b7458f22cea0a9e757b5fbf7f5ff4bc8c23cb9a`
- GitHub Release tag commit: `596e4898c915b55339521814ae7303953b50f4d2`
- PyPI focused-package publication: HOLD

## Evidence

- full locked validation ladder: PASS
- actionlint 1.7.12 with Go 1.26.1: PASS
- implemented-diff review: P0=0, P1=0
- reviewed head: use the exact 40-character output from `git rev-parse HEAD`

## Boundaries

No domain example, Docker-backed execution, publish/release action, or runtime
architecture/sequence diagram is included. Risk, review, and lesson evidence is
linked from `docs/superpowers/`.
```

Then run:

```bash
git push -u origin chore/issue-2-workshop-bootstrap
gh pr create --repo bluetape4k/bluetape-py-workshop \
  --base develop \
  --head chore/issue-2-workshop-bootstrap \
  --title "Bootstrap the reproducible Python workshop foundation" \
  --body-file .omx/pr/issue-2-body.md
```

The PR body must include issue linkage (`Closes #2`), scenario/scope, exact
source commit and PyPI HOLD, validation evidence, P0/P1 result, risk/lesson
links, and the explicit statement that no Docker-backed example or runtime
diagram is included.

- [ ] **Step 2: Update and commit the resumable PR checkpoint**

Read the PR number and current head using `gh pr view`. Update `WIP.md` with the
actual PR link, last validated 40-character head, CI state, blocker, and next
action. Commit this state with a Lore message and push it; then treat the new
commit as a new head requiring CI/review evidence.

- [ ] **Step 3: Prove exact-head merge readiness**

After the first CI run passes, prove same-head cache restoration without changing
the branch:

```bash
head_sha="$(git rev-parse HEAD)"
run_id="$(gh run list --repo bluetape4k/bluetape-py-workshop \
  --workflow CI --branch chore/issue-2-workshop-bootstrap \
  --json databaseId,headSha \
  --jq '.[] | select(.headSha == "'"$head_sha"'") | .databaseId' | head -1)"
test -n "$run_id"
gh run rerun "$run_id" --repo bluetape4k/bluetape-py-workshop
gh run watch "$run_id" --repo bluetape4k/bluetape-py-workshop --exit-status
gh run view "$run_id" --repo bluetape4k/bluetape-py-workshop --log | \
  rg 'Cache restored|cache hit'
```

Expected: the unchanged head passes again and setup-uv reports restored cache
evidence. A missing cache message is an operability finding, not a reason to use
a wall-clock threshold.

Then run the exact-head checks:

Run:

```bash
git status --short --branch
git rev-parse HEAD
gh pr view --repo bluetape4k/bluetape-py-workshop --json number,url,headRefOid,baseRefName,headRefName,mergeable,reviewDecision,statusCheckRollup
gh pr checks --repo bluetape4k/bluetape-py-workshop
```

Expected: local `HEAD` equals `headRefOid`, base/head are the approved branches,
all required checks pass for that exact head, mergeability is not blocked, and
live review threads have no unresolved P0/P1 findings.

- [ ] **Step 4: Stop and request fresh merge approval**

Report the PR URL, exact head, check/review evidence, changed files, package
status caveat, and remaining external risks. Do not enable auto-merge and do not
merge, close the milestone, tag, publish, release, or delete the branch/worktree
without the separately required authority.
