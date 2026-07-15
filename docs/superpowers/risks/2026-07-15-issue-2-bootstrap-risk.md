# Issue #2 bootstrap risk record

## Scope

Issue #2 adds a non-package Python project, source-only Git dependencies, a
committed lockfile, contract tests, CI, and bilingual documentation. It adds no
domain service, public Python API, database, coroutine ownership, or Docker-backed
execution.

## Triggered risks

| Risk | Signal | Mitigation | Rollback or rerun boundary |
|---|---|---|---|
| Git source resolves from the wrong repository, commit, or subdirectory | dependency contract fails while parsing `pyproject.toml` or `uv.lock` | all ten sources use one canonical repository/full commit; tests verify repository, fragment, and subdirectory | restore the last reviewed `pyproject.toml`/`uv.lock` pair; regenerate both together and rerun fresh sync |
| Optional Fory/native provider enters the default lane | `pyfory`, `lz4`, `cramjam`, or `zstandard` appears in lock or installed metadata | negative lock and `importlib.metadata` assertions | remove the extra/dependency drift, regenerate the lock, delete `.venv`, and rerun the full ladder |
| Testcontainers import contacts Docker or creates lifecycle work | isolated import calls Docker client construction, process start, or thread start | patched import probe with a ten-second subprocess bound | stop; do not weaken the probe or use Docker to make it pass; re-evaluate the pinned upstream commit |
| PR code gains credentials or CI validates a merge ref | CI contract detects unsafe event, secret mapping, persisted credentials, or missing head expression | ordinary `pull_request`, read-only contents, no secrets, non-persisted credentials, explicit PR head checkout | revert the workflow change and rerun CI contract plus actionlint before push |
| Action SHA becomes stale or invalid | canonical GitHub commit lookup fails | verify every action SHA against its official repository before committing | select a reviewed official tag commit, update workflow/test/plan atomically, rerun actionlint |
| Hosted runner, network, or cache fails transiently | setup/fetch fails while source and tests are unchanged | Ubuntu line, tool versions, timeout, head/tool diagnostics, lock-keyed setup-uv cache | rerun only the unchanged exact head; code, lock, or test failures require a new commit |
| English/Korean reader facts drift | documentation contract or locale fact comparison fails | one task owns both locale files; commands, links, commits, and issue order are structural assertions | revert or repair both locale files together; never merge a one-locale status change |

## Evidence-backed N/A

- Database consistency and backend migration: no database/provider implementation.
- Coroutine cancellation and concurrency: no async API or task lifecycle.
- Public API compatibility and KDoc: no publishable workshop package or reusable helper.
- Hot-path benchmark: no application execution path.
- Release/publish/BOM/changelog: no release artifact, publication, or existing changelog change.

## Remaining external variables

Git/network availability and GitHub's `ubuntu-24.04` hosted image are not
bit-for-bit immutable. The workshop claims reproducible project inputs and
bounded recovery, not a fully immutable external runner.
