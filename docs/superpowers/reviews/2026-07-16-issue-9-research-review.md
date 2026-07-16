# Issue #9 Research Review

Date: 2026-07-16 KST
Branch: `docs/issue-9-asgi-fastapi-boundary`
Base: `develop@a6eae41ed7b946e6859d2cc3d1866a04ea539590`
Scope: Type E research/documentation; no runtime or dependency mutation.

## Result

`P0=0`, `P1=0`. The decision satisfies Issue #9 without claiming an unavailable
adapter. Direct FastAPI is the recommended first realistic HTTP lesson; Raw
ASGI is retained as an advanced protocol exercise; future `bluetape-fastapi`
adoption is gated on upstream #21, #22, and an exact stable release tag or
commit.

## Six-Lens Review

| Lens | Evidence | Result |
|---|---|---|
| Correctness | Primary ASGI lifespan/HTTP and Starlette/FastAPI lifecycle, request, DI, and error sources are linked with retrieval date | PASS |
| Scope | `pyproject.toml` and `uv.lock` unchanged; no Python source or FastAPI dependency added | PASS |
| Ownership | Parsing, DI, context reset, public errors, response shaping, disconnect, timeout, lifespan, and cleanup each name an owner | PASS |
| Learner value | One concrete `POST /orders` scenario, prerequisites, pros/cons, non-goals, and adoption rule are explicit | PASS |
| Locale parity | English/Korean guides have 11 matching level-two headings, 10 matching external URLs, reciprocal navigation, and no missing local links | PASS |
| Visual clarity | Architecture and Sequence PNGs inspected at full size after final render; labels, paths, frames, arrowheads, and whitespace are readable | PASS |

## Diagram Evidence

| Asset | XML/render | Audit evidence | Full-size result |
|---|---|---|---|
| Architecture | CairoSVG `-s 2`, PNG `3600x2100` | `markers=4`, `cards=9`, visible semantic connectors `7`, geometry/endpoint/mixed-corner failures `0` | PASS; four ownership lanes and gated future path are clear |
| Sequence | CairoSVG `-s 2`, PNG `3600x3000` | `markers=6`, `connectors=17`, numbered labels `17`, lifelines `6`, activations `4`, sequence-style PASS, geometry/endpoint/mixed-corner failures `0` | PASS; startup, request branches, context reset, and shutdown remain chronological |

The generic architecture connector audit recognizes one connector class because
semantic colors use four class names. The fallback invariant counts the seven
visible paths whose classes are `flow`, `context`, `lifecycle`, or `future`;
manual full-size inspection confirms all seven endpoints and arrowheads.

Reference images inspected before drawing:

- `/Users/debop/work/bluetape4k/bluetape4k-wiki/docs/diagrams/best-practices/assets/infra-opentelemetry-sequence-01.png`
- `examples/integrated_order_backend/docs/images/sequence.png`
- `examples/integrated_order_backend/docs/images/architecture.png`

## Validation

- Documentation contract: `10 passed`.
- Dependency baseline within full suite: `19 passed`.
- Full deterministic suite: `290 passed, 1 skipped, 1 deselected`.
- Ruff lint: PASS; Ruff format: `66 files already formatted`.
- actionlint: PASS.
- XML, CairoSVG render, diagram audits, local-link scan, URL parity, and
  `git diff --check`: PASS.
- Docker/Testcontainers, optional Fory, benchmark, release/tag, milestone
  closure: N/A by approved research scope.

## Remaining Gate

[PR #19](https://github.com/bluetape4k/bluetape-py-workshop/pull/19) was created
from the approved branch to `develop`. Verify the exact hosted head and current
CI/review/thread state, then stop for fresh merge approval.
