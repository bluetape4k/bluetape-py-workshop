# bluetape-py-workshop

English | [한국어](README.ko.md)

Runnable, application-shaped Python backend examples using
[`bluetape-py`](https://github.com/bluetape4k/bluetape-py).

## Current Status

The repository foundation is runnable: dependency resolution, source provenance,
provider isolation, lint, and tests are locked and automated. Runnable domain
scenarios now include [validated order intake](examples/order_intake/README.md),
[bounded catalog enrichment](examples/catalog_enrichment/README.md), and the
[cached product catalog](examples/cached_product_catalog/README.md), plus
[bounded payload processing](examples/bounded_payload_processing/README.md) with
separate default JSON and optional Apache Fory trust profiles, and a
[Redis test server workshop](examples/redis_test_server/README.md) with explicit
container lifecycle ownership. The
[integrated order backend](examples/integrated_order_backend/README.md) combines
order intake, enrichment, shared caching, bounded JSON payloads, request
deadlines, and retryable shutdown in one realistic two-order scenario. Each
example provides aligned bilingual guidance, Architecture, and Sequence Diagram
assets.

Follow [WIP.md](WIP.md) for the current issue, dependency order, validation
evidence, and next action.

## Milestone 0.1.0 Learning Path

| Order | Issue | Reader outcome | Requires |
|---:|---|---|---|
| 1 | [#2](https://github.com/bluetape4k/bluetape-py-workshop/issues/2) | Reproducible workshop foundation | None |
| 2 | [#3](https://github.com/bluetape4k/bluetape-py-workshop/issues/3) | Validated order intake | #2 |
| 3 | [#4](https://github.com/bluetape4k/bluetape-py-workshop/issues/4) | Bounded catalog enrichment | #2 |
| 4 | [#5](https://github.com/bluetape4k/bluetape-py-workshop/issues/5) | Cached product catalog | #2 |
| 5 | [#6](https://github.com/bluetape4k/bluetape-py-workshop/issues/6) | Bounded payload processing | #2 |
| 6 | [#7](https://github.com/bluetape4k/bluetape-py-workshop/issues/7) | Redis Testcontainers integration | #2 |
| 7 | [#8](https://github.com/bluetape4k/bluetape-py-workshop/issues/8) | Integrated order backend | #3, #4, #5, #6 |

## Requirements

- Python 3.13 or newer; the reference interpreter is Python 3.13.14.
- uv 0.11.28. The project configuration rejects a different uv version.
- Git access to the public `bluetape-py` repository.
- Docker is not required for the deterministic foundation, order-intake,
  catalog-enrichment, cached-product-catalog, or bounded-payload-processing
  lanes, or for the integrated order backend. It is required only for the
  explicitly selected Redis integration and Redis CLI lanes.

## Setup

From the repository root:

```bash
uv sync --locked --python 3.13.14
```

This command creates the environment from the committed lockfile. Committed
local path or editable overrides are not supported.

## Dependency Baseline

All ten focused distributions resolve from the same source tree:

- Repository: <https://github.com/bluetape4k/bluetape-py>
- Workshop source commit: `4b7458f22cea0a9e757b5fbf7f5ff4bc8c23cb9a`
- GitHub Release `v0.1.0` tag commit:
  `596e4898c915b55339521814ae7303953b50f4d2`
- PyPI focused-package publication: **HOLD**

The GitHub Release is not the workshop installation source. The supported path
is the root `uv sync` command using the commit-pinned Git sources in
`pyproject.toml` and `uv.lock`.

The baseline includes `bluetape-core`, `bluetape-logging`, `bluetape-testing`,
`bluetape-async`, `bluetape-collections`, `bluetape-cache`, `bluetape-codec`,
`bluetape-compression`, `bluetape-serde`, and `bluetape-testcontainers`.
Apache Fory and native compression providers remain absent from the default
environment. Importing the Testcontainers wrapper is tested not to contact
Docker or start a container, process, or background thread.

The bounded payload example keeps that baseline intact. Its default JSON lane
runs in the root environment, while its trusted-internal Fory lane installs
`pyfory==1.3.0` only in a disposable `.venv-fory` environment. See the
[bilingual example guide](examples/bounded_payload_processing/README.md) for
the exact run, test, and cleanup commands.

The Redis workshop also preserves the default baseline: deterministic probe,
application, CLI, and documentation tests do not contact Docker. Its explicit
integration lane starts the commit-pinned `bluetape-testcontainers`
`RedisServer`, consumes wrapper-provided connection details, and proves cleanup
after both successful and failing application bodies. See its
[bilingual example guide](examples/redis_test_server/README.md).

The integrated order backend preserves the same baseline and leaves Redis and
Fory as separate optional examples. Its fixed composition root reuses one cache
across two in-memory orders, exposes safe public cache statistics, fixes the
external artifact boundary to untrusted JSON, and owns request/close tasks in
one application lifecycle. See its
[bilingual example guide](examples/integrated_order_backend/README.md).

## Validation

Run the same locked gates used by CI:

```bash
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked pytest -m "not testcontainers"
```

The dependency baseline test can be run on its own:

```bash
uv run --locked pytest tests/test_dependency_baseline.py -q
```

Run the Redis Docker lane sequentially, then run the reader-facing CLI:

```bash
uv run --locked pytest -m testcontainers examples/redis_test_server/tests/test_redis_integration.py -q
uv run --locked python -m examples.redis_test_server
```

Run the deterministic integrated scenario and its focused tests:

```bash
uv run --locked python -m examples.integrated_order_backend
uv run --locked pytest examples/integrated_order_backend/tests -q
```

## Example Documentation Contract

Every runnable example from issue #3 onward provides aligned `README.md` and
`README.ko.md` files with:

1. a business-shaped Scenario and explicit non-goals;
2. a source-backed Architecture diagram and textual ownership explanation;
3. a source-backed Sequence Diagram for the request or lifecycle path;
4. the exact `bluetape-py` distributions and APIs used;
5. prerequisites, working directory, run command, observable result, targeted
   test, cleanup command, and troubleshooting boundary.

The Architecture and Sequence Diagram embeds are mandatory for every example;
an example is incomplete without both visuals in both README locales. Diagram
source and rendered assets are created only after the implementing code exists.
Both locales share the same English-label assets and link back to the relevant
source.

## Current Limits

Milestone `0.1.0` does not introduce an ASGI/FastAPI adapter, a production Redis
provider, persistent order store, authentication/authorization adapter, package
publication, or release automation. The Redis example is test infrastructure,
not a production Redis client or cache provider, and every Docker-backed path
runs sequentially.
