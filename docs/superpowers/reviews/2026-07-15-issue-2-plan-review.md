# Issue #2 implementation plan review

## 결론

- Target: `../plans/2026-07-15-issue-2-workshop-bootstrap-plan.md`
- Spec basis: `../specs/2026-07-15-issue-2-workshop-bootstrap-design.md`
- Initial result: P0=0, P1=2
- Final integrated result: P0=0, P1=0
- Risk prediction: triggered and included in the plan
- Gate: implementation-plan approval pending; implementation has not started

## 검토 방식

Native review-agent dispatch stalled and the call was aborted after the user
reported the delay. Following the full-feature timeout fallback, the main session
performed six separate bounded lenses against the same plan and spec instead of
waiting longer.

| Lens | Initial P0 | Initial P1 | Final P0 | Final P1 | Disposition |
|---|---:|---:|---:|---:|---|
| Performance | 0 | 0 | 0 | 0 | Root install cost is an approved tradeoff; repeat-run cache proof is explicit. |
| Stability | 0 | 0 | 0 | 0 | Fresh sync, bounded import probe, rerun/rollback boundaries are ordered. |
| Security | 0 | 1 | 0 | 0 | CI contract now asserts no secret mapping and records the checked-out head. |
| Operator/Ops | 0 | 0 | 0 | 0 | Timeout, diagnostics, cache rerun, checkpoint, and merge stop are assigned. |
| Developer/API | 0 | 1 | 0 | 0 | Lock provenance now verifies the canonical Git repository as well as commit/subdirectory. |
| User/caller | 0 | 0 | 0 | 0 | Both locale files share exact facts, commands, learning path, and diagram boundary. |

## Step 3-R checks

- Every spec acceptance criterion and DoD item maps to Tasks 1-5 and an exact
  command.
- Task order is executable: dependency authority precedes CI, CI/dependency facts
  precede public docs, and local evidence precedes PR creation.
- No task depends on an artifact created later.
- Docker/provider capability, lifecycle side effects, CI security, cache recovery,
  rollback, README parity, Type A review, risk, and lesson evidence are assigned.
- Database, coroutine/cancellation, public Python API migration, benchmark,
  Spring/Exposed, publish/BOM, and changelog checks have evidence-backed `N/A`
  decisions.
- PR creation is scoped to the approved repository/base/head; merge, milestone
  closure, release, publish, and cleanup remain separate gates.

## Remaining external variables

Git/network availability and the hosted `ubuntu-24.04` image are not immutable.
The plan bounds them with exact source/tool inputs, a job timeout, diagnostic
output, unchanged-head rerun rules, and explicit rollback; it does not claim
bit-for-bit runner reproducibility.
