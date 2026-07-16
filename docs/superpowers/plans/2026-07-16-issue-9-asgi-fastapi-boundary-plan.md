# ASGI and FastAPI Workshop Boundary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> `subagent-driven-development` (recommended) or `executing-plans` to implement
> this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Record a bilingual, source-backed decision for the first HTTP workshop
example without introducing framework code or claiming an upstream adapter that
does not exist.

**Architecture:** The research guide compares direct FastAPI, raw ASGI, and a
future `bluetape-fastapi` distribution. It recommends a workshop-owned FastAPI
transport around the existing framework-neutral `OrderBackendApplication`,
while keeping request DTOs, dependency injection, context reset, public error
mapping, response shaping, disconnect policy, and lifespan wiring explicit.

**Tech Stack:** Markdown, pytest documentation contracts, SVG, CairoSVG,
official ASGI/Starlette/FastAPI documentation, GitHub issue evidence.

---

## Execution Contract

- Repository: `bluetape4k/bluetape-py-workshop`
- Base: `develop@a6eae41ed7b946e6859d2cc3d1866a04ea539590`
- Head: `docs/issue-9-asgi-fastapi-boundary`
- Worktree:
  `/Users/debop/work/bluetape4k/bluetape-py-workshop/.worktrees/issue-9-asgi-fastapi-boundary`
- Issue: <https://github.com/bluetape4k/bluetape-py-workshop/issues/9>
- Workflow type: Type E documentation/research.
- PR authority: create a PR from the approved head to `develop`; merging remains
  a separate fresh approval gate and auto-merge is forbidden.
- Explicit N/A: Python implementation, FastAPI dependency, lockfile changes,
  Docker/Testcontainers, benchmark, release/tag, and milestone closure.

## File Map

- Create `docs/research/asgi-fastapi-boundary/README.md`: English decision guide.
- Create `docs/research/asgi-fastapi-boundary/README.ko.md`: aligned Korean guide.
- Create `docs/research/asgi-fastapi-boundary/images/architecture.svg` and
  `.png`: static ownership map.
- Create `docs/research/asgi-fastapi-boundary/images/sequence.svg` and `.png`:
  request, branch, disconnect, context-reset, and lifespan sequence.
- Modify `tests/test_documentation_contract.py`: lock the research and diagram
  contract before prose is written.
- Modify `README.md` and `README.ko.md`: expose the accepted 0.2.0 decision.
- Modify `WIP.md`: close the stale Issue #8 checkpoint and make Issue #9 current.
- Create `docs/superpowers/reviews/2026-07-16-issue-9-research-review.md`:
  record the final correctness, parity, and visual review.

### Task 1: Lock the documentation contract

- [x] Add tests that require reciprocal locale navigation, the three named
  alternatives, the seven ownership topics, upstream #21/#22 gates, the
  `POST /orders` recommendation, and all four diagram assets.
- [x] Require both root README locales and `WIP.md` to link the decision guide
  and identify Issue #9 as the 0.2.0 current target.
- [x] Run `uv run --locked pytest tests/test_documentation_contract.py -q` and
  verify failure is caused only by the absent Issue #9 artifacts.

### Task 2: Write the bilingual research decision

- [x] Write the English and Korean guides with aligned headings, facts, tables,
  links, limits, and recommendation.
- [x] Cite ASGI lifespan and HTTP/disconnect specifications, Starlette lifespan
  and request behavior, FastAPI lifespan, dependencies, and error handling, all
  retrieved on 2026-07-16.
- [x] Define the adoption gate as both upstream #21 decision acceptance and #22
  implementation availability through an exact stable release tag or commit.
- [x] State that disconnect is an input signal, not proof of automatic task
  cancellation, and define application-owned cancellation policy explicitly.

### Task 3: Create the architecture diagram

- [x] Draw a horizontal responsibility map for client/ASGI server, workshop
  FastAPI transport, request-context boundary, existing order backend, lifespan,
  and the gated future adapter.
- [x] Parse, render at scale 2, run connector/geometry/endpoint/mixed-corner
  audits, inspect the full-size PNG, and record concrete counts.

### Task 4: Create the sequence diagram

- [x] Draw startup, `POST /orders`, validation, context open/reset, backend
  processing, success/error/timeout/disconnect branches, and shutdown.
- [x] Use visible numbered messages, lifelines, activations, transparent branch
  frames, explicit per-color markers, and the approved muted palette.
- [x] Parse, render at scale 2, run common plus sequence-style audits, inspect
  the full-size PNG, and record concrete counts.

### Task 5: Update roadmap and verify

- [x] Update both root README locales and `WIP.md` without changing dependency
  or runtime instructions.
- [x] Run focused documentation tests, dependency tests, Ruff checks, the full
  deterministic test suite, actionlint, XML/render/audits, asset dimensions,
  locale parity checks, and `git diff --check`.
- [x] Write the six-lens research review with `P0=0/P1=0` or repair every
  blocking finding before continuing.
- [x] Mark this plan's completed steps, commit with Lore trailers, push the
  approved branch, and create the approved PR to `develop` with Issue #9's
  milestone, assignee, and labels.
- [x] Wait for exact-head hosted CI and current review/thread state, then stop
  for a fresh explicit merge approval.

## Self-Review

- Spec coverage: every Issue #9 acceptance criterion maps to Tasks 1-5.
- Scope control: no framework implementation, dependency, lockfile, release, or
  milestone side effect is authorized.
- Placeholder scan: no `TBD`, deferred implementation instruction, or unnamed
  validation step remains.
- Type consistency: this plan introduces documentation artifacts only; all
  referenced runtime types already exist in the integrated order example.
