# Issue #2 written design review

## 결론

- Review target: `2026-07-15-issue-2-workshop-bootstrap-design.md`, `WIP.md`
- Review shape: six independent read-only perspectives plus main-thread integration
- Initial result: P0=0, P1=14
- Final recheck: P0=0, P1=0
- Gate: user written-spec approval pending; implementation and implementation-plan work have not started

## 독립 검토 결과

| Perspective | Initial P0 | Initial P1 | Final P0 | Final P1 |
|---|---:|---:|---:|---:|
| Performance | 0 | 2 | 0 | 0 |
| Stability | 0 | 3 | 0 | 0 |
| Security | 0 | 2 | 0 | 0 |
| Operator/Ops | 0 | 3 | 0 | 0 |
| Developer/API | 0 | 3 | 0 | 0 |
| User/caller | 0 | 1 | 0 | 0 |

## 반영한 P1 결정

- `uv 0.11.28`, `uv-build 0.11.28`, Python `3.13.14`를 project/local/CI
  reference로 고정했다.
- `pyfory`, `lz4`, `cramjam`, `zstandard`가 default lock과 installed metadata에
  없음을 negative assertion으로 증명한다.
- Testcontainers boundary import가 Docker client, process, background thread,
  container 또는 cleanup obligation을 만들지 않음을 검증한다.
- CI event/ref, exact PR head checkout, minimum token permissions, credential
  non-persistence, secret-free PR lane, timeout, concurrency를 명시했다.
- actionlint는 Go toolchain과 module version을 모두 고정한 exact pre-PR command로
  실행한다.
- WIP resume checkpoint에 full head, PR state, last gate, validation evidence,
  blocker, next command, runnable status를 고정했다.
- 모든 validation-time `uv run`은 `--locked`를 사용한다.

## Main-thread adjudication

Performance review는 `bluetape-testcontainers`를 future issue group으로 옮기는 대안을
제시했다. 이 대안은 적용하지 않았다. 사용자가 승인한 Issue #2 dependency model은 열
개 focused distribution을 하나의 root baseline으로 고정하는 것이며, source drift를
모든 milestone issue에서 조기에 검출하는 이점이 설치 비용보다 크다고 판단했다.
대신 Docker runtime side effect를 별도 negative test로 금지한다.

나머지 P2/P3는 cache/concurrency, transient failure와 rollback, example dependency
boundary, README prerequisites/cleanup/troubleshooting, diagram source/render/alt-text 계약으로
설계에 반영했다. GitHub-hosted `ubuntu-24.04` image와 network availability는 외부
변수로 남으므로 완전한 bit-for-bit 환경 재현성은 주장하지 않는다.

## 다음 gate

사용자가 written design을 승인한 뒤에만 implementation/test plan을 작성한다. 그 plan은
TDD 순서, exact dependency declarations, action SHA/version resolution, CI workflow,
README parity, fresh verification을 task 단위로 고정해야 한다.
