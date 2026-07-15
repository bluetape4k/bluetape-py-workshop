# Issue #4 bounded catalog enrichment lessons

## Context

The workshop needed to demonstrate async fan-out without adding an HTTP
framework, retry/cache policy, provider clients, or a workshop-owned concurrency
layer. Required catalog data, optional recommendations, duplicate caller input,
one global concurrency limit, total timeout, and caller cancellation still had
to remain distinguishable and testable.

## Decision

Normalize and bound input before provider work, preserve first-seen IDs with
`distinct`, batch them with `chunked`, and place required and optional jobs in
one ordered list. Submit that list through exactly one `map_bounded` call.
Represent the only expected provider outage with explicit
`ProviderUnavailable`; treat every other provider exception as a defect.

Required `ProviderUnavailable` becomes a safe `RequiredProviderFailure` and,
when every exception-group leaf is required, a `CatalogEnrichmentFailed`.
Optional `ProviderUnavailable` becomes a product-scoped warning. Native
`TimeoutError`, native `CancelledError`, and mixed/unexpected `ExceptionGroup`
values remain unchanged.

## Surprise and failure

### Separate provider pools silently multiply the caller budget

Giving catalog and recommendation work separate `map_bounded` calls would make
a caller limit of two allow four active calls. One combined ordered job list
keeps the limit global. The event-controlled test measures both provider types
with one active counter so a later refactor cannot turn the budget into a
per-provider setting.

### A broad optional fallback hides programming defects

Catching `Exception` around the optional provider makes recommendation data
look resilient while also turning assertions, parsing defects, and adapter bugs
into warnings. Catch only `ProviderUnavailable`. A synchronized mixed-failure
test proves that a required outage plus an optional defect remains the original
`ExceptionGroup` rather than being collapsed into `CatalogEnrichmentFailed`.

### Cleanup ownership must stay with the concurrency primitive

Adding a service semaphore, task registry, or cancellation loop duplicates
`map_bounded` and creates two owners for the same tasks. Event-gated tests prove
that timeout, caller cancellation, and required failure return only after every
managed sibling reaches `finally`, with no `bluetape.map_bounded.*` task left.

### Provider response validation is part of the trust boundary

Static provider protocols do not validate runtime mappings. Required responses
must match the exact requested key set and contain records whose internal ID,
name, and non-boolean non-negative price are valid. Optional extra keys invalidate
the whole optional batch; missing or invalid requested records become stable
per-product warnings. Raw payload values and provider exception details never
enter public messages.

### Independent example tests need package-qualified module names

The second example introduced another `test_service.py` and
`test_application.py`. Pytest's default import mode loaded both directories as
top-level modules and reported import-file mismatches. A global import-mode
change passed tests but changed `pyproject.toml`, violating the approved
dependency-authority checksum. Package markers in each example's `tests`
directory fix the source of the collision while leaving project configuration
and the lockfile byte-identical to `develop`.

### Diagram audits and PNG inspection catch different failures

The first Architecture SVG had rounded-corner coordinates with zero pre-bend
clearance; geometry and endpoint audits rejected them. The first Sequence PNG
passed structural audits but showed crowded badges for messages 10-12. Repair
coordinates, rerender with CairoSVG, rerun every affected audit, and inspect the
final full-size PNG rather than treating SVG validity as visual completion.

## Outcome

Duplicate product IDs share provider calls and reappear in normalized caller
order. Required data fails closed, optional operational outages degrade to safe
warnings, defects stay visible, and timeout/cancellation retain native Python
semantics after task cleanup. The network-free CLI and aligned English/Korean
guides make the behavior runnable without external infrastructure.

## Verification

- Focused catalog-enrichment suite: 34 tests passed.
- Full repository suite: 91 tests passed.
- Ruff check and format check passed.
- actionlint 1.7.12 passed with Go 1.26.1.
- `pyproject.toml` and `uv.lock` SHA-256 values match `origin/develop`.
- Architecture: 2 markers, 8 connectors, 9 cards, 0 intrusions/crossings,
  geometry/endpoint/mixed-corner failures 0, PNG 3200x1800 inspected.
- Sequence: 5 markers, 12 connectors and numbered messages, 0
  intrusions/crossings, geometry/endpoint/mixed-corner/style failures 0, PNG
  3600x2500 inspected.

## Review misses

The plan anticipated lifecycle races and raw-payload leakage, but it did not
anticipate pytest basename collisions after a second independently testable
example. The first README wording also described the allowed character set
without stating that the first character must be alphanumeric. Pre-PR review
corrected both without changing runtime behavior.

## Future guard

For later workshop fan-out examples:

1. put every job that shares a caller budget into one bounded invocation;
2. define an explicit operational exception and never use it for defects;
3. let the concurrency primitive own task creation, cancellation, and cleanup;
4. validate provider mappings and records before aggregation;
5. add `tests/__init__.py` when an example reuses common pytest basenames;
6. keep project/lock authority unchanged unless the approved issue requires a
   dependency or global configuration change;
7. verify SVG structure and full-size PNG semantics as separate gates.
