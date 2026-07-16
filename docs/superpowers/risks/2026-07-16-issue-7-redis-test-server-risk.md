# Issue #7 Redis Test Server Risk Record

## Triggered Risks

| Risk | Signal | Mitigation | Rollback or rerun boundary |
|---|---|---|---|
| Untrusted image executes in Docker | Image comes from request, environment, or PR input | Use only wrapper default `redis:8`; expose no image input in the example | Remove the input path and rerun deterministic configuration tests before Docker |
| Docker runtime or image acquisition fails | `TestcontainerStartError.kind` reports runtime or pull failure | Keep 30-second wrapper bound and safe stable CLI kind; document sanitized runtime checks | Stop Docker lane, retain deterministic proof, repair environment, rerun one serial test |
| Readiness exceeds its operation bound | Startup reports `readiness-timeout` | Use wrapper `startup_timeout=30.0`; add no workshop retry | Close/inspect labeled container, rerun only after runtime health is restored |
| Labeled container remains after a run | Post-run label set differs from baseline | Context ownership plus pre/post label equality; remove only a confirmed workshop container | Preserve evidence, inspect, confirmed cleanup, rerun the failed command serially |
| Application body masks or skips cleanup | Probe failure changes identity or server remains running | Let the wrapper context receive the original exception; assert exact identity and closed state | Repair orchestration and rerun deterministic plus one real body-failure test |
| Cleanup itself fails | Wrapper retains cleanup-pending state or labeled residue | Document `close()` retry and label inspection; never discard primary failure | Retry public close when available, inspect residue, stop delivery until baseline restored |
| Docker launches overlap | More than one test/CLI process or shared server owner exists | One marked module, no xdist/background launch, sequential commands only | Stop all workshop runs, inspect labels, rerun one command at a time |
| RESP input or response allocates without bound | Arbitrary command API, caller-relaxable limits, or unbounded line/bulk read appears | Fixed commands; 64-byte parts/bulk, 128-byte lines, 2-second socket timeout | Revert the protocol slice and rerun every bound/failure test before Docker |
| Protocol helper is mistaken for production client | Generic command, authentication, pooling, pipelining, retry, or provider API appears | Domain name, private command method, fixed round trip, explicit README non-goal | Delete expanded surface and rerun public-shape/document tests |
| Default verification contacts Docker | Unmarked integration test or default selection includes marker | Registered marker, default `not testcontainers`, CI explicit exclusion, import-side-effect test | Stop PR, fix selection, rerun full deterministic ladder with Docker labels unchanged |

## Remaining External Variables

Docker daemon availability, local `redis:8` cache state, registry reachability,
and machine startup latency are external. The wrapper bounds and classifies
these operations; the workshop does not retry or claim portability to an
unverified runtime. An abnormal process termination can still leave a labeled
container, so exact inspection and confirmed cleanup remain part of delivery.
