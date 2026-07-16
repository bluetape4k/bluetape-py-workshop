# WIP

Snapshot: 2026-07-17 KST
Scope: [`0.2.0`](https://github.com/bluetape4k/bluetape-py-workshop/milestone/2)
web and Redis expansion boundary.

[English README](README.md) | [한국어 README](README.ko.md)

## Current Target

Issue [#10](https://github.com/bluetape4k/bluetape-py-workshop/issues/10):
provide a realistic Redis load coordination example in which two application
instances keep separate local caches but reuse one owner-bound result through
the upstream public coordinator.

Active branch: `feat/issue-10-redis-load-coordination`
Base branch: `develop`
Pull request: pending creation after local Type A verification
Stop boundary: create the approved PR to `develop`, verify exact-head hosted
CI/review state, then stop for a fresh explicit merge approval. Auto-merge is
forbidden.

## Resume Checkpoint

- Branch/base head: `feat/issue-10-redis-load-coordination` /
  `836ff2090eb6a998b7247e9bf89ea3d77065c29d`
- Issue #9 completed through
  [PR #19](https://github.com/bluetape4k/bluetape-py-workshop/pull/19), merged as
  `836ff2090eb6a998b7247e9bf89ea3d77065c29d`
- Current topology: two caller-owned `AsyncRedisProvider` clients, two separate
  `AsyncTTLCache` instances, one versioned Redis coordination namespace, one
  strict `ProductSummaryCodec`, and one authoritative loader call
- Optional dependency boundary: default sync remains free of
  `bluetape-cache-redis` and `redis`; `.venv-redis` installs the
  `redis-coordination` extra from the exact pinned upstream commit
- Current artifacts: approved Type A spec/plan/risk records, implementation,
  aligned English/Korean example guides, and source-backed Architecture and
  Sequence Diagram SVG/PNG pairs
- Current validation: default `296 passed, 5 skipped, 1 deselected`; optional
  deterministic `36 passed, 1 deselected`; serial Docker Redis `1 passed`;
  Ruff, XML/render/audits, full-size PNG inspection, locale/link parity, and
  diff hygiene pass
- Issue [#20](https://github.com/bluetape4k/bluetape-py-workshop/issues/20)
  keeps near-cache invalidation `blocked:upstream`; no private RESP3 API,
  Pub/Sub, or polling workaround is included in #10
- Next action: commit the converged implementation review and lesson, rerun the
  exact head, then create the approved PR
- Runnable now: `uv run --locked python -m examples.order_intake`
- Runnable now: `uv run --locked python -m examples.catalog_enrichment`
- Runnable now: `uv run --locked python -m examples.cached_product_catalog`
- Runnable now: `uv run --locked python -m examples.bounded_payload_processing`
- Runnable now: `uv run --locked python -m examples.redis_test_server`
- Runnable now: `uv run --locked python -m examples.integrated_order_backend`
- Optional runnable: `UV_PROJECT_ENVIRONMENT=.venv-redis uv run --locked --extra redis-coordination python -m examples.redis_load_coordination`
- Integrated tests: `uv run --locked pytest examples/integrated_order_backend/tests -q`
- Deterministic Redis tests: `uv run --locked pytest -m "not testcontainers" examples/redis_test_server/tests -q`
- Serial Docker test: `uv run --locked pytest -m testcontainers examples/redis_test_server/tests/test_redis_integration.py -q`
- Focused default tests: `uv run --locked pytest examples/bounded_payload_processing/tests -q --ignore=examples/bounded_payload_processing/tests/test_fory_service.py`
- Optional setup: `UV_PROJECT_ENVIRONMENT=.venv-fory uv sync --locked --extra fory --python 3.13.14`
- Optional runnable: after activating `.venv-fory`, `python -m examples.bounded_payload_processing.fory_demo`
- Optional tests: after activating `.venv-fory`, `pytest examples/bounded_payload_processing/tests/test_fory_service.py -q`
- Redis optional setup: `UV_PROJECT_ENVIRONMENT=.venv-redis uv sync --locked --extra redis-coordination --python 3.13.14`
- Redis optional tests: `UV_PROJECT_ENVIRONMENT=.venv-redis uv run --locked --extra redis-coordination pytest -m "not testcontainers" examples/redis_load_coordination/tests -q`
- Redis serial Docker test: `UV_PROJECT_ENVIRONMENT=.venv-redis uv run --locked --extra redis-coordination pytest -m testcontainers examples/redis_load_coordination/tests/test_redis_integration.py -q`

Current artifacts: [issue #10](https://github.com/bluetape4k/bluetape-py-workshop/issues/10),
[implementation plan](docs/superpowers/plans/2026-07-17-issue-10-redis-load-coordination-plan.md),
[English example guide](examples/redis_load_coordination/README.md),
[Korean example guide](examples/redis_load_coordination/README.ko.md), and
[blocked invalidation follow-up #20](https://github.com/bluetape4k/bluetape-py-workshop/issues/20).

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

#8 + upstream bluetape-py #21/#22 evidence
  └─> #9 ASGI/FastAPI workshop boundary

#5 + upstream bluetape-py #54/#55
  └─> #10 Redis load coordination

#10 + upstream bluetape-py #56 + public redis-py RESP3 push
  └─> #20 Redis near-cache invalidation (blocked:upstream)
```

## Execution Queue

| Order | Issue | Outcome | Dependencies | State |
|---:|---|---|---|---|
| 1 | [#2](https://github.com/bluetape4k/bluetape-py-workshop/issues/2) | Reproducible `uv` foundation and CI | None | Completed |
| 2 | [#3](https://github.com/bluetape4k/bluetape-py-workshop/issues/3) | Validated order intake service | #2 | Completed |
| 3 | [#4](https://github.com/bluetape4k/bluetape-py-workshop/issues/4) | Bounded catalog enrichment service | #2 | Completed |
| 4 | [#5](https://github.com/bluetape4k/bluetape-py-workshop/issues/5) | Cached product catalog service | #2 | Completed |
| 5 | [#6](https://github.com/bluetape4k/bluetape-py-workshop/issues/6) | Bounded payload processing service | #2 | Completed |
| 6 | [#7](https://github.com/bluetape4k/bluetape-py-workshop/issues/7) | Redis-backed integration-test workshop | #2 | Completed |
| 7 | [#8](https://github.com/bluetape4k/bluetape-py-workshop/issues/8) | Integrated framework-neutral order backend | #3, #4, #5, #6 | Completed |
| 8 | [#9](https://github.com/bluetape4k/bluetape-py-workshop/issues/9) | ASGI/FastAPI workshop boundary decision | #8, upstream #21/#22 evidence | Completed |
| 9 | [#10](https://github.com/bluetape4k/bluetape-py-workshop/issues/10) | Redis load coordination | #5, upstream #54/#55 | In progress |
| 10 | [#20](https://github.com/bluetape4k/bluetape-py-workshop/issues/20) | Redis near-cache invalidation | #10, upstream #56, public RESP3 push | blocked:upstream |

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

Every example README pair must embed both architecture and sequence PNGs and
link their SVG sources. Missing either visual blocks example completion. Assets
are created only after the implementing source exists, and English-label assets
are shared by both README locales. Placeholder diagrams and visuals modeled
from old rendered images are not allowed.

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

Issue #4 adds these focused commands:

```bash
uv run --locked python -m examples.catalog_enrichment
uv run --locked pytest examples/catalog_enrichment/tests -q
```

The async tests must use bounded event-driven synchronization rather than long
sleeps and must prove concurrency, timeout, cancellation, and task cleanup.

Issue #5 adds these focused commands:

```bash
uv run --locked python -m examples.cached_product_catalog
uv run --locked pytest examples/cached_product_catalog/tests -q
```

The cache tests use a manual nanosecond clock and asyncio events. They prove
hit, miss, exact expiry, LRU eviction, loader recovery, shared async loading,
partial cancellation, and terminal cache-task cleanup without real sleeps.

Issue #6 adds separate default and optional commands:

```bash
uv run --locked python -m examples.bounded_payload_processing
uv run --locked pytest examples/bounded_payload_processing/tests -q \
  --ignore=examples/bounded_payload_processing/tests/test_fory_service.py

UV_PROJECT_ENVIRONMENT=.venv-fory uv sync --locked --extra fory --python 3.13.14
UV_PROJECT_ENVIRONMENT=.venv-fory uv run --locked --extra fory \
  python -m examples.bounded_payload_processing.fory_demo
UV_PROJECT_ENVIRONMENT=.venv-fory uv run --locked --extra fory \
  pytest examples/bounded_payload_processing/tests/test_fory_service.py -q
```

The JSON lane is untrusted and default-install safe. The Fory lane is
trusted-internal only, uses a fixed registered root type, and never participates
in default imports or automatic format selection.

Issue #7 adds a deterministic default lane and an explicitly selected serial
Docker lane:

```bash
uv run --locked pytest -m "not testcontainers"
uv run --locked pytest -m testcontainers examples/redis_test_server/tests/test_redis_integration.py -q
uv run --locked python -m examples.redis_test_server
```

The application owns one `RedisServer` context and uses only wrapper-provided
connection details. The bounded RESP teaching probe has fixed operations and
input/response limits. Integration tests prove success, application-body
failure cleanup, and fresh state without leaving labeled containers behind.

Issue #8 adds a deterministic composed application lane:

```bash
uv run --locked python -m examples.integrated_order_backend
uv run --locked pytest examples/integrated_order_backend/tests -q
```

The application validates the whole aggregate before external work, preserves
duplicate line occurrences, shares one cache across both example orders, fixes
the external payload boundary to untrusted JSON, observes late task failures,
and uses shielded finite request/close waits. Redis and trusted-internal Fory
remain separate optional examples.

Issue #10 adds an isolated optional Redis coordination lane:

```bash
UV_PROJECT_ENVIRONMENT=.venv-redis uv sync --locked --extra redis-coordination --python 3.13.14
UV_PROJECT_ENVIRONMENT=.venv-redis uv run --locked --extra redis-coordination python -m examples.redis_load_coordination
UV_PROJECT_ENVIRONMENT=.venv-redis uv run --locked --extra redis-coordination pytest -m "not testcontainers" examples/redis_load_coordination/tests -q
UV_PROJECT_ENVIRONMENT=.venv-redis uv run --locked --extra redis-coordination pytest -m testcontainers examples/redis_load_coordination/tests/test_redis_integration.py -q
```

The default environment remains free of `bluetape-cache-redis` and `redis`.
The optional example uses public upstream APIs only, runs deterministic tests
before its serial Docker lane, and never falls back to an uncoordinated load.

Issue #7 exact-head verification on Python 3.13.14, uv 0.11.28, and Docker
server 28.4.0:

- dependency boundary: `19 passed`;
- Redis deterministic lane: `55 passed, 1 deselected`;
- full deterministic repository lane: `221 passed, 1 skipped, 1 deselected`;
- focused serial Docker lane: `1 passed`;
- real CLI: documented compact success JSON;
- labeled Redis containers: empty before and after the focused test and CLI;
- Ruff format/lint, actionlint, `git diff --check`, and unchanged `uv.lock`: pass;
- Architecture and Sequence XML/render/audits/full-size inspection: pass.

Issue #8 converged local exact-head checkpoint:

- integrated example: `66 passed`;
- dependency baseline: `19 passed`;
- full deterministic repository: `287 passed, 1 skipped, 1 deselected`;
- deterministic CLI: exact five safe events, cache `hits=1`, `misses=3`,
  `loads=3`, with zero inflight/abandoned loads;
- Ruff lint/format, actionlint, authority-file, and `git diff --check`: pass;
- Architecture PNG: `3600x2100`, marker/card/geometry/endpoint/corner audits
  pass, full-size inspection pass;
- Sequence PNG: `3600x3000`, `18` visible numbered messages, sequence style,
  marker, geometry, endpoint, and corner audits pass, full-size inspection pass;
- six-lens implementation review: four P1 findings repaired, final
  `P0=0/P1=0`;
- exact-head post-commit rerun: pass;
- PR #18 created with milestone `0.1.0`, assignee `debop`, and Issue #8 labels;
- exact-head hosted CI: pass; GitHub mergeability/state: `MERGEABLE` / `CLEAN`;
- reviews, comments, and review threads: 0; hosted README and all four diagram
  assets: present;
- rebase merge SHA: `a6eae41ed7b946e6859d2cc3d1866a04ea539590`;
- post-merge local sync, focused/dependency/full deterministic validation, and
  owned worktree/local branch cleanup: pass.

Issue #9 local research checkpoint:

- three alternatives: Direct FastAPI, Raw ASGI, and future
  `bluetape-fastapi` compared from primary sources;
- recommendation: workshop-owned Direct FastAPI `POST /orders` transport around
  the existing `OrderBackendApplication`;
- adoption gate: upstream #21 accepted, #22 shipped, and exact stable release
  tag or commit pinned;
- Python implementation, dependency, lockfile, Docker, release, and milestone
  changes: N/A by research scope;
- bilingual decision guide and both required diagram pairs: present;
- documentation `10 passed`; full deterministic repository
  `290 passed, 1 skipped, 1 deselected`;
- Ruff lint/format, actionlint, XML/render/audits, locale/link parity, and
  `git diff --check`: pass;
- six-lens research review: `P0=0`, `P1=0`;
- PR #19 created with milestone `0.2.0`, assignee `debop`, and Issue #9 labels;
- hosted exact-head CI: pass; GitHub mergeability/state:
  `MERGEABLE` / `CLEAN`;
- reviews, comments, and review threads: 0; hosted English/Korean guides and all
  four diagram assets: present;
- rebase merge SHA: `836ff2090eb6a998b7247e9bf89ea3d77065c29d`;
- post-merge local sync and owned worktree/branch cleanup: pass.

Issue #10 current local checkpoint:

- exact upstream source: `bluetape-cache-redis==0.1.0` at
  `4b7458f22cea0a9e757b5fbf7f5ff4bc8c23cb9a`;
- default dependency boundary remains Redis-provider-free;
- deterministic owner/follower/local-hit behavior: one loader call, owner
  `LOADED`, follower `RESULT_REUSED`, then one Cache B local hit;
- default repository: `296 passed, 5 skipped, 1 deselected`;
- optional example: `36 passed, 1 deselected`;
- serial real Redis lane: `1 passed`;
- Architecture PNG: `3200x2000`, `10` cards, `4` markers, no crossings or
  intrusions, geometry/endpoint/mixed-corner audits and full-size inspection pass;
- Sequence PNG: `3600x3000`, `18` numbered messages, `5` markers, sequence
  style/geometry/endpoint/mixed-corner audits and full-size inspection pass;
- example README pair: reciprocal locale navigation, exact commands, outcomes,
  security, cleanup, troubleshooting, non-goals, and both diagram pairs present;
- root documentation and six-perspective implementation review: pass;
- durable Type A lesson: present; exact-head post-lesson rerun: pending.

## Holds and Exclusions

- Issue #9 is research-only; no ASGI/FastAPI adapter or FastAPI dependency is
  introduced.
- Issue #20 remains `blocked:upstream` on public near-cache invalidation and
  RESP3 push consumption; #10 contains no private API or workaround.
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
- 2026-07-16: implement issue #5 with separate sync/async services and
  caller-owned `TTLCache`/`AsyncTTLCache`; reject a workshop cache adapter so
  exact expiry, coalescing, cancellation, and public stats remain visible.
- 2026-07-16: implement issue #6 as separate JSON and Apache Fory services;
  accept small pipeline duplication so the untrusted/default and
  trusted-internal/optional boundaries remain obvious to readers.
- 2026-07-16: implement issue #7 with one application-owned `RedisServer`
  context and a bounded RESP teaching probe; exclude Docker tests by default
  and require explicit serial selection for real-container evidence.
- 2026-07-16: implement issue #8 by preserving the focused service contracts
  while one outer application owns request deadlines, terminal exception
  observation, and retryable finite shutdown; keep Redis and Fory as separate
  optional learning lanes.
- 2026-07-16: recommend Direct FastAPI for the first realistic HTTP order
  example while keeping transport policy workshop-owned; reject Raw ASGI as the
  first lesson and gate a reusable adapter on upstream #21, #22, and an exact
  stable release tag or commit.
- 2026-07-17: split ready load coordination from blocked near-cache
  invalidation; implement #10 with separate local caches/providers and the
  public upstream coordinator, while retaining invalidation as blocked #20.
