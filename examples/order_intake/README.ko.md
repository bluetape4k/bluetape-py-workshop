# 검증된 주문 접수

[English](README.md) | 한국어

이 실행 가능한 예제는 애플리케이션이 `bluetape-core`, `bluetape-logging`,
`bluetape-testing`의 작은 API를 조합해 예측 가능한 주문 접수 경계를 만드는 방법을
보여 줍니다.

## Scenario

파트너가 요청, 파트너, 주문, SKU, 수량 값을 담은 주문 command를 제출합니다.
애플리케이션은 이 값들을 결정적인 순서로 검증하고, 승인된 caller 입력을 그대로
보존하며, 안전한 correlation ID를 로그 record에 추가하고, 불변 승인 주문 또는
안정적인 공개 problem을 반환해야 합니다.

비목표는 다음과 같습니다.

- HTTP, ASGI, FastAPI, database, queue, cache 또는 retry adapter를 추가하지 않습니다.
- credential, 결제, 재고 또는 fulfillment를 처리하지 않습니다.
- workshop 공용 utility layer를 만들지 않고 애플리케이션이 policy를 소유합니다.
- Docker 또는 background service에 의존하지 않습니다.

## Architecture

![검증된 주문 접수 Architecture](docs/images/architecture.png)

[Architecture SVG source 열기](docs/images/architecture.svg).

| 구성 요소 | 소유자 | 책임 |
|---|---|---|
| `PartnerOrderCommand` | 예제 | 불변 입력 계약. caller 값을 정규화하거나 다시 쓰지 않음 |
| `OrderIntakeService` | 예제 | 검증 순서, 공개 오류 mapping, context event, 승인 결과 |
| `AcceptedOrder` / `OrderIntakeProblem` | 예제 | 안정적인 성공 및 실패 projection |
| `require_instance` / `require_not_blank` | `bluetape-core` | 작은 runtime validation primitive |
| `log_context` | `bluetape-logging` | 자동 reset을 제공하는 scoped correlation metadata |
| `ContextLogFilter`와 handler | 애플리케이션 entry point | context 주입, format, severity, 출력 destination |

라이브러리 package는 집중된 primitive를 제공합니다. Domain policy, 검증 순서, 오류
어휘와 logging 설정은 애플리케이션의 책임으로 남습니다.

## Sequence Diagram

![검증된 주문 접수 Sequence Diagram](docs/images/sequence.png)

[Sequence Diagram SVG source 열기](docs/images/sequence.svg).

두 경로는 같은 안전한 log context를 열고 같은 순서로 field를 검증합니다. 유효한
경로는 `order_intake.accepted`를 기록하고 `AcceptedOrder`를 반환합니다. 유효하지
않은 경로는 library exception을 `InvalidOrderCommand`로 mapping하고
`order_intake.rejected`를 기록하며, 위험한 값을 `str()` 또는 `repr()`로 평가하지
않은 채 cause를 보존합니다. Context를 벗어나면 검증이나 logging이 예외를
발생시켜도 모든 correlation metadata가 reset됩니다.

## Packages and APIs

Runtime 예제는 다음 API를 사용합니다.

- `bluetape-core`: `bluetape.core.require_instance`,
  `bluetape.core.require_not_blank`;
- `bluetape-logging`: `bluetape.logging.log_context`,
  `bluetape.logging.ContextLogFilter`;
- `bluetape-testing`: focused test의 `bluetape.testing.eventually`.

테스트는 성공, validation 실패 또는 logger 실패 이후 context가 유출되지 않음을
증명하기 위해 `bluetape.logging.get_log_context`도 사용합니다.

모든 package는 고정된 `bluetape-py` source commit
[`4b7458f22cea0a9e757b5fbf7f5ff4bc8c23cb9a`](https://github.com/bluetape4k/bluetape-py/tree/4b7458f22cea0a9e757b5fbf7f5ff4bc8c23cb9a)에서
해석합니다.

## Run

Workshop 저장소 root에서 고정된 Python 3.13.14 환경을 준비합니다.

```bash
uv sync --locked --python 3.13.14
```

결정적인 sample을 실행합니다.

```bash
uv run --locked python -m examples.order_intake
```

예상 stderr log:

```text
INFO order_intake.accepted request_id=request-1001 partner_id=partner-acme order_id=order-1001
```

예상 stdout JSON:

```json
{"order_id": "order-1001", "partner_id": "partner-acme", "quantity": 2, "request_id": "request-1001", "sku": "SKU-BLUE-42", "status": "accepted"}
```

## Tests

예제 test만 실행합니다.

```bash
uv run --locked pytest examples/order_intake/tests -q
```

Workshop 전체 gate를 실행합니다.

```bash
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked pytest
```

Test suite는 승인 입력, 결정적인 validation 실패, 위험한 값, contextual record,
context reset, logger 실패, `eventually` API, module entry point와 이 다국어 문서
계약을 다룹니다.

## Logging and Data Boundary

비밀이 아닌 correlation identifier인 `request_id`, `partner_id`, `order_id`만 log
context에 넣습니다. Credential, token, 개인정보, 결제 정보 또는 민감한 payload를
이 field에 넣지 마세요. Source가 민감하다면 command를 만들기 전에 identifier를
hash하거나 대체하세요. SKU와 quantity는 business payload이므로 의도적으로 log
context에서 제외합니다.

Service는 root logger를 변경하지 않습니다. Entry point는 자체 handler를 만들고
제거하며, 주입된 logger 실패는 context cleanup 이후 caller에게 전파됩니다.

## Cleanup and Troubleshooting

중지하거나 삭제할 server, container, file 또는 background process가 없습니다.
명령은 sample 주문 하나를 처리한 뒤 종료하며 Docker는 필요하지 않습니다.

- `examples.order_intake`를 import할 수 있도록 저장소 root에서 명령을 실행하세요.
- 의존성 해석이 달라졌다면 local editable override를 추가하지 말고
  `uv sync --locked --python 3.13.14`를 다시 실행하세요.
- 지원하는 source는 위의 pinned commit이며 `v0.1.0` release tag 또는 공개되지 않은
  PyPI package 경로가 아닙니다.
- Validation 오류는 예상된 domain 결과입니다. 원시 입력값을 log에 남기지 말고
  `field`와 안정적인 message를 확인하세요.

## Source

- [models.py](models.py) — 불변 입력 및 승인 출력 계약
- [errors.py](errors.py) — 공개 오류 type과 안전한 problem mapping
- [service.py](service.py) — 결정적인 validation과 contextual logging
- [__main__.py](__main__.py) — 독립 실행 가능한 애플리케이션 entry point
- [tests](tests) — behavior, isolation, application, documentation 검증
