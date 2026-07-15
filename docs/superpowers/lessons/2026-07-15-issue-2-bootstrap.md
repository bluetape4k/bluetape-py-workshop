# Issue #2 bootstrap lessons

## Worktree-qualified edits are part of correctness

`apply_patch` resolves paths from the primary checkout tool context, not from a
shell command's worktree directory. A bare path can therefore edit `develop`
while tests run in a feature worktree. Use worktree-qualified paths and verify
both the primary checkout and worktree status immediately after every durable
document batch.

## A checkpoint cannot contain its own commit hash

A committed WIP file cannot self-reference the hash of the commit that contains
it. Record the last validated content head, then treat a checkpoint-only commit
as a new head that still needs CI evidence. Labeling the field accurately avoids
false exact-head claims after interruption.

## Release tags and source-only baselines are separate provenance facts

GitHub Release `v0.1.0` points to `596e4898c915b55339521814ae7303953b50f4d2`,
while this workshop needs the later source-only commit
`4b7458f22cea0a9e757b5fbf7f5ff4bc8c23cb9a`. Display both hashes and state which
one drives installation; a release label must not imply that it authenticates a
later unsigned commit.

## Verify action pins against the canonical repository

A pinned SHA copied from a sibling workflow can become stale or invalid. The
previous setup-uv SHA no longer resolved through the official repository, so the
workshop selected and verified the official v8.3.2 commit. Validate every action
pin live before creating a new workflow and keep that SHA under a contract test.

## Installing a wrapper is different from using its runtime

`bluetape-testcontainers` intentionally installs Docker client libraries in the
root baseline so all milestone issues detect source drift. Provider-free in this
repository means no Docker connection/container/process/thread is created during
the deterministic lane, not that the wrapper distribution is absent. An isolated
import-side-effect test states and proves that boundary precisely.

## Validate the entire branch, not only the working tree

Plain `git diff --check` can report a clean working tree while earlier commits
still contain whitespace errors. Before PR creation, run the check against the
base (`git diff --check origin/develop`) so the evidence covers the complete PR
diff.
