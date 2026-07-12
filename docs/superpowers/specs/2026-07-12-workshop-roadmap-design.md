# bluetape-py-workshop 로드맵 설계

## 문제

`bluetape-py`는 Python 백엔드 개발을 위한 여러 focused distribution을 제공하지만,
각 기능을 실제 서비스 경계에서 조합하는 독립 예제 저장소가 없다. 새 워크숍은
단순 API 호출 모음이 아니라 입력 검증, 비동기 처리, 캐시, 직렬화, 로깅, 테스트와
자원 정리를 보여 주는 실행 가능한 백엔드 예제를 제공해야 한다.

## 목표

- 공개 저장소 `bluetape4k/bluetape-py-workshop`을 `develop` 기본 브랜치로 운영한다.
- 하나의 로드맵 Epic에서 학습 순서와 upstream 의존성을 관리한다.
- 현재 구현된 패키지는 독립 실행 가능한 하위 이슈로 나눈다.
- 아직 계획 또는 개발 중인 기능은 upstream 이슈가 충족될 때까지 명시적으로
  blocked 상태로 둔다.
- 각 예제는 영문/한글 README, 실행 명령, 성공·실패·경계 테스트를 갖는다.

## 현재 근거

### bluetape-py

현재 source workspace에는 다음 distribution이 있다.

- foundation: `bluetape-core`, `bluetape-logging`, `bluetape-testing`
- concurrency and transforms: `bluetape-async`, `bluetape-collections`
- data boundaries: `bluetape-codec`, `bluetape-compression`, `bluetape-serde`
- state: `bluetape-cache`
- integration testing: `bluetape-testcontainers`

PyPI 배포는 아직 보류 중이다. 웹 어댑터는 upstream #21과 #22, Redis provider와
coordination은 upstream #51, #54, #55, #56에서 추적한다.

### 기존 워크숍

- `bluetape-go-workshop`은 하나의 milestone-aligned Epic에서 application-shaped
  예제와 현재 안정 버전 기준을 관리한다.
- `bluetape-rs-workshop`은 foundation에서 시작해 collections/async 같은 다음
  milestone이 앞선 패턴을 재사용하도록 학습 경로를 만든다.
- `bluetape4k-workshop`은 광범위한 기능을 독립 구현 가능한 도메인 예제로 나누고,
  컨테이너나 외부 서비스 경로를 선택적 검증으로 둔다.

## 접근 방식

### 선택: 통합 로드맵 Epic과 focused child issues

하나의 장기 로드맵 Epic을 만들고, 현재 구현 가능한 예제와 upstream-blocked 예제를
하위 이슈로 등록한다. 이 방식은 Go 워크숍의 일관된 로드맵과 Rust 워크숍의 단계별
학습 경로를 함께 취한다.

### 거절: milestone마다 별도 Epic

명확하지만 초기 저장소에서 Epic 수가 먼저 늘어난다. 실제 구현과 release cadence가
자리 잡은 뒤 필요하면 로드맵 Epic에서 milestone Epic을 분리한다.

### 거절: 기술 영역별 Epic

Web, cache, serde 같은 영역 구분은 장기적으로 유용하지만 upstream API가 아직
확정되지 않은 영역이 많다. 현재는 focused issue label로 충분하다.

## 저장소 메타데이터

- visibility: public
- default branch: `develop`
- description: `Runnable Python backend service examples using bluetape-py`
- topics: `python`, `backend`, `workshop`, `examples`, `bluetape`
- milestones: `0.1.0` for the first runnable lane, `0.2.0` for upstream-backed expansion
- assignee: `debop` for every Epic and issue

Milestone assignment is explicit:

- `0.1.0`: bootstrap, validated intake, bounded enrichment, local cache,
  payload processing, Redis integration testing, and the integrated order backend
- `0.2.0`: ASGI/FastAPI boundary research and Redis cache coordination

Labels use the existing sibling convention where practical:

- type: `type:epic`, `type:feature`, `type:research`, `type:chore`
- area: `area:foundation`, `area:async`, `area:cache`, `area:serde`,
  `area:testcontainers`, `area:web`, `area:integration`
- dependency: `blocked:upstream`
- common GitHub labels: `documentation`, `enhancement`

## Epic

Title: `[Epic] Milestone-aligned bluetape-py backend workshop roadmap`

The Epic records:

- the current source and publication baseline;
- the learning path from foundation examples to an integrated backend;
- child issue dependency order;
- exact upstream `bluetape-py` issue links;
- the rule that source-only packages must use a pinned Git ref until a published
  package baseline is available;
- bilingual documentation, deterministic verification, and sequential
  Docker-backed checks.

The roadmap Epic has no milestone because it spans multiple workshop releases.

## Initial child issues

### 1. Bootstrap the repository

Title: `chore: bootstrap the bluetape-py workshop repository`

Create the Python 3.13+ `uv` workspace, Ruff and pytest configuration, CI,
bilingual root documentation, and authoritative local validation commands.
Decide and pin the initial Git source baseline for source-only packages.

### 2. Validated order intake service

Title: `feat: add a validated order intake service`

Use `bluetape-core`, `bluetape-logging`, and `bluetape-testing` to validate an
order request, attach request context to application-owned logging, and test
success, invalid input, context reset, and log capture.

### 3. Bounded catalog enrichment service

Title: `feat: add a bounded catalog enrichment service`

Use `bluetape-collections` and `bluetape-async` for deterministic batching and
bounded provider fan-out. Prove required versus optional provider failures,
timeouts, cancellation propagation, result ordering, and task cleanup.

### 4. Cached product catalog service

Title: `feat: add a cached product catalog service`

Use sync and async `bluetape-cache` contracts for hit, miss, expiry, bounded
capacity, loader failure, and cancellation behavior without global cache state.

### 5. Bounded payload processing service

Title: `feat: add a bounded payload processing service`

Compose `bluetape-codec`, `bluetape-compression`, and `bluetape-serde` at an
explicit trust boundary. Cover strict metadata, malformed input, decompression
limits, unsupported formats, round trips, and caller-owned data preservation.

### 6. Redis-backed integration test workshop

Title: `feat: add a Redis-backed integration test workshop`

Use `bluetape-testcontainers` for Redis lifecycle and readiness. Keep the
example focused on integration-test infrastructure until a production Redis
provider is available. Run Docker-backed validation sequentially.

### 7. ASGI and FastAPI workshop boundary research

Title: `research: define the ASGI and FastAPI workshop boundary`

Link upstream #21 and #22. Decide what remains application-owned, how request
context and cancellation cross the ASGI boundary, and when a workshop may adopt
`bluetape-fastapi`. This issue belongs to milestone `0.2.0` and can proceed as
research without waiting for the upstream implementation issue to close.

### 8. Redis cache coordination examples

Title: `feat: add Redis cache coordination examples`

Link upstream #51, #54, #55, and #56. Mark `blocked:upstream` until the required
provider contracts are merged and pinned. Cover distributed load coordination,
near-cache invalidation, failure isolation, cancellation, and cleanup.

### 9. Integrated order backend

Title: `feat: compose the foundation examples into an order backend`

Combine the approved foundation, enrichment, cache, and payload-processing
examples without copying reusable helpers. Keep infrastructure adapters at the
application boundary and prove end-to-end success, partial provider failure,
timeout/cancellation, and orderly shutdown.

## Issue contract

Every child issue must include:

- user-facing scenario and explicit non-goals;
- exact `bluetape-py` distributions and upstream issue links;
- prerequisites and blocked conditions;
- public behavior, error, timeout, cancellation, and resource ownership;
- success, failure, empty/boundary, and lifecycle tests where applicable;
- runnable local commands and expected evidence;
- `README.md` and `README.ko.md` impact;
- diagram requirement only when the visual materially reduces cognitive load.

## Failure modes and controls

1. **Workshop claims packages that are not publishable or stable.**
   Pin exact Git refs, label source-only dependencies, and update the baseline
   only through a dedicated issue.
2. **Examples become thin snippets instead of services.**
   Require an inbound boundary, application workflow, explicit failure policy,
   and tests for every example.
3. **Planned upstream APIs are reimplemented locally.**
   Mark the issue `blocked:upstream`; reusable code belongs in `bluetape-py`.
4. **Cancellation or resources leak.**
   Require bounded cancellation and cleanup assertions for async, cache,
   container, and integration flows.
5. **Container tests destabilize CI.**
   Keep deterministic tests in the default lane and run Docker-backed checks
   sequentially in their own job.

## Compatibility and dependency policy

- Target Python 3.13+.
- Use `uv` as the dependency and lockfile authority.
- Do not depend on an unpublished package name as if it were available from
  PyPI.
- Use exact Git tag or commit pins for source-only packages; local path overrides
  are developer conveniences, not the committed reproducibility contract.
- Frameworks and clients remain application dependencies unless `bluetape-py`
  explicitly owns an adapter.

## Acceptance criteria

- The public repository exists with the approved name, description, topics,
  and `develop` default branch.
- The roadmap Epic and nine child issues exist and are linked.
- All GitHub artifacts are assigned to `debop` and have verified labels and
  milestones.
- Upstream-blocked issues name their exact release/adoption gate.
- No example source is implemented during the roadmap-registration phase.

## Definition of done for this phase

- Repository metadata and initial bilingual landing documentation are live.
- This design is committed and reviewed.
- The Epic and all child issues are created from the reviewed design.
- Live GitHub metadata is re-read after creation.
- Work stops before example implementation and reports the recommended first
  implementation issue.
