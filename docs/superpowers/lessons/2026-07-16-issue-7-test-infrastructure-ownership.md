# Test Infrastructure Ownership: Keep Lifecycle and Application Proof Separate

## Context

A runnable workshop needed to demonstrate a temporary Redis dependency without
duplicating container configuration or presenting a teaching probe as a
production Redis client.

## Reusable Lesson

Compose infrastructure wrappers at the application boundary and keep the
application proof deliberately narrower than the wrapper:

1. let the ecosystem wrapper own image policy, readiness, dynamic port mapping,
   stable startup failures, labels, and cleanup;
2. let one application context own exactly one wrapper instance and consume its
   published immutable connection details only after entry;
3. keep the teaching probe fixed, bounded, timeout-controlled, and incapable of
   selecting arbitrary commands, endpoints, images, or credentials;
4. validate remote responses as untrusted data before returning them through an
   application API, even when the service is only a temporary test dependency;
5. prove lifecycle behavior twice: fast deterministic doubles for ordering and
   error shape, then one explicitly selected serial Docker lane for readiness,
   body-failure cleanup, and fresh-state evidence; and
6. exclude Docker tests in default pytest configuration and hosted CI, while
   documenting the exact opt-in command and label-based residue inspection.

## Why This Boundary Works

The wrapper remains the single source of truth for infrastructure mechanics,
while the example remains readable application code. Deterministic tests catch
protocol, validation, redaction, and ownership regressions without requiring
Docker. The focused real-container test proves the one property doubles cannot:
that the composed public contracts start, communicate, and clean up together.

## Warning for Future Examples

Do not reconstruct endpoints from container internals, add a second readiness
loop, share one mutable container across tests, or run Docker-backed examples in
parallel. Before removing residue, inspect the ecosystem ownership label and
confirm the resource belongs to the current workshop run.

