# Issue #3 Design Review

Status: P0=0, P1=0 after convergence

Reviewed artifact:
[2026-07-15-issue-3-validated-order-intake-design.md](../specs/2026-07-15-issue-3-validated-order-intake-design.md)

## Review Method

The Type A design was reviewed through six separate lenses before planning.
The performance lane completed independently. A stability subagent could not
access the tracked draft under its no-command restriction and was immediately
reclaimed per the user's latency rule. The remaining lenses were completed as
separate main-session passes so the written-spec gate would not stall.

| Lens | Initial P0 | Initial P1 | Result |
|---|---:|---:|---|
| Performance | 0 | 0 | Safe context conversion and synchronous log assertions clarified |
| Stability | 0 | 0 | Deterministic validation order and narrow exception translation fixed |
| Security | 0 | 0 | No coercion of hostile values; correlation-ID data boundary documented |
| Operations | 0 | 1 | Direct logger level, handler level, propagation, and stdout/stderr ownership fixed |
| Developer/API | 0 | 0 | Logger constructor validation and public boundary clarified |
| User/caller | 0 | 0 | Deterministic runnable output and sensitive-identifier guidance clarified |

## Resolved Findings

### Operations P1 — direct logger configuration was incomplete

`logging.Logger` defaults could suppress INFO success events or allow an
implementation to depend on ambient logging state. The design now requires
explicit INFO levels, `propagate = False`, an application-owned handler, and
separate stderr logging/stdout JSON output.

### Performance P2 — invalid identifiers could trigger user conversion

The safe-context algorithm was underspecified. The design now permits only an
`isinstance(value, str)` check and forbids `str`, `repr`, serialization,
truncation, or other user-defined conversion for invalid runtime values.

### Performance P3 — polling obscured synchronous logging

Standard handler emission is synchronous in this example. Service logging tests
now assert captured records directly. A single labelled test demonstrates
`bluetape.testing.eventually` with a minimum bounded timeout without presenting
it as synchronization.

### Stability — validation and exception boundaries needed precision

The design now fixes command and field validation order. Only validation
failures become `InvalidOrderCommand`; logging failures remain application
failures while `log_context` still guarantees reset.

### Security and caller guidance — identifier classification was implicit

Request, partner, and order IDs are explicitly non-secret operational
correlation IDs. Documentation must warn callers not to put credentials or
sensitive payloads in them and to hash or replace identifiers when required by
their own classification rules.

## Convergence Result

- P0: 0
- P1: 0
- Implementation started: no
- Next gate: explicit approval of the converged written spec, followed by the
  implementation-plan workflow
