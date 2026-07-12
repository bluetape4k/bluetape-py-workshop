# AGENTS.md - bluetape-py-workshop

This repository inherits the workspace guidance from `../AGENTS.md`.
Read and follow the workspace root guide first. This file only adds
Python-workshop layout, commands, and local rules.

Runnable backend service examples using `bluetape-py`.

## Skills

- Use `bluetape-workflow` for task classification and issue/PR discipline.
- Use `bluetape-py-patterns` for Python implementation, async behavior,
  packaging, tests, and review.

## Rules

- Target Python 3.13+ and use `uv` as the project and lockfile authority.
- Keep examples application-shaped; reusable helpers belong in `bluetape-py`.
- Keep each example independently runnable and testable.
- Keep `README.md` and `README.ko.md` aligned for every user-facing change.
- Run Docker-backed examples sequentially and use ecosystem Testcontainers
  wrappers when available.
- Link examples to the exact `bluetape-py` package status and upstream issue
  when they depend on source-only or planned capabilities.

