# Issue #8 Implementation Plan Review

## Scope

- Plan:
  `docs/superpowers/plans/2026-07-16-issue-8-integrated-order-backend-plan.md`
- Approved spec:
  `docs/superpowers/specs/2026-07-16-issue-8-integrated-order-backend-design.md`
- Risk prediction:
  `docs/superpowers/risks/2026-07-16-issue-8-integrated-order-backend-risk.md`
- Repository baseline: `develop@15bbe2efced086eb06ccf67aa03f4efb7633e7bb`
- Review kind: Type A Step 3-R, six perspectives plus main-session integration

## Lane Execution

Three bounded read-only native lanes were assigned performance, stability, and
security. They did not produce usable output in the bounded response window and
were interrupted immediately under the active user fallback rule. Because the
same agents had already shown repeated latency during the design review, the
main session reclaimed all six lenses as separate checklist passes instead of
starting another delayed wave. No child had write permission or ran a heavy
command.

## Findings and Repairs

| Priority | Lens | Finding | Required plan edit | Resolution |
|---|---|---|---|---|
| P1 | Stability | Application telemetry called the caller-owned logger directly before/inside lifecycle transitions; a raising handler could detach a request or leave close at `CLOSING`. | Add a narrow best-effort lifecycle emitter, prove handler failure cannot change outcomes, and move abnormal close-task completion to `CLOSE_FAILED`. | Resolved in Task 4 and the risk record. |
| P1 | Stability | Cancellation-resistant fake tests covered retained work, but the plan did not explicitly prove cooperative cleanup of a real `AsyncTTLCache` loader after the outer request timeout. | Add an event-gated real-service timeout test requiring loader `finally`, zero inflight/abandoned gauges, and no named cache task. | Resolved in Task 4. |
| P1 | Stability | The first cancellation-resistant test double suppressed only one cancellation, so shutdown's second cancel could make the pending-error/retry assertion pass for the wrong reason. | Loop on the release event and suppress every cancellation until explicit release. | Resolved in Task 4. |
| P1 | Developer/API | The composition root returned only the application while public cache stats were defined only on the service, leaving the CLI dependent on a private object graph. | Add exact `OrderBackendApplication.cache_stats()` delegation and prove root sharing through that public method. | Resolved in Tasks 4-5. |
| P1 | Developer/API | Initial method skeletons and validation ownership did not fully define implementable constructor seams for real services and event-driven doubles. | Add complete constructor validation, exact service/application/root signatures, method-callable test seams, and constructor-owned settings. | Resolved in Tasks 3-5. |
| P2 | Stability | An unexpected close-task failure/cancellation could retain `CLOSING` even after the shared task became terminal. | Make the close observer converge abnormal terminal state to `CLOSE_FAILED` for retry. | Resolved in Task 4. |
| P2 | Performance | The plan ran a performance/stability scan but did not explicitly dispose of benchmark execution. | Record benchmark N/A from the fixed 100-line bound, no performance claim, and deliberate sequential cache-read teaching trade-off. | Resolved in Task 8. |
| P2 | Operator/Ops | Lifecycle event categories were named but safe logging failure ownership and the exact numeric shutdown diagnostic were not tied to tests/docs. | Fix event names/error fields, best-effort ownership, failing-handler proof, and README guidance. | Resolved in Tasks 4 and 6. |
| P2 | User/caller | The five CLI events were ordered but the complete `order_processed` field set and deterministic totals/warnings were not exact. | Pin prices, recommendations, totals, warning counts, artifact summary keys, and cache counters. | Resolved in Task 5. |
| P2 | Security | Caller identifiers remain validated-but-unbounded operational context in the reused intake service. | Keep them out of event messages/metrics, document them as non-secret structured data, and assign production bounds/privacy/auth/retention to an adapter. | Accepted with explicit Task 3 redaction tests and Task 6 documentation; changing the focused intake contract is out of scope. |

## Step 3-R Required Checks

| Check | Evidence | Result |
|---|---|---|
| Spec and DoD coverage | Acceptance traceability maps every issue criterion to Tasks 1-8 and fresh proof. | PASS |
| Implementable order | Models/errors -> cache adapter -> service -> application -> root/CLI -> example docs/diagrams -> root docs -> final evidence. | PASS |
| No later-artifact dependency | Each task creates the contracts consumed by the next; diagrams intentionally follow implemented source. | PASS |
| Test breadth | Success, invalid shape/line, required/optional failure, cache recovery, payload limits, timeout, caller cancellation, races, concurrent/cancelled close, retry, cross-loop use, CLI, and docs are named. | PASS |
| Concrete commands | Every task has focused RED/GREEN commands; Task 8 has locked full validation, actionlint, diagram, scope, and CLI checks. | PASS |
| README locales and visuals | Both example/root locales plus direct Architecture/Sequence PNG embeds and SVG links are mandatory. | PASS |
| Contributor artifacts | English issue/PR text, WIP, review, lesson, and final DoD are assigned; Kotlin KDoc/changelog/release notes are not applicable. | PASS |
| Module/CI/catalog hazards | No new package distribution, dependency, lockfile, workflow, module registration, BOM, coverage aggregation, Nightly, or publish surface; byte-identity checks enforce N/A. | PASS |
| Framework/ORM hazards | No Spring Boot, Exposed, DB, schema, stream, JDK preview, or backend-capability dependency. | PASS |
| Coroutine boundaries | Shielded request/close waits, finite grace/cancel, late exception observation, cooperative cache cleanup, and caller cancellation propagation have deterministic tests. | PASS |
| Performance/stability | 100-line cap, distinct-SKU work, one outer concurrency owner, fixed task cardinality, finite waits, cache gauges, no blocking/sleep, and benchmark N/A evidence are assigned. | PASS |
| Reuse/duplication | Existing intake, enrichment, cache, payload, logging context, and model contracts are reused; only aggregate/lifecycle/adapter composition is local. | PASS |
| Rollback/compatibility | Additive removal path is exact; existing examples, pinned source, lockfile, workflows, persistence, and release state remain unchanged. | PASS |

## Final Perspective Verdicts

| Lens | Final evidence | P0 | P1 | P2/P3 disposition |
|---|---|---:|---:|---|
| Performance | Tasks cap aggregate size, deduplicate provider work, keep one concurrency owner, bound cache/payload/task counts, scan the final diff, and record benchmark N/A without a performance claim. | 0 | 0 | Initial P2 repaired. |
| Stability | Ordering covers admission atomicity, shielded deadlines, real cache cleanup, terminal exception observation, shared/cancelled close callers, abnormal close state, retry, context precedence, loop binding, and failing logging handlers. | 0 | 0 | Initial P1/P2 findings repaired. |
| Security | Every line validates before I/O, errors/events are fixed and redacted, the artifact has an allowlist and untrusted JSON profile, payload limits remain active, and Fory stays separate. | 0 | 0 | Identifier-policy P2 explicitly accepted within scope. |
| Operator/Ops | Stable lifecycle events, best-effort telemetry ownership, numeric pending diagnostics, cache counters, WIP/rollback, exact-head PR/CI evidence, and merge hold are assigned. | 0 | 0 | Initial P2 repaired. |
| Developer/API | Exact paths, signatures, ownership, test seams, RED/GREEN commands, dependency order, public cache stats, no private cache inspection, and unchanged authority files are implementable. | 0 | 0 | Initial P1 findings repaired. |
| User/caller | Realistic duplicate-line orders, deterministic totals/warnings/cache behavior, bilingual guidance, troubleshooting/non-goals, identifier obligations, Fory boundary, and mandatory source-backed diagrams are exact. | 0 | 0 | Initial P2 repaired. |

## Integration Verdict

- The plan follows the approved architecture without introducing a framework,
  reusable library port, dependency, persistence layer, or production adapter.
- Concurrency/cache/trust risks have signals, failing-first tests, repair points,
  and rollback in the committed risk prediction.
- PR creation authority is scoped to the named repository/base/head only after
  plan approval; merge and every release side effect remain separate gates.
- Placeholder scan, type/signature consistency, task ordering, acceptance
  traceability, and `git diff --check` pass.

Final verdict: **PASS — P0=0, P1=0**. The plan is ready for user approval and
then task-by-task TDD execution.
