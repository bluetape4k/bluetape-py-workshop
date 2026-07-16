# Redis Test Server Workshop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> `subagent-driven-development` (recommended) or `executing-plans` to implement
> this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an independently runnable Redis integration-test workshop that
uses the pinned `RedisServer` for bounded readiness and lifecycle ownership,
performs a fixed application-owned RESP round trip, and proves cleanup in
separate deterministic and serial Docker lanes.

**Architecture:** `run_workshop()` owns one `RedisServer` context and passes its
immutable `RedisConnectionDetails` to `RedisOrderStatusProbe`. The private probe
implements only bounded `PING`, `SET`, and `GET`; the CLI emits redacted stable
JSON and default pytest selection excludes all Docker-backed tests.

**Tech Stack:** Python 3.13.14, uv 0.11.28,
`bluetape-testcontainers==0.1.0` pinned to source commit `4b7458f`, Python socket
RESP2 subset, pytest 8.4.2, Ruff 0.12.12, Docker server 28.4.0, SVG/CairoSVG.

---

## Execution Contract

- Repository: `bluetape4k/bluetape-py-workshop`
- Base: `develop@55c0555bb0ac778df838db077afd1cbcf4eed21e`
- Head: `feat/issue-7-redis-test-server`
- Worktree:
  `/Users/debop/work/bluetape4k/bluetape-py-workshop/.worktrees/issue-7-redis-test-server`
- Issue: <https://github.com/bluetape4k/bluetape-py-workshop/issues/7>
- Approved spec:
  `docs/superpowers/specs/2026-07-16-issue-7-redis-test-server-design.md`
- Spec review:
  `docs/superpowers/reviews/2026-07-16-issue-7-design-review.md`
- Workflow type: Type A
- Heavy-command limit: one pytest, Docker, actionlint, or diagram-render process
  at a time. Every Docker-backed test and CLI invocation is sequential.
- Side effects authorized by plan approval: local edits, temporary labeled
  Docker containers, Lore commits, push of the exact head branch, and PR
  creation in `bluetape4k/bluetape-py-workshop` from the named head into
  `develop`.
- Side effects not authorized: merge, auto-merge, remote branch deletion, tag,
  release, publish, workflow dispatch, milestone closure, or removal of an
  unconfirmed container.
- Stop boundary: report the exact PR head as merge-ready after CI, current
  reviews/threads, local deterministic checks, and serial Docker evidence pass;
  wait for fresh explicit merge approval.

## File Map

| Path | Responsibility |
|---|---|
| `pyproject.toml` | Register `testcontainers` and exclude it from default pytest selection |
| `.github/workflows/ci.yml` | Make the deterministic non-Docker selection explicit |
| `examples/redis_test_server/probe.py` | Immutable result, safe error, fixed bounded RESP round trip |
| `examples/redis_test_server/application.py` | `RedisServer` context ownership and probe composition |
| `examples/redis_test_server/__init__.py` | Deliberate example exports |
| `examples/redis_test_server/__main__.py` | Docker-backed CLI and redacted JSON outcomes |
| `examples/redis_test_server/tests/test_probe.py` | Deterministic protocol, validation, bound, timeout, and failure tests |
| `examples/redis_test_server/tests/test_application.py` | Deterministic lifecycle, cleanup, and CLI tests |
| `examples/redis_test_server/tests/test_redis_integration.py` | Serial real Redis success/failure/fresh-state proof |
| `examples/redis_test_server/tests/test_documentation.py` | Locale, command, source, and diagram contract |
| `examples/redis_test_server/README.md` | English reader path and operations guidance |
| `examples/redis_test_server/README.ko.md` | Meaning-equivalent Korean reader path |
| `examples/redis_test_server/docs/images/architecture.{svg,png}` | Source-backed ownership view |
| `examples/redis_test_server/docs/images/sequence.{svg,png}` | Source-backed success/failure cleanup sequence |
| `README.md`, `README.ko.md` | Root navigation and deterministic/Docker commands |
| `WIP.md` | Issue #7 gate, commands, validation, PR, and next action |
| `docs/superpowers/risks/2026-07-16-issue-7-redis-test-server-risk.md` | Docker/protocol/lifecycle risk controls |
| `docs/superpowers/reviews/2026-07-16-issue-7-implementation-review.md` | Final six-lens evidence |
| `docs/superpowers/lessons/2026-07-16-issue-7-test-infrastructure-ownership.md` | Required Type A reusable lesson |

`uv.lock` and all existing example source files must remain byte-identical to
`origin/develop`.

## Acceptance Traceability

| Acceptance criterion | Tasks | Proof |
|---|---|---|
| Explicit started/unstarted lifecycle | 1, 3, 4 | public wrapper and fake/real context tests |
| Bounded readiness and causal failure context | 3, 4 | exact startup timeout, stable kind JSON, probe cause tests |
| Wrapper-provided connection details | 2, 3, 4 | exact `RedisConnectionDetails` constructor and identity assertions |
| Sequential Docker tests and cleanup on success/failure | 1, 4, 7 | marker selection, real contexts, fresh state, label-set equality |
| Deterministic configuration/lifecycle proof | 1–3 | default marker exclusion, fake socket/server tests |
| Equivalent English/Korean docs and root navigation | 5, 6 | token parity, shared PNG/SVG assets, root contract |
| Full Type A delivery and merge gate | 7 | validation, review, lesson, exact-head PR/CI evidence |

## Task 1: Lock the Deterministic and Docker Test Lanes

**Files:**

- Modify: `pyproject.toml`
- Modify: `.github/workflows/ci.yml`
- Test: `tests/test_dependency_baseline.py`

- [ ] **Step 1.1: Write failing marker-configuration assertions**

Extend `test_project_declares_the_approved_root_contract()` with:

```python
pytest_config = project["tool"]["pytest"]["ini_options"]
assert pytest_config["markers"] == [
    "testcontainers: requires a reachable Docker runtime and runs serially",
]
assert pytest_config["addopts"] == '-ra -m "not testcontainers"'
```

- [ ] **Step 1.2: Observe RED**

Run:

```bash
uv run --locked pytest tests/test_dependency_baseline.py::test_project_declares_the_approved_root_contract -q
```

Expected: FAIL because marker registration and default exclusion do not exist.

- [ ] **Step 1.3: Register the marker and default exclusion**

Set this exact pytest configuration in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests", "examples"]
pythonpath = ["."]
addopts = "-ra -m \"not testcontainers\""
asyncio_mode = "auto"
markers = [
    "testcontainers: requires a reachable Docker runtime and runs serially",
]
```

Change the CI test step to make the same boundary visible:

```yaml
- name: Run deterministic tests without Docker
  run: uv run --locked pytest -m "not testcontainers"
```

- [ ] **Step 1.4: Observe GREEN and verify selection**

Run:

```bash
uv run --locked pytest tests/test_dependency_baseline.py -q
uv run --locked pytest --collect-only -q
uv run --locked pytest -m testcontainers --collect-only -q
```

Expected: dependency tests pass; default collection contains no selected Docker
test after Task 4 exists; explicit selection contains only the integration test.
At this early task, the explicit selection may report no tests collected.

- [ ] **Step 1.5: Validate workflow syntax and commit**

Run actionlint and `git diff --check`, then commit with a Lore message whose
intent is that default verification must remain Docker-independent. Expected:
both commands pass and no dependency or lockfile change exists.

## Task 2: Implement the Fixed Bounded Redis Probe with TDD

**Files:**

- Create: `examples/redis_test_server/__init__.py`
- Create: `examples/redis_test_server/probe.py`
- Create: `examples/redis_test_server/tests/__init__.py`
- Create: `examples/redis_test_server/tests/test_probe.py`

- [ ] **Step 2.1: Write failing public-shape and success tests**

Create an empty test package and scripted socket doubles that implement
`__enter__`, `__exit__`, `settimeout`, `sendall`, and `recv`. The first tests
must assert:

```python
details = RedisConnectionDetails(
    host="127.0.0.1",
    port=46379,
    url="redis://127.0.0.1:46379",
)
probe = RedisOrderStatusProbe(details=details, socket_factory=scripted_factory)
result = probe.verify(order_id=" ord-1001 ", status=" Accepted ")

assert result == RedisProbeResult(
    order_id="ORD-1001",
    status="accepted",
    ping_succeeded=True,
    write_succeeded=True,
    read_succeeded=True,
)
assert [call.address for call in scripted_factory.calls] == [
    ("127.0.0.1", 46379),
] * 3
assert all(call.timeout == 2.0 for call in scripted_factory.calls)
```

Assert the exact RESP requests are:

```text
*1\r\n$4\r\nPING\r\n
*3\r\n$3\r\nSET\r\n$23\r\nworkshop:order:ORD-1001\r\n$8\r\naccepted\r\n
*2\r\n$3\r\nGET\r\n$23\r\nworkshop:order:ORD-1001\r\n
```

- [ ] **Step 2.2: Observe RED**

Run:

```bash
uv run --locked pytest examples/redis_test_server/tests/test_probe.py -q
```

Expected: collection fails because the package and probe contracts do not exist.

- [ ] **Step 2.3: Implement the minimal immutable result and fixed probe**

Implement `probe.py` with this exact bounded surface and private protocol flow:

```python
import math
import socket
from collections.abc import Callable
from dataclasses import dataclass

from bluetape.testcontainers import RedisConnectionDetails


@dataclass(frozen=True, slots=True, kw_only=True)
class RedisProbeResult:
    order_id: str
    status: str
    ping_succeeded: bool
    write_succeeded: bool
    read_succeeded: bool


class RedisProbeError(RuntimeError):
    """A safe application-level Redis probe failure."""


_MAX_PART_BYTES = 64
_MAX_ORDER_ID_BYTES = 48
_MAX_STATUS_BYTES = 64
_MAX_LINE_BYTES = 128
_MAX_BULK_BYTES = 64
_SocketFactory = Callable[[tuple[str, int], float], socket.socket]


class RedisOrderStatusProbe:
    def __init__(
        self,
        *,
        details: RedisConnectionDetails,
        command_timeout: float = 2.0,
        socket_factory: _SocketFactory = socket.create_connection,
    ) -> None:
        if not isinstance(details, RedisConnectionDetails):
            raise TypeError("details must be RedisConnectionDetails")
        if isinstance(command_timeout, bool) or not isinstance(command_timeout, (int, float)):
            raise TypeError("command_timeout must be a finite positive number")
        timeout = float(command_timeout)
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("command_timeout must be a finite positive number")
        self._details = details
        self._command_timeout = timeout
        self._socket_factory = socket_factory

    def verify(self, *, order_id: str, status: str) -> RedisProbeResult:
        normalized_order_id = _token(
            order_id, field="order_id", uppercase=True, max_bytes=_MAX_ORDER_ID_BYTES
        )
        normalized_status = _token(
            status, field="status", uppercase=False, max_bytes=_MAX_STATUS_BYTES
        )
        key = _key(normalized_order_id)
        if self._command("PING") != b"PONG":
            raise RedisProbeError("Redis ping returned an unexpected response")
        if self._command("SET", key, normalized_status) != b"OK":
            raise RedisProbeError("Redis write returned an unexpected response")
        if self.read_status(order_id=normalized_order_id) != normalized_status:
            raise RedisProbeError("Redis read returned an unexpected response")
        return RedisProbeResult(
            order_id=normalized_order_id,
            status=normalized_status,
            ping_succeeded=True,
            write_succeeded=True,
            read_succeeded=True,
        )

    def read_status(self, *, order_id: str) -> str | None:
        normalized_order_id = _token(
            order_id, field="order_id", uppercase=True, max_bytes=_MAX_ORDER_ID_BYTES
        )
        response = self._command("GET", _key(normalized_order_id))
        if response is None:
            return None
        try:
            return response.decode("utf-8")
        except UnicodeError as error:
            raise RedisProbeError("Redis status was not valid UTF-8") from error

    def _command(self, *parts: str) -> bytes | None:
        request = _request(parts)
        try:
            with self._socket_factory(
                (self._details.host, self._details.port), self._command_timeout
            ) as stream:
                stream.settimeout(self._command_timeout)
                stream.sendall(request)
                return _response(stream)
        except RedisProbeError:
            raise
        except (OSError, UnicodeError) as error:
            raise RedisProbeError("Redis command failed") from error


def _token(value: str, *, field: str, uppercase: bool, max_bytes: int) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field} must be non-blank")
    if not normalized.isascii() or any(
        not (character.isalnum() or character in "_-") for character in normalized
    ):
        raise ValueError(f"{field} must use ASCII letters, digits, '_' or '-'")
    normalized = normalized.upper() if uppercase else normalized.lower()
    if len(normalized.encode()) > max_bytes:
        raise ValueError(f"{field} exceeds {max_bytes} UTF-8 bytes")
    return normalized


def _key(order_id: str) -> str:
    return f"workshop:order:{order_id}"


def _request(parts: tuple[str, ...]) -> bytes:
    encoded = [part.encode("utf-8") for part in parts]
    request = [f"*{len(encoded)}\r\n".encode()]
    for part in encoded:
        request.extend((f"${len(part)}\r\n".encode(), part, b"\r\n"))
    return b"".join(request)


def _response(stream: socket.socket) -> bytes | None:
    prefix = _read_exact(stream, 1)
    line = _read_line(stream)
    if prefix == b"+":
        return line
    if prefix == b"-":
        raise RedisProbeError("Redis returned an error response")
    if prefix != b"$":
        raise RedisProbeError("Redis returned an unsupported response type")
    try:
        size = int(line)
    except ValueError as error:
        raise RedisProbeError("Redis returned an invalid bulk length") from error
    if size == -1:
        return None
    if size < 0 or size > _MAX_BULK_BYTES:
        raise RedisProbeError("Redis returned an invalid bulk length")
    payload = _read_exact(stream, size)
    if _read_exact(stream, 2) != b"\r\n":
        raise RedisProbeError("Redis returned an invalid bulk trailer")
    return payload


def _read_line(stream: socket.socket) -> bytes:
    data = bytearray()
    while not data.endswith(b"\r\n"):
        if len(data) >= _MAX_LINE_BYTES + 2:
            raise RedisProbeError("Redis response line exceeded the limit")
        data.extend(_read_exact(stream, 1))
    return bytes(data[:-2])


def _read_exact(stream: socket.socket, size: int) -> bytes:
    data = bytearray()
    while len(data) < size:
        chunk = stream.recv(size - len(data))
        if not chunk:
            raise RedisProbeError("Redis closed the connection unexpectedly")
        data.extend(chunk)
    return bytes(data)
```

Use exact private constants `_MAX_PART_BYTES = 64`, `_MAX_ORDER_ID_BYTES = 48`,
`_MAX_STATUS_BYTES = 64`, `_MAX_LINE_BYTES = 128`, and `_MAX_BULK_BYTES = 64`.
Validate exact connection-details type, finite
positive timeout, ASCII token grammar `[A-Za-z0-9_-]+`, and encoded length.
Normalize order ID uppercase and status lowercase. The public method issues only
fixed `PING`, `SET`, and `GET` tuples and compares exact `PONG`, `OK`, and status
bytes. `read_status()` exposes only the fixed order-status key and returns the
decoded normalized status or `None`; `verify()` calls it for read-back.

The private command function must use one socket context per command, pass the
timeout to `create_connection`, call `settimeout`, and raise
`RedisProbeError("Redis command failed") from error` for socket/Unicode causes.
The parser accepts only `+` simple strings and `$` bulk strings, treats `$-1`
as missing, rejects Redis `-` errors and every unexpected/truncated/oversized
response without including response bytes in its message.

Export only:

```python
__all__ = [
    "RedisOrderStatusProbe",
    "RedisProbeError",
    "RedisProbeResult",
    "run_workshop",
]
```

`run_workshop` is added to this export in Task 3; use a temporary probe-only
export until then.

- [ ] **Step 2.4: Observe GREEN**

Run the Step 2.2 command. Expected: public-shape and success tests pass.

- [ ] **Step 2.5: Add one RED/GREEN test at a time for failure boundaries**

Cover and observe RED before each minimal repair:

- non-`RedisConnectionDetails`, bool/string/non-finite/non-positive timeout;
- non-string, blank, non-ASCII, grammar-invalid, 49-byte order IDs, and 65-byte
  statuses before any socket call;
- `PONG` mismatch, `OK` mismatch, missing key, and stored-value mismatch;
- `read_status()` returns `None` for a missing key and never exposes a generic
  command method;
- empty/truncated prefix, unterminated/oversized line, invalid/negative/
  oversized/truncated bulk length, invalid trailer, Redis error, and unexpected
  RESP prefix;
- `TimeoutError` and `OSError` produce the safe message, retain `__cause__`,
  close the socket, and never expose scripted sensitive text in `str(error)`.

After each behavior, run the focused test node then the entire `test_probe.py`.

- [ ] **Step 2.6: Refactor and commit**

Run Ruff on the package, inspect that no arbitrary public command method exists,
and commit with a Lore message whose directive preserves the fixed bounded RESP
surface. Expected: focused tests and Ruff pass.

## Task 3: Compose Lifecycle Ownership and the Redacted CLI

**Files:**

- Create: `examples/redis_test_server/application.py`
- Create: `examples/redis_test_server/__main__.py`
- Modify: `examples/redis_test_server/__init__.py`
- Create: `examples/redis_test_server/tests/test_application.py`

- [ ] **Step 3.1: Write failing lifecycle orchestration tests**

Use a fake single-use context server that records `enter`, `details`, and
`exit:<exception-name>`. Inject a recording probe factory. Prove this order on
success:

```python
assert events == [
    "enter",
    "details",
    "probe_factory",
    "verify:ORD-1001:accepted",
    "exit:none",
]
```

Then make `verify()` raise `ExpectedBodyFailure` and assert the same context
exits with `exit:ExpectedBodyFailure`, the exact body exception is preserved,
and no second details read occurs.

- [ ] **Step 3.2: Observe RED**

Run:

```bash
uv run --locked pytest examples/redis_test_server/tests/test_application.py -q
```

Expected: collection fails because `run_workshop` and the CLI do not exist.

- [ ] **Step 3.3: Implement minimal context ownership**

Implement:

```python
def run_workshop(
    *,
    server: RedisServer,
    probe_factory: Callable[..., RedisOrderStatusProbe] = RedisOrderStatusProbe,
) -> RedisProbeResult:
    with server as running:
        probe = probe_factory(details=running.details)
        return probe.verify(order_id="ORD-1001", status="accepted")
```

Do not catch body exceptions and do not access wrapper private fields.

- [ ] **Step 3.4: Add failing CLI event tests**

Call `main()` directly with injected factories/runners and capture output.
Assert exact success JSON, stable startup failure JSON containing only
`error_code`, `event`, and `kind`, stable probe failure JSON containing only
`error_code` and `event`, return statuses 0/1, and empty stderr. Construct the
startup error with public `TestcontainerStartError` and `StartFailureKind`.

- [ ] **Step 3.5: Implement the minimal CLI and observe GREEN**

Implement keyword-only test seams:

```python
def main(
    *,
    server_factory: Callable[..., RedisServer] = RedisServer,
    workshop_runner: Callable[..., RedisProbeResult] = run_workshop,
) -> int:
    try:
        result = workshop_runner(server=server_factory(startup_timeout=30.0))
    except TestcontainerStartError as error:
        _emit({"event": "redis_workshop_failed", "error_code": "testcontainer_start_failed", "kind": error.kind.value})
        return 1
    except RedisProbeError:
        _emit({"event": "redis_workshop_failed", "error_code": "redis_probe_failed"})
        return 1
    _emit({"event": "redis_workshop_succeeded", **asdict(result)})
    return 0
```

Use sorted compact JSON and `raise SystemExit(main())` at module entry. Run the
Step 3.2 command and expect all tests to pass.

- [ ] **Step 3.6: Verify deterministic wrapper boundaries and commit**

Add public tests proving `RedisServer()` is initially not running, unstarted
details raise, close-before-start is safe/terminal, invalid untagged/latest
images fail, and invalid timeouts fail without Docker. Run focused tests, Ruff,
and commit with a Lore message preserving context-manager ownership.

## Task 4: Prove Real Redis Readiness, Round Trip, and Cleanup Serially

**Files:**

- Create: `examples/redis_test_server/tests/test_redis_integration.py`
- Create: `docs/superpowers/risks/2026-07-16-issue-7-redis-test-server-risk.md`

- [ ] **Step 4.1: Record risk gates before Docker mutation**

The risk table must name signals, mitigations, and rerun/rollback points for:
untrusted image selection, Docker unavailability, bounded image/readiness time,
stale labeled containers, application-body cleanup, cleanup failure, parallel
launch, RESP allocation/protocol drift, and accidental default-lane Docker
contact.

- [ ] **Step 4.2: Write the focused marked integration test**

Mark the module with `pytestmark = pytest.mark.testcontainers`. In one serial
test:

1. assert `DEFAULT_REDIS_IMAGE == "redis:8"`, call `run_workshop()` with one
   new `RedisServer()`, capture the wrapper-provided details through the injected
   probe factory, and assert successful dynamic details plus result;
2. after exit, assert `running is False` and details reject access;
3. pass a probe factory whose `verify()` raises `ExpectedBodyFailure`, assert
   the exact body exception, then assert the server is closed;
4. start a fresh server, construct `RedisOrderStatusProbe` from its public
   details, assert `read_status(order_id="ORD-1001") is None`, then complete a
   second round trip; and
5. assert the second server is closed.

Do not import Docker SDK internals, `GenericContainer`, wrapper private names,
or redis-py.

- [ ] **Step 4.3: Observe pre-run label baseline**

Run:

```bash
docker ps -a --filter label=com.bluetape.testcontainers.redis=true \
  --format '{{.ID}} {{.Image}} {{.Status}} {{.Names}}'
```

Expected: empty. If not empty, inspect each entry and remove only a confirmed
stale workshop container before restarting this step.

- [ ] **Step 4.4: Verify collection and deterministic fresh-state behavior**

Run collection only:

```bash
uv run --locked pytest -m testcontainers \
  examples/redis_test_server/tests/test_redis_integration.py \
  --collect-only -q
```

Expected: exactly one marked integration test collects. Rerun the deterministic
`read_status()` missing-key scripted-socket test and require PASS before the
real backend proof. The application behavior was already introduced RED-first
in Task 2; this step adds backend-capability evidence rather than new behavior.

- [ ] **Step 4.5: Run the Docker test once, serially**

Run exactly:

```bash
uv run --locked pytest -m testcontainers \
  examples/redis_test_server/tests/test_redis_integration.py -q
```

Expected: PASS with real Redis 8 readiness, round trips, success/body-failure
cleanup, and fresh state. Do not start another heavy command concurrently.

- [ ] **Step 4.6: Prove no new labeled residue and run the real CLI**

Repeat Step 4.3 and require the exact pre-run container set. Then run:

```bash
uv run --locked python -m examples.redis_test_server
```

Expected: exit 0 and one compact `redis_workshop_succeeded` JSON line. Repeat
the label check and require the baseline again.

- [ ] **Step 4.7: Run the performance/stability scan and commit**

Inspect the exact diff for repeated startup, unbounded reads, timeout loss,
container references, and tests that could pass without cleanup. Fix P0/P1,
rerun only affected deterministic tests and the serial Docker test, then commit
with a Lore message recording Docker server/image evidence.

## Task 5: Write Bilingual Reader Documentation and Source-Backed Diagrams

**Files:**

- Create: `examples/redis_test_server/README.md`
- Create: `examples/redis_test_server/README.ko.md`
- Create: `examples/redis_test_server/tests/test_documentation.py`
- Create: `examples/redis_test_server/docs/images/architecture.svg`
- Create: `examples/redis_test_server/docs/images/architecture.png`
- Create: `examples/redis_test_server/docs/images/sequence.svg`
- Create: `examples/redis_test_server/docs/images/sequence.png`

- [ ] **Step 5.1: Load `bluetape-writer` and `bluetape-diagram` before edits**

Follow their README parity, source-backed asset, rendering, audit, and visual
inspection contracts. Diagram labels are English and shared by both locales.

- [ ] **Step 5.2: Write failing documentation tests**

Require exact reciprocal locale navigation and equivalent tokens for scenario,
non-goals, Architecture, Sequence Diagram, `RedisServer`,
`RedisConnectionDetails`, `StartFailureKind`, deterministic pytest, Docker
marker pytest, CLI, label inspection, confirmed removal, `redis:8`,
`startup_timeout`, single-use ownership, cleanup retry, no redis-py, and all
four asset names. Require source references to `probe.py`, `application.py`,
`__main__.py`, and the integration test.

- [ ] **Step 5.3: Observe RED, then write both README files together**

Run the documentation test and expect missing files. Add meaning-equivalent
English/Korean reader paths with exact prerequisites, working directory,
commands, expected safe JSON, startup kinds, failure/cleanup behavior, trusted
image warning, deterministic/Docker separation, troubleshooting, and explicit
production non-goals.

- [ ] **Step 5.4: Create Architecture SVG from implemented source**

Show reader/CLI, `run_workshop`, `RedisServer`, Docker Redis 8,
`RedisConnectionDetails`, and `RedisOrderStatusProbe`, with lifecycle ownership
and data direction. Link the SVG and embed its PNG in both READMEs.

- [ ] **Step 5.5: Create Sequence SVG from implemented source**

Show constructor-without-Docker, bounded start/readiness, details delivery,
three bounded commands, success cleanup, and an alternate application-failure
cleanup branch. Link the SVG and embed its PNG in both READMEs.

- [ ] **Step 5.6: Render, audit, inspect, and observe GREEN**

Render both SVGs at readable full-size PNG resolution using the diagram skill.
Validate XML, dimensions, source-label correspondence, and README references;
inspect both PNGs visually. Run documentation tests and require PASS.

- [ ] **Step 5.7: Commit the aligned docs and assets**

Run Ruff, focused tests, and `git diff --check`; commit with a Lore message
whose directive requires diagrams to follow the implemented lifecycle.

## Task 6: Register Root Navigation and the Delivery Checkpoint

**Files:**

- Modify: `README.md`
- Modify: `README.ko.md`
- Modify: `tests/test_documentation_contract.py`
- Modify: `WIP.md`

- [ ] **Step 6.1: Write failing root discovery/navigation assertions**

Require both root locales to link `examples/redis_test_server`, name the
deterministic and explicit Docker commands, and preserve the existing four
examples. Extend automatic example discovery so the new README pair and four
assets are mandatory.

- [ ] **Step 6.2: Observe RED and update both root README files together**

Run `tests/test_documentation_contract.py` and expect missing navigation.
Add the Redis workshop with a concise ownership description and separate
deterministic/Docker/CLI commands in both locales.

- [ ] **Step 6.3: Update WIP to the implementation-validation gate**

Record exact branch/base, committed artifacts, deterministic counts, Docker
server/image, label-baseline equality, focused CLI/test commands, exclusions,
and the next gate. Do not claim PR/CI evidence before it exists.

- [ ] **Step 6.4: Observe GREEN and commit**

Run root and example documentation tests plus diff check. Commit with a Lore
message preserving bilingual discovery and explicit Docker opt-in.

## Task 7: Verify, Review, Capture the Lesson, and Deliver the Exact PR Head

**Files:**

- Create: `docs/superpowers/reviews/2026-07-16-issue-7-implementation-review.md`
- Create: `docs/superpowers/lessons/2026-07-16-issue-7-test-infrastructure-ownership.md`
- Modify: `WIP.md`

- [ ] **Step 7.1: Run deterministic validation first**

Sequentially run:

```bash
uv --version
uv sync --locked --python 3.13.14
uv run --locked pytest tests/test_dependency_baseline.py -q
uv run --locked pytest -m "not testcontainers" examples/redis_test_server/tests -q
uv run --locked ruff format --check .
uv run --locked ruff check .
uv run --locked pytest -m "not testcontainers"
GOTOOLCHAIN=go1.26.1 go run github.com/rhysd/actionlint/cmd/actionlint@v1.7.12 \
  .github/workflows/ci.yml
git diff --check
```

Expected: exact toolchain, all deterministic tests pass, the existing optional
Fory test remains skipped, Ruff/actionlint/diff checks pass, and neither Docker
nor a labeled container is contacted/created by this ladder.

- [ ] **Step 7.2: Run Docker validation serially and audit cleanup**

Record the label set, run the focused marker test, run the CLI, and record the
label set after each command. Expected: both commands pass and every post-run
set equals the original baseline.

- [ ] **Step 7.3: Prove dependency and scope invariants**

Run:

```bash
git diff --exit-code origin/develop -- uv.lock
git diff --name-only origin/develop
rg -n "GenericContainer|redis[_-]?py|create_task|ThreadPool|latest" \
  examples/redis_test_server pyproject.toml .github/workflows/ci.yml
```

Expected: lockfile unchanged; only planned files differ; no forbidden provider,
container construction, concurrency, or latest-image path is introduced.

- [ ] **Step 7.4: Run final six-perspective implementation review**

Review exact changed source, tests, workflows, docs, and assets independently
for performance, stability, security, operator/Ops, developer/API, and
user/caller lenses. Reclaim delayed children immediately. Integrate findings in
the review artifact; fix and rerun affected lanes until P0=0/P1=0. Resolve every
P2/P3 or file a linked follow-up with rationale.

- [ ] **Step 7.5: Verify spec, plan, hazards, and diagrams**

Load `verification-before-completion` and the Type A verifier checklist. Map
every acceptance row to fresh output, inspect both PNGs at full size, validate
SVG XML, and require verifier PASS. Update plan checkboxes and WIP only from
actual evidence.

- [ ] **Step 7.6: Capture the required reusable lesson and final local commit**

Record why test infrastructure owns image/readiness/details/cleanup while the
application owns only the fixed probe and context scope. Include stale-container
and default-marker safeguards. Commit review, lesson, and final WIP checkpoint
with a Lore message, then rerun the deterministic ladder and focused Docker
test at the resulting exact head.

- [ ] **Step 7.7: Push and create the approved PR**

Push `feat/issue-7-redis-test-server` and create a PR into `develop` titled in
English, linking `Closes #7`, listing deterministic/Docker/diagram evidence,
and explicitly excluding merge/release. Do not enable auto-merge.

- [ ] **Step 7.8: Verify exact-head CI and current review state**

Pin the PR head SHA; verify hosted CI is for that exact SHA, all required checks
pass, the PR is mergeable, no unresolved thread or blocking review exists, and
any required human-review artifact matches the head. If anything changes,
rerun local proportional validation and refresh the evidence.

- [ ] **Step 7.9: Stop for fresh merge approval**

Report PR URL, exact head, commits, changed files, deterministic and Docker
counts, container-label baseline equality, CI/review state, lesson, remaining
risks, and `P0=0/P1=0`. Do not merge until a new explicit user approval arrives.

## Rollback

Before PR creation, revert only the current task's commit and retain its failing
test when repairing a boundary. After PR creation, use additive repair commits.
Full rollback removes the new example, marker/CI selection, root navigation,
WIP/docs/review/lesson artifacts, and no library API, dependency lock, persisted
data, remote container, or release state remains.
