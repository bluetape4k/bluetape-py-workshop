# Redis Load Coordination Workshop Lesson

## Context

Issue #10 originally combined two different capabilities: distributed cold-load
coordination, which exists at the pinned upstream commit, and near-cache
invalidation, whose public RESP3 push boundary is still blocked. The workshop
also had to keep Redis provider packages out of the default environment while
showing a realistic two-instance lifecycle.

## Decision

- Split invalidation into blocked issue #20 and make #10 only about the ready
  public load coordinator.
- Install `bluetape-cache-redis` only through the `redis-coordination` extra in
  `.venv-redis`; keep the example package initializer dependency-free.
- Give each catalog instance its own `AsyncTTLCache` and provider while sharing
  only a versioned Redis coordination namespace.
- Use the upstream coordinator and envelope contracts directly. Keep strict
  product JSON, redacted event recording, orchestration, CLI, and diagrams as
  example-local teaching code rather than a reusable workshop abstraction.

## Surprise and Failure

Event-controlled orchestration removed timing sleeps, but the first version
waited only for the expected teaching signals. If a provider failed before
emitting the owner-loader or follower-lease signal, the provider task completed
while the scenario waited forever. The focused RED test timed out and also
reported an unretrieved `RedisProviderError`.

The same optional-boundary review found a documentation mismatch: importing
Redis-facing names from the package initializer made default pytest collection
fail before `pytest.importorskip` could protect optional tests.

## Repair

Race every signal derived from a task against that task's terminal state. When
the task fails first, await it immediately so its original exception wins; the
outer `finally` then releases/cancels peer work and `AsyncExitStack` closes both
providers. Keep optional package initializers dependency-free and put
`pytest.importorskip` before any optional application import, including marked
integration tests because pytest imports a module before marker deselection.

## Outcome and Proof

- Default dependency contract: `22 passed`.
- Root documentation contract: `10 passed`.
- Default repository: `296 passed, 5 skipped, 1 deselected`.
- Optional deterministic example: `36 passed, 1 deselected`.
- Serial real Redis test: `1 passed`.
- CLI: one loader call, owner `loaded`, follower `result-reused`, and one
  follower local hit.
- Architecture: `3200x2000`, 10 cards, 4 markers, no crossings/intrusions.
- Sequence: `3600x3000`, 18 numbered messages, 5 markers, sequence-style PASS.
- Ruff format/lint, actionlint, XML/CairoSVG/audits, full-size PNG inspection,
  and diff hygiene pass.

## Review Misses

The initial deterministic happy path and cancellation test did not cover a task
that fails before its expected orchestration signal. The first spec also treated
`__init__.py` as a convenience export surface without reconciling that choice
with the optional dependency boundary.

## Future Guard

1. For every event used to order tasks, test the producer task failing before
   the event and race the event against that task.
2. Put optional-dependency guards before optional imports; pytest marker
   deselection alone is not an import guard.
3. Keep workshop package initializers dependency-free when an example has an
   opt-in extra.
4. Separate a ready public capability from a blocked adjacent feature instead
   of teaching private APIs or workaround architectures.
5. Keep bilingual README diagrams source-backed and verify rendered PNGs, not
   only SVG syntax.
