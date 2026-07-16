# Issue #10 Redis Load Coordination Risk Prediction

## Scope

- Spec: `docs/superpowers/specs/2026-07-17-issue-10-redis-load-coordination-design.md`
- Plan: `docs/superpowers/plans/2026-07-17-issue-10-redis-load-coordination-plan.md`
- Trigger: distributed cache coordination, async cancellation, optional
  dependency isolation, Redis security, and Testcontainers lifecycle make Step
  3-P mandatory.

## Predicted Risks

| Priority | Risk and signal | Prevention / proof | Rollback or rerun |
|---|---|---|---|
| P1 | Optional Redis imports leak into default collection; signal is default `uv sync` installing redis or collection error. | Keep package and example imports behind the extra; dependency test proves distribution/module absence; optional test files use module-level skip. | Revert metadata/import commit and rerun default sync plus full collection. |
| P1 | Two instances both load because the follower starts before the owner lease; signal is `loader_calls != 1`. | Event-control owner loader admission before starting follower; real Redis test asserts one call and `LOADED`/`RESULT_REUSED`. | Return to application choreography and rerun fake then real Redis tests. |
| P1 | Cancellation leaks a lease, flight, provider, task, or container; signal is active marker/task/client/server after bounded completion. | Upstream shielded cleanup, event-driven cancellation test, `AsyncExitStack`, `RedisServer` context, outer one-second guards, serial Docker proof. | Stop docs/PR, release test gates, inspect tasks/container labels, repair lifecycle, rerun all optional tests. |
| P1 | A stale/mismatched envelope is returned as fresh; signal is stale `ProductSummary` equality. | Strict owner-token matching through upstream codec; test stale then matching result and bounded stale-only failure. | Revert service/application task, retain failing test, inspect only public snapshot/result contracts. |
| P1 | Redis failure silently falls back and duplicates side effects; signal is loader called after provider timeout/error. | Assert stable exception identity/code and zero loader calls; document no fallback. | Repair composition and rerun timeout/provider/loader matrix. |
| P1 | Unsafe or ambiguous deserialization accepts malicious shape or bool price; signal is decoded object from wrong metadata/keys/types. | Exact untrusted metadata, public bounded JSON serde, exact key/type/range validation, no Fory. | Revert codec, keep negative fixtures, rerun codec and envelope tests. |
| P1 | Cleanup failure masks loader failure/cancellation; signal is changed primary exception. | Assert object identity and only the static upstream cleanup note/event flag. | Repair no workshop catch/wrap; rerun failure and cancellation paths. |
| P1 | Docker evidence is flaky or leaves resources; signal is retry-only pass or labeled container after test. | Run one Testcontainers command at a time, use readiness wrapper, prove body-failure and fresh-state cleanup, investigate every retry. | Stop validation, remove only confirmed test container, rerun serially from clean Docker state. |
| P2 | Poll budgets make tests slow. | Use event-driven fake backend and minimum supported finite poll budgets; no long sleep. | Tighten only test options, not production example defaults. |
| P2 | Learners mistake coordination for invalidation/fencing/exactly-once. | Repeat non-goals in both READMEs and diagrams; link blocked follow-up/upstream #56. | Repair docs/assets together and rerun parity/visual review. |
| P2 | Workshop container settings are copied to production. | Mark disposable local-only; document TLS, CA/hostname verification, ACL, timeouts, zero retry, no downgrade. | Remove any production-ready claim and rerun security lens. |

## Exit Condition

Every P1 maps to a failing-first test and a final command. The gate passes only
after default and optional environments both prove their boundaries, Docker
runs serially, final review reports `P0=0, P1=0`, and no retry-only success is
left unexplained.
