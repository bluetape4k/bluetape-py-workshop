# WIP

Snapshot: 2026-07-15 KST
Scope: [`0.1.0`](https://github.com/bluetape4k/bluetape-py-workshop/milestone/1)
workshop foundation and runnable examples.

[English README](README.md) | [한국어 README](README.ko.md)

## Current Target

Issue [#4](https://github.com/bluetape4k/bluetape-py-workshop/issues/4):
build a framework-neutral catalog enrichment service that normalizes and
batches product identifiers, bounds provider concurrency, preserves input
order, and distinguishes required failures, optional warnings, timeouts, and
caller cancellation.

Active branch: `feat/issue-4-bounded-catalog-enrichment`
Base branch: `develop`
Stop boundary: report the exact PR head as merge-ready; merging requires a fresh
explicit approval and auto-merge is forbidden.

## Resume Checkpoint

- Branch/base head: `feat/issue-4-bounded-catalog-enrichment` /
  `b40df76bce2c13825c8247a050cfefdcd1e988e8`
- Pull request: not created; approved target is this branch into `develop`
- Workflow run: `20260715T130803Z-2df009df`
- Last completed gate: Type A classification and concrete execution plan
  approved in the active thread
- Last completed gate: isolated worktree created from current `origin/develop`;
  locked baseline passed with `57 passed`
- Last completed gate: written design review converged at P0=0/P1=0 and the
  converged written spec received explicit user approval
- Last completed gate: executable implementation plan review converged at
  P0=0/P1=0 through six separated main-session perspectives
- Current gate: explicit approval of the converged implementation plan
- Next action: after plan approval, commit the plan checkpoint, record workflow
  review evidence, load TDD/execution skills, and start Task 1 RED
- Runnable now: `uv run --locked python -m examples.order_intake`

Current artifacts: [issue #4](https://github.com/bluetape4k/bluetape-py-workshop/issues/4),
[written design](docs/superpowers/specs/2026-07-15-issue-4-bounded-catalog-enrichment-design.md),
[design review](docs/superpowers/reviews/2026-07-15-issue-4-design-review.md),
[implementation plan](docs/superpowers/plans/2026-07-15-issue-4-bounded-catalog-enrichment-plan.md),
[plan review](docs/superpowers/reviews/2026-07-15-issue-4-plan-review.md),
and the milestone dependency map below. Issue #2 closed through
[PR #12](https://github.com/bluetape4k/bluetape-py-workshop/pull/12), and issue
#3 closed through [PR #13](https://github.com/bluetape4k/bluetape-py-workshop/pull/13).

## Dependency Baseline

- Source repository: <https://github.com/bluetape4k/bluetape-py>
- Pinned source commit: `4b7458f22cea0a9e757b5fbf7f5ff4bc8c23cb9a`
  (`origin/develop`, post-release source-only baseline; not the `v0.1.0` tag)
- GitHub Release: [`v0.1.0`](https://github.com/bluetape4k/bluetape-py/releases/tag/v0.1.0)
- PyPI publication: HOLD; the focused distributions are not a supported PyPI
  install path and the GitHub Release is not the workshop installation source.
  Use root `uv sync` with the commit-pinned Git sources.
- Local path overrides are developer-local only and are not part of the
  committed reproducibility contract.
- Apache Fory and native compression providers remain outside the default
  installation lane.

## Milestone Dependency Map

```text
#2 repository bootstrap
  ├─> #3 validated order intake
  ├─> #4 bounded catalog enrichment
  ├─> #5 cached product catalog
  ├─> #6 bounded payload processing
  └─> #7 Redis Testcontainers workshop

#3 + #4 + #5 + #6
  └─> #8 integrated order backend
```

## Execution Queue

| Order | Issue | Outcome | Dependencies | State |
|---:|---|---|---|---|
| 1 | [#2](https://github.com/bluetape4k/bluetape-py-workshop/issues/2) | Reproducible `uv` foundation and CI | None | Completed |
| 2 | [#3](https://github.com/bluetape4k/bluetape-py-workshop/issues/3) | Validated order intake service | #2 | Completed |
| 3 | [#4](https://github.com/bluetape4k/bluetape-py-workshop/issues/4) | Bounded catalog enrichment service | #2 | Design in progress |
| 4 | [#5](https://github.com/bluetape4k/bluetape-py-workshop/issues/5) | Cached product catalog service | #2 | Pending |
| 5 | [#6](https://github.com/bluetape4k/bluetape-py-workshop/issues/6) | Bounded payload processing service | #2 | Pending |
| 6 | [#7](https://github.com/bluetape4k/bluetape-py-workshop/issues/7) | Redis-backed integration-test workshop | #2 | Pending |
| 7 | [#8](https://github.com/bluetape4k/bluetape-py-workshop/issues/8) | Integrated framework-neutral order backend | #3, #4, #5, #6 | Pending |

## Example Documentation Contract

Every runnable example must provide equivalent `README.md` and `README.ko.md`
files with these reader-facing sections:

1. exact reciprocal locale navigation: `English | [한국어](README.ko.md)` in
   English and `[English](README.md) | 한국어` in Korean;
2. business-shaped scenario and explicit non-goals;
3. source-backed architecture and ownership boundaries;
4. source-backed request or lifecycle sequence;
5. exact `bluetape-py` distributions and APIs used;
6. prerequisites, exact working directory, run command, expected observable
   result, targeted test, cleanup/stop command, and unsupported configuration;
7. failure, cancellation, troubleshooting, cleanup, and trust-boundary policies.

Each example receives architecture and sequence SVG/PNG assets only after the
implementing source exists. English-label assets are shared by both README
locales. Placeholder diagrams and visuals modeled from old rendered images are
not allowed.

## Working Rules

- Keep examples application-shaped, independently runnable, and independently
  testable.
- Put reusable helpers in `bluetape-py`; do not grow a workshop-owned utility
  layer.
- Use one implementation PR per issue with `develop` as the base branch.
- Keep one write lane because root documentation, the lockfile, and visual
  assets are shared surfaces.
- Run deterministic checks before Docker-backed checks; run every Docker-backed
  path sequentially.
- Update this file in every issue PR with the current branch, PR, validation,
  blocker, and next issue.
- After an approved merge, sync local `develop`, remove the merged worktree and
  local feature branch, and then start the next dependency-ready issue.

## Repository Validation Contract

```bash
uv --version  # must report 0.11.28
uv sync --locked --python 3.13.14
uv run --locked pytest tests/test_dependency_baseline.py -q
uv run --locked ruff format --check .
uv run --locked ruff check .
uv run --locked pytest
GOTOOLCHAIN=go1.26.1 go run github.com/rhysd/actionlint/cmd/actionlint@v1.7.12 \
  .github/workflows/ci.yml
git diff --check
```

CI must use `uv 0.11.28`, `uv-build 0.11.28`, the committed lockfile, and the
same Python line. The default lane installs the approved Testcontainers wrapper
baseline but must not contact Docker or start containers; Apache Fory and native
compression providers must remain absent.

Issue #3 adds these focused commands after implementation:

```bash
uv run --locked python -m examples.order_intake
uv run --locked pytest examples/order_intake/tests -q
```

The example must also pass the full repository validation contract above.

Issue #4 will add these focused commands after implementation:

```bash
uv run --locked python -m examples.catalog_enrichment
uv run --locked pytest examples/catalog_enrichment/tests -q
```

The async tests must use bounded event-driven synchronization rather than long
sleeps and must prove concurrency, timeout, cancellation, and task cleanup.

## Holds and Exclusions

- Issues #9 and #10 belong to milestone `0.2.0` and are outside this execution
  train.
- No ASGI/FastAPI adapter or production Redis cache provider is introduced in
  `0.1.0`.
- Tagging, package publishing, GitHub Release creation, and milestone closure
  require separate explicit authority.

## Decision Log

- 2026-07-15: use one commit-pinned Git source per focused distribution rather
  than the upstream meta package or committed local path overrides.
- 2026-07-15: keep `WIP.md` as the milestone execution board; detailed design,
  implementation, review, and lesson artifacts remain under `docs/`.
- 2026-07-15: create diagrams only from implemented behavior, starting with
  issue #3 rather than adding speculative assets during bootstrap.
- 2026-07-15: accept the root install cost of all ten milestone distributions
  so every issue detects source drift early; prove that Testcontainers import
  has no Docker runtime side effect.
- 2026-07-15: verify action pins against their canonical repositories; use the
  `setup-uv` v8.3.2 commit instead of the stale SHA found in an upstream workflow.
- 2026-07-15: implement issue #3 as a small importable application package with
  immutable contracts and an injected application-owned logger; reject both a
  single-file script and premature adapter layering.
- 2026-07-15: implement issue #4 as deterministic batch-provider jobs under one
  `map_bounded` budget; deduplicate provider work while restoring duplicate
  results in normalized input occurrence order.
