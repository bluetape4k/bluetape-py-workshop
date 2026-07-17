# Direct FastAPI Boundary Workshop Lesson

## Context

Issue #23 had to turn a framework-neutral order backend into a realistic HTTP
lesson without presenting workshop transport code as a reusable upstream
adapter. It also had to keep FastAPI and its web stack outside the default
environment, preserve the backend's timeout/cancellation ownership, and make
the bilingual visual explanation trustworthy at rendered size.

## Decision

- Keep Direct FastAPI policy in an optional application-shaped example and
  convert strict Pydantic DTOs into the existing immutable backend commands.
- Construct one backend in FastAPI lifespan, expose it through app state, and
  close it before deleting the state reference.
- Add no HTTP timeout or watcher task; translate only the backend's terminal
  outcome and allow `CancelledError` to propagate.
- Build explicit allowlisted success and problem bodies instead of serializing
  backend dataclasses or Pydantic error objects.
- Bind the teaching CLI to `127.0.0.1` with one worker, no reload, and no proxy
  header trust. Keep production deployment, auth, persistence, TLS, and raw
  body limiting outside the example.

## Surprise and Failure

Bounding a decoded Pydantic model does not bound the raw HTTP bytes consumed
before decoding. The first design wording could easily have implied a stronger
denial-of-service boundary than FastAPI/Uvicorn actually supplied, so the
README now names the missing upstream raw-body limit explicitly.

The first validation field helper also treated any Python identifier as safe.
Pydantic includes an unknown request key in the error location, so a key such
as `customer_secret` was reflected in the public problem even though its value
was redacted. In addition, context-manager structure made restoration likely,
but the tests did not directly prove every promised failure path.

The first architecture layout was mechanically valid yet did not reserve the
rendered arrowhead projection. Moving cards alone was insufficient until both
inter-card gaps and terminal connector segments included marker width,
`refX/viewBox` projection, stroke, and a visible safety margin.

## Repair

Allow only known public DTO path segments in validation problems; omit the
field entirely when any location segment is unknown. Seed an outer logging
context around validation and every mapped backend failure, then emit a record
after the response to prove restoration. Keep `CancelledError` outside the
`Exception` mapping and scan for terminal named backend tasks.

In lifespan shutdown, execute `await backend.aclose()` before deleting app
state. A failed close therefore preserves the backend reference and the
original shutdown exception for deterministic diagnostics.

For diagrams, calculate marker projection from the SVG marker geometry, make
card gaps exceed projection plus stroke and safety, and keep every terminal
segment longer than the arrowhead clearance. Render with CairoSVG at 2x, run
all connector audits, and inspect the final PNG rather than trusting SVG source
coordinates alone.

## Outcome and Proof

- Optional Direct FastAPI example: `65 passed`.
- Lifecycle/cancellation subset: `3 passed` in each of three consecutive runs.
- Default dependency boundary: `31 passed`.
- Default repository: `312 passed, 9 skipped, 1 deselected`.
- Documentation and diagram contract: `16 passed`.
- Architecture: `3600x1440`, 6 cards, 5 connectors, 1 marker, no crossings or
  intrusions.
- Sequence: `3000x2800`, 15 numbered messages, 15 connectors, 5 markers,
  sequence-style PASS.
- Ruff format/lint, actionlint, XML/CairoSVG rendering, endpoint/geometry/
  mixed-corner audits, full-size PNG inspection, and diff hygiene pass.

## Review Misses

The initial tests checked that a secret value was absent but did not check that
an attacker-chosen unknown field name was also absent. They also inferred log
context cleanup from the context manager instead of asserting the full matrix
promised by the design. The initial visual pass considered line endpoints but
not the arrowhead dimensions rendered beyond those endpoints.

## Future Guard

1. Distinguish raw transport-byte limits from decoded-model limits in every web
   example and never imply that one proves the other.
2. Treat validation locations as untrusted input. Allowlist public schema path
   components instead of filtering them with a general identifier predicate.
3. Test context restoration after every documented success, error, timeout,
   and cancellation category, not only representative paths.
4. Close owned resources before deleting their diagnostic references; retain
   state when close fails.
5. Include marker projection, stroke, and safety margin in both card gaps and
   terminal connector lengths, then inspect the rendered PNG at full size.
