# Issue #3 validated order intake lessons

## Context

The first workshop domain example needed to teach three focused
`bluetape-py` packages as one application-shaped path without introducing an
HTTP framework, shared workshop utilities, global logging configuration, or an
external backend.

## Decision

Keep the example as a small importable package with frozen keyword-only
contracts, one injected application-owned logger, deterministic validation,
safe public errors, a runnable module, and aligned bilingual documentation.
Use the existing `bluetape-core` validation primitives,
`bluetape-logging` context/filter APIs, and one isolated
`bluetape-testing.eventually` demonstration rather than adding wrappers.

## Surprise and failure

### Safe context must be built before validation without rendering input

Context needs the request identifiers while validation failures still need a
contextual rejection event. Calling `str`, `repr`, serialization, or truncation
at that point can execute hostile user code or expose data. Type-check the three
identifier values and substitute a stable sentinel for non-strings. Lock this
boundary with an object whose `__str__` and `__repr__` both fail.

### Direct loggers do not inherit useful application defaults

A direct `logging.Logger` avoids global registry and root mutations, but its
logger and handler levels, propagation, context filter, formatter, removal, and
close all need explicit ownership. Test success and rejection handler failures;
otherwise validation-path logging can mask its original error without evidence
that context still resets.

### Synchronous logging should not be tested as asynchronous work

The handler receives records synchronously. Ordinary assertions should inspect
the captured records directly. Demonstrate `eventually` in one bounded test
that probes an already-emitted record; do not add sleeps, threads, or polling to
make a synchronous example look concurrent.

### Pytest launcher behavior can change repository discovery

`python -m pytest` included the repository root while the installed `pytest`
console script did not in this environment. Configure `pythonpath = ["."]` and
include both `tests` and `examples` in `testpaths`, then prove targeted and full
collection. Do not depend on incidental launcher `sys.path` behavior.

### Structural diagram audits do not replace semantic inspection

The first Architecture render passed connector audits while a failure arrow
still pointed to the accepted result. The first Sequence wording also implied
that the service returned a problem object rather than raising
`InvalidOrderCommand`. Render SVG to PNG, inspect the full-size image after
every semantic edit, and rerun both generic and diagram-family audits.

## Outcome

The example preserves accepted caller values, rejects invalid fields in a
stable order, emits safe contextual outcome events, resets context on every
tested exit, exposes deterministic stderr/stdout behavior, and is independently
runnable and testable. English and Korean guides share the same verified
Architecture and Sequence Diagram assets.

## Verification

- Focused example suite: 32 tests passed.
- Full repository suite: 57 tests passed.
- Ruff check and format check passed.
- actionlint 1.7.12 passed with Go 1.26.1.
- `uv.lock` remained unchanged from the issue #3 base.
- Architecture and Sequence SVG audits and final PNG inspections passed.

## Review misses

The implementation plan correctly named logger-failure propagation and
contextual rejection records, but the first test set proved logger failure only
on the success path and did not assert all rejection correlation fields. The
pre-PR review added those assertions. The diagrams also needed semantic review
beyond their initial geometry/style PASS results.

## Future guard

For later workshop services:

1. construct prevalidation context without user-defined conversion;
2. test both normal and failure-path logger exceptions with context reset;
3. distinguish synchronous assertions from teaching-only eventual probes;
4. configure example discovery explicitly at the repository root;
5. treat SVG audits and full-size PNG inspection as separate required gates;
6. update both README locales and their executable documentation contract in
   the same change.
