# 통합 주문 Backend

[English](README.md) | 한국어

이 실행 가능한 예제는 앞에서 다룬 작은 예제를 실제 주문 처리 흐름 하나로
조합합니다. 주문 전체를 먼저 검증한 뒤 catalog 정보를 cache에서 읽고, 선택
recommendation을 붙이고, 안전한 JSON artifact를 만들며, 바깥 application이 요청
deadline과 shutdown을 소유합니다.

## Scenario

한 partner가 여러 line으로 구성된 주문을 보냅니다. 같은 SKU가 한 주문 안에
중복될 수 있고 다음 주문에서도 다시 등장할 수 있습니다.

- 첫 주문: `SKU-1 x2`, `SKU-2 x1`, `SKU-1 x1` — 합계 `45,400`
- 둘째 주문: `SKU-2 x2`, `SKU-3 x1` — 합계 `31,700`
- 두 주문은 같은 application과 `AsyncTTLCache`를 사용합니다.
- 첫 주문에서 읽은 `SKU-2`는 둘째 주문에서 cache hit가 됩니다.
- recommendation record가 없는 line은 주문을 실패시키지 않고 안전한 warning을
  남깁니다.

이 예제의 핵심은 새 framework를 만드는 것이 아니라, 이미 검증된 작은 service의
계약을 유지하면서 실제 application 모양으로 조합하는 방법입니다.

## Architecture

![통합 주문 Backend Architecture](docs/images/architecture.png)

[Architecture SVG source 열기](docs/images/architecture.svg).

| 구성 요소 | 소유 책임 |
|---|---|
| `OrderBackendApplication` | 요청 task, 전체 request timeout, task exception 관찰, shared close와 retry |
| `OrderBackendService` | 주문 전체 validation, occurrence 순서, 금액 합산, 명시적 JSON document 조립 |
| `OrderIntakeService` | header·SKU·quantity 정규화와 검증, 안전한 log context |
| `CatalogEnrichmentService` | distinct SKU provider 작업, 필수·선택 응답 정책, occurrence 복원 |
| `CachedCatalogProvider` | 기존 async catalog를 enrichment provider에 연결하는 순차 adapter |
| `AsyncProductCatalogService` / `AsyncTTLCache` | read-through cache, concurrent load coalescing, 공개 `CacheStats` |
| `JsonPayloadService` | untrusted JSON, gzip, base64url, 크기·nesting 제한 |
| `build_application()` | application마다 cache와 service graph를 한 번 구성하는 composition root |

`build_application()`은 cache를 전역으로 두지 않습니다. 한 application context 안에서는
두 주문이 같은 cache를 공유하지만, 새 application은 새 cache를 받습니다. 이 경계 덕분에
test 간 상태가 섞이지 않고 lifecycle 소유자도 명확합니다.

## Sequence Diagram

![통합 주문 Backend Sequence Diagram](docs/images/sequence.png)

[Sequence Diagram SVG source 열기](docs/images/sequence.svg).

Admission check, named request task 생성, task 등록은 중간 `await` 없이 이어집니다.
따라서 shutdown이 이미 받아들인 요청을 snapshot에서 놓치지 않습니다. Service는 모든
line을 `OrderIntakeService`로 검증한 뒤에만 enrichment I/O를 시작합니다. 중복 SKU는
provider 작업을 공유하지만 결과는 원래 occurrence 순서와 수량으로 복원됩니다.

Application은 owned request task를 `asyncio.shield()`로 기다리고 바깥
`asyncio.timeout()`으로 전체 deadline을 적용합니다. Timeout이나 caller cancellation이
발생하면 owned task에 취소를 전달한 뒤 무제한으로 기다리지 않고 caller에게 즉시
돌아갑니다. 늦게 끝난 task의 exception은 done callback이 관찰합니다.

## Packages and APIs

통합 예제는 다음 `bluetape-py` API를 기존 focused example을 통해 재사용합니다.

- `bluetape-core`: 주문 입력의 exact type·문자열 validation;
- `bluetape-logging`: `log_context`, `ContextLogFilter`;
- `bluetape-collections`: distinct SKU와 안정적인 batch 구성;
- `bluetape-async`: provider task의 bounded concurrency와 cleanup;
- `bluetape-cache`: `AsyncTTLCache`, read-through load, `CacheStats`;
- `bluetape-compression`: 제한된 `GzipCompressor`;
- `bluetape-serde`: untrusted JSON metadata와 serialization limit.

모든 package는 고정된 `bluetape-py` source commit
[`4b7458f22cea0a9e757b5fbf7f5ff4bc8c23cb9a`](https://github.com/bluetape4k/bluetape-py/tree/4b7458f22cea0a9e757b5fbf7f5ff4bc8c23cb9a)에서
해석합니다.

Fory는 신뢰된 내부 object graph를 위한 별도 예제인
[`bounded_payload_processing`](../bounded_payload_processing/README.ko.md)에서 다룹니다.
이 주문 backend의 외부 artifact 경계는 caller가 format을 선택하지 못하는 untrusted
JSON으로 고정합니다. Fory를 외부 입력 경계에 섞지 않는 것도 의도적인 security
contract입니다.

## Run

저장소 root에서 Python 3.13.14 환경을 준비합니다.

```bash
uv sync --locked --python 3.13.14
```

두 주문 시나리오를 실행합니다.

```bash
uv run --locked python -m examples.integrated_order_backend
```

stdout에는 정렬된 compact JSON line이 정확히 다섯 개 출력됩니다.

1. `backend_started`
2. 첫 `order_processed`
3. 둘째 `order_processed`
4. `cache_stats`
5. `backend_stopped`

`cache_stats`는 `hits=1`, `misses=3`, `loads=3`, `load_failures=0`,
`inflight_loads=0`, `abandoned_loads=0`을 보여줍니다. 주문 event는 line count, total,
warning count, artifact metadata와 encoded size만 포함합니다. Product name,
recommendation, artifact `data`, provider exception text는 출력하지 않습니다.

## Aggregate Invariants

- `OrderBackendCommand.lines`는 exact tuple이며 occurrence가 1개 이상 100개
  이하입니다.
- 모든 line validation이 성공하기 전에는 cache, provider, payload 작업을 시작하지
  않습니다.
- SKU는 focused intake/catalog 계약에 따라 trim·uppercase·ASCII 검증됩니다.
- 중복 SKU는 cache/provider 작업을 공유하지만 line index, 입력 순서, 수량은 그대로
  유지합니다.
- `total_cents`는 각 `unit_price_cents * quantity` 합계입니다.
- Artifact document는 명시적 allowlist로 만들며 artifact가 자기 자신을 포함하지
  않습니다.
- Artifact metadata의 trust profile은 항상 `untrusted`입니다.

## Failure, Timeout, Cancellation, and Shutdown

| 상황 | 공개 동작 |
|---|---|
| Aggregate shape 오류 | `InvalidOrderBackendCommand`, 외부 작업 없음 |
| 특정 line 오류 | index를 포함한 `InvalidOrderLine`, 원래 `InvalidOrderCommand`는 cause로 유지 |
| 필수 catalog 실패 | `CatalogEnrichmentFailed` 전파, 실패한 load는 cache하지 않음 |
| 선택 recommendation 실패·누락 | `optional_provider_failed` 또는 `optional_record_missing` warning |
| Payload 크기·compression·serde 한도 위반 | 기존 payload exception 전파 |
| 전체 request timeout | native `TimeoutError`, owned request에 cancel 전달 |
| Caller cancellation | native `CancelledError`, owned request에 cancel 전달 |
| Shutdown grace 안에 종료되지 않음 | 한 번 더 cancel하고 finite cancel timeout 대기 |
| Cancel을 계속 억제하는 작업 | pending count를 가진 `OrderBackendShutdownError`; reference 유지 후 retry 가능 |

여러 caller가 동시에 `aclose()`를 호출해도 하나의 close task를 shield해 기다립니다.
Close waiter 하나가 취소되어도 shared close와 request task는 분리되지 않습니다. Context
body가 실패한 상태에서 cleanup도 terminal state에 도달하지 못하면 body exception을
우선 유지하고 cleanup note를 붙입니다.

Application lifecycle event는 best-effort입니다. Caller가 주입한 logging handler가
실패해도 request task 등록, timeout 처리, shutdown state transition은 계속됩니다.
반대로 `OrderIntakeService`의 기존 logging contract를 application이 몰래 삼키지는
않습니다.

## Security and Production Boundaries

- 외부 식별자는 길이와 문자 집합을 제한하고 raw payload를 log에 남기지 마세요.
- 이 예제는 이해를 위해 request/partner/order ID를 memory에 잠시 보관합니다. 실제
  서비스는 retention, deletion, masking 정책을 명시해야 합니다.
- CLI는 인증·인가를 구현하지 않습니다. Production adapter는 partner가 해당 order와
  SKU를 처리할 권한이 있는지 I/O 전에 검증해야 합니다.
- Provider exception message와 원시 response를 public error, warning, metric label에
  복사하지 마세요.
- JSON artifact는 untrusted 입력으로 decode하며 size, compression, serialized size,
  nesting depth 제한을 유지하세요.
- HTTP/ASGI/FastAPI endpoint, database persistence, retry, circuit breaker, distributed
  cache, tracing exporter는 이 예제의 범위가 아닙니다.

`CachedCatalogProvider`는 학습 흐름을 명확히 하려고 distinct SKU를 순차로 읽습니다.
주문당 최대 100 line이고 실제 provider concurrency는 기존 enrichment/cache 계층이
소유하므로, 이 예제는 throughput benchmark나 최적화를 주장하지 않습니다. Production에서
latency가 문제라면 측정 자료와 upstream API 한도를 바탕으로 별도 설계를 하세요.

## Tests

이 예제만 검증합니다.

```bash
uv run --locked pytest examples/integrated_order_backend/tests -q
```

Workshop 전체 gate도 실행할 수 있습니다.

```bash
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked pytest
```

테스트는 validation-before-I/O, duplicate occurrence, shared cache hit, loader recovery,
optional warning, payload limit, timeout, caller cancellation, 실제 cache loader cleanup,
동시 close, cancellation-resistant shutdown retry, event-loop binding, best-effort lifecycle
logging, CLI redaction, 다국어 문서와 diagram contract를 검증합니다.

## Cleanup and Troubleshooting

중지할 server, container, file, network connection이 없습니다. CLI는 in-memory provider만
사용하고 application context가 종료되면 request/close task도 정리합니다.

- 저장소 root에서 명령을 실행하세요.
- 환경이 달라졌다면 `uv sync --locked --python 3.13.14`를 다시 실행하세요.
- 반복되는 `TimeoutError`를 retry로 숨기기 전에 request timeout, provider timeout,
  cache loader latency를 각각 확인하세요.
- `OrderBackendShutdownError`가 발생하면 pending count를 기록하고 provider가
  `CancelledError`를 억제하는지 확인한 뒤 close를 retry하세요.
- Cache miss가 예상보다 많으면 application을 주문마다 새로 만들고 있지 않은지
  확인하세요.
- 지원 source는 위 pinned commit이며 unpublished PyPI package 경로가 아닙니다.

## Source

- [models.py](models.py) — aggregate command와 processed result
- [errors.py](errors.py) — validation, closed, shutdown public errors
- [composition.py](composition.py) — cache adapter와 fixed composition root
- [service.py](service.py) — validation-first aggregate processing과 payload allowlist
- [application.py](application.py) — deadline, task observation, shared shutdown
- [__main__.py](__main__.py) — 두 주문을 처리하는 network-free CLI
- [tests](tests) — behavior, lifecycle, CLI, documentation 검증
