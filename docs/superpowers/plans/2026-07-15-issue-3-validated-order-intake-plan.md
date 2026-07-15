# Issue #3 Validated Order Intake Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a runnable, framework-neutral order intake example that combines pinned `bluetape-core`, `bluetape-logging`, and `bluetape-testing` contracts with immutable application models, explicit failure mapping, isolated contextual logs, bilingual guidance, and source-backed diagrams.

**Architecture:** `examples/order_intake` is one small importable application package. Frozen input/output models and a stable error mapper surround an `OrderIntakeService` that validates caller values, scopes non-secret correlation identifiers with `log_context`, writes only to an injected direct logger, and returns without retaining mutable caller state. A standard-library entrypoint owns logger configuration and produces deterministic JSON.

**Tech Stack:** Python 3.13.14, uv 0.11.28, pinned bluetape-py commit `4b7458f22cea0a9e757b5fbf7f5ff4bc8c23cb9a`, pytest, Ruff, stdlib `dataclasses`/`logging`/`json`, CairoSVG, bluetape diagram audit scripts.

---

## Scope and file ownership

| File | Responsibility | Write task |
|---|---|---:|
| `examples/order_intake/__init__.py` | Stable example import surface | 1, 2 |
| `examples/order_intake/models.py` | Frozen command and accepted result | 1 |
| `examples/order_intake/errors.py` | Public exception and immutable problem mapping | 1 |
| `examples/order_intake/service.py` | Validation, safe context, isolated logging, immutable projection | 2 |
| `examples/order_intake/__main__.py` | Direct logger ownership and deterministic runnable sample | 3 |
| `examples/order_intake/tests/test_service.py` | Success, invalid, boundary, mutation, context, logging, API demonstration | 1, 2 |
| `examples/order_intake/tests/test_application.py` | Subprocess runnable-output contract | 3 |
| `pyproject.toml` | Include `examples` in configured pytest discovery | 3 |
| `examples/order_intake/README.md` | English scenario, architecture, sequence, APIs, commands, limits | 4 |
| `examples/order_intake/README.ko.md` | Natural Korean equivalent of the example contract | 4 |
| `examples/order_intake/tests/test_documentation.py` | Locale, command, link, and asset parity | 4 |
| `examples/order_intake/docs/images/architecture.svg` | Static ownership/responsibility source | 4 |
| `examples/order_intake/docs/images/architecture.png` | Authoritative rendered architecture image | 4 |
| `examples/order_intake/docs/images/sequence.svg` | Success/failure/reset time-flow source | 4 |
| `examples/order_intake/docs/images/sequence.png` | Authoritative rendered sequence image | 4 |
| `README.md` | English root navigation to the runnable example | 4 |
| `README.ko.md` | Korean root navigation parity | 4 |
| `tests/test_documentation_contract.py` | Root navigation and current WIP state contract | 4 |
| `WIP.md` | Resume checkpoint, validation evidence, PR boundary | 4, 5 |
| `docs/superpowers/reviews/2026-07-15-issue-3-implementation-review.md` | Final Type A six-lens review evidence | 5 |
| `docs/superpowers/lessons/2026-07-15-issue-3-order-intake.md` | Reusable outcome and guardrails | 5 |

Tasks 1–4 are sequential because later work imports the contracts and source
created earlier. Diagram files are created only after the implementing source
exists. No task changes `uv.lock`, dependencies, CI workflow, package
publication metadata, Docker state, or a global logger.

## Acceptance mapping

| Spec/issue criterion | Implementing task | Proof command |
|---|---:|---|
| Immutable accepted result without caller mutation | 1, 2 | `uv run --locked pytest examples/order_intake/tests/test_service.py -q` |
| Explicit public exception and application error mapping | 1, 2 | focused service tests |
| Blank, invalid, empty, bool, zero, and negative values rejected | 2 | parametrized service tests |
| Context present and reset on success/failure/logger failure | 2 | focused context/logging tests |
| No coercion of hostile invalid identifiers | 2 | `test_invalid_identifier_is_not_rendered_for_context` |
| Application-owned log capture without global mutation | 2, 3 | handler/root-state tests and subprocess test |
| `eventually` taught without fake synchronization | 2 | isolated API-demonstration test |
| Runnable deterministic JSON example | 3 | `uv run --locked python -m examples.order_intake` and application test |
| Root pytest collects example tests | 3 | `uv run --locked pytest --collect-only -q` |
| Equivalent README locales and root navigation | 4 | example and root documentation contract tests |
| Source-backed Architecture and Sequence Diagram | 4 | XML/render/audit/full-size inspection ledger |
| Full repository quality gates | 5 | locked Ruff, full pytest, diff check |
| Exact-head PR delivery | 5 | remote SHA, live PR metadata/body, CI/review evidence |

## Conditional scope decisions

- Async/cancellation/concurrency: `N/A`; the service creates no coroutine,
  task, timer, thread, socket, process, or blocking external call.
- Testcontainers/real backend: `N/A`; no Docker-backed API or external provider
  is imported by the example.
- Packaging build and lock refresh: `N/A`; the root remains `package = false`,
  no distribution/namespace/dependency/source changes, and `uv.lock` must stay
  byte-identical.
- Database/cache/HTTP/ASGI migration: `N/A`; the public boundary is an in-process
  application service with no adapter.
- Performance benchmark: `N/A`; validation and logging are bounded O(1) work
  over five scalar fields with no collection growth or external round trip.
- Changelog/release/tag/milestone closure: `N/A`; issue #3 delivers an example
  PR only and does not publish version `0.1.0`.
- Cleanup/deslop pass: conditional; run only if the implemented diff introduces
  duplicated helpers, generated verbosity, or files that exceed the focused
  responsibilities above.

## Risk prediction

Step 3-P is triggered by the public error boundary, contextual logging state,
untrusted runtime values, and generated visual artifacts.

| Risk | Early signal | Mitigation | Rollback/rerun point |
|---|---|---|---|
| Invalid object executes `str`/`repr` during context setup | sentinel conversion method is called | type-check identifiers only; dedicated hostile-object test | revert `service.py` context helper and rerun Task 2 RED/GREEN |
| `ContextVar` state leaks after failure | `get_log_context()` is non-empty | keep one `with log_context(...)` boundary around validation and logging | revert service change and rerun all Task 2 lifecycle tests |
| INFO event is silently disabled or propagates globally | captured record missing or root handler receives it | explicit logger/handler INFO levels and `propagate = False` | revert entrypoint/logger fixture and rerun Tasks 2–3 |
| Validation catches logger failure as invalid input | chained public exception points to handler error | catch only validation failures; let logger exceptions propagate | restore narrow catch boundary and rerun logger-failure test |
| Root CI omits example tests | collect-only output lacks example test nodes | extend pytest `testpaths` to `tests` and `examples` | revert only after moving equivalent tests under root, then rerun full collection |
| README or diagrams claim behavior not in source | participant/message/API token has no source anchor | create visuals after code, documentation contract links every artifact | return to Task 4 source ledger and regenerate one asset at a time |
| Binary PNG drifts from SVG | dimensions/labels differ after render | CairoSVG scale 2 is authoritative; inspect final PNG after last SVG edit | discard PNG, rerender from canonical SVG, rerun audits |

### Task 1: Add immutable public models and error mapping with TDD

**Complexity:** Medium
**Dependencies:** Approved and reviewed written spec
**Required skills:** `test-driven-development`, `bluetape-py-patterns`
**Files:**
- Create: `examples/order_intake/__init__.py`
- Create: `examples/order_intake/models.py`
- Create: `examples/order_intake/errors.py`
- Create: `examples/order_intake/tests/test_service.py`

- [ ] **Step 1: Write failing model and error contract tests**

Create `examples/order_intake/tests/test_service.py`:

```python
import importlib
from dataclasses import FrozenInstanceError
from types import ModuleType

import pytest


def _load_api() -> ModuleType:
    try:
        return importlib.import_module("examples.order_intake")
    except ModuleNotFoundError as error:
        pytest.fail(f"order intake API is missing: {error}")


def test_command_and_result_are_immutable_values() -> None:
    api = _load_api()
    command = api.PartnerOrderCommand(
        request_id="req-1",
        partner_id="partner-1",
        order_id="order-1",
        sku="sku-1",
        quantity=2,
    )
    accepted = api.AcceptedOrder(
        request_id="req-1",
        partner_id="partner-1",
        order_id="order-1",
        sku="sku-1",
        quantity=2,
    )

    assert accepted.status == "accepted"
    with pytest.raises(FrozenInstanceError):
        command.quantity = 3  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        accepted.status = "rejected"  # type: ignore[misc]


def test_invalid_order_maps_to_a_safe_immutable_problem() -> None:
    api = _load_api()
    error = api.InvalidOrderCommand("sku", "must not be blank")

    assert str(error) == "sku: must not be blank"
    assert api.map_order_error(error) == api.OrderIntakeProblem(
        code="invalid_order_command",
        field="sku",
        message="sku must not be blank",
    )
    with pytest.raises(FrozenInstanceError):
        api.map_order_error(error).field = "other"  # type: ignore[misc]
```

- [ ] **Step 2: Run the focused test and observe RED**

Run:

```bash
uv run --locked pytest examples/order_intake/tests/test_service.py -q
```

Expected: both tests fail with the explicit assertion
`order intake API is missing`; pytest collection itself succeeds.

- [ ] **Step 3: Implement the minimal frozen models**

Create `examples/order_intake/models.py`:

```python
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True, slots=True, kw_only=True)
class PartnerOrderCommand:
    request_id: str
    partner_id: str
    order_id: str
    sku: str
    quantity: int


@dataclass(frozen=True, slots=True, kw_only=True)
class AcceptedOrder:
    request_id: str
    partner_id: str
    order_id: str
    sku: str
    quantity: int
    status: Literal["accepted"] = "accepted"
```

- [ ] **Step 4: Implement the safe public error mapping**

Create `examples/order_intake/errors.py`:

```python
from dataclasses import dataclass
from typing import Literal


class InvalidOrderCommand(ValueError):
    def __init__(self, field: str, reason: str) -> None:
        self.field = field
        self.reason = reason
        super().__init__(f"{field}: {reason}")


@dataclass(frozen=True, slots=True, kw_only=True)
class OrderIntakeProblem:
    code: Literal["invalid_order_command"]
    field: str
    message: str


def map_order_error(error: InvalidOrderCommand) -> OrderIntakeProblem:
    return OrderIntakeProblem(
        code="invalid_order_command",
        field=error.field,
        message=f"{error.field} {error.reason}",
    )
```

Create `examples/order_intake/__init__.py` with the initial import surface:

```python
from .errors import InvalidOrderCommand, OrderIntakeProblem, map_order_error
from .models import AcceptedOrder, PartnerOrderCommand

__all__ = [
    "AcceptedOrder",
    "InvalidOrderCommand",
    "OrderIntakeProblem",
    "PartnerOrderCommand",
    "map_order_error",
]
```

- [ ] **Step 5: Run focused tests and Ruff and observe GREEN**

Run:

```bash
uv run --locked pytest examples/order_intake/tests/test_service.py -q
uv run --locked ruff check examples/order_intake
uv run --locked ruff format --check examples/order_intake
```

Expected: 2 tests pass and Ruff reports no changes or findings.

- [ ] **Step 6: Commit the immutable boundary**

Stage the four Task 1 files and commit with Lore trailers. The intent line is
`Make order acceptance preserve caller-owned values` and `Tested:` records the
focused pytest and Ruff results.

### Task 2: Implement validation, safe context, and application-owned logging with TDD

**Complexity:** High
**Dependencies:** Task 1 GREEN
**Required skills:** `test-driven-development`, `bluetape-py-patterns`
**Files:**
- Modify: `examples/order_intake/tests/test_service.py`
- Create: `examples/order_intake/service.py`
- Modify: `examples/order_intake/__init__.py`

- [ ] **Step 1: Add failing success, validation, lifecycle, and isolation tests**

Extend `test_service.py` with a direct capture handler, a logger factory, and
these exact behaviors:

```python
import logging
from dataclasses import replace

from bluetape.logging import ContextLogFilter, get_log_context
from bluetape.testing import eventually

class CaptureHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__(logging.INFO)
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


@pytest.fixture
def log_capture():
    root = logging.getLogger()
    root_before = (root.level, tuple(root.handlers), tuple(root.filters))
    logger = logging.Logger("order-intake-test", level=logging.INFO)
    logger.propagate = False
    handler = CaptureHandler()
    handler.addFilter(ContextLogFilter())
    logger.addHandler(handler)
    try:
        yield logger, handler
    finally:
        logger.removeHandler(handler)
        handler.close()
        assert (root.level, tuple(root.handlers), tuple(root.filters)) == root_before


def valid_command():
    return _load_api().PartnerOrderCommand(
        request_id=" req-1 ",
        partner_id="partner-1",
        order_id="order-1",
        sku=" sku-1 ",
        quantity=2,
    )


def make_service(logger: object):
    service_type = getattr(_load_api(), "OrderIntakeService", None)
    assert service_type is not None, "OrderIntakeService is not exported"
    return service_type(logger)


def test_accept_preserves_values_and_captures_context(log_capture) -> None:
    logger, handler = log_capture
    command = valid_command()

    result = make_service(logger).accept(command)

    assert result == _load_api().AcceptedOrder(
        request_id=" req-1 ",
        partner_id="partner-1",
        order_id="order-1",
        sku=" sku-1 ",
        quantity=2,
    )
    assert command == valid_command()
    assert handler.records[-1].getMessage() == "order_intake.accepted"
    assert handler.records[-1].request_id == " req-1 "
    assert handler.records[-1].partner_id == "partner-1"
    assert handler.records[-1].order_id == "order-1"
    assert "sku" not in handler.records[-1].__dict__
    assert "quantity" not in handler.records[-1].__dict__
    assert "sku-1" not in handler.records[-1].getMessage()
    assert get_log_context() == {}


@pytest.mark.parametrize("field", ["request_id", "partner_id", "order_id", "sku"])
@pytest.mark.parametrize("value", ["", "   "])
def test_blank_text_is_rejected(field: str, value: str, log_capture) -> None:
    logger, handler = log_capture
    with pytest.raises(InvalidOrderCommand) as raised:
        make_service(logger).accept(replace(valid_command(), **{field: value}))
    assert raised.value.field == field
    assert isinstance(raised.value.__cause__, ValueError)
    assert handler.records[-1].getMessage() == "order_intake.rejected"
    assert handler.records[-1].error_field == field
    assert get_log_context() == {}


@pytest.mark.parametrize("field", ["request_id", "partner_id", "order_id", "sku"])
def test_non_string_text_is_rejected(field: str, log_capture) -> None:
    logger, _ = log_capture
    with pytest.raises(InvalidOrderCommand) as raised:
        make_service(logger).accept(replace(valid_command(), **{field: 7}))
    assert raised.value.field == field
    assert isinstance(raised.value.__cause__, TypeError)
    assert get_log_context() == {}


@pytest.mark.parametrize("quantity", [True, False, 1.5, "2", None, 0, -1])
def test_invalid_quantity_is_rejected(quantity: object, log_capture) -> None:
    logger, _ = log_capture
    with pytest.raises(InvalidOrderCommand) as raised:
        make_service(logger).accept(replace(valid_command(), quantity=quantity))
    assert raised.value.field == "quantity"
    assert isinstance(raised.value.__cause__, (TypeError, ValueError))
    assert get_log_context() == {}


def test_invalid_command_type_is_mapped(log_capture) -> None:
    logger, _ = log_capture
    with pytest.raises(InvalidOrderCommand) as raised:
        make_service(logger).accept(object())  # type: ignore[arg-type]
    assert raised.value.field == "command"
    assert isinstance(raised.value.__cause__, TypeError)


def test_service_requires_a_real_logger() -> None:
    with pytest.raises(TypeError, match="logger must be Logger"):
        make_service(object())  # type: ignore[arg-type]


def test_invalid_identifier_is_not_rendered_for_context(log_capture) -> None:
    class HostileValue:
        def __str__(self) -> str:
            raise AssertionError("str called")

        def __repr__(self) -> str:
            raise AssertionError("repr called")

    logger, handler = log_capture
    command = replace(valid_command(), request_id=HostileValue())
    with pytest.raises(InvalidOrderCommand):
        make_service(logger).accept(command)
    assert handler.records[-1].request_id == "<invalid>"


def test_root_logger_state_is_unchanged(log_capture) -> None:
    logger, _ = log_capture
    make_service(logger).accept(valid_command())


def test_eventually_api_demo_observes_an_existing_record(log_capture) -> None:
    logger, handler = log_capture
    make_service(logger).accept(valid_command())
    record = eventually(
        lambda: next((item for item in handler.records if item.msg == "order_intake.accepted"), None),
        timeout=0.02,
        interval=0.001,
    )
    assert record is handler.records[-1]


def test_logger_failure_propagates_and_context_resets() -> None:
    class FailingHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            raise RuntimeError("logging unavailable")

    logger = logging.Logger("order-intake-failure", level=logging.INFO)
    logger.propagate = False
    handler = FailingHandler()
    logger.addHandler(handler)
    try:
        with pytest.raises(RuntimeError, match="logging unavailable"):
            make_service(logger).accept(valid_command())
    finally:
        logger.removeHandler(handler)
        handler.close()
    assert get_log_context() == {}
```

- [ ] **Step 2: Run the expanded tests and observe RED**

Run `uv run --locked pytest examples/order_intake/tests/test_service.py -q`.

Expected: collection fails because `OrderIntakeService` is not exported.

- [ ] **Step 3: Implement the minimal service**

Create `examples/order_intake/service.py`:

```python
import logging

from bluetape.core import require_instance, require_not_blank
from bluetape.logging import log_context

from .errors import InvalidOrderCommand
from .models import AcceptedOrder, PartnerOrderCommand

INVALID_CONTEXT_VALUE = "<invalid>"


def _safe_identifier(value: object) -> str:
    return value if isinstance(value, str) else INVALID_CONTEXT_VALUE


def _safe_context(command: object) -> dict[str, str]:
    if not isinstance(command, PartnerOrderCommand):
        return {
            "request_id": INVALID_CONTEXT_VALUE,
            "partner_id": INVALID_CONTEXT_VALUE,
            "order_id": INVALID_CONTEXT_VALUE,
        }
    return {
        "request_id": _safe_identifier(command.request_id),
        "partner_id": _safe_identifier(command.partner_id),
        "order_id": _safe_identifier(command.order_id),
    }


def _validated_text(value: object, field: str) -> str:
    try:
        return require_not_blank(require_instance(value, str, field), field)
    except TypeError as error:
        raise InvalidOrderCommand(field, "must be text") from error
    except ValueError as error:
        raise InvalidOrderCommand(field, "must not be blank") from error


def _validated_quantity(value: object) -> int:
    if isinstance(value, bool):
        error = TypeError("quantity must be int")
        raise InvalidOrderCommand("quantity", "must be an integer") from error
    try:
        quantity = require_instance(value, int, "quantity")
    except TypeError as error:
        raise InvalidOrderCommand("quantity", "must be an integer") from error
    if quantity <= 0:
        error = ValueError("quantity must be greater than 0")
        raise InvalidOrderCommand("quantity", "must be greater than 0") from error
    return quantity


class OrderIntakeService:
    def __init__(self, logger: logging.Logger) -> None:
        self._logger = require_instance(logger, logging.Logger, "logger")

    def accept(self, command: PartnerOrderCommand) -> AcceptedOrder:
        with log_context(**_safe_context(command)):
            try:
                typed = require_instance(command, PartnerOrderCommand, "command")
                request_id = _validated_text(typed.request_id, "request_id")
                partner_id = _validated_text(typed.partner_id, "partner_id")
                order_id = _validated_text(typed.order_id, "order_id")
                sku = _validated_text(typed.sku, "sku")
                quantity = _validated_quantity(typed.quantity)
            except InvalidOrderCommand as error:
                self._logger.warning(
                    "order_intake.rejected",
                    extra={"error_field": error.field},
                )
                raise
            except TypeError as error:
                mapped = InvalidOrderCommand("command", "must be PartnerOrderCommand")
                self._logger.warning(
                    "order_intake.rejected",
                    extra={"error_field": mapped.field},
                )
                raise mapped from error

            result = AcceptedOrder(
                request_id=request_id,
                partner_id=partner_id,
                order_id=order_id,
                sku=sku,
                quantity=quantity,
            )
            self._logger.info("order_intake.accepted")
            return result
```

Add `OrderIntakeService` to `examples/order_intake/__init__.py` imports and
`__all__`.

- [ ] **Step 4: Run service tests, inspect failure causes, and observe GREEN**

Run:

```bash
uv run --locked pytest examples/order_intake/tests/test_service.py -q
uv run --locked ruff check examples/order_intake
uv run --locked ruff format --check examples/order_intake
```

Expected: all model, validation, lifecycle, isolation, hostile-input, logger
failure, and `eventually` demonstration tests pass.

- [ ] **Step 5: Commit the validated service**

Stage `service.py`, the updated exports, and service tests. Use intent line
`Keep validation context local to one order intake call`; record the exact test
count in `Tested:` and the absence of async/external-resource tests in
`Not-tested:`.

### Task 3: Add the deterministic runnable entrypoint and root test discovery

**Complexity:** Medium
**Dependencies:** Task 2 GREEN
**Required skills:** `test-driven-development`, `bluetape-py-patterns`
**Files:**
- Create: `examples/order_intake/tests/test_application.py`
- Create: `examples/order_intake/__main__.py`
- Modify: `pyproject.toml`

- [ ] **Step 1: Write the failing subprocess contract**

Create `examples/order_intake/tests/test_application.py`:

```python
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_runnable_module_emits_contextual_log_and_deterministic_json() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "examples.order_intake"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == {
        "order_id": "order-1001",
        "partner_id": "partner-acme",
        "quantity": 2,
        "request_id": "request-1001",
        "sku": "SKU-BLUE-42",
        "status": "accepted",
    }
    assert "order_intake.accepted" in completed.stderr
    assert "request_id=request-1001" in completed.stderr
    assert "partner_id=partner-acme" in completed.stderr
    assert "order_id=order-1001" in completed.stderr
```

- [ ] **Step 2: Run the application test and observe RED**

Run `uv run --locked pytest examples/order_intake/tests/test_application.py -q`.

Expected: subprocess fails because `examples.order_intake.__main__` is absent.

- [ ] **Step 3: Implement the direct-logger entrypoint**

Create `examples/order_intake/__main__.py`:

```python
import json
import logging
from dataclasses import asdict

from bluetape.logging import ContextLogFilter

from .models import PartnerOrderCommand
from .service import OrderIntakeService


def main() -> None:
    logger = logging.Logger("order-intake-example", level=logging.INFO)
    logger.propagate = False
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    handler.addFilter(ContextLogFilter())
    handler.setFormatter(
        logging.Formatter(
            "%(levelname)s %(message)s request_id=%(request_id)s "
            "partner_id=%(partner_id)s order_id=%(order_id)s"
        )
    )
    logger.addHandler(handler)
    try:
        result = OrderIntakeService(logger).accept(
            PartnerOrderCommand(
                request_id="request-1001",
                partner_id="partner-acme",
                order_id="order-1001",
                sku="SKU-BLUE-42",
                quantity=2,
            )
        )
        print(json.dumps(asdict(result), sort_keys=True))
    finally:
        logger.removeHandler(handler)
        handler.close()


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Include example tests in configured full-suite discovery**

Change only the pytest path line in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests", "examples"]
addopts = "-ra"
asyncio_mode = "auto"
```

Do not regenerate `uv.lock`; assert `git diff --exit-code -- uv.lock`.

- [ ] **Step 5: Prove the runnable and collection contracts**

Run:

```bash
uv run --locked python -m examples.order_intake
uv run --locked pytest examples/order_intake/tests/test_application.py -q
uv run --locked pytest --collect-only -q
git diff --exit-code -- uv.lock
```

Expected: stderr contains one contextual INFO record, stdout contains the
documented JSON, the application test passes, collect-only lists all root and
example tests, and `uv.lock` is unchanged.

- [ ] **Step 6: Commit the runnable example**

Stage `__main__.py`, `test_application.py`, and `pyproject.toml`. Use intent
line `Make the first workshop service runnable without framework state` and
record runnable, collection, and unchanged-lock evidence.

### Task 4: Add bilingual guidance and source-backed diagrams test-first

**Complexity:** High
**Dependencies:** Task 3 source and behavior GREEN
**Required skills:** `bluetape-writer`, `bluetape-diagram` with `common.md`, `architecture.md`, and `sequence.md`
**Files:**
- Create: `examples/order_intake/tests/test_documentation.py`
- Create: `examples/order_intake/README.md`
- Create: `examples/order_intake/README.ko.md`
- Create: `examples/order_intake/docs/images/architecture.svg`
- Create: `examples/order_intake/docs/images/architecture.png`
- Create: `examples/order_intake/docs/images/sequence.svg`
- Create: `examples/order_intake/docs/images/sequence.png`
- Modify: `README.md`
- Modify: `README.ko.md`
- Modify: `tests/test_documentation_contract.py`
- Modify: `WIP.md`

- [ ] **Step 1: Write the failing documentation parity contract**

Create `examples/order_intake/tests/test_documentation.py` to read both locale
files and assert reciprocal navigation plus these shared tokens:

```python
from pathlib import Path

EXAMPLE = Path(__file__).resolve().parents[1]
ENGLISH = (EXAMPLE / "README.md").read_text(encoding="utf-8")
KOREAN = (EXAMPLE / "README.ko.md").read_text(encoding="utf-8")

COMMON = (
    "Scenario",
    "Architecture",
    "Sequence Diagram",
    "bluetape-core",
    "bluetape-logging",
    "bluetape-testing",
    "python -m examples.order_intake",
    "pytest examples/order_intake/tests -q",
    "architecture.png",
    "architecture.svg",
    "sequence.png",
    "sequence.svg",
    "service.py",
)


def test_locale_navigation_and_shared_contract() -> None:
    assert "English | [한국어](README.ko.md)" in ENGLISH
    assert "[English](README.md) | 한국어" in KOREAN
    for token in COMMON:
        assert token in ENGLISH
        assert token in KOREAN


def test_diagram_sources_and_renders_exist() -> None:
    for name in ("architecture.svg", "architecture.png", "sequence.svg", "sequence.png"):
        assert (EXAMPLE / "docs" / "images" / name).is_file()
```

Update the root documentation contract so it expects issue #3 as the current
WIP target, requires both locale files to link
`examples/order_intake/README.md` or its Korean peer, and no longer expects the
obsolete `Issue #2`/`In progress` checkpoint. Replace the current WIP assertion
and add the navigation assertion with this exact code:

```python
def test_wip_keeps_the_dependency_order_and_current_issue() -> None:
    positions = [
        WIP.index(f"| {order} | [#{issue}]")
        for order, issue in enumerate(range(2, 9), start=1)
    ]
    assert positions == sorted(positions)
    assert "Issue [#3]" in WIP
    assert "Validated order intake service" in WIP


def test_readme_pair_links_the_first_runnable_example() -> None:
    assert "examples/order_intake/README.md" in ENGLISH
    assert "examples/order_intake/README.ko.md" in KOREAN
```

- [ ] **Step 2: Run documentation tests and observe RED**

Run:

```bash
uv run --locked pytest examples/order_intake/tests/test_documentation.py tests/test_documentation_contract.py -q
```

Expected: failures identify missing locale files/assets and obsolete root WIP
assertions.

- [ ] **Step 3: Write aligned example README files and root navigation**

Both example README files use this exact section order:

1. reciprocal `English | 한국어` navigation;
2. `Scenario` with partner order acceptance and non-goals;
3. `Architecture` with shared PNG embed, SVG source link, and ownership table;
4. `Sequence Diagram` with shared PNG embed, SVG source link, success/failure/reset explanation;
5. `Packages and APIs` listing the six pinned APIs from the spec;
6. `Run` with repository-root `uv sync` and `uv run --locked python -m examples.order_intake`;
7. `Expected output` separating stderr contextual log from stdout JSON;
8. `Tests` with targeted pytest and the three full validation commands;
9. `Logging and data boundary` stating correlation IDs are non-secret, raw
   command/SKU/quantity are not log context, and applications should hash IDs
   when classification requires it;
10. `Cleanup and troubleshooting` stating there is no server/container/file to
    clean, Docker is not required, and pinned source/working directory are the
    supported path;
11. `Source` links to `models.py`, `errors.py`, `service.py`, `__main__.py`, and
    pinned bluetape-py source APIs.

Write English directly and Korean as natural engineer-facing prose while
keeping commands, API names, numbers, links, and assets identical. Replace the
root README current-status paragraph with a link to the runnable order-intake
example in both locales. Update WIP to implementation/docs status without
claiming validation or PR completion.

- [ ] **Step 4: Create and validate the architecture asset**

Use
`/Users/debop/work/bluetape4k/bluetape-go-workshop/docs/images/readme-diagrams/order-fulfillment-integration-architecture.png`
as the nearest workshop visual reference. Create a static responsibility view
with these source-backed cards: Partner Caller, `PartnerOrderCommand`,
`OrderIntakeService`, bluetape-core validation, bluetape-logging context,
application-owned handler, `AcceptedOrder`, and `OrderIntakeProblem`. Use
horizontal ownership groups, muted colors, `Architects Daughter`/`Comic Mono`,
rounded orthogonal connectors, explicit fixed-size markers, even margins, and
an adjacent legend for validation/log/result relationships.

Run the one-asset loop before starting the sequence image:

```bash
xmllint --noout examples/order_intake/docs/images/architecture.svg
cairosvg examples/order_intake/docs/images/architecture.svg -o examples/order_intake/docs/images/architecture.png -s 2
python3 "${CODEX_HOME:-$HOME/.codex}/skills/bluetape-diagram/scripts/diagram-connector-audit.py" examples/order_intake/docs/images/architecture.svg
python3 "${CODEX_HOME:-$HOME/.codex}/skills/bluetape-diagram/scripts/diagram-geometry-audit.py" --fail-diagonal examples/order_intake/docs/images/architecture.svg
python3 "${CODEX_HOME:-$HOME/.codex}/skills/bluetape-diagram/scripts/diagram-endpoint-audit.py" examples/order_intake/docs/images/architecture.svg
python3 "${CODEX_HOME:-$HOME/.codex}/skills/bluetape-diagram/scripts/diagram-mixed-corner-audit.py" examples/order_intake/docs/images/architecture.svg
```

Open the rendered PNG at full size and record card count, connector count,
failures=0, dimensions, readable labels, marker parity, endpoint clearance,
crossings, and whitespace.

- [ ] **Step 5: Create and validate the sequence asset**

Open these two full-size references first:

- `/Users/debop/work/bluetape4k/bluetape4k-wiki/docs/diagrams/best-practices/assets/infra-opentelemetry-sequence-01.png`
- `/Users/debop/work/bluetape4k/bluetape-go-workshop/docs/images/readme-diagrams/order-fulfillment-integration-sequence.png`

Create participants Partner Caller, Order Intake Service, bluetape-core,
bluetape-logging Context, and App Handler. Number visible messages for command,
context open, deterministic field validation, `alt valid` accepted projection
and success log, `else invalid` public mapping and rejection log, context reset,
and result/exception return. Use transparent chronological branch frames,
activations, continuous message lanes, explicit per-color 16x16 arrowheads,
and enough row height to prevent label overlap.

Run XML, CairoSVG scale-2 render, all common connector/geometry/endpoint/corner
audits, and:

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/bluetape-diagram/scripts/diagram-sequence-style-audit.py" examples/order_intake/docs/images/sequence.svg
```

Open the rendered PNG at full size and record reference parity, visible numbered
label count, transparent branch frames, marker color parity, no overlaps, and
dimensions.

- [ ] **Step 6: Run documentation, diagram, and locale proof**

Run:

```bash
uv run --locked pytest examples/order_intake/tests/test_documentation.py tests/test_documentation_contract.py -q
uv run --locked ruff check examples/order_intake/tests/test_documentation.py tests/test_documentation_contract.py
uv run --locked ruff format --check examples/order_intake/tests/test_documentation.py tests/test_documentation_contract.py
git diff --check -- README.md README.ko.md WIP.md examples/order_intake
```

Expected: both contract suites pass, Ruff is clean, both PNGs have completed
full-size inspection ledgers, and no locale/link/asset drift remains.

- [ ] **Step 7: Commit documentation and diagrams**

Commit both locale sets, both SVG/PNG pairs, documentation tests, root
navigation, and WIP together. Intent line:
`Teach order intake through one bilingual source-backed path`. `Tested:` names
the documentation tests, diagram audits, PNG inspection, and diff check.

### Task 5: Converge verification, learning, PR, and merge-ready evidence

**Complexity:** High
**Dependencies:** Tasks 1–4 GREEN and clean scoped commits
**Required skills:** `verification-before-completion`, `bluetape-py-patterns`, Type A review references
**Files:**
- Create: `docs/superpowers/reviews/2026-07-15-issue-3-implementation-review.md`
- Create: `docs/superpowers/lessons/2026-07-15-issue-3-order-intake.md`
- Modify: `WIP.md`

- [ ] **Step 1: Run the fresh validation ladder sequentially**

Run and read every result:

```bash
git diff --check
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked pytest examples/order_intake/tests -q
uv run --locked pytest
uv run --locked python -m examples.order_intake
git diff --exit-code -- uv.lock
```

Expected: no diff errors, Ruff clean, focused and full pytest PASS, runnable
output matches docs, and lockfile is unchanged. Docker/Testcontainers commands
remain N/A and are not run.

- [ ] **Step 2: Verify the exact spec and plan mapping**

Read the approved spec, this plan, current branch diff, root/example README
pair, all four diagram files, and test collection. Record each acceptance row as
PASS or return to the owning task. Confirm public names, validation order,
context reset, log ownership, stdout/stderr split, locale parity, source links,
and visual participants/messages match source.

- [ ] **Step 3: Run six review lenses plus main integration**

Review the full implemented branch diff independently for performance,
stability, security, operator/Ops, developer/API, and user/caller concerns.
Reclaim any delayed native lane immediately and perform that lens in the main
session. Normalize findings to P0–P3 in the implementation review artifact,
repair every P0/P1, rerun affected tests/lenses, and close only at P0=0/P1=0.

- [ ] **Step 4: Commit the required Type A lesson**

Create the lesson with sections Context, Decision, Outcome, Verification,
Review Misses, and Future Guard. Record the actual evidence for safe prevalidation
context, direct logger defaults, synchronous log assertions versus the isolated
`eventually` demonstration, pytest example discovery, and SVG-to-PNG visual QA.
Commit the review and lesson with a Lore message after final validation.

- [ ] **Step 5: Finalize WIP and authorize exact-head PR delivery**

Update WIP with exact local head, test counts, P0=0/P1=0, diagram inspection
state, and the authorized delivery target:

- repository `bluetape4k/bluetape-py-workshop`;
- base `develop`;
- head `feat/issue-3-validated-order-intake`;
- issue #3, milestone `0.1.0`, assignee `debop`.

Commit the checkpoint and confirm the worktree is clean.

- [ ] **Step 6: Publish the exact head and create the PR**

Push the head without force, read back the remote SHA, create or update an
English PR assigned to `debop` with issue milestone/labels, and verify the live
body ends with `## DoD Status`. The PR title is
`feat: add a validated order intake example` and the body links issue #3,
summarizes scenario/architecture/tests/docs, and contains reconciled Type A DoD
rows.

- [ ] **Step 7: Pass exact-head CI and live review**

Wait for required CI, re-read checks, reviews, and unresolved threads against
the exact remote head, and confirm diagram/human review evidence. Any failure or
new P0/P1 returns to the owning task and requires a new exact-head validation.

- [ ] **Step 8: Report merge-ready and stop at the merge gate**

Render all workflow rows with `Required checks: X/Y; N/A: N; Blocked: 0`, exact
PR URL/head, CI, reviews, lesson, diagram evidence, and residual risks. Mark
CG-16 through CG-18 PENDING and request a fresh merge decision. Do not enable
auto-merge or merge on the implementation-plan approval.

## Plan self-review

- Spec coverage: every acceptance criterion and Design DoD item maps to Tasks
  1–5 and a concrete command.
- Ordering: models/errors precede service; service precedes runnable; source
  precedes docs/diagrams; validation precedes PR.
- Type consistency: `PartnerOrderCommand`, `AcceptedOrder`,
  `InvalidOrderCommand`, `OrderIntakeProblem`, `map_order_error`, and
  `OrderIntakeService.accept` use the same names and fields throughout.
- Lifecycle coverage: success, validation failure, hostile values, logger
  failure, context reset, handler/root isolation, subprocess timeout, and
  deterministic cleanup are explicit; async/backend cases have concrete N/A.
- Hazard coverage: test discovery, lock immutability, locale parity, SVG/PNG
  parity, PR authority, exact-head CI, and fresh merge approval are assigned.
- Placeholder scan: no deferred implementation placeholder is present.

## Pre-implementation approval gate

This plan and its Type A review artifact remain a draft until the user approves
them. After that approval and before Task 1, commit the plan, plan review, and
WIP checkpoint with Lore trailers, record the `plan-review` workflow check, and
load `test-driven-development`. No production/example source or test file may
be created before that checkpoint commit.
