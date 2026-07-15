# 제한된 Catalog Enrichment

[English](README.md) | 한국어

이 실행 가능한 예제는 catalog와 recommendation provider를 동시에 호출하되 전체
동시성 한도를 넘지 않는 enrichment service를 구성합니다. 중복 product ID는 한
번만 조회하고, 결과는 원래 입력 순서와 중복 횟수대로 복원합니다.

## Scenario

상품 목록을 만드는 애플리케이션이 product ID마다 필수 catalog 정보와 선택
recommendation을 붙입니다. Catalog 정보가 없으면 결과를 만들 수 없지만,
recommendation 장애는 안전한 warning으로 남기고 catalog 결과는 반환할 수
있습니다. 한 요청의 provider 작업은 모두 같은 동시성 예산과 전체 timeout을
공유합니다.

비목표는 다음과 같습니다.

- HTTP, ASGI, FastAPI endpoint를 만들지 않습니다.
- retry, cache, circuit breaker 또는 실제 provider client를 구현하지 않습니다.
- provider가 소유한 connection이나 session lifecycle을 관리하지 않습니다.
- Docker, network, credential 또는 background service를 사용하지 않습니다.

## Architecture

![제한된 Catalog Enrichment Architecture](docs/images/architecture.png)

[Architecture SVG source 열기](docs/images/architecture.svg).

| 구성 요소 | 소유자 | 책임 |
|---|---|---|
| `CatalogEnrichmentService` | 예제 | 입력 정규화, 한도 검증, provider 응답 정책, 입력 순서 복원 |
| `RequiredCatalogProvider` | 주입된 adapter | batch별 필수 catalog record 조회 |
| `OptionalRecommendationProvider` | 주입된 adapter | batch별 선택 recommendation 조회 |
| `CatalogRecord` / `RecommendationRecord` | 예제 | provider 응답의 불변 record |
| `EnrichedProduct` / `EnrichmentWarning` | 예제 | caller에게 반환하는 불변 결과와 안전한 warning |
| `bluetape.collections.distinct` | `bluetape-collections` | 첫 등장 순서를 유지하며 중복 provider 작업 제거 |
| `bluetape.collections.chunked` | `bluetape-collections` | 고정 크기 batch 생성 및 batch size 검증 |
| `bluetape.asyncio.map_bounded` | `bluetape-async` | 전역 동시성, 전체 timeout, task 생성과 cleanup 소유 |

애플리케이션은 domain policy를 소유합니다. `bluetape-py`는 validation,
collection transform, bounded task lifecycle에 필요한 작은 API를 제공합니다.

## Sequence Diagram

![제한된 Catalog Enrichment Sequence Diagram](docs/images/sequence.png)

[Sequence Diagram SVG source 열기](docs/images/sequence.svg).

Service는 먼저 ID를 trim하고 ASCII 형식과 길이를 검증한 뒤 uppercase로
정규화합니다. `distinct`와 `chunked`로 provider batch를 만들고, 필수·선택 작업을
하나의 ordered list에 담아 `map_bounded`를 한 번 호출합니다. Provider 작업은 중복
ID를 공유하지만 마지막 단계에서 정규화된 입력 occurrence마다 `EnrichedProduct`를
다시 만듭니다.

## Packages and APIs

Runtime 예제는 다음 API를 사용합니다.

- `bluetape-core`: `bluetape.core.require_instance`,
  `bluetape.core.require_not_blank`;
- `bluetape-collections`: `bluetape.collections.distinct`,
  `bluetape.collections.chunked`;
- `bluetape-async`: `bluetape.asyncio.map_bounded`.

모든 package는 고정된 `bluetape-py` source commit
[`4b7458f22cea0a9e757b5fbf7f5ff4bc8c23cb9a`](https://github.com/bluetape4k/bluetape-py/tree/4b7458f22cea0a9e757b5fbf7f5ff4bc8c23cb9a)에서
해석합니다.

## Run

Workshop 저장소 root에서 Python 3.13.14 환경을 준비합니다.

```bash
uv sync --locked --python 3.13.14
```

결정적인 in-memory sample을 실행합니다.

```bash
uv run --locked python -m examples.catalog_enrichment
```

stdout은 `SKU-2`, `SKU-1`, `SKU-2` 순서의 JSON array입니다. 두 `SKU-2` 결과는
같고, recommendation을 제공하지 않은 `SKU-1`에는 다음 warning이 들어갑니다.

```json
{
  "code": "optional_record_missing",
  "message": "recommendation is unavailable",
  "product_id": "SKU-1",
  "provider": "recommendations"
}
```

## Failure, Timeout, and Cancellation

| 상황 | 공개 동작 |
|---|---|
| 필수 provider의 `ProviderUnavailable` | 안전한 `CatalogEnrichmentFailed`로 변환 |
| 필수 응답의 누락·추가 key 또는 잘못된 record | `response_invalid`로 fail closed |
| 선택 provider의 `ProviderUnavailable` | product별 `optional_provider_failed` warning |
| 선택 record 누락 또는 오류 | 안전한 `optional_record_missing` / `optional_record_invalid` warning |
| 전체 시간 초과 | native `TimeoutError` 유지 |
| caller task 취소 | native `CancelledError` 유지 |
| 예상하지 못한 provider defect | 원래 `ExceptionGroup` 전파 |

`map_bounded`는 실패, `TimeoutError`, `CancelledError`가 발생해도 자신이 만든 형제
task를 취소하고 cleanup이 끝난 뒤 caller에게 제어를 돌려줍니다. Service가 별도
semaphore나 task registry를 만들지 않는 이유입니다.

## Input and Trust Boundary

- 한 요청은 최대 1,000개 occurrence를 받습니다.
- product ID는 trim 후 64자 이하의 ASCII여야 하며 `[A-Z0-9]`로 시작하고 나머지는
  `[A-Z0-9._-]`만 사용할 수 있습니다.
- batch size는 1 이상 100 이하입니다.
- `concurrency_limit`은 1 이상 1,024 이하이며 모든 provider 작업에 함께 적용됩니다.
- provider mapping은 요청한 key와 record의 내부 `product_id`가 일치해야 합니다.
- provider exception detail과 잘못된 payload 값은 공개 error/warning에 넣지 않습니다.

Service는 log나 metric을 내보내지 않습니다. 실제 adapter가 telemetry를 추가한다면
caller가 소유한 안전한 ID와 집계값만 사용하고 원시 provider payload는 제외해야
합니다.

실제 adapter는 `ProviderUnavailable`을 예상 가능한 운영 장애에만 사용해야 합니다.
Programming defect를 이 예외로 감싸면 service가 버그를 warning으로 오인합니다.

## Tests

이 예제만 검증합니다.

```bash
uv run --locked pytest examples/catalog_enrichment/tests -q
```

Workshop 전체 gate도 실행할 수 있습니다.

```bash
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked pytest
```

테스트는 입력 한도, 중복 제거와 순서 복원, 필수·선택 응답 검증, 하나의 전역
동시성 한도, timeout, caller cancellation, 형제 task cleanup, network 없는 module
entry point와 다국어 문서 계약을 검증합니다.

## Cleanup and Troubleshooting

중지하거나 삭제할 server, container, file 또는 background process가 없습니다.
명령은 in-memory sample 하나를 출력한 뒤 종료하며 Docker가 필요하지 않습니다.

- `examples.catalog_enrichment`를 import할 수 있도록 저장소 root에서 실행하세요.
- 환경이 달라졌다면 local editable override를 추가하지 말고
  `uv sync --locked --python 3.13.14`를 다시 실행하세요.
- `TimeoutError`가 반복되면 provider timeout을 숨기지 말고 caller의 전체 timeout과
  `concurrency_limit`을 함께 점검하세요.
- 지원 source는 위 pinned commit이며 공개되지 않은 PyPI package 경로가 아닙니다.

## Source

- [models.py](models.py) — 불변 provider record와 caller 결과
- [errors.py](errors.py) — 안전한 공개 error와 required failure metadata
- [providers.py](providers.py) — 필수·선택 provider protocol
- [service.py](service.py) — validation, batching, bounded fan-out, response policy
- [__main__.py](__main__.py) — network 없는 독립 실행 entry point
- [tests](tests) — behavior, lifecycle, application, documentation 검증
