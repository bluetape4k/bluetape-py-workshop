from __future__ import annotations

import importlib
import importlib.metadata
import importlib.util
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
OPTIONAL_PACKAGES = {
    "bluetape-cache-redis": (
        "packages/bluetape-cache-redis",
        "bluetape.cache.redis",
    ),
}
FORBIDDEN_LOCKED_DISTRIBUTIONS = {"cramjam", "lz4", "zstandard"}
FORBIDDEN_DEFAULT_DISTRIBUTIONS = FORBIDDEN_LOCKED_DISTRIBUTIONS | {
    "anyio",
    "bluetape-cache-redis",
    "fastapi",
    "httpcore",
    "httpx",
    "pydantic",
    "pydantic-core",
    "pyfory",
    "redis",
    "starlette",
    "uvicorn",
}
WEB_DISTRIBUTIONS = {"fastapi", "httpx", "uvicorn"}


def _load_toml(path: str) -> dict[str, object]:
    return tomllib.loads((ROOT / path).read_text(encoding="utf-8"))


def test_project_declares_the_approved_root_contract() -> None:
    project = _load_toml("pyproject.toml")
    metadata = project["project"]
    uv = project["tool"]["uv"]
    pytest_config = project["tool"]["pytest"]["ini_options"]

    assert metadata["requires-python"] == ">=3.13"
    assert set(metadata["dependencies"]) == {f"{name}==0.1.0" for name in PACKAGES}
    assert uv["package"] is False
    assert uv["required-version"] == "==0.11.28"
    assert uv["build-constraint-dependencies"] == ["uv-build==0.11.28"]
    assert pytest_config["markers"] == [
        "testcontainers: requires a reachable Docker runtime and runs serially",
    ]
    assert pytest_config["addopts"] == '-ra -m "not testcontainers"'


def test_project_declares_optional_providers() -> None:
    project = _load_toml("pyproject.toml")

    assert project["project"]["optional-dependencies"] == {
        "fastapi-order-api": [
            "fastapi>=0.139.2,<0.140",
            "httpx>=0.28.1,<0.29",
            "uvicorn>=0.51.0,<0.52",
        ],
        "fory": ["bluetape-serde[fory]==0.1.0"],
        "redis-coordination": ["bluetape-cache-redis==0.1.0"],
    }


def test_every_source_uses_one_repository_commit_and_subdirectory() -> None:
    sources = _load_toml("pyproject.toml")["tool"]["uv"]["sources"]

    assert set(sources) == set(PACKAGES) | set(OPTIONAL_PACKAGES)
    for name, (subdirectory, _) in (PACKAGES | OPTIONAL_PACKAGES).items():
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
    for name, (subdirectory, _) in OPTIONAL_PACKAGES.items():
        source_url = locked[name]["source"]["git"]
        parsed = urlsplit(source_url)
        query = parse_qs(parsed.query)
        assert f"{parsed.scheme}://{parsed.netloc}{parsed.path}" == UPSTREAM_REPOSITORY
        assert parsed.fragment == UPSTREAM_COMMIT
        assert query["subdirectory"] == [subdirectory]
    assert locked["redis"]["version"] == "8.0.1"
    assert locked["pyfory"]["version"] == "1.3.0"
    assert FORBIDDEN_LOCKED_DISTRIBUTIONS.isdisjoint(locked)


def test_lock_contains_the_isolated_web_extra() -> None:
    locked = {item["name"]: item for item in _load_toml("uv.lock")["package"]}
    root = locked["bluetape-py-workshop"]

    assert WEB_DISTRIBUTIONS <= locked.keys()
    assert root["optional-dependencies"]["fastapi-order-api"] == [
        {"name": "fastapi"},
        {"name": "httpx"},
        {"name": "uvicorn"},
    ]
    assert WEB_DISTRIBUTIONS.isdisjoint(dependency["name"] for dependency in root["dependencies"])


@pytest.mark.parametrize(("distribution", "package_info"), PACKAGES.items())
def test_required_distribution_is_installed_and_importable(
    distribution: str,
    package_info: tuple[str, str],
) -> None:
    _, import_name = package_info
    assert importlib.metadata.version(distribution) == "0.1.0"
    importlib.import_module(import_name)


@pytest.mark.parametrize("distribution", sorted(FORBIDDEN_DEFAULT_DISTRIBUTIONS))
def test_optional_provider_is_not_installed(distribution: str) -> None:
    with pytest.raises(importlib.metadata.PackageNotFoundError):
        importlib.metadata.version(distribution)


def test_redis_coordination_module_is_absent_from_the_default_environment() -> None:
    assert importlib.util.find_spec("bluetape.cache.redis") is None


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
