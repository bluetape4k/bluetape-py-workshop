# Issue #8 Integrated Order Backend Risk Prediction

## Scope

- Issue: <https://github.com/bluetape4k/bluetape-py-workshop/issues/8>
- Spec:
  `docs/superpowers/specs/2026-07-16-issue-8-integrated-order-backend-design.md`
- Plan:
  `docs/superpowers/plans/2026-07-16-issue-8-integrated-order-backend-plan.md`
- Trigger: async lifecycle, cancellation, shared cache, provider trust, and
  bounded serialization make Step 3-P mandatory.

## Predicted Risks

| Priority | Risk and signal | Prevention / acceptance proof | Rollback or rerun point |
|---|---|---|---|
| P1 | A request passes the accepting check but registers after shutdown snapshots; signal is `aclose()` returning while a gated processor remains active. | Keep admission check, task creation, and registration in one no-`await` section; stop/snapshot uses the same single-loop atomicity; Task 4 event test proves close sees admitted work. | Revert Task 4 application commit, retain the race test, and redesign before Task 5. |
| P1 | `wait_for`-style cancellation waits forever when provider code suppresses cancellation; signal is process/close exceeding its outer one-second test guard. | Await shielded request tasks, cancel on timeout/caller cancellation without an unbounded await, use finite `asyncio.wait` grace/cancel phases, and retain non-terminal references. | Return to Task 4, release every test gate, inspect all named request/close tasks, then rerun lifecycle tests from the start. |
| P1 | Late task failure becomes `Task exception was never retrieved`; signal is a captured loop exception-handler event after timeout, caller cancellation, or cancelled close waiter. | Every request and close task has a done observer that retrieves non-cancelled exceptions; tests force late failure after caller return. | Block docs/PR, repair Task 4 observation, rerun lifecycle and full example tests. |
| P1 | A caller-owned logging handler raises during admission or close and detaches work or leaves lifecycle state at `CLOSING`; signal is a request/close outcome changing under a failing handler. | Application lifecycle telemetry uses a narrow best-effort emitter, close-task abnormal completion moves to `CLOSE_FAILED`, and event-driven tests prove cleanup/retry is unchanged. | Return to Task 4, retain the failing-handler test, and rerun every lifecycle path before CLI/docs. |
| P1 | Validation performs cache/provider/payload I/O before all lines pass; signal is any spy call for invalid line index greater than zero. | Complete aggregate-shape and all delegated intake validation first; Task 3 parameterized spies must remain empty. | Revert Task 3 service commit and retain the failing call-order test. |
| P1 | Required loader failure is cached or optional failure aborts the order; signal is missing recovery load or wrong exception/warning contract. | Reuse `AsyncTTLCache` and `CatalogEnrichmentService` unchanged; adapter catches nothing; Task 2/3 prove required propagation, optional warning, and later recovery. | Revert Tasks 2-3 only; existing focused examples remain untouched. |
| P1 | The artifact recursively includes itself or exposes a trusted serializer; signal is an `artifact` key, Fory import, caller-selected format, or non-UNTRUSTED metadata. | Build the explicit JSON document allowlist and always call existing `JsonPayloadService`; decoded equality tests and import scans block drift. | Return to Task 3 document builder and rerun payload plus CLI redaction tests. |
| P2 | Sequential catalog reads reduce batch throughput; signal is one loader await per distinct SKU rather than internal parallel fan-out. | Accept deliberately for one visible concurrency owner, cap orders at 100 lines, document the teaching trade-off, and make no production performance claim. | If requirements change, open a separate library/provider design issue; do not add nested tasks in this PR. |
| P2 | Caller identifiers amplify logs or are mistaken for metric labels/secrets; signal is identifier interpolation, raw provider text, or docs promising production privacy. | Establish aggregate context only after intake validation, keep identifiers structured, exclude sensitive provider/artifact fields, and document production bounds/privacy/auth/retention as adapter obligations. | Repair Task 3 logging and Task 6 docs together, then rerun redaction/parity tests. |
| P2 | Diagrams describe planned rather than implemented ownership; signal is a class/arrow/event absent from final source or sequence tests. | Create assets only after Tasks 1-5, audit source labels and geometry, inspect full-size PNGs, and require direct embeds in both locales. | Regenerate only Task 6 assets/docs from final source and rerun all diagram audits. |

## Non-Triggered Hazards

- Dependency/catalog/lockfile migration: not triggered; all pinned sources and
  versions remain unchanged.
- Database/schema/backfill: not triggered; no persistence exists.
- Docker/Testcontainers/native/JNI: not triggered by the integrated example.
- Framework/HTTP/auth/deployment/release: explicitly out of scope.
- Cross-repository library API: not triggered; all new contracts are local to
  this workshop example.

## Exit Condition

Risk prediction passes when every P1 maps to a failing-first deterministic test,
Tasks 3/4/8 rerun affected proof after any repair, final review reaches
P0=0/P1=0, and no non-triggered hazard appears in the actual diff.
