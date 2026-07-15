# Issue #5 Design Review

## Scope

- Artifact: `docs/superpowers/specs/2026-07-16-issue-5-cached-product-catalog-design.md`
- Issue: <https://github.com/bluetape4k/bluetape-py-workshop/issues/5>
- Pinned dependency evidence:
  - `bluetape-cache/README.md`
  - `bluetape/cache/_core.py`
  - `bluetape/cache/_sync.py`
  - `bluetape/cache/_async.py`
- Review kind: Type A spec, six perspectives plus main-session integration

## Lane Execution

| Lens | Execution | Result |
|---|---|---|
| Performance | Native `code-reviewer` lane completed | No findings |
| Stability | Native `verifier` lane completed | P2=2, P3=1; all repaired |
| Security | Native lane produced no result within 15 seconds and was interrupted | Main-session fallback completed |
| Operator/Ops | Native lane produced no result within 15 seconds and was interrupted | Main-session fallback completed |
| Developer/API | Native lane produced no result within 15 seconds and was interrupted | Main-session fallback completed |
| User/caller | Native lane produced no result within 15 seconds and was interrupted | Main-session fallback completed |

The bounded fallback follows the active user instruction to reclaim delayed
subagent work immediately. No lane had write permission or ran a heavy command.

## Findings and Repairs

| Priority | Lens | Evidence | Repair | Final state |
|---|---|---|---|---|
| P2 | Stability | Async cancellation flow could imply that named cache tasks disappear before a slow loader reaches terminal cleanup | Split caller cancellation, held abandoned/inflight state, released cleanup, terminal gauges, and named-task removal into an explicit order | Resolved |
| P2 | Stability | Same-key coalescing and shared outcomes were described but had no concurrent acceptance proof | Added event-driven shared success/failure, one-loader, exact-counter, and one-waiter-cancelled scenarios | Resolved |
| P3 | Stability | Exact-expiry proof lacked the `expires_at - 1ns` control | Added pre-boundary hit and exact-boundary expiry requirements for sync and async | Resolved |
| P2 | Security | Non-blank-only validation left oversized, non-ASCII, grammar-invalid, and context-confused keys underspecified | Reused the workshop ASCII SKU grammar, 64-character bound, uppercase normalization, and tenant/auth/locale key warning | Resolved |
| P2 | Operator/Ops | Stats exposure did not explicitly separate lifetime counters from point-in-time gauges | Added lifetime/gauge semantics and documented that `clear()` does not reset counters | Resolved |
| P2 | Developer/API | The public immutable model example did not follow the repository's keyword-only construction convention | Added `kw_only=True` and prohibited private cache-field inspection | Resolved |
| P2 | User/caller | Deterministic JSON output was named but not shaped, and capacity/value-identity limits were easy to miss | Defined safe JSON fields, nonzero unexpected-failure behavior, entry-count sizing, and immutable value guidance | Resolved |

## Integration Review

- The chosen split service architecture uses the exact pinned sync and async
  cache types without adding a cache protocol or adapter.
- Cache, clock, loader, and event-loop ownership remain outside the service.
- Loader exceptions and `asyncio.CancelledError` remain unmodified.
- The deterministic scenario uses public APIs only and has no network, Docker,
  real-clock sleep, global state, or dependency change.
- Every issue acceptance criterion maps to a service, test, CLI, README, or
  diagram requirement.
- English/Korean README parity and mandatory Architecture/Sequence assets are
  explicit completion blockers.
- Compatibility aliases, publishing, release, Redis, and distributed cache
  behavior remain out of scope.

## Final Verdict

| Priority | Count |
|---|---:|
| P0 | 0 |
| P1 | 0 |
| P2 | 0 |
| P3 | 0 |

Verdict: **PASS**. The written design is ready for user review. Planning and
implementation remain blocked until the written-spec approval gate passes.
