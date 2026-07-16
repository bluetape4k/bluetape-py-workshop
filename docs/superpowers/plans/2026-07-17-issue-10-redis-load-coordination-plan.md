# Redis Load Coordination Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `executing-plans` to
> implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for
> tracking. This run is main-session single-writer because the lockfile, root
> docs, and diagram assets are shared surfaces.

**Goal:** Add an optional, independently runnable two-instance Redis load
coordination example that proves one cold load, remote result reuse, local-hit
Redis bypass, bounded failure behavior, and cleanup without implementing
near-cache invalidation.

**Architecture:** Two `RedisCatalogInstance` values own separate
`AsyncTTLCache` objects and borrow separate `AsyncRedisProvider` resources while
sharing one versioned namespace and strict `ProductSummaryCodec`. The
application owns provider and Docker lifecycles; the upstream
`AsyncRedisLoadCoordinator` owns the distributed lease/snapshot/publish state
machine.

**Tech Stack:** Python 3.13.14, uv 0.11.28, asyncio,
`bluetape-cache-redis==0.1.0`, `bluetape-cache`, `bluetape-serde`,
`bluetape-testcontainers`, redis-py 8.0.1, pytest 8.4, Ruff 0.12,
SVG/CairoSVG.

---

## Execution Contract

- Repository: `bluetape4k/bluetape-py-workshop`
- Base: `develop@836ff2090eb6a998b7247e9bf89ea3d77065c29d`
- Head: `feat/issue-10-redis-load-coordination`
- Worktree: `.worktrees/issue-10-redis-load-coordination`
- Issue: <https://github.com/bluetape4k/bluetape-py-workshop/issues/10>
- Approved spec:
  `docs/superpowers/specs/2026-07-17-issue-10-redis-load-coordination-design.md`
- Spec review:
  `docs/superpowers/reviews/2026-07-17-issue-10-redis-load-coordination-design-review.md`
- Authorized side effects: edit Issue #10, remove its `blocked:upstream` label,
  create one blocked near-cache follow-up issue in milestone `0.2.0`, local
  edits/Lore commits, push this exact head, and create a PR from this branch to
  `develop` in `bluetape4k/bluetape-py-workshop`.
- Not authorized: merge/auto-merge, release, tag, publish, workflow dispatch,
  milestone closure, remote branch deletion, or production Redis mutation.
- Stop boundary: exact-head PR, hosted checks, current reviews/threads, diagrams,
  and Type A DoD are merge-ready; then wait for fresh merge approval.

## File Map

| Path | Responsibility |
|---|---|
| `pyproject.toml`, `uv.lock` | Exact optional Redis distribution and source; default isolation |
| `tests/test_dependency_baseline.py` | Optional-extra/source/lock/default-install contract |
| `examples/redis_load_coordination/codec.py` | Strict untrusted JSON `ProductSummary` payload codec |
| `examples/redis_load_coordination/observer.py` | Redacted immutable coordination event snapshots |
| `examples/redis_load_coordination/service.py` | One local cache plus upstream Redis coordinator |
| `examples/redis_load_coordination/application.py` | Two-instance scenario and provider lifecycle |
| `examples/redis_load_coordination/__main__.py` | Disposable RedisServer CLI |
| `examples/redis_load_coordination/tests/` | Codec, fake-provider, scenario, Docker, docs proofs |
| `examples/redis_load_coordination/README.md` | English learner guide |
| `examples/redis_load_coordination/README.ko.md` | Meaning-equivalent Korean learner guide |
| `examples/redis_load_coordination/docs/images/*` | Architecture and Sequence SVG/PNG assets |
| `README.md`, `README.ko.md`, `WIP.md` | Workshop registration, commands, live checkpoint |
| `tests/test_documentation_contract.py` | Root registration and mandatory visual contract |
| `docs/superpowers/reviews/*issue-10*` | Spec, plan, and implementation convergence |
| `docs/superpowers/risks/*issue-10*` | Triggered Redis/async/Testcontainers risk controls |
| `docs/superpowers/lessons/*issue-10*` | Required Type A reusable lesson |

## Acceptance Traceability

| Acceptance criterion | Task | Fresh proof |
|---|---:|---|
| Ready and blocked issue scopes are separated | 1 | live issue bodies, labels, milestone, assignee |
| Redis package is optional at the exact commit | 2 | dependency RED/GREEN, lock readback, default and extra sync |
| Strict result envelope payload | 3 | success/wrong type/shape/metadata/size tests |
| Two local caches share one distributed load | 4-5 | fake provider and real Redis assertions |
| Timeout/failure/cancellation/stale/lease/cleanup | 4 | deterministic event-driven tests |
| Providers and container close on every path | 5 | context/body failure/cancellation assertions |
| Bilingual guides and source-backed diagrams | 6 | locale/asset tests, XML/audits/full-size inspection |
| Root discovery and reproducible commands | 7 | root docs and documentation contract tests |
| Type A delivery convergence | 8 | validation ladder, reviews, lesson, exact PR head/CI |

## Task 1: Separate the Ready and Blocked GitHub Scopes

**Complexity:** Low. **Depends on:** approved plan. **Write scope:** GitHub issue
metadata only. **Rollback:** restore Issue #10 body/label and close the new issue
only if live readback differs from the approved split.

- [ ] Edit Issue #10 in English to cover only cross-process load coordination,
  record closed upstream #54/#55 and exact commit `4b7458f...`, exclude
  invalidation, and remove `blocked:upstream`.
- [ ] Create `feat: add Redis near-cache invalidation example` in milestone
  `0.2.0`, assigned to `debop`, with labels `enhancement`, `type:feature`,
  `area:cache`, `area:integration`, `blocked:upstream`.
- [ ] Link upstream #56 and redis/redis-py#3916; require documented public sync
  and async invalidation consumption before implementation; reject private APIs,
  Pub/Sub, polling, and workshop-owned invalidation.
- [ ] Read both issues back with `gh issue view --json` and record exact URLs,
  labels, milestone, and assignee in `WIP.md`.

## Task 2: Add the Exact Optional Redis Dependency

**Complexity:** Medium. **Depends on:** Task 1. **Pattern:**
`bluetape-py-patterns`; packaging TDD. **Rollback:** revert only metadata/lock
and keep Issue #10 open.

- [ ] RED: extend `tests/test_dependency_baseline.py` to require:

```python
OPTIONAL_PACKAGES = {
    "bluetape-cache-redis": ("packages/bluetape-cache-redis", "bluetape.cache.redis"),
}
assert optional_dependencies["redis-coordination"] == [
    "bluetape-cache-redis==0.1.0"
]
assert importlib.util.find_spec("bluetape.cache.redis") is None
```

Run `uv run --locked pytest tests/test_dependency_baseline.py -q`; expect the
new assertions to fail because the extra/source/lock entry is absent.

- [ ] GREEN: add the optional dependency and matching `[tool.uv.sources]` entry
  using the existing Git URL, exact revision, and
  `packages/bluetape-cache-redis`; run `uv lock --python 3.13.14`.
- [ ] Prove default isolation with a fresh default sync and dependency test.
- [ ] Prove the extra in `.venv-redis`:

```bash
UV_PROJECT_ENVIRONMENT=.venv-redis uv sync --locked \
  --extra redis-coordination --python 3.13.14
UV_PROJECT_ENVIRONMENT=.venv-redis uv run --locked \
  --extra redis-coordination python -c \
  'from bluetape.cache.redis import AsyncRedisLoadCoordinator; print(AsyncRedisLoadCoordinator.__name__)'
```

- [ ] Run Ruff and `git diff --check`; commit the dependency boundary with Lore
  trailers before feature code.

## Task 3: Implement the Strict Payload Codec

**Complexity:** Medium. **Depends on:** Task 2. **Write scope:** codec, exports,
and codec tests only. **Pattern:** strict TDD.

- [ ] RED: create optional test module guarded by
  `pytest.importorskip("bluetape.cache.redis")`. Require an exact
  `ProductSummary` round trip and reject non-exact input, wrong JSON shape,
  unknown/missing fields, bool-as-int price, negative price, mismatched
  format/version/content-type/trust profile, oversized input, and invalid UTF-8.
- [ ] Observe the focused test fail because `ProductSummaryCodec` is absent.
- [ ] GREEN: implement `PayloadCodec[ProductSummary]` with exact metadata:

```python
PRODUCT_METADATA = PayloadMetadata(
    format="json",
    version=1,
    content_type="application/json",
    trust_profile=TrustProfile.UNTRUSTED,
)
```

Encode only `product_id`, `name`, and `price_cents`; decode through public
`json_deserialize`, validate the exact dictionary contract, and reconstruct the
existing immutable `ProductSummary`.
- [ ] Run focused RED/GREEN, Ruff, and diff check; commit.

## Task 4: Compose One Instance and Prove Distributed Failure Contracts

**Complexity:** High. **Depends on:** Task 3. **Write scope:** observer/service,
fake support, and deterministic tests. **Pattern:** async TDD. **Rollback:**
revert this task's commit while retaining its failing tests.

- [ ] RED: require `CoordinationEventRecorder.snapshot()` to return a tuple of
  upstream `RedisCoordinationEvent` values without raw operational data.
- [ ] RED: require `RedisCatalogInstance` to validate an exact non-blank ASCII
  SKU of at most 64 characters before any provider call, then delegate to one
  `AsyncRedisLoadCoordinator` with the configured local TTL.
- [ ] Build a test-only `FakeAsyncRedisProvider` subclass with a shared
  event-locked in-memory marker/result backend and finite `RedisCommandPolicy`.
  It implements only the public provider operations used by the coordinator and
  records acquire/snapshot/publish/cleanup calls.
- [ ] RED/GREEN behaviors, one test at a time:
  - two instances, one loader call, `LOADED` plus `RESULT_REUSED`;
  - later local hit adds no provider call/event;
  - attempts/polls/deadline timeout preserves stable code;
  - provider error identity and stable code propagate;
  - loader error identity survives one marker cleanup;
  - caller cancellation survives one shielded cleanup with no active flight;
  - mismatched stale envelope is not returned and a later matching result is;
  - failed publish reports `LEASE_LOST`, returns only the owner's value, and
    does not create a reusable remote result;
  - cleanup failure adds only the upstream static note.
- [ ] Use `asyncio.Event`, short option budgets, and outer one-second guards;
  do not use long sleeps or monkeypatch private implementation state.
- [ ] Run focused tests, Ruff, diff check, and commit.

## Task 5: Own the Two-Instance and Docker Lifecycles

**Complexity:** High. **Depends on:** Task 4. **Write scope:** application, CLI,
and application/Docker tests. **Hazard:** Testcontainers runs serially.

- [ ] RED: define immutable `ScenarioResult` with owner/follower/local values,
  loader call count, per-instance event tuples, and local cache statistics.
- [ ] RED: `run_scenario(redis_url, loader=None, provider_factory=None)` must
  create two providers with
  `socket_connect_timeout=0.2`, `socket_timeout=0.3`, and
  `retry_on_timeout=False`; create two caches and one shared namespace; close
  both providers for success, loader failure, provider failure, and
  cancellation. The default factory is `AsyncRedisProvider.from_url`; injected
  factories must return exact provider subclasses so tests can prove closure.
- [ ] GREEN: use `AsyncExitStack` for reverse-order provider closure. The
  default event-controlled loader admits instance B after A begins loading,
  releases A, then verifies B's later local hit.
- [ ] RED/GREEN CLI: `python -m examples.redis_load_coordination` owns one
  `RedisServer` context, runs the async scenario, prints fixed JSON-safe summary
  fields only, and exits with no container.
- [ ] RED/GREEN serial Docker test with real `RedisServer` proves one loader,
  result reuse, local hit, application-body failure cleanup, a fresh server has
  no prior keys, provider closure, and `server.running is False`.
- [ ] Run deterministic optional tests first, then exactly one serial Docker
  command. Investigate any retry-only pass; commit only after both are green.

## Task 6: Add Bilingual Learner Guides and Diagrams

**Complexity:** High. **Depends on:** implemented Tasks 3-5. **Skills:**
`bluetape-writer`, `bluetape-diagram`. **Write scope:** example README pair,
diagram assets, and documentation tests.

- [ ] RED: require reciprocal locale navigation; Scenario, Architecture,
  Sequence Diagram, ownership, APIs, optional setup, working directory, CLI,
  deterministic tests, serial Docker test, expected result, cleanup, failure
  matrix, troubleshooting, security, rollback, and non-goals in both locales.
- [ ] RED: require direct PNG embeds plus SVG links for `architecture` and
  `sequence` in both locales.
- [ ] Write Korean and English guides from the implemented source. Keep exact
  commands/identifiers/numbers/links aligned and link Issue #10, the new blocked
  issue, upstream #54/#55/#56, and redis-py#3916.
- [ ] Create `architecture.svg` from source ownership: caller → instance A/B →
  separate local caches → upstream coordinators → separate providers → shared
  Redis, plus authoritative loader and redacted observers.
- [ ] Render/inspect architecture PNG before starting sequence.
- [ ] Create `sequence.svg` with visible numbered rows for cold owner, follower
  poll/reuse, local hit, and explicit failure/cancellation/lease-loss branches.
- [ ] Render/inspect sequence PNG. Run XML, CairoSVG scale 2, connector,
  geometry, endpoint, mixed-corner, architecture/sequence-specific audits, and
  open both final PNGs at full size.
- [ ] Run example documentation tests and diff check; commit.

## Task 7: Register the Example and Live Checkpoint

**Complexity:** Medium. **Depends on:** Task 6. **Write scope:** root README pair,
WIP, root documentation tests.

- [ ] RED: extend root tests to require example links, optional setup/run/test
  commands, exact upstream package/commit, the split blocked issue, and current
  branch/stop boundary.
- [ ] Update `README.md` and `README.ko.md` with aligned learning-path entry,
  Architecture/Sequence references through the example guide, optional Redis
  commands, failure boundary, and no invalidation claim.
- [ ] Update `WIP.md` snapshot/current target/dependency map/queue/artifacts/
  commands/validation from merged Issue #9 to active Issue #10 and the blocked
  follow-up. Do not invent a PR number before creation.
- [ ] Run root documentation and dependency tests, Ruff, diff check; commit.

## Task 8: Converge Type A Proof and Deliver the PR

**Complexity:** High. **Depends on:** Tasks 1-7. **Stop:** fresh merge approval.

- [ ] Run deterministic validation in the default environment:

```bash
uv --version
uv sync --locked --python 3.13.14
uv run --locked pytest tests/test_dependency_baseline.py -q
uv run --locked pytest tests/test_documentation_contract.py -q
uv run --locked ruff format --check .
uv run --locked ruff check .
uv run --locked pytest
```

- [ ] Run optional validation:

```bash
UV_PROJECT_ENVIRONMENT=.venv-redis uv sync --locked \
  --extra redis-coordination --python 3.13.14
UV_PROJECT_ENVIRONMENT=.venv-redis uv run --locked \
  --extra redis-coordination pytest \
  examples/redis_load_coordination/tests -q \
  -m "not testcontainers"
UV_PROJECT_ENVIRONMENT=.venv-redis uv run --locked \
  --extra redis-coordination python -m examples.redis_load_coordination
UV_PROJECT_ENVIRONMENT=.venv-redis uv run --locked \
  --extra redis-coordination pytest -m testcontainers \
  examples/redis_load_coordination/tests/test_redis_integration.py -q
```

- [ ] Run actionlint, every diagram command/audit, link/locale parity, lock
  readback, default-provider absence, `git diff --check`, and status inspection.
- [ ] Complete performance/stability scan and six-perspective implementation
  review in the main session; fix and rerun until `P0=0, P1=0`.
- [ ] Write and commit the Type A lesson with context, decision, surprise,
  outcome, commands, review misses, and future guard.
- [ ] Verify CG-01 through CG-10 and PY-01 through PY-07; push exact local head,
  read back the remote SHA, and create the authorized PR to `develop`.
- [ ] Assign `debop`, mirror Issue #10 milestone/labels, use an English body
  ending with `## DoD Status`, and verify live metadata/body/head.
- [ ] Wait for exact-head CI, reread reviews and unresolved threads, rerun final
  review on the PR diff, and update DoD evidence.
- [ ] Report merge readiness with exact PR/head and stop at CG-16. Do not enable
  auto-merge or merge from the earlier plan approval.

## Plan Self-Review

- Every spec acceptance item maps to Tasks 1-8 and a fresh command or live
  readback.
- Dependency and lock changes precede optional imports; code precedes diagrams;
  deterministic tests precede Docker; local proof precedes push/PR.
- No task depends on a later artifact. No production helper is introduced.
- Success, validation, timeout, provider/loader/envelope failure, stale result,
  cancellation, lease loss, cleanup, provider lifecycle, container lifecycle,
  and default/optional packaging are all named.
- Rollback/rerun points exist for GitHub scope, dependency, implementation,
  visual, and delivery boundaries.
- Placeholder scan: no `TBD`, `TODO`, or deferred implementation instruction.
