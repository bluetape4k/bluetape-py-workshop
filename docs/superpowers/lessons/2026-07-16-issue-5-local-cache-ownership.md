# Local Cache Ownership Is Part of the Example Contract

## Context

Issue #5 needed to teach `bluetape-cache` through a product-catalog service.
The tempting shortcut was a workshop cache interface that could make sync and
async examples look uniform. That would also hide the most important behavior:
who owns TTL, capacity, event-loop binding, loader tasks, and observability.

## Lesson

Keep the cache in the composition root and inject the exact library type into a
small application service. The service should own application policy—key
normalization and the domain-shaped method—but delegate cache behavior once.
This preserves the real API, lets callers use `set`, `invalidate`, and `clear`
through their owned cache, and prevents a global lifecycle from leaking into an
otherwise independent example.

Separate sync and async services are clearer than an adapter. Their loader
shapes, return contracts, statistics access, event-loop ownership, and
cancellation behavior are genuinely different. Sharing immutable models and
validation is enough; forcing the operations behind one protocol would teach
uniformity that the runtime does not have.

## Cancellation Guard

Caller cancellation and loader terminal cleanup are different moments. When
the last async waiter cancels, `CancelledError` may reach the caller before a
slow loader finishes its cancellation handler. Tests should therefore prove the
ordered states:

1. caller receives native cancellation;
2. held cleanup exposes one inflight abandoned load;
3. releasing cleanup lets the loader terminate;
4. inflight and abandoned gauges return to zero; and
5. no named cache-owned task remains.

Use events as the behavior signal and a short outer timeout only as a failure
guard. A sleep or immediate-zero assertion can pass without proving the owned
task lifecycle.

## Statistics Guard

`CacheStats` mixes lifetime counters and point-in-time gauges. Hits, misses,
loads, failures, evictions, and expirations accumulate; inflight, abandoned,
and superseded loads describe current state. Documentation and operations must
not imply that `clear()` resets the lifetime counters or that an entry-count
limit is a byte-size memory limit.

## Review Learning

The implementation review found that the async tests had correct event-driven
ordering but no bound on the event waits themselves. A broken future
implementation could therefore hang the suite instead of failing it. The guard
is now explicit: every externally awaited coordination event uses a one-second
`wait_for`, while `eventually_async` bounds the terminal state probe. Future
concurrency examples should establish this distinction in their first test,
not add it during final review.

The review also replaced exception list equality with explicit identity
assertions. When the contract says coalesced callers observe the same failure
object, the test should say `is`, even if the current exception type happens to
make equality equivalent.

## Evidence

- 28 service tests passed, including three sequential stability runs.
- 31 focused example tests and 123 repository tests passed.
- Ruff, actionlint, diff checks, and dependency-file SHA parity passed.
- Architecture and Sequence PNG/SVG pairs passed their complete audit ladders
  and full-size inspection.
- Final implementation review converged at P0=0/P1=0.
