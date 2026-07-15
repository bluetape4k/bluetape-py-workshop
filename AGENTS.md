# AGENTS.md - bluetape-py-workshop

This repository inherits the workspace guidance from `../AGENTS.md`.
Read and follow the workspace root guide first. This file only adds
Python-workshop layout, commands, and local rules.

Runnable backend service examples using `bluetape-py`.

## Commands

```bash
uv sync --locked --python 3.13.14
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked pytest
GOTOOLCHAIN=go1.26.1 go run github.com/rhysd/actionlint/cmd/actionlint@v1.7.12 \
  .github/workflows/ci.yml
```

## Skills

- Use `bluetape-workflow` for task classification and issue/PR discipline.
- Use `bluetape-py-patterns` for Python implementation, async behavior,
  packaging, tests, and review.

## Rules

- Target Python 3.13+ with Python 3.13.14 as the reference interpreter.
- Require uv 0.11.28 and use the committed lockfile as dependency authority.
- Keep examples application-shaped; reusable helpers belong in `bluetape-py`.
- Keep each example independently runnable and testable.
- Keep `README.md` and `README.ko.md` aligned for every user-facing change.
- Run Docker-backed examples sequentially and use ecosystem Testcontainers
  wrappers when available.
- Link examples to the exact `bluetape-py` package status and upstream issue
  when they depend on source-only or planned capabilities.
