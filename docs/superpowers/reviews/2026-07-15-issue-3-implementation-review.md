# Issue #3 implementation review

## Reviewed scope

- Base: `develop` at `a711f4747bc1abcf430d4c209b789a60aa0a7dce`
- Implemented content checkpoint: `617c8e4376050ad579e6ff0e57c931bdf2ea7965`
- Scope: the full base-to-branch diff plus the evidence repairs recorded below
- Spec: `../specs/2026-07-15-issue-3-validated-order-intake-design.md`
- Plan: `../plans/2026-07-15-issue-3-validated-order-intake-plan.md`

Earlier native review lanes did not return usable evidence within the user's
bounded wait policy and were reclaimed. The final implementation review used
six separate read-only main-session passes over the same diff, followed by one
integration pass. No delayed agent assertion is counted as review evidence.

## Verifier mapping

| Verifier row | Result | Evidence |
|---|---|---|
| A-VER-01 accepted requirements | PASS | Frozen contracts, deterministic validation, public mapping, context/reset tests, runnable module, bilingual docs, and source-backed diagrams map every spec row. |
| A-VER-02 planned tasks | PASS | Tasks 1–4 are committed; Task 5 validation, review, lesson, WIP, and authorized PR delivery remain in their declared order. |
| A-VER-03 scope discipline | PASS | The diff contains only issue #3 source, tests, pytest discovery, docs, diagrams, plan/review/lesson, and WIP evidence; `uv.lock`, dependencies, and CI are unchanged. |
| A-VER-04 public documentation | PASS | Root and example README locale pairs are aligned; the SVG sources and PNG renders match implemented participants and events. |
| A-VER-05 planned risks | PASS | Tests cover hostile conversions, context reset, root logger isolation, logger failure on success and rejection, test discovery, subprocess timeout, and documentation assets. |
| A-VER-06 fresh evidence | PASS | Locked Ruff, focused pytest, full pytest, runnable output, actionlint, lock immutability, SVG audits, and diff checks were rerun against the current working tree. |
| A-VER-07 known gaps | PASS | Async, backend, Docker, packaging, benchmark, release, and migration checks are evidence-backed N/A for this synchronous in-process example. |

Verifier verdict: **PASS**.

## Findings and convergence

| Lens | Initial P0 | Initial P1 | Initial P2 | Final P0 | Final P1 | Final P2 | Evidence/disposition |
|---|---:|---:|---:|---:|---:|---:|---|
| Performance | 0 | 0 | 0 | 0 | 0 | 0 | Five scalar fields, bounded validation, one result allocation, and one log event per path; no collection growth, retry, blocking I/O, or benchmark claim. |
| Stability | 0 | 1 | 0 | 0 | 0 | 0 | Rejection-side handler failure was not independently proved. Added a failing-handler rejection test that requires the original `RuntimeError` and empty context; focused suite is 29 tests after the repair. |
| Security | 0 | 0 | 0 | 0 | 0 | 0 | Safe context type-checks identifiers without conversion; logs exclude SKU, quantity, full command, credentials, and sensitive payload claims. |
| Operator/Ops | 0 | 1 | 0 | 0 | 0 | 0 | Rejection records had event assertions but incomplete correlation-field proof. Added exact request/partner/order context assertions and raw-SKU exclusion. |
| Developer/API | 0 | 0 | 0 | 0 | 0 | 0 | Frozen keyword-only contracts, narrow validation exception mapping, injected direct logger, and test discovery match the approved API and Python patterns. |
| User/caller | 0 | 0 | 1 | 0 | 0 | 0 | Sequence step 7 said “public problem” although `accept` raises `InvalidOrderCommand`. Updated SVG/PNG wording, reran audits, and reinspected the full-size render. |

Final integrated result: **P0=0, P1=0, P2=0**.

## Integration review

- Public names in code, tests, README files, Architecture, and Sequence Diagram
  are consistent.
- Validation order is command, request ID, partner ID, order ID, SKU, then
  quantity; accepted values retain caller whitespace.
- `log_context` surrounds validation and logging, while direct application
  loggers own handler levels, formatting, propagation, removal, and close.
- The runnable path writes one contextual log to stderr and deterministic JSON
  to stdout; no server or cleanup process is hidden.
- No dependency, lock, CI, release, changelog, publication, or Docker surface
  changed. Those hazards remain out of scope with concrete source evidence.
- The architecture and sequence PNG files were rendered from the committed SVG
  sources at 2x and inspected after the last semantic edit.

## Fresh validation evidence

| Command | Result |
|---|---|
| `uv sync --locked --python 3.13.14` | PASS; 30 packages resolved, 27 checked |
| `uv run --locked pytest examples/order_intake/tests -q` | PASS; 32 tests |
| `uv run --locked pytest tests/test_dependency_baseline.py -q` | PASS; 18 tests |
| `uv run --locked pytest` | PASS; 57 tests |
| `uv run --locked ruff check .` | PASS |
| `uv run --locked ruff format --check .` | PASS; 11 files formatted |
| `uv run --locked python -m examples.order_intake` | PASS; documented stderr and stdout |
| actionlint 1.7.12 with Go 1.26.1 | PASS |
| `git diff --exit-code ... -- uv.lock` | PASS; unchanged from base |
| SVG XML, geometry, endpoint, corner, sequence-style audits | PASS |
| full-size Architecture and Sequence PNG inspection | PASS |
| `git diff --check` | PASS |

## N/A evidence and residual risk

- Async/cancellation/concurrency is N/A: the service creates no coroutine,
  task, timer, thread, socket, or executor.
- Docker/Testcontainers/backend recovery is N/A: the example imports no
  provider and opens no external connection.
- Benchmarking is N/A: there is no performance claim or variable-size hot path.
- Packaging, migration, release, and changelog work is N/A: the root remains a
  non-package project and no dependency or version authority changed.
- Residual risk is limited to caller data classification: the documented
  correlation IDs must remain non-secret or be hashed/replaced by the caller.
