# WIP

Snapshot: 2026-07-15 KST  
Scope: [`0.1.0`](https://github.com/bluetape4k/bluetape-py-workshop/milestone/1)
workshop foundation and runnable examples.

[English README](README.md) | [한국어 README](README.ko.md)

## Current Target

Issue [#2](https://github.com/bluetape4k/bluetape-py-workshop/issues/2):
bootstrap the Python 3.13+ `uv` project, lockfile- and source-pinned validation, pinned
`bluetape-py` source baseline, CI, and bilingual setup documentation.

Active branch: `chore/issue-2-workshop-bootstrap`  
Base branch: `develop`  
Stop boundary: report the exact PR head as merge-ready; merging requires a fresh
explicit approval and auto-merge is forbidden.

## Resume Checkpoint

- Branch/last validated head: `chore/issue-2-workshop-bootstrap` /
  `dd449526ab207928d0ecf67e1b7a69d205f2b51d`
- Pull request: pending
- Last completed gate: six-perspective written-design review; `git diff --check`
  passed and the review converged at P0=0, P1=0 on 2026-07-15 KST
- Blocker: implementation-plan approval pending
- Next command: after approval, execute Task 1 with failing dependency tests
- Runnable now: none; the bootstrap commands below are planned until #2 lands

Current artifacts: [issue #2](https://github.com/bluetape4k/bluetape-py-workshop/issues/2),
[written design](docs/superpowers/specs/2026-07-15-issue-2-workshop-bootstrap-design.md),
[design review](docs/superpowers/reviews/2026-07-15-issue-2-design-review.md),
[implementation plan](docs/superpowers/plans/2026-07-15-issue-2-workshop-bootstrap-plan.md),
[plan review](docs/superpowers/reviews/2026-07-15-issue-2-plan-review.md),
pull request pending.

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
| 1 | [#2](https://github.com/bluetape4k/bluetape-py-workshop/issues/2) | Reproducible `uv` foundation and CI | None | In progress |
| 2 | [#3](https://github.com/bluetape4k/bluetape-py-workshop/issues/3) | Validated order intake service | #2 | Pending |
| 3 | [#4](https://github.com/bluetape4k/bluetape-py-workshop/issues/4) | Bounded catalog enrichment service | #2 | Pending |
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

## Issue #2 Planned Validation Contract

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
