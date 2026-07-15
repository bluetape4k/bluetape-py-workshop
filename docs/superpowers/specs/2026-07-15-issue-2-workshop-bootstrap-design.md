# Issue #2 workshop bootstrap 설계

## 상태

- Workflow: Type A - Full Feature
- Issue: <https://github.com/bluetape4k/bluetape-py-workshop/issues/2>
- High-level design approved in conversation: 2026-07-15
- Written spec approved in conversation: 2026-07-15
- Independent review: P0=0, P1=0
- Review record: `../reviews/2026-07-15-issue-2-design-review.md`
- Target branch: `chore/issue-2-workshop-bootstrap`
- Base branch: `develop`

## 문제

`bluetape-py-workshop`에는 로드맵과 초기 README만 있고 Python 프로젝트,
lockfile, 테스트 도구, CI가 없다. 한편 예제가 소비해야 할 focused
distribution 대부분은 `bluetape-py` source workspace에는 존재하지만 PyPI에는
아직 게시되지 않았다. 로컬 경로에 의존하면 다른 개발자와 CI가 같은 환경을 재현할
수 없고, 움직이는 `develop` branch를 직접 참조하면 같은 lockfile이 같은 소스를
뜻하지 않게 된다.

Issue #2는 이후 모든 예제가 공유할 재현 가능한 실행 기반과 문서 계약을 만든다.
도메인 예제 구현은 포함하지 않는다.

## 목표

1. Python 3.13+와 `uv`를 authority로 사용하는 non-package root project를 만든다.
2. milestone `0.1.0`이 사용할 focused distribution을 하나의 정확한
   `bluetape-py` commit으로 고정한다.
3. committed `uv.lock`, Ruff, pytest, deterministic GitHub Actions CI를 제공한다.
4. `WIP.md`, `README.md`, `README.ko.md`, repo-local `AGENTS.md`에 동일한 setup과
   validation contract를 기록한다.
5. 이후 예제가 따라야 할 bilingual README와 source-backed diagram 규칙을 고정한다.

## 제약과 비목표

- Python은 `>=3.13`이며 local/CI reference interpreter는 `3.13.14`이다.
- local/CI reference `uv`는 `0.11.28`이며 committed `uv.lock`이 dependency
  resolution authority다.
- default sync와 CI는 Docker, Apache Fory, native compression provider를 요구하지
  않는다.
- local path override는 committed configuration에 포함하지 않는다.
- source-only package를 PyPI에서 사용할 수 있다고 문서화하지 않는다.
- 도메인 서비스, HTTP adapter, production Redis provider, publish/release는 구현하지
  않는다.
- 아직 source가 없는 architecture/sequence diagram을 만들지 않는다.

## 현재 근거

### Repository 상태

- `bluetape-py-workshop` base는 `origin/develop`의
  `9b9d1a02a7a5da1bd75fd14de88958198d56f5a4`이며 clean하다.
- milestone `0.1.0`에는 open issue #2부터 #8까지 7개가 있다.
- issue #3부터 #7은 #2를 요구하고, #8은 #3부터 #6을 요구한다.

### Upstream 상태

- 고정 대상 commit은 release tag 이후의 source-only baseline인
  `4b7458f22cea0a9e757b5fbf7f5ff4bc8c23cb9a`이다.
- `v0.1.0` tag는 `596e4898c915b55339521814ae7303953b50f4d2`를
  가리키며 고정 대상 commit의 provenance를 보증하지 않는다. 2026-07-15 현재 고정
  대상은 canonical repository의 `origin/develop`에 포함돼 있다. 서명되지 않은
  commit이므로 signature를 trust root로 주장하지 않고 repository URL, full hash,
  branch containment를 함께 기록한다.
- 이 commit에는 `core`, `logging`, `testing`, `async`, `collections`, `cache`,
  `codec`, `compression`, `serde`, `testcontainers` distribution이 모두 있다.
- GitHub Release `v0.1.0`은 존재하지만 release note는 PyPI publication hold를
  명시한다.
- 각 distribution은 Python `>=3.13`, version `0.1.0`, `uv_build` backend를
  사용한다.

### 참고한 workshop 패턴

- `bluetape-go-workshop`은 root `WIP.md`에 current milestone, scope, next examples,
  decision log를 둔다.
- `bluetape-go-workshop`과 `bluetape4k-workshop`은 root catalog와 example별
  영/한 README를 함께 유지한다.
- 구현된 예제 문서는 scenario, architecture, sequence, run/test 정보를 source와
  연결하고 같은 시각 자산을 locale 간 공유한다.

### 공식 uv 근거

uv는 `[tool.uv.sources]`에서 Git repository, exact `rev`, package
`subdirectory`를 지정할 수 있다.

<https://docs.astral.sh/uv/concepts/projects/dependencies/>

## 대안

### 선택: distribution별 Git source와 공통 commit

Root dependencies에 필요한 distribution을 명시하고, 각 source에 같은 Git URL과
`rev`, package별 `subdirectory`를 지정한다.

장점:

- package/import 경계가 `pyproject.toml`에 드러난다.
- 모든 개발자와 CI가 같은 source tree를 사용한다.
- package별 사용 상태와 lockfile provenance를 확인할 수 있다.
- local checkout 유무와 무관하다.

비용:

- source entry가 반복된다.
- upstream commit을 바꿀 때 모든 entry와 lockfile을 함께 갱신해야 한다.

반복은 재현성과 auditability를 위한 의도적인 비용으로 수용한다.

### 거절: `bluetape` meta distribution 하나만 참조

표면상 설정은 짧지만 workshop이 실제 사용하는 focused distribution 경계가 숨겨진다.
또한 upstream meta package의 workspace source 설정을 외부 project가 동일하게 해석할
것이라고 가정해야 한다. Example별 package mapping과 default-install 격리를 검증하기
어렵기 때문에 거절한다.

### 거절: local path 또는 editable source

로컬 개발 속도는 빠르지만 CI와 다른 checkout에서 재현되지 않는다. 승인된 issue
contract도 local path override를 committed reproducibility contract 밖에 두도록
요구하므로 거절한다.

## 프로젝트 구조

```text
.
├── .github/workflows/ci.yml
├── AGENTS.md
├── README.md
├── README.ko.md
├── WIP.md
├── docs/superpowers/
│   ├── plans/
│   └── specs/
├── tests/
│   ├── test_dependency_baseline.py
│   └── test_documentation_contract.py
├── pyproject.toml
└── uv.lock
```

Root project는 배포 대상이 아니므로 `[tool.uv] package = false`를 사용한다. 예제
package/workspace 구조는 각 issue가 실제 source와 독립 실행 경계를 추가할 때 결정한다.
Git source의 isolated build에는 root
`[tool.uv] required-version = "==0.11.28"`과
`build-constraint-dependencies = ["uv-build==0.11.28"]`를 적용해 upstream의
`uv_build>=0.11.28,<0.12` 범위가 실행마다 달라지지 않게 한다.

## 의존성 모델

Root dependency set은 issue #2가 고정하도록 요구한 다음 distribution을 포함한다.

| Distribution | Import boundary | First consumer |
|---|---|---|
| `bluetape-core` | `bluetape.core` | #3 |
| `bluetape-logging` | `bluetape.logging` | #3 |
| `bluetape-testing` | `bluetape.testing` | #3 and repository tests |
| `bluetape-async` | `bluetape.asyncio` | #4 |
| `bluetape-collections` | `bluetape.collections` | #4 |
| `bluetape-cache` | `bluetape.cache` | #5 |
| `bluetape-codec` | `bluetape.codec` | #6 |
| `bluetape-compression` | `bluetape.compression` | #6 |
| `bluetape-serde` | `bluetape.serde` | #6 |
| `bluetape-testcontainers` | `bluetape.testcontainers` | #7 |

Dependency declarations use `==0.1.0`, while `tool.uv.sources` chooses the exact
Git source. The lockfile must resolve every source to the approved full commit.

Development dependencies are declared under `[dependency-groups].dev` as `pytest`,
`pytest-asyncio`, and Ruff. The default `uv sync` includes this group. Future
runtime-only commands may use `--no-default-groups`, but issue #2 validation does
not. Optional Fory and native compression extras are not selected.

Issue #2에서 열 개 distribution을 모두 root baseline으로 설치하는 것은 승인된
milestone integration 결정이다. `bluetape-testcontainers`가 가져오는 Docker client
library의 설치 비용은 #7 이전에도 발생하지만, package/source drift를 모든 issue에서
일찍 발견하는 이점을 선택한다. 이 결정은 Docker daemon 접속이나 container 실행을
허용한다는 뜻이 아니며, default validation은 아래 negative side-effect test로 그
경계를 증명한다.

## 검증 가능한 계약

### Dependency baseline

`tests/test_dependency_baseline.py`는 세 authority를 구분한다. `tomllib`으로
`pyproject.toml` declaration을 읽고, `uv.lock`에서 Git provenance를 확인하며,
`importlib.metadata`와 실제 import는 synchronized environment만 검증한다.

- required distribution/import 목록이 빠짐없이 고정돼 있다.
- 모든 Git source가 같은 repository와 exact commit을 사용한다.
- source subdirectory가 expected package path와 일치한다.
- exact `uv-build==0.11.28` build constraint가 있다.
- forbidden default extras와 local path sources가 없다.
- freshly locked/synchronized default environment의 `uv.lock`과
  `importlib.metadata` 모두에 `pyfory`, `lz4`, `cramjam`, `zstandard` distribution이
  없다.
- required import boundaries를 실제 environment에서 import할 수 있다.
- Docker SDK client constructor, `subprocess.Popen`, `threading.Thread.start`를
  호출되면 실패하도록 가로챈 뒤 `bluetape.testcontainers` boundary를 import해
  daemon 접속, container/process/thread 생성, cleanup obligation이 없음을 확인한다.

### Documentation contract

`tests/test_documentation_contract.py`는 root README locale pair와 `WIP.md`를
검증한다.

- 영어 README는 `English | [한국어](README.ko.md)`를 제공한다.
- 한국어 README는 `[English](README.md) | 한국어`를 제공한다.
- 두 README가 setup, dependency baseline, validation, milestone navigation을
  같은 범위로 포함한다.
- WIP issue queue가 #2부터 #8까지 포함하고 dependency order를 잃지 않는다.
- `AGENTS.md`가 Python `3.13+`, `uv sync --locked`, `uv run --locked` validation,
  bilingual README parity, independent example rule을 유지한다.

문장 번역의 품질은 review로 확인하고, test는 구조적 drift만 차단한다.

### CI contract

CI는 `ubuntu-24.04` GitHub-hosted runner와 `timeout-minutes: 15`에서 다음 순서로
실행한다.

1. pinned SHA의 `actions/checkout`; PR에서는
   `github.event.pull_request.head.sha`, push에서는 `github.sha`를 explicit `ref`로
   checkout하고 실제 `git rev-parse HEAD`를 출력;
2. pinned SHA의 `astral-sh/setup-uv` with `version: 0.11.28`;
3. pinned SHA의 `actions/setup-python` with Python `3.13.14`;
4. `uv --version`과 `python --version`을 출력하고 exact reference version을 검증;
5. `uv sync --locked --python 3.13.14`;
6. default-provider import와 negative side-effect smoke;
7. `uv run --locked ruff format --check .`과 `uv run --locked ruff check .`;
8. `uv run --locked pytest`.

Workflow는 ordinary `pull_request`의 `develop` base와 `develop` 대상 `push`만
사용하고 `pull_request_target`을 금지한다. Workflow/job `permissions`는
`contents: read`, checkout은 `persist-credentials: false`, PR lane은 secret이나
privileged credential을 받지 않는다. `concurrency`는 workflow와 PR/ref를 key로 하고
`cancel-in-progress: true`를 사용한다.

`setup-uv` cache를 명시적으로 활성화하고 `uv.lock`과 `pyproject.toml`을 invalidation
inputs로 사용한다. 설치 후 CI용 cache pruning을 수행한다. 첫 run은 cache miss여도
정상이며, 같은 head를 rerun했을 때 setup step의 cache-restore log를 evidence로
보존한다. Wall-clock threshold는 acceptance criterion으로 사용하지 않는다.

`git diff --check`는 local/pre-PR verification에서 실행한다. Workflow는 작은 YAML로
유지한다. 재현 가능한 pre-PR lane은
`GOTOOLCHAIN=go1.26.1 go run github.com/rhysd/actionlint/cmd/actionlint@v1.7.12
.github/workflows/ci.yml`을 사용하고 `go version`을 evidence에 기록한다. CI action과
`uv`는 별도로 pinned SHA/version을 사용하므로 Go/actionlint는 runtime test job의
dependency가 아니다.

## 문서 설계

### `WIP.md`

Milestone의 current target, exact dependency baseline, dependency map, execution
queue, documentation contract, working rules, validation, holds, decision log를
관리한다. 이 파일은 진행판이며 상세 spec/plan/review/lesson을 복제하지 않는다.
각 PR은 resume checkpoint의 branch/full head, PR state, 마지막 완료 gate와
command/result/timestamp, blocker, 다음 명령을 갱신한다.

### Root README locale pair

두 README는 같은 순서와 범위를 유지한다.

1. locale switch;
2. repository purpose;
3. milestone learning path;
4. Python/uv setup;
5. pinned upstream baseline and package status;
6. deterministic validation commands;
7. current example status and issue navigation;
8. source-only/PyPI hold caveat.

`README.md`는 영어, `README.ko.md`는 자연스러운 한국어로 작성한다. 코드, URL,
version, commit, command는 locale 간 동일하다.

### Diagram boundary

Issue #2는 실행 behavior가 없으므로 speculative diagram을 만들지 않는다. Issue #3부터
각 example의 source를 먼저 읽고 editable source와 rendered PNG를 보존하는 architecture
diagram 및 sequence diagram을 각각 하나씩 만든다. README는 meaningful alt text와
caption, 인접한 textual fallback, 구현 source link를 제공하고 두 locale은 같은
English-label asset path를 공유한다. 모든 asset은 render 후 full-size inspect한다.

## 실패 모드와 대응

### Upstream commit이 필요한 package를 포함하지 않음

Lock 또는 import contract가 실패한다. Git/network fetch의 일시적 실패면 같은
workshop head와 baseline을 변경하지 않고 rerun한다. 재현 가능한 package/content
mismatch면 구현을 멈추고 live `develop`, upstream diff, issue 상태를 읽는다. Baseline
교체는 명시적 승인 후 한 개의 새 full commit으로만 수행하고 `WIP.md`, README pair,
`pyproject.toml`, `uv.lock`, tests를 atomic하게 갱신해 full validation한다. 실패하면
이전 commit/lock pair로 rollback하며 서로 다른 package commit을 섞지 않는다.

### CI infrastructure 또는 잘못 병합된 bootstrap

Runner/network 장애만 같은 exact head에서 rerun한다. Code, lock, test failure는 수정
commit 없이 rerun으로 숨기지 않는다. Bootstrap이 잘못 병합되면 merge commit을
revert하고 `WIP.md` resume checkpoint를 마지막 검증된 head/lock으로 복구한 뒤 새
수정 PR에서 다시 검증한다.

### Git subdirectory source가 lock에서 다른 commit으로 정규화됨

`uv.lock` source provenance test가 실패한다. `pyproject.toml`과 lockfile을 함께
재생성하고 모든 entry가 같은 resolved commit인지 확인한다.

### PyPI fallback이 source 오류를 숨김

각 distribution source entry와 import/metadata test가 missing source를 실패시키도록
한다. `--no-sources` 성공을 요구하지 않는다. 현재 package publication hold에서는
Git source가 의도된 계약이다.

### Default lane에 optional provider가 유입됨

Lock과 installed metadata의 negative assertion이 `pyfory`, `lz4`, `cramjam`,
`zstandard` 부재를 확인한다. Import side-effect test는 Docker daemon 접속이나
container/process/thread 생성이 없음을 별도로 확인한다. optional extra가 root
dependency에 추가되거나 import만으로 runtime side effect가 발생하면 P1로 취급한다.

### README locale drift

구조 test와 writer review가 서로 다른 command, package status, issue navigation을
차단한다. 한 locale만 변경된 PR은 merge-ready가 아니다.

### CI는 통과하지만 local lock이 stale함

CI가 `--locked` sync를 사용하므로 stale lock은 setup 단계에서 실패한다. 로컬에서도
같은 command를 첫 검증으로 실행한다.

## 호환성과 변경 정책

- 최소 Python compatibility는 `>=3.13`; reference CI는 patch version을 고정한다.
- Upstream source upgrade는 별도 의식적인 change다. `WIP.md`, 두 README,
  `pyproject.toml`, `uv.lock`, baseline test를 함께 갱신한다.
- PyPI publication이 가능해져도 자동으로 registry source로 전환하지 않는다. 별도
  issue에서 artifact availability와 install compatibility를 검증한다.
- 각 example issue는 필요한 package boundary를 유지하되 동일 lockfile과 pinned
  source baseline을 공유한다.
- 모든 distribution이 root에 설치돼 있어도 example별 manifest/contract test는 그
  issue가 허용한 distribution 목록을 명시하고 source import가 그 경계를 넘지 않는지
  검사한다. 편의를 위해 undeclared milestone package를 import하지 않는다.

## Acceptance criteria 추적

| Issue criterion | Design proof |
|---|---|
| `uv sync --locked` succeeds | non-package root project, exact Git sources, committed lock, CI locked sync |
| Ruff format/lint pass | root Ruff config and `uv run --locked` CI/local commands |
| Root pytest passes | `uv run --locked pytest` structural baseline and documentation tests |
| `git diff --check` passes | pre-PR validation ladder |
| Equivalent README setup and baseline | aligned root README design plus structural drift tests |
| Thin `AGENTS.md` commands and rules | documentation test asserts the exact authoritative commands and workshop-specific rules |
| Exact tag or commit for source-only packages | common full commit in every Git source and lock provenance test |
| No Docker in deterministic lane | default extras excluded; Docker execution deferred to #7 |

## Definition of Done

- `WIP.md`, `pyproject.toml`, `uv.lock`, CI, tests, README locale pair, and
  `AGENTS.md` implement this design.
- `uv 0.11.28`, `uv-build 0.11.28`, Python `3.13.14`를 local/CI에서 검증한다.
- `uv sync --locked --python 3.13.14`, Ruff, pytest, `actionlint`, and
  `git diff --check` pass freshly.
- Dependency/source/import tests prove the exact upstream baseline and default
  provider boundary.
- README parity review reports no factual, command, link, or scope drift.
- Spec, plan, risk, review, and lesson artifacts are committed.
- P0=0 and P1=0 before PR creation.
- The issue-linked PR passes exact-head CI and live review, then stops at the
  fresh merge-approval gate.
