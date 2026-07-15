# Issue #4 Implementation Review

Date: 2026-07-15 KST  
Base: `b40df76bce2c13825c8247a050cfefdcd1e988e8` (`origin/develop`)  
Reviewed implementation head: `3056554e193a8dcea5da218c8ec7185d62f7706f` plus the documented pre-PR corrections below  
Specification: `docs/superpowers/specs/2026-07-15-issue-4-bounded-catalog-enrichment-design.md`  
Plan: `docs/superpowers/plans/2026-07-15-issue-4-bounded-catalog-enrichment-plan.md`

## Scope and Method

The review covered the complete branch diff, public models/errors/protocols,
input normalization, provider response validation, the single global
`map_bounded` invocation, timeout/cancellation behavior, deterministic CLI,
bilingual documentation, and both diagram source/render pairs.

Two bounded native review lanes were started for performance/stability and
security/Ops. Neither returned inside the 30-second window, so both were
interrupted immediately and their scopes were rerun in the main session. The
developer/API and user/caller scopes were reviewed in the main session from the
start. No child result was treated as evidence without local verification.

## Validation Evidence

| Gate | Evidence | Result |
|---|---|---|
| Locked environment | `uv sync --locked --python 3.13.14` | 30 packages resolved; 27 checked |
| Runnable output | `uv run --locked python -m examples.catalog_enrichment` | deterministic `SKU-2`, `SKU-1`, `SKU-2` JSON; duplicate results equal; optional warning present |
| Focused example | `uv run --locked pytest examples/catalog_enrichment/tests -q` | 34 passed |
| Dependency baseline | `uv run --locked pytest tests/test_dependency_baseline.py -q` | 18 passed |
| Formatting | `uv run --locked ruff format --check .` | 22 files formatted after package-marker correction |
| Static checks | `uv run --locked ruff check .` | all checks passed |
| Repository suite | `uv run --locked pytest` | 91 passed |
| Workflow lint | `GOTOOLCHAIN=go1.26.1 go run github.com/rhysd/actionlint/cmd/actionlint@v1.7.12 .github/workflows/ci.yml` | exit 0 |
| Diff hygiene | `git diff --check origin/develop` | exit 0 after removing plan-only trailing whitespace found by the complete branch check |
| Dependency authority | SHA-256 of `pyproject.toml` and `uv.lock` compared with `origin/develop` | both pairs identical after correction |
| Docker/Testcontainers | Example imports neither provider and starts no external resource | N/A by design |

The first full-suite run exposed duplicate pytest module basenames across two
non-package `tests` directories. A global pytest import-mode change fixed the
symptom but changed `pyproject.toml`, violating the approved unchanged-authority
gate. The final correction restores `pyproject.toml` byte-for-byte and adds
package markers to the two example test directories. The full 91-test suite
passes with default pytest import behavior.

## Diagram Evidence

| Asset | XML / Render | Structural audits | Full-size inspection |
|---|---|---|---|
| `examples/catalog_enrichment/docs/images/architecture.svg` / `.png` | `xmllint` PASS; CairoSVG scale 2; PNG 3200x1800 | markers=2, connectors=8, cards=9, intrusions=0, crossings=0, geometry failures=0, endpoint PASS, mixed-corner paths=8/q_bends=6/failures=0 | labels, arrowheads, ownership lanes, margins, and card spacing readable |
| `examples/catalog_enrichment/docs/images/sequence.svg` / `.png` | `xmllint` PASS; CairoSVG scale 2; PNG 3600x2500 | markers=5, connectors=12, intrusions=0, crossings=0, geometry failures=0, endpoint PASS, mixed-corner paths=12/q_bends=2/failures=0, sequence-style PASS | six participants, 12 numbered messages, transparent three-branch frame, role colors, labels, and cleanup path readable |

Reference family:

- repo-local architecture and sequence:
  `examples/order_intake/docs/images/architecture.png` and
  `examples/order_intake/docs/images/sequence.png`;
- adjacent best-practices sequence:
  `/Users/debop/work/bluetape4k/exposed-r2dbc-workshop/docs/images/readme-diagrams/05-exposed-r2dbc-dml-04-transactions-sequence-01.png`.

Infrastructure icons are N/A: every node is an application object, library API,
or injected protocol rather than a real server, database, queue, cache, or
managed service. No local review page exists.

## Six-Lens Review

### Performance

- `service.py:54-75` stops before accepting occurrence 1,001, so normalization
  cannot consume an unbounded iterable.
- `service.py:142-148` deduplicates before batching and builds one required plus
  one optional job per unique batch.
- `service.py:150-156` calls `map_bounded` once, preventing separate provider
  pools from multiplying the caller's limit.
- `test_service.py:183-196` proves first-seen deduplication and occurrence-order
  restoration; `test_service.py:356-377` proves the combined active-call count
  never exceeds two.

Result: P0=0, P1=0. No benchmark is required for a bounded deterministic
workshop example; the explicit 1,000-occurrence, 100-item batch, and 1,024-task
limits cap the relevant work.

### Stability

- `service.py:157-167` translates only all-required failure groups; mixed
  unexpected defects remain visible.
- `service.py:198-243` catches only `ProviderUnavailable` and validates every
  required response fail-closed.
- `test_service.py:380-411` proves native timeout/cancellation and completed
  sibling cleanup; `test_service.py:414-477` proves required-outage cleanup and
  mixed-failure propagation.
- Test synchronization uses events and only 1-second assertion guards; the sole
  behavior probe timeout is 0.01 seconds.

Result: P0=0, P1=0.

### Security

- `service.py:54-75` validates type, blank input, raw ASCII, length, and the
  product-ID grammar before provider calls.
- `service.py:87-105` rejects mismatched IDs, blank text, boolean prices, and
  negative prices.
- `errors.py:19-35` and `service.py:213-243` expose stable codes/messages without
  serializing provider exception details or invalid payload values.
- Tests inject `secret-provider-detail` and `secret-extra` and prove neither
  appears in public output.

Result: P0=0, P1=0.

### Operator / Ops

- `__main__.py` uses immutable in-memory mappings and no network, environment,
  clock, random, thread, process, or global logger state.
- `README.md` and `README.ko.md` state the input, batch, concurrency, timeout,
  provider trust, telemetry, cleanup, source, and unsupported-production
  boundaries.
- The example deliberately emits no operational telemetry; a real adapter owns
  safe IDs and aggregates. This is a documented non-production boundary, not a
  hidden omission.

Result: P0=0, P1=0.

### Developer / API

- Public values are frozen, slotted, keyword-only records; provider interfaces
  are narrow async protocols.
- Public errors carry only bounded index/code metadata. `TimeoutError`,
  `CancelledError`, and unexpected `ExceptionGroup` remain distinguishable.
- The constructor checks for callable `fetch` methods exactly as approved; full
  async correctness remains the injected adapter's protocol responsibility.
- One documentation imprecision allowed punctuation as the first ID character;
  both locales now state that the first character must be `[A-Z0-9]`.

Result: P0=0, P1=0. P2=0 after the documentation correction.

### User / Caller

- Duplicate results retain caller-visible order and count without mutating the
  caller list.
- Optional outages and invalid optional data return per-product safe warnings;
  required invalid data fails the request.
- Both locales share the same scenario, architecture, sequence, limits,
  commands, expected JSON semantics, failure table, troubleshooting, and source
  links. Root README navigation points to the matching locale.

Result: P0=0, P1=0.

## Main Integration Review

- The implementation stays under `examples/catalog_enrichment`; no reusable
  workshop utility or framework adapter was introduced.
- `pyproject.toml` and `uv.lock` match `origin/develop` byte-for-byte.
- The test package markers solve cross-example collection without changing
  project-wide pytest semantics.
- Root status and WIP remain aligned with the milestone dependency order and the
  separate exact-head merge approval gate.

## Final Finding Count

| Severity | Open | Resolved during review |
|---|---:|---:|
| P0 | 0 | 0 |
| P1 | 0 | 0 |
| P2 | 0 | 2 |

Resolved P2 items:

1. pytest basename collision across independent example test directories;
2. README product-ID grammar omitted the stricter first-character rule.

Final review result: **P0=0, P1=0, P2=0**. The implementation can proceed to
the durable lesson and exact-head pre-PR checkpoint.
