# Compose Focused Contracts Under One Lifecycle Owner

## Context

Issue #8 needed to turn four independently runnable examples into one realistic
order backend without copying their validation, enrichment, cache, or payload
policies into a workshop-owned framework.

## Reusable Lesson

Keep focused service contracts intact and compose them under one thin aggregate
service plus one outer application lifecycle:

1. validate the complete aggregate shape and every line before provider I/O;
2. let focused services retain field validation, bounded concurrency, required
   versus optional provider policy, cache behavior, and payload limits;
3. create shared resources once in the composition root and expose their
   operational state through the service instead of global variables;
4. let exactly one application boundary own overall deadlines, request-task
   observation, stop-accept behavior, and finite retryable shutdown; and
5. keep received metadata descriptive, never a selector for caches, providers,
   serializers, compressors, or classes.

This produces application-shaped teaching code while preserving the library
boundaries learners should reuse in a real adapter such as ASGI or a queue
consumer.

## Admission Race Guard

The important admission/shutdown race is solved by doing the state check,
sequence allocation, task creation, tracking registration, and done-callback
registration in one event-loop section with no `await`. Shutdown changes state
and snapshots tracked tasks in the same way. Future lifecycle changes must not
insert an await between admission and registration or accept work after the
close snapshot.

## Cancellation-Resistant Cleanup Guard

`asyncio.shield()` protects owned request and close tasks from caller
cancellation, but shield alone does not provide observation or a terminal
bound. Every owned task needs a done callback that retrieves its exception,
and shutdown needs separate finite grace and cancellation waits. If work still
resists cancellation, return a stable pending-count error and allow a later
close retry after the work terminates.

The surprising case is when every current `aclose()` waiter is cancelled while
the shared close task later fails. Without explicit close-task observation, the
event loop can report an un-retrieved exception and the application can become
permanently ambiguous. A regression test must cancel the waiter, release the
late failure, prove no loop-level exception report, and prove a subsequent
close attempt can complete.

## Documentation Guard

Architecture diagrams for composed examples must show adapter and resource
ownership as separate nodes. Sequence diagrams must show optional degradation,
invalid input before provider I/O, timeout/cancellation cleanup, and shutdown as
distinct branches. A source-backed diagram can still mislead if it collapses
the exact boundary the code is teaching.

## Evidence

- Integrated example: 66 passed.
- Dependency baseline: 19 passed.
- Full deterministic repository: 287 passed, 1 skipped, 1 deselected.
- Lifecycle tests cover the admission race, cancellation-resistant requests,
  cancelled close waiters, late failure observation, explicit pending count,
  and retry.
- CLI emits exactly five safe events and ends with zero inflight and abandoned
  cache loads.
- Both source-backed diagram pairs pass XML, render, geometry, endpoint,
  mixed-corner, and full-size visual inspection; Sequence also passes its style
  audit.
- Final six-lens implementation review converged from four P1 findings to
  P0=0/P1=0.
