# Issue #6 Bounded Payload Processing Risk Record

## Triggered Risks

| Risk | Signal | Mitigation | Rollback or rerun boundary |
|---|---|---|---|
| Received metadata selects unsafe deserializer | Registry, mapping, dynamic import, or branch on received format appears | Separate fixed services own independent expected metadata; source and tests scan for selectors | Revert the selector/registry and rerun all metadata-order tests before continuing |
| Encoded/compressed attacker input allocates before decompression bound | Codec/decompress spy runs for over-limit input | Bound encoded text and decoded compressed bytes before downstream calls | Revert current service slice, repair ordered checks, rerun spy tests |
| Compression bomb or trailing gzip reaches serde | Decompression limit/trailing-input test does not raise exact compression error | Caller-owned `GzipCompressor` with bound no larger than serde/Fory input; exact negative tests | Stop serde work, repair compressor configuration/order, rerun JSON and Fory limits |
| Default import installs or imports Fory | `pyfory` installed in default env or provider modules appear in isolated `sys.modules` | Optional project extra, separate `.venv-fory`, default export/import probe | Delete environments, restore default sync, repair dependency/import graph |
| Fory schema/type chosen from payload | Received field affects registration, Python class, schema, or adapter | One fixed composition root and registration ids; tamper tests reject envelope mismatch | Remove dynamic path; rerun actual provider round trip and mismatch tests |
| Frozen registered model serializes but cannot deserialize | Actual Fory round trip raises `MalformedPayloadError` after successful encode | Use provider-compatible mutable slotted root and prove service input preservation by deep-copy assertions | Reproduce frozen/non-frozen behavior, repair model only, rerun all actual Fory tests |
| Optional environment contaminates default validation | Full default tests pass only after extra sync | Separate `UV_PROJECT_ENVIRONMENT=.venv-fory`, cleanup, final default resync/import probe | Delete `.venv-fory`, recreate default `.venv`, rerun full default ladder |
| Bilingual docs imply Fory is safe for untrusted input | Trust warning/command parity test fails | Explicit trust table, no auto-detection warning, matched commands and diagrams | Repair both locales and rerun docs tests/asset inspection together |
| Diagrams drift from implemented order | Asset shows decode/decompress before metadata or omits limits | Generate after source; source-backed audits and full-size PNG review | Edit SVG, rerender PNG, rerun all affected audits before docs completion |

## Remaining External Variables

Git source availability and the native `pyfory` wheel for CPython 3.13 are
external. The workshop pins the provider version and proves the actual isolated
lane; it does not claim availability for other Python implementations or lines.
