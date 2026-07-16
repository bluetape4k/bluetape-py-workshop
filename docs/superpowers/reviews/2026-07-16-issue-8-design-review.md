# Issue #8 Design Review

## Scope

- Artifact:
  `docs/superpowers/specs/2026-07-16-issue-8-integrated-order-backend-design.md`
- Issue: <https://github.com/bluetape4k/bluetape-py-workshop/issues/8>
- Repository baseline: `develop@15bbe2efced086eb06ccf67aa03f4efb7633e7bb`
- Review kind: Type A Step 2-R spec review, six perspectives plus main-session
  integration

## Lane Execution

The stability verifier completed an independent bounded review. The remaining
native lanes did not produce usable results inside their bounded response
windows, so they were interrupted and reclaimed immediately under the active
user fallback rule. The main session then completed performance, security,
operator/Ops, developer/API, and user/caller as five separate checklist passes
before integrating the findings. No review lane had write permission or ran a
heavy command.

## Initial Findings and Repairs

| Priority | Lens | Evidence | Required repair | Resolution |
|---|---|---|---|---|
| P1 | Stability | Acceptance, task registration, and the shutdown snapshot had no shared atomic boundary. | Make admission/registration and stop/snapshot no-`await` critical sections on one bound event loop and test the boundary race. | Resolved. |
| P1 | Stability | Direct timeout/cancellation awaiting could exceed its deadline when provider code resisted cancellation. | Await the owned request through `shield`, cancel on timeout/caller cancellation, return promptly, and retain tracking until true terminal completion. | Resolved. |
| P1 | Stability | Idempotent close did not define concurrent callers, cancelled close callers, or retry ownership. | Add an explicit lifecycle state machine and one shielded shared close task, with retained failed state and retry. | Resolved. |
| P1 | Stability | Context-manager cleanup could mask an exception raised by the body. | Preserve the body exception as primary, attach only a redacted cleanup note, and raise cleanup failure directly only after a successful body. | Resolved. |
| P1 | Stability | A task that completed after its caller returned could produce an un-retrieved exception. | Observe every request/close task's terminal result, retain only fixed outcome state, and test late success/failure without loop exception noise. | Resolved. |
| P1 | Security | Aggregate identifier context was described before validation and as low-cardinality even though caller identifiers are unbounded operational values. | Establish aggregate context only after intake validation, prohibit message interpolation, classify identifiers as non-secret operational data, and document production privacy/length policy as an adapter concern. | Resolved. |
| P1 | Developer/API | The result claimed normalized header identifiers although the reused intake service preserves validated caller strings. | Preserve validated header values and reserve normalization for the SKU enrichment boundary. | Resolved. |
| P1 | Developer/API | Artifact construction could be read as serializing a result that already contains its artifact. | Define an explicit document allowlist and exclude the `artifact` field and result object from serialization. | Resolved. |
| P2 | Stability | Event-loop binding time and cross-loop rejection were unspecified. | Bind on first async use and reject cross-loop calls before task creation or state mutation. | Resolved. |
| P2 | Performance | Sequential cache-backed reads inside a provider batch trade throughput for one concurrency owner without naming the trade-off. | Keep the bounded design and document that it is a teaching choice, not production tuning guidance. | Resolved. |
| P2 | Operator/Ops | Lifecycle observability did not name stable event categories or the safe shutdown-failure payload. | Define fixed request/shutdown events, fixed error kinds, and numeric `pending_count` as the only shutdown diagnostic field. | Resolved. |
| P2 | Developer/API | Configuration validation ownership was assigned broadly to the composition root. | Require each owning service/application constructor to validate its own settings; composition only supplies validated dependencies. | Resolved. |
| P2 | User/caller | README requirements did not explicitly state caller-identifier privacy/retention limits or the sequential-read performance caveat. | Add both items to the bilingual learner guidance and keep production adapters out of scope. | Resolved. |

## Final Perspective Verdicts

| Lens | Final evidence | P0 | P1 | P2/P3 disposition |
|---|---|---:|---:|---|
| Performance | At most 100 lines, occurrence deduplication, fixed batch/concurrency/timeouts, no nested unbounded tasks, and bounded serialization constrain work. Sequential cache reads are an explicit teaching trade-off. | 0 | 0 | Initial P2 documented and accepted. |
| Stability | One-loop admission atomicity, shielded deadline handling, retained non-terminal tasks, observed terminal outcomes, shared close ownership, retry state, exception precedence, and deterministic race tests are explicit. | 0 | 0 | Initial P1/P2 findings repaired. |
| Security | Aggregate validation precedes provider/cache/payload work; the artifact has an explicit allowlist and untrusted JSON metadata; logs/CLI exclude payloads, provider text, recommendations, product names, and task representations. | 0 | 0 | Initial P1 repaired; production auth/privacy remains explicitly unsupported. |
| Operator/Ops | Fixed lifecycle events, safe error kinds, bounded shutdown, numeric pending diagnostics, retry semantics, cache counters, additive rollback, and no deployment/release side effects are defined. | 0 | 0 | Initial P2 repaired. |
| Developer/API | Exact aggregate/result ownership, existing public-service reuse, constructor-owned validation, no recursive artifact, no new dependency, and event-driven tests make the design implementable. | 0 | 0 | Initial P1/P2 findings repaired. |
| User/caller | The realistic two-order scenario, duplicate order lines, cache miss/hit, optional warnings, trust boundary, unsupported production concerns, bilingual parity, and mandatory Architecture/Sequence assets are explicit. | 0 | 0 | Initial P2 repaired. |

## Integration Review

- The aggregate remains example-local and application-shaped; it does not add a
  reusable library abstraction.
- Existing validation, enrichment, cache, and payload contracts remain the
  source of truth instead of being copied.
- The lifecycle boundary owns only request/close tasks and does not reach into
  cache loader internals.
- Stable occurrence ordering, duplicate SKUs, required/optional failures,
  cache recovery, payload limits, timeout/cancellation, and bounded shutdown all
  map to deterministic tests.
- Both README locales must directly embed Architecture and Sequence PNGs and
  link the source SVGs; diagram validation remains a completion blocker.
- PR creation, merge, release, and milestone side effects remain outside this
  design approval.

Final verdict: **PASS — P0=0, P1=0**. The written design is ready for user
approval before implementation planning begins.
