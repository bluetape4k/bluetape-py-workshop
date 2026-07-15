# bluetape-py-workshop

English | [한국어](README.ko.md)

Runnable, application-shaped Python backend examples using
[`bluetape-py`](https://github.com/bluetape4k/bluetape-py).

## Current Status

The repository foundation is runnable: dependency resolution, source provenance,
provider isolation, lint, and tests are locked and automated. The first runnable
domain scenario is the [validated order intake example](examples/order_intake/README.md),
with aligned bilingual guidance, Architecture, and Sequence Diagram assets.

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
- Docker is not required for the deterministic foundation or order-intake lanes.

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

## Validation

Run the same locked gates used by CI:

```bash
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked pytest
```

The dependency baseline test can be run on its own:

```bash
uv run --locked pytest tests/test_dependency_baseline.py -q
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

Diagram source and rendered assets are created only after the implementing code
exists. Both locales share the same English-label assets and link back to the
relevant source.

## Current Limits

Milestone `0.1.0` does not introduce an ASGI/FastAPI adapter, a production Redis
provider, package publication, or release automation. Docker-backed examples run
sequentially when issue #7 adds them.
