# bluetape-py-workshop

[English](README.md) | 한국어

[`bluetape-py`](https://github.com/bluetape4k/bluetape-py)를 사용하는 실행 가능한
애플리케이션 형태의 Python 백엔드 예제 저장소입니다.

## 현재 상태

의존성 해석, source provenance, provider 격리, lint, 테스트를 lockfile과 자동화된
계약으로 검증하는 저장소 기반은 실행할 수 있습니다. 실행 가능한 domain
scenario는 [검증된 주문 접수](examples/order_intake/README.ko.md),
[제한된 catalog enrichment](examples/catalog_enrichment/README.ko.md),
[캐시 기반 product catalog](examples/cached_product_catalog/README.ko.md)입니다.
각 예제는 서로 맞춘 다국어 안내, Architecture, Sequence Diagram을 제공합니다.

현재 이슈, 의존 순서, 검증 근거와 다음 작업은 [WIP.md](WIP.md)에서 확인하세요.

## 마일스톤 0.1.0 학습 경로

| 순서 | 이슈 | 학습 결과 | 선행 이슈 |
|---:|---|---|---|
| 1 | [#2](https://github.com/bluetape4k/bluetape-py-workshop/issues/2) | 재현 가능한 workshop 기반 | 없음 |
| 2 | [#3](https://github.com/bluetape4k/bluetape-py-workshop/issues/3) | 검증된 주문 접수 | #2 |
| 3 | [#4](https://github.com/bluetape4k/bluetape-py-workshop/issues/4) | 제한된 catalog enrichment | #2 |
| 4 | [#5](https://github.com/bluetape4k/bluetape-py-workshop/issues/5) | 캐시된 product catalog | #2 |
| 5 | [#6](https://github.com/bluetape4k/bluetape-py-workshop/issues/6) | 제한된 payload 처리 | #2 |
| 6 | [#7](https://github.com/bluetape4k/bluetape-py-workshop/issues/7) | Redis Testcontainers 통합 | #2 |
| 7 | [#8](https://github.com/bluetape4k/bluetape-py-workshop/issues/8) | 통합 주문 backend | #3, #4, #5, #6 |

## 요구 사항

- Python 3.13 이상. 기준 interpreter는 Python 3.13.14입니다.
- uv 0.11.28. 프로젝트 설정이 다른 uv 버전을 거부합니다.
- 공개 `bluetape-py` 저장소에 접근할 수 있는 Git 환경.
- 결정적인 foundation, 주문 접수, catalog enrichment, cached product catalog
  경로에는 Docker가 필요하지 않습니다.

## 설치

저장소 root에서 실행합니다.

```bash
uv sync --locked --python 3.13.14
```

이 명령은 commit된 lockfile로 환경을 생성합니다. Commit된 local path 또는 editable
override는 지원하지 않습니다.

## 의존성 기준선

열 개의 focused distribution을 모두 같은 source tree에서 해석합니다.

- 저장소: <https://github.com/bluetape4k/bluetape-py>
- Workshop source commit: `4b7458f22cea0a9e757b5fbf7f5ff4bc8c23cb9a`
- GitHub Release `v0.1.0` tag commit:
  `596e4898c915b55339521814ae7303953b50f4d2`
- PyPI focused-package publication: **HOLD**

GitHub Release는 workshop 설치 source가 아닙니다. 지원하는 경로는
`pyproject.toml`과 `uv.lock`의 commit-pinned Git source를 사용하는 root `uv sync`
명령입니다.

기준선에는 `bluetape-core`, `bluetape-logging`, `bluetape-testing`,
`bluetape-async`, `bluetape-collections`, `bluetape-cache`, `bluetape-codec`,
`bluetape-compression`, `bluetape-serde`, `bluetape-testcontainers`가 포함됩니다.
Apache Fory와 native compression provider는 기본 환경에 설치하지 않습니다.
Testcontainers wrapper import가 Docker에 접속하거나 container, process, background
thread를 시작하지 않는 것도 테스트합니다.

## 검증

CI와 같은 locked gate를 실행합니다.

```bash
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked pytest
```

의존성 기준선 테스트만 실행할 수도 있습니다.

```bash
uv run --locked pytest tests/test_dependency_baseline.py -q
```

## 예제 문서 계약

이슈 #3부터 모든 실행 가능한 예제는 서로 일치하는 `README.md`와 `README.ko.md`에
다음을 제공합니다.

1. 비즈니스 형태의 Scenario와 명시적인 비목표;
2. source에 근거한 Architecture diagram과 ownership 설명;
3. 요청 또는 lifecycle 경로를 표현한 source-backed Sequence Diagram;
4. 사용하는 정확한 `bluetape-py` distribution과 API;
5. 선행 조건, 작업 directory, 실행 명령, 관찰 가능한 결과, targeted test, cleanup
   명령과 troubleshooting 경계.

모든 예제는 두 README 언어 문서에 Architecture와 Sequence Diagram을 반드시 직접
표시해야 합니다. 두 시각 자료 중 하나라도 빠지면 예제가 완료된 것으로 보지 않습니다.
Diagram source와 rendered asset은 구현 code가 생긴 뒤에만 만듭니다. 두 언어 문서는
같은 English-label asset을 공유하고 관련 source로 연결합니다.

## 현재 제한 사항

마일스톤 `0.1.0`에서는 ASGI/FastAPI adapter, production Redis provider, package
publication 또는 release automation을 추가하지 않습니다. Docker-backed 예제는 이슈
#7에서 추가한 뒤 순차 실행합니다.
