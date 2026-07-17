# Issue #23 Direct FastAPI Order API Plan Review

Reviewed artifact:
`docs/superpowers/plans/2026-07-17-issue-23-fastapi-order-api-plan.md`

Review mode: six read-only perspectives and Step 3-R integration completed in
the main session. Native subagents are excluded from this issue after the prior
stalled dispatch. No implementation source or dependency was changed.

## Initial Findings

| Priority | Lens | Finding | Required plan edit | Result |
|---|---|---|---|---|
| P1 | Stability + developer/API | Pytest imports a package parent before a test module can call `importorskip`; an exporting `__init__.py` could import FastAPI and break default collection | Keep package `__init__.py` import-safe and empty; require reasoned `importorskip` before optional module imports | Repaired |
| P1 | Developer/API + user/caller | Task 4 introduced an unapproved 415 code absent from the reviewed spec | Keep non-JSON/missing-body failures inside approved 422 `invalid_request` | Repaired |
| P1 | Security + Ops | CLI prose rejected proxy trust but the concrete `uvicorn.run` call left its proxy-header default implicit | Set `proxy_headers=False`, `reload=False`, fixed loopback host, one worker | Repaired |
| P2 | Stability | Readiness polling could submit more than one POST during retries | Poll TCP only, then submit exactly one order | Repaired |
| P2 | Operator/Ops | Error mapping tests did not lock transport event names and safe fields | Add fixed low-cardinality event and leak-negative log assertions | Repaired |
| P2 | Developer/API | Public OpenAPI schema was not explicitly verified | Assert the success/problem schemas and artifact-model absence | Repaired |
| P3 | Performance | No benchmark command exists for bounded DTO/response work | Accepted: maximum 100 lines and deterministic focused tests make a benchmark disproportionate; performance scan remains required after implementation |

## Step 3-R Checks

| Check | Result | Evidence |
|---|---|---|
| Every spec/DoD row maps to a task | PASS | Traceability table and Tasks 1-9 |
| Dependency order is implementable | PASS | metadata -> DTO/context -> lifespan -> HTTP -> CLI -> docs -> registration -> verification -> PR |
| No task depends on a later artifact | PASS | diagrams begin only after source; root registration follows local docs |
| Success/failure/edge/concurrency/lifecycle/backend capability | PASS | Tasks 2-5 and risk table |
| Concrete targeted commands | PASS | Every RED/GREEN and verification task names commands and expected outcomes |
| README locales and diagrams | PASS | Task 6 plus Task 7 root registration |
| HTTP lifecycle hazards | PASS | source inspection, TestClient lifespan, real cancellation, proxy trust off |
| Resource ownership and close | PASS | Task 3 close-before-delete and Task 5 process cleanup |
| Rollback and compatibility | PASS | per-task commit/revert points and default isolation rerun |

## Perspective Closure

| Perspective | P0 | P1 | P2 | P3 | Closure |
|---|---:|---:|---:|---:|---|
| Performance | 0 | 0 | 0 | 1 | Bounded shape; implementation performance scan retained |
| Stability | 0 | 0 | 0 | 0 | import-safe collection, real cancellation, TCP readiness, finite cleanup |
| Security | 0 | 0 | 0 | 0 | request/redaction tests and explicit proxy trust off |
| Operator/Ops | 0 | 0 | 0 | 0 | fixed events, loopback port, lifecycle/process cleanup |
| Developer/API | 0 | 0 | 0 | 0 | approved status set, OpenAPI, exact files/commands |
| User/caller | 0 | 0 | 0 | 0 | realistic 200 contract, retry warning, bilingual commands/visuals |

## Integration Verdict

Latest result: **P0=0, P1=0**. The plan fully maps the approved spec, contains
the triggered HTTP/lifecycle/security/diagram risks, and is ready for user
approval. Implementation remains blocked until the plan and this review are
approved and committed.
