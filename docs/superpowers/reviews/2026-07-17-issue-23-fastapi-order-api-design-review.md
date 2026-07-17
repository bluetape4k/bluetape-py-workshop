# Issue #23 Direct FastAPI Order API Design Review

Reviewed artifact:
`docs/superpowers/specs/2026-07-17-issue-23-fastapi-order-api-design.md`

Review mode: six read-only perspectives completed in the main session after a
native subagent dispatch stalled and was reclaimed. No implementation source or
dependency was changed during this review.

## Initial Findings

| Priority | Lens | Evidence | Required repair | Result |
|---|---|---|---|---|
| P1 | User/caller + developer/API | Success used `201 Created` although persistence and an addressable created resource are non-goals | Use `200 OK`; explain why no `Location` or 201 contract exists | Repaired |
| P1 | Stability/Ops | Lifespan removed `app.state.order_backend` before awaiting the finite close contract | Close first; remove state only on success; retain reference and propagate shutdown failure | Repaired |
| P1 | Security | “bounded HTTP request” and security wording could be read as a raw byte limit although Pydantic bounds only the decoded model | State the raw-body limitation and production gateway/server requirement | Repaired |
| P1 | Developer/API | Dependency isolation was assigned to an optional example test that is skipped when FastAPI is absent | Name root baseline/documentation test modifications explicitly | Repaired |
| P2 | Operator/Ops | CLI required a test-selected port but exposed no port contract | Add validated `--port`; keep host fixed to loopback | Repaired |
| P2 | User/caller | Reusing `X-Request-ID` could be mistaken for idempotency and safe automatic retry | State correlation-only semantics and no automatic POST retry | Repaired |
| P2 | Stability | Cancellation proof allowed a generic fake and did not necessarily exercise existing backend task ownership | Require a real backend with event-held injected provider | Repaired |
| P3 | Performance | Pydantic validation and response shaping add bounded per-line work up to 100 lines; no new hot-path benchmark is justified | Keep the line cap and verify latency only through deterministic focused tests | Accepted |

## Perspective Closure

| Perspective | P0 | P1 | P2 | P3 | Closure evidence |
|---|---:|---:|---:|---:|---|
| Performance | 0 | 0 | 0 | 1 | Fixed line bound; no blocking or duplicate provider round trip added by transport |
| Stability | 0 | 0 | 0 | 0 | Close-before-delete and real-backend cancellation proof |
| Security | 0 | 0 | 0 | 0 | Header allowlist, response redaction, decoded/raw bound distinction |
| Operator/Ops | 0 | 0 | 0 | 0 | Explicit loopback port and visible shutdown failure |
| Developer/API | 0 | 0 | 0 | 0 | Root dependency tests, app factory seam, precise status contract |
| User/caller | 0 | 0 | 0 | 0 | 200 semantics, correlation-only request ID, retry warning |

## Integration Verdict

Latest result: **P0=0, P1=0**. The repaired `200 OK` contract changes an
approved public behavior and therefore requires explicit user approval before
Step 3 planning. All other repairs clarify ownership, proof location, or
unsupported production behavior without expanding implementation scope.
