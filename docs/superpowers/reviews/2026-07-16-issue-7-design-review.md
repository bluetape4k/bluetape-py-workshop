# Issue #7 Design Review

## Scope

- Artifact: `docs/superpowers/specs/2026-07-16-issue-7-redis-test-server-design.md`
- Source baseline: `bluetape-py@4b7458f22cea0a9e757b5fbf7f5ff4bc8c23cb9a`
- Review kind: Type A Step 2-R spec review
- Execution note: three bounded native review lanes were interrupted after the
  first response window. Per the user fallback rule, the main session reclaimed
  performance, stability, and security immediately and completed all six
  perspectives as separate checklist passes before integration.

## Initial Findings and Repairs

| Priority | Lens | Evidence | Required edit | Resolution |
|---|---|---|---|---|
| P1 | Security | Protocol bounds were caller-configurable and had no exact safe defaults; the CLI allowed probe exception text and connection causes to reach a traceback. | Fix small immutable protocol bounds and convert probe failures to a redacted CLI event while preserving causes for direct API callers. | Fixed 64-byte parts/bulk payloads, 128-byte lines, safe CLI handling, and stderr requirements. |
| P1 | Stability | The cleanup claim checked server state but did not require evidence that the labeled container set returned to its baseline. | Record label-filtered containers before and after the serial Docker command and require equality. | Added exact pre/post container-set proof. |
| P1 | Developer/API | The CLI injection and exit contract were not exact enough to implement deterministic startup-failure tests. | Define `main(*, server_factory=RedisServer) -> int`, module exit behavior, and the factory's test-only scope. | Added an exact CLI contract. |
| P2 | Performance | The probe opens three short-lived connections without explaining the extra round trips. | State the trade-off and keep pooling/pipelining outside the workshop. | Accepted and documented as a one-shot teaching trade-off. |
| P2 | Operator/Ops | Cleanup guidance named the label but not the exact safe removal procedure. | Add the inspection command and restrict force-removal to a confirmed workshop container ID. | Added exact inspect/confirmed-remove guidance. |
| P2 | User/caller | Probe-failure CLI behavior and stderr expectations were ambiguous. | Add a stable `redis_probe_failed` event and deterministic stderr assertions. | Added to CLI and test contracts. |

## Final Perspective Verdicts

| Lens | Final evidence | P0 | P1 | P2/P3 disposition |
|---|---|---:|---:|---|
| Performance | Fixed small buffers and finite socket timeout bound work; the deliberate three-connection cost is documented and production pooling is excluded. | 0 | 0 | Initial P2 accepted with rationale. |
| Stability | Single-owner contexts, exact startup/command bounds, body-failure cleanup, fresh-state proof, and pre/post label equality cover lifecycle recovery. | 0 | 0 | Initial P1 fixed. |
| Security | Trusted fixed image, length-delimited fixed command flow, immutable small bounds, redacted startup/probe CLI failures, and no credentials or arbitrary command surface are explicit. | 0 | 0 | Initial P1 fixed. |
| Operator/Ops | Stable failure kinds, safe JSON, serial runbook, labeled inspection, confirmed cleanup, rollback, and no release side effects are explicit. | 0 | 0 | Initial P2 fixed. |
| Developer/API | Exact package responsibilities, immutable result, fixed probe behavior, context ordering, test-only CLI injection, and deterministic/Docker commands are implementable. | 0 | 0 | Initial P1 fixed. |
| User/caller | Scenario, non-goals, expected events, two test lanes, troubleshooting, bilingual parity, and mandatory source-backed visuals are testable. | 0 | 0 | Initial P2 fixed. |

## Integration Review

- The selected design teaches the ecosystem wrapper without duplicating its
  Docker configuration or introducing a production provider.
- The protocol boundary is intentionally narrow, length-delimited, bounded,
  synchronous, and private to the application example.
- Every issue acceptance criterion maps to a deterministic or explicit serial
  Docker proof.
- Default and Docker test selection, container ownership, failure redaction,
  locale parity, diagrams, rollback, and merge authority are explicit.
- No new dependency, lockfile change, package publication, persisted data,
  concurrency contract, or migration is introduced.

Final verdict: **PASS — P0=0, P1=0**.
