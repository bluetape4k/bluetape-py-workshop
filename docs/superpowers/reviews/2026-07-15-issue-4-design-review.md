# Issue #4 Design Review

Status: P0=0, P1=0 after convergence

Reviewed artifact:
[2026-07-15-issue-4-bounded-catalog-enrichment-design.md](../specs/2026-07-15-issue-4-bounded-catalog-enrichment-design.md)

## Review Method

The Type A design was reviewed through the required performance, stability,
security, operator/Ops, developer/API, and user/caller lenses. Two native
read-only lanes exceeded the bounded response window and were immediately
interrupted; a third could not start because the native thread limit retained
older interrupted issue #3 lanes. Per the user's latency rule, all affected
perspectives were reclaimed and completed as separate main-session passes.

No review lane wrote files, ran heavy commands, or owned integration decisions.

| Lens | Initial P0 | Initial P1 | Result |
|---|---:|---:|---|
| Performance | 0 | 1 | Fixed request, identifier, and batch caps bound eager work independently of concurrency |
| Stability | 0 | 1 | Expected outages, programming defects, mixed ExceptionGroups, timeout, and cancellation are distinct |
| Security | 0 | 1 | ASCII grammar and provider-response validation prevent normalization collision and cross-batch contamination |
| Operator/Ops | 0 | 0 | Caller telemetry ownership and source-only rollback are explicit |
| Developer/API | 0 | 1 | `ProviderUnavailable` makes the expected operational failure contract implementable |
| User/caller | 0 | 0 | Duplicate restoration, warning codes, output cardinality, and unsupported behavior are explicit |

## Resolved Findings

### Performance P1 — bounded concurrency did not bound eager request work

The first draft allowed an arbitrary synchronous iterable and arbitrary batch
size before building the complete job list. The design now limits requests to
1,000 occurrences, identifiers to 64 ASCII characters, and batches to 100
identifiers ([design lines 46-50](../specs/2026-07-15-issue-4-bounded-catalog-enrichment-design.md)).

### Stability and Developer/API P1 — provider failure classification was ambiguous

The first draft caught generic provider exceptions as expected required or
optional failures while also claiming programming defects would propagate. The
design now requires provider adapters to translate operational outages into
`ProviderUnavailable`; any other exception propagates. An `ExceptionGroup`
becomes `CatalogEnrichmentFailed` only when every leaf is an expected
`RequiredProviderFailure` ([design lines 159-170 and 209-229](../specs/2026-07-15-issue-4-bounded-catalog-enrichment-design.md)).

### Security P1 — Unicode normalization and unbounded input could collide or exhaust

Uppercasing arbitrary Unicode can collapse distinct caller values and an eager
iterable can consume unbounded memory before the concurrency helper starts. The
design now rejects raw non-ASCII identifiers, applies a strict normalized SKU
grammar, stops at the request cap, and validates provider mapping keys and
record identifiers against the exact batch ([design lines 180-200](../specs/2026-07-15-issue-4-bounded-catalog-enrichment-design.md)).

### Security P2 — provider text was incorrectly described as display-safe

Provider names and recommendations have no output-context guarantee. The design
now labels them untrusted provider content and leaves HTML/SQL escaping or
binding to the future adapter ([design lines 121-127](../specs/2026-07-15-issue-4-bounded-catalog-enrichment-design.md)).

### Operator/Ops P2 — observability and rollback ownership was implicit

The example now exposes stable warning/error/timeout/cancellation hooks without
configuring global telemetry. A caller owns safe logging and metrics, while
rollback is limited to reverting the source-only example
([design lines 236-247](../specs/2026-07-15-issue-4-bounded-catalog-enrichment-design.md)).

## Integration Verdict

- Alternatives, boundaries, and pinned APIs: complete
- Required/optional provider policy: testable and fail-closed
- Stable ordering and duplicate semantics: explicit
- Timeout, cancellation, and task ownership: explicit
- Documentation, diagrams, compatibility, rollback, and delivery boundary: complete
- P0: 0
- P1: 0
- Implementation started: no
- Next gate: explicit approval of the converged written spec, followed by the
  implementation-plan workflow
