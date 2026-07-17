# Issue #23 Direct FastAPI Order API Implementation Review

## Scope

- Base: `origin/develop@a750245e5afec772ccd1af6ae41c483281a4cf99`
- Head candidate: `feat/fastapi-order-api`
- Reviewed slice: optional web metadata, transport/lifespan/CLI implementation,
  tests, bilingual documentation, diagram assets, and milestone registration
- Review execution: six main-session perspective passes plus one integration
  pass. Native subagents were not reused after the previously reported delay.

## Baseline Findings and Repairs

| Priority | Lens | Evidence | Repair | Rerun |
|---|---|---|---|---|
| P1 | Security + user/caller | `_safe_validation_field()` accepted every Python identifier from Pydantic's error location. A forbidden request key such as `customer_secret` was reflected as `body.customer_secret`, crossing the promise not to return raw user-controlled input. | Replaced identifier acceptance with an allowlist of the six public DTO path segments and return no field when any segment is unknown. Added a leak-negative request test. | HTTP application `20 passed`; optional example `65 passed`; security and user/caller passes. |
| P1 | Stability + developer/API | The design required outer logging-context restoration after validation, domain, timeout, unknown-failure, and cancellation paths, but tests directly proved only success and cancellation. | Seeded an outer context around validation and every mapped backend failure, logged after each response, and asserted the restored outer request ID. | HTTP application `20 passed`; lifecycle/cancellation repeated three times; stability and developer/API passes. |

## Final Perspective Results

| Lens | Reviewed evidence | P0 | P1 | P2 | P3 | Verdict |
|---|---|---:|---:|---:|---:|---|
| Performance | Maximum 100 decoded lines, bounded identifiers and quantities, one backend deadline, no transport watcher/timeout, one lifespan-owned backend | 0 | 0 | 0 | 0 | PASS |
| Stability | Startup/shutdown ownership, close-before-delete, retained state on close failure, native cancellation, named-task cleanup, process smoke, three repeated lifecycle/cancellation runs | 0 | 0 | 0 | 0 | PASS after repair |
| Security | JSON-only transport, strict DTOs, validated request ID, allowlisted success/problem fields and validation paths, redacted logs, proxy trust disabled, honest raw-body limitation | 0 | 0 | 0 | 0 | PASS after repair |
| Operator/Ops | Fixed loopback bind, one worker, no reload, stable low-cardinality events, visible shutdown failure, exact start/stop/troubleshooting commands, production non-goals | 0 | 0 | 0 | 0 | PASS |
| Developer/API | Import-safe optional package, injected backend factory/logger, existing immutable domain command, explicit OpenAPI response schemas, no reusable adapter claim | 0 | 0 | 0 | 0 | PASS after repair |
| User/caller | Reciprocal bilingual guides, realistic request/response, retry/idempotency warning, failure table, cleanup guidance, Architecture and Sequence diagrams | 0 | 0 | 0 | 0 | PASS |

## Step 5 Verifier

| Gate | Evidence | Result |
|---|---|---|
| A-VER-01 requirements | Independently runnable Direct FastAPI example; one lifespan backend; strict transport/domain split; stable problems; cancellation; optional isolation; bilingual diagrams; root registration | PASS |
| A-VER-02 planned tasks | Tasks 1-7 implemented and committed; Task 8 review, repair, lesson, and local verification complete. Push/PR/CI remain Task 9 delivery gates. | PASS |
| A-VER-03 scope | `git diff --name-status origin/develop...HEAD` contains only issue #23 design/plan/review/lesson, optional metadata/lock, example, tests, diagrams, and root registration. | PASS |
| A-VER-04 public docs | Both example locales embed both PNGs and link both SVGs; both root locales link the example and exact isolated setup/run/test commands. | PASS |
| A-VER-05 planned risks | Unknown input reflection, request context, validation, domain failures, timeout, cancellation, close failure, process cleanup, default isolation, and arrowhead clearance have direct tests or audits. | PASS |
| A-VER-06 fresh evidence | Python 3.13.14, uv 0.11.28; dependency `31 passed`; docs/diagram `16 passed`; default `312 passed`; optional `65 passed`; lifecycle/cancellation `3 passed` in each of three runs; Ruff/actionlint/diff checks pass. | PASS |
| A-VER-07 gaps | Raw HTTP byte limiting, auth, TLS, persistence, proxy/deployment topology, monitoring, and rollback automation are explicit production non-goals. The upstream FastAPI TestClient import emits one non-failing Starlette deprecation warning. | PASS |

Verifier verdict: **PASS**.

## Diagram Evidence

- Architecture: `3600x1440`, 6 cards, 5 connectors, 1 marker, zero
  intrusions/crossings/geometry failures; endpoint and mixed-corner audits PASS.
- Sequence: `3000x2800`, 15 visible numbered messages, 15 connectors, 5
  markers, zero intrusions/crossings/geometry failures; endpoint,
  mixed-corner, and sequence-style audits PASS.
- Both final PNGs were inspected at original size after the last SVG change.
  Labels, terminal segments, arrowheads, card gaps, branch frame, activations,
  and shutdown order remain readable without overlap.

## Integration Verdict

Final normalized result: `P0=0, P1=0, P2=0, P3=0`.

PR creation may proceed only after this review and the lesson are committed and
the exact head reruns the final gates. Merge, auto-merge, release, tag, publish,
milestone closure, and remote branch deletion remain unauthorized.
