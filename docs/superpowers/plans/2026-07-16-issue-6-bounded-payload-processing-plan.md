# Bounded Payload Processing Implementation Plan

> **Execution mode:** inline main-session execution with TDD checkpoints. Native
> review lanes are bounded and immediately reclaimed if they delay.

**Goal:** Build separate runnable JSON and optional Apache Fory payload services
that expose strict metadata, canonical base64url, bounded gzip decompression,
and fixed trust profiles without payload-driven format selection.

**Architecture:** `JsonPayloadService` is the default untrusted lane.
`ForyPayloadService` lives in an optional module and accepts one fixed
`ForyAdapter[OrderSnapshot]` for authenticated trusted-internal payloads. The
services share immutable models and transport-policy errors only; each owns its
small concrete pipeline and independent expected metadata.

**Tech Stack:** Python 3.13.14, uv 0.11.28, `bluetape-codec`,
`bluetape-compression`, `bluetape-serde`, optional `pyfory==1.3.0`, pytest
8.4.2, Ruff 0.12.12, SVG/CairoSVG.

## Execution Contract

- Repository: `bluetape4k/bluetape-py-workshop`
- Base: `develop` at `51d7e457384ea4f84b7f18afd00a13e939218ef1`
- Head: `feat/issue-6-bounded-payload-processing`
- Worktree: `/Users/debop/work/bluetape4k/bluetape-py-workshop/.worktrees/feat-issue-6-bounded-payload-processing`
- Issue: <https://github.com/bluetape4k/bluetape-py-workshop/issues/6>
- Approved spec: `docs/superpowers/specs/2026-07-16-issue-6-bounded-payload-processing-design.md`
- Spec review: `docs/superpowers/reviews/2026-07-16-issue-6-design-review.md`
- Workflow run: `20260716T065828Z-3fe71fd5`
- Workflow type: Type A
- Heavy-command limit: one repository-wide pytest, actionlint, or optional
  native-provider command at a time; no Docker/Testcontainers runtime.
- Authorized: local edits, Lore commits, non-force push of this head, and PR
  creation into `develop` with issue #6 metadata.
- Excluded: merge, auto-merge, remote branch deletion, tag, release, publish,
  workflow dispatch, milestone closure, native compression extras.
- Stop: exact-head merge-ready report after CI/review, then fresh merge approval.

## File Map

| Path | Responsibility |
|---|---|
| `pyproject.toml`, `uv.lock` | Optional `fory` extra and reproducible provider lock |
| `tests/test_dependency_baseline.py` | Default installed-provider absence plus optional lock contract |
| `examples/bounded_payload_processing/models.py` | Immutable `EncodedPayload` and `OrderSnapshot` |
| `examples/bounded_payload_processing/errors.py` | Unsupported transport and transport-limit errors |
| `examples/bounded_payload_processing/service.py` | Default untrusted JSON service |
| `examples/bounded_payload_processing/fory_service.py` | Optional trusted-internal Fory service |
| `examples/bounded_payload_processing/__init__.py` | Default exports without Fory import |
| `examples/bounded_payload_processing/__main__.py` | Deterministic JSON scenario |
| `examples/bounded_payload_processing/fory_demo.py` | Explicit optional Fory composition root |
| `examples/bounded_payload_processing/tests/` | Default, optional, CLI, import, and docs contracts |
| `examples/bounded_payload_processing/README.md` | English reader path |
| `examples/bounded_payload_processing/README.ko.md` | Equivalent Korean reader path |
| `examples/bounded_payload_processing/docs/images/architecture.*` | Static trust/component view |
| `examples/bounded_payload_processing/docs/images/sequence.*` | Metadata-first encode/decode flow |
| `README.md`, `README.ko.md` | Root example navigation |
| `WIP.md` | Live milestone checkpoint |
| `docs/superpowers/reviews/2026-07-16-issue-6-implementation-review.md` | Final review evidence |
| `docs/superpowers/lessons/2026-07-16-issue-6-payload-trust-boundaries.md` | Required Type A lesson |

No existing example source or CI workflow is modified.

## Acceptance Traceability

| Requirement | Tasks | Proof |
|---|---|---|
| Default install/import excludes Fory | 1, 4, 8 | metadata, isolated import, full default tests |
| Separate fixed JSON/Fory services | 2, 5 | public shape and source/import scan |
| Metadata/transport checks before deserialization | 2, 3, 5 | spies and ordered negative tests |
| Explicit malformed/limit failures | 3, 5 | exact exception tests |
| Round trip and caller input preservation | 2, 3, 5 | equality/deep-copy tests |
| Empty and boundary payloads | 3, 5 | parameterized edge tests |
| Optional real Fory lane on CPython 3.13 | 1, 5, 8 | isolated `.venv-fory` commands |
| Bilingual docs and mandatory diagrams | 6, 7 | docs tests, audits, PNG inspection |
| Full quality, review, lesson, PR/CI | 8 | validation ladder and live exact-head proof |

## Task 1: Lock the Optional Provider Boundary

**Complexity:** Medium  
**Depends on:** approved spec commit `db4e0ac`  
**Patterns:** `test-driven-development`, `bluetape-py-patterns`

**Files:** `pyproject.toml`, `uv.lock`, `tests/test_dependency_baseline.py`

- [ ] Write RED tests requiring project extra `fory = ["bluetape-serde[fory]==0.1.0"]`,
  `pyfory==1.3.0` in the lock, native compression providers absent from the
  lock, and every optional provider absent from default installed metadata.
- [ ] Run `uv run --locked pytest tests/test_dependency_baseline.py -q`; expect
  failure because the extra and lock entry do not exist.
- [ ] Add the optional dependency, run `uv lock --python 3.13.14`, and inspect
  that only the intended provider graph changed.
- [ ] Run `uv sync --locked --python 3.13.14` and the focused dependency test;
  expect GREEN and `pyfory` absent from default installed metadata.
- [ ] Create the isolated optional environment with
  `UV_PROJECT_ENVIRONMENT=.venv-fory uv sync --locked --extra fory --python 3.13.14`
  and prove Python 3.13 plus `pyfory==1.3.0`; do not run service tests yet.

**Rollback/rerun:** Restore the reviewed `pyproject.toml`/`uv.lock` pair and
delete `.venv-fory` if the extra changes any base package source or native
compression provider. Regenerate and rerun the default sync before continuing.

## Task 2: Implement Immutable Contracts and the JSON Happy Path

**Complexity:** Medium  
**Depends on:** Task 1 GREEN  
**Patterns:** `test-driven-development`, `bluetape-py-patterns`

**Files:** package `__init__.py`, `models.py`, `errors.py`, `service.py`, tests

- [ ] Write RED public-shape tests for frozen, slotted, keyword-only
  `EncodedPayload`/`OrderSnapshot`, exact string/metadata validation, exact
  package exports, and absence of `ForyPayloadService` from the default module.
- [ ] Write a RED JSON round-trip test with nested caller input, configured
  limits, fixed JSON metadata, gzip, and canonical unpadded base64url.
- [ ] Run the focused test and record collection/behavior RED.
- [ ] Implement the smallest models/errors/default exports and
  `JsonPayloadService.encode/decode` happy path.
- [ ] Assert output metadata and transport identifiers, decoded equality,
  original deep-copy equality, and that the service retains no caller value.
- [ ] Run focused tests to GREEN and Ruff on the new files.

**Rollback/rerun:** Revert only the current behavior slice if the public shape
requires a registry, adapter protocol, mutable global, or Fory import.

## Task 3: Lock JSON Ordering, Limits, and Failure Types

**Complexity:** High  
**Depends on:** Task 2 GREEN  
**Patterns:** `test-driven-development`, `bluetape-py-patterns`

**Files:** `service.py`, `errors.py`, `tests/test_service.py`

- [ ] Add RED tests for exact metadata format/version/content type/trust
  mismatch and unsupported encoding/compression. Codec and compressor spies
  must show zero calls for every preflight failure.
- [ ] Add RED tests for encoded-size rejection before decode and
  compressed-size rejection before decompress.
- [ ] Add RED tests for malformed/non-canonical base64url, invalid/truncated
  and trailing gzip, decompression limit, invalid UTF-8/JSON, duplicate keys,
  serde input/output/nesting limits, empty JSON values, and exact size boundary.
- [ ] Implement explicit validation order and minimal constructor invariants.
  Preserve upstream exception classes; do not catch/flatten them.
- [ ] Run focused tests to GREEN, then repeat the focused suite three times
  sequentially to detect state leakage.

**Rollback/rerun:** Any test that passes without proving a downstream spy was
not called is repaired before progression. No broad exception assertion counts.

## Task 4: Add the Default CLI and Import-Isolation Proof

**Complexity:** Medium  
**Depends on:** Task 3 GREEN

**Files:** `__main__.py`, `tests/test_application.py`

- [ ] Write RED subprocess tests for deterministic newline-delimited JSON
  events and an isolated `-I` import probe.
- [ ] The probe must fail if `pyfory` or `bluetape.serde.fory` enters
  `sys.modules` after importing the package and running the default CLI.
- [ ] Implement a deterministic JSON scenario that reports fixed profile,
  stage, safe byte counts, round-trip result, and typed expected failures. Never
  emit serialized bytes, encoded text, credentials, or document fields.
- [ ] Run the CLI and focused application tests to GREEN.

**Rollback/rerun:** Remove any default re-export or helper import that crosses
the provider boundary; do not weaken the isolated probe.

## Task 5: Implement the Optional Fory Lane

**Complexity:** High  
**Depends on:** Tasks 1 and 3 GREEN  
**Patterns:** `test-driven-development`, `bluetape-py-patterns`

**Files:** `fory_service.py`, `fory_demo.py`, `tests/test_fory_service.py`

- [ ] Keep default collection safe: the test module checks provider
  availability before importing `bluetape.serde.fory` or `fory_service`.
- [ ] In `.venv-fory`, write RED tests for exact fixed registration, trusted
  metadata, actual `OrderSnapshot` round trip, empty list, caller input
  preservation, encoded/compressed/decompressed/Fory bounds, metadata mismatch,
  malformed input, schema mismatch, and type mismatch.
- [ ] Implement `ForyPayloadService` with the same explicit transport order but
  no shared processor abstraction. Validate gzip/Fory bound compatibility.
- [ ] Implement `fory_demo.py` as the only optional composition root with
  schema/type id `1001` and logical name `workshop.order_snapshot`.
- [ ] Run optional focused tests and CLI in `.venv-fory`; scan default files to
  prove only the three optional files import Fory/provider symbols.
- [ ] Rerun default sync and default import/application tests after optional
  proof; provider isolation must still pass.

**Rollback/rerun:** Delete `.venv-fory`, restore default sync, and keep the
optional lane uncommitted if CPython/provider behavior differs from the pinned
source. Never replace the real provider proof with a fake adapter.

## Task 6: Write Bilingual Documentation and Diagrams

**Complexity:** High  
**Depends on:** Tasks 4 and 5 GREEN  
**Patterns:** `bluetape-writer`, `bluetape-diagram`

**Files:** example README pair, documentation tests, four diagram assets

- [ ] Write RED documentation tests for reciprocal locale navigation,
  scenario/non-goals, trust table, exact default/optional/test/cleanup commands,
  CPython 3.13 gate, provider isolation, unsupported auto-detection, PNG embeds,
  and SVG links.
- [ ] Draft English and natural Korean README files with equivalent technical
  facts and the approved reader path.
- [ ] Architecture asset, one-asset loop: model the two explicit composition
  roots, fixed services, shared immutable envelope, library stages, trust
  boundary, and no automatic selector; XML-validate, render with CairoSVG `-s
  2`, run audits, and inspect full-size PNG.
- [ ] Sequence asset, one-asset loop: model metadata-first decode, encoded and
  compressed limit branches, codec/decompression/serde stages, and separate
  JSON/Fory deserialization; XML-validate, render, run common plus sequence
  audits, and inspect full-size PNG.
- [ ] Embed both PNGs and link both SVGs in both locales. Run documentation
  tests and `git diff --check`.

**Rollback/rerun:** Source behavior is authoritative. Repair SVG then rerender
PNG one asset at a time; never hand-edit PNG or accept SVG-only evidence.

## Task 7: Register Root Navigation and the WIP Checkpoint

**Complexity:** Low  
**Depends on:** Task 6 GREEN

**Files:** `README.md`, `README.ko.md`, `WIP.md`, root docs tests

- [ ] Add equivalent root navigation and command/trust summaries.
- [ ] Update WIP with current commits, commands, validation state, PR boundary,
  and next dependency-ready issue #7.
- [ ] Run root and example documentation contract tests and stale issue-status
  scans.

## Task 8: Converge Validation, Review, Lesson, and PR Delivery

**Complexity:** High  
**Depends on:** Tasks 1–7 GREEN  
**Patterns:** `verification-before-completion`, `requesting-code-review`

- [ ] Run default ladder sequentially:
  `uv sync --locked --python 3.13.14`, dependency tests, focused default tests,
  default CLI, Ruff format/check, full pytest, actionlint 1.7.12, and diff check.
- [ ] Run isolated optional ladder sequentially: sync extra, provider/version
  probe, Fory focused tests, Fory CLI, then delete `.venv-fory` and rerun the
  default import probe.
- [ ] Complete diagram evidence ledgers and full-size PNG inspection after the
  final coordinate change.
- [ ] Verify every spec/plan requirement and repository hazard. Run six-lens
  final review plus main integration; fix and rerun until P0=0/P1=0.
- [ ] Write and commit the required lesson with context, decision, proof,
  misses, and future guard.
- [ ] Commit the converged branch with Lore messages, rerun the full default
  ladder on the exact head, push without force, and verify remote SHA equality.
- [ ] Create/verify the PR into `develop`, assign `debop`, mirror issue #6
  milestone/labels, end the body with `## DoD Status`, wait for exact-head CI,
  reread reviews/threads, and report merge readiness.
- [ ] Stop with `CG-16`, `CG-17`, `CG-18`, and `A-12` pending fresh merge
  approval. Do not enable auto-merge.

## Evidence-Backed N/A

- Async/cancellation/concurrency owned by the workshop service: both services
  are synchronous and create no tasks/threads; Fory pool bounds are upstream
  adapter behavior tested only through the fixed service.
- Database/Docker/Testcontainers: no backend or container path is executed.
- Publishable API, changelog, BOM, release: the example is non-package workshop
  code and the issue excludes release actions.
- HTTP/authentication implementation: the trusted-internal claim is a caller
  precondition and documentation warning; no transport/auth adapter is added.
