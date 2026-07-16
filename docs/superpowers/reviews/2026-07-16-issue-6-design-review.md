# Issue #6 Design Review

## Scope

- Artifact: `docs/superpowers/specs/2026-07-16-issue-6-bounded-payload-processing-design.md`
- Source baseline: `bluetape-py@4b7458f22cea0a9e757b5fbf7f5ff4bc8c23cb9a`
- Review kind: Type A Step 2-R spec review
- Execution note: two bounded native review lanes were interrupted after they
  exceeded the response window. Per the user fallback rule, the main session
  completed all six perspectives independently and integrated the result.

## Initial Findings and Repairs

| Priority | Lens | Evidence | Required edit | Resolution |
|---|---|---|---|---|
| P1 | security | The initial decode flow bounded only decompressed and serde bytes. An arbitrarily large encoded string or compressed byte sequence could allocate before those limits. | Add encoded-text and decoded-compressed bounds before decompression in both services. | Added `max_encoded_size`, `max_compressed_size`, `TransportLimitError`, ordered checks, and tests. |
| P2 | performance | The initial contract did not make codec/decompression allocation bounds independently observable. | Name transport limits separately from serde limits and test the no-call boundary with spies. | Added separate constructor limits and pre-call test requirements. |
| P2 | operator/Ops | CLI observability did not state whether payload contents could be emitted. | Define safe event fields and prohibit payload/object content. | Added stage/profile/size/error-class events with sensitive content excluded. |
| P2 | user/caller | The optional Fory environment had no cleanup command or explicit received-metadata routing warning. | Add cleanup and misuse warning to the documentation contract. | Added `rm -rf .venv-fory` and routing warning. |
| P1 | developer/API | Runtime proof showed `pyfory==1.3.0` serializes but cannot deserialize a frozen slotted registered dataclass; pinned upstream tests use mutable slotted dataclasses. | Keep only the transport envelope frozen and make `OrderSnapshot` mutable/slotted while proving caller input preservation. | Minimal frozen/non-frozen reproduction confirmed the root cause; spec and tests were revised and 12 actual Fory tests pass. |

## Final Perspective Verdicts

| Lens | Final evidence | P0 | P1 | P2/P3 disposition |
|---|---|---:|---:|---|
| Performance | Encoded, compressed, decompressed, serde, and Fory pool bounds are explicit; tests require pre-call rejection. | 0 | 0 | Initial P2 fixed. |
| Stability | Deterministic typed failures cover malformed codec/gzip/serde/Fory, trailing gzip input, boundaries, and isolated optional environment cleanup. | 0 | 0 | None open. |
| Security | Independent expected metadata precedes codec/decompression; no registry, dynamic class, schema, or adapter selection exists; default imports exclude Fory. | 0 | 0 | Initial P1 fixed. |
| Operator/Ops | Fixed profiles, safe CLI events, provider prerequisites, exact commands, cleanup, and delivery exclusions are explicit. | 0 | 0 | Initial P2 fixed. |
| Developer/API | Separate concrete services fit the workshop goal; the envelope is immutable, the registered model matches provider construction needs, and exact exports/errors/tests are implementable. | 0 | 0 | Runtime-discovered P1 fixed. |
| User/caller | Scenario, trust comparison, misuse guards, run/test/cleanup commands, locale parity, and mandatory visuals are testable acceptance criteria. | 0 | 0 | Initial P2 fixed. |

## Integration Review

- Alternatives are explicit and the selected duplication is intentional.
- Boundaries cover default/optional dependencies, imports, trust, input sizes,
  side effects, and PR/merge authority.
- Eight concrete failure modes map to typed errors and tests.
- Compatibility is additive; only the optional dependency graph changes.
- Documentation and diagrams are tied to implemented source behavior.

Final verdict: **PASS — P0=0, P1=0**.
