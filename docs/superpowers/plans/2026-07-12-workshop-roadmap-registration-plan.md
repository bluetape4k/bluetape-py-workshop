# Workshop Roadmap Registration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Register the approved roadmap Epic and nine dependency-ordered issues with verified milestones, labels, assignee, and live links.

**Architecture:** GitHub is the source of truth for roadmap execution. The committed design remains the decision record; GitHub milestones and labels classify work, the Epic owns ordering and upstream gates, and focused child issues own independently implementable examples.

**Tech Stack:** GitHub CLI/API, Git, Markdown

---

## File map

- Modify: `docs/superpowers/specs/2026-07-12-workshop-roadmap-design.md`
  - Add the verified live Epic and child issue links after creation.
- Create transiently: `.omx/issues/*.md`
  - Hold exact GitHub bodies during registration; `.omx/` is ignored and must not be committed.
- Modify: `docs/superpowers/plans/2026-07-12-workshop-roadmap-registration-plan.md`
  - Check completed steps and attach live evidence before the final commit.

No Python source, package metadata, CI workflow, or example implementation changes in this plan.

### Task 1: Revalidate the approved baseline

- [ ] **Step 1: Confirm repository and branch state**

Run:

```bash
repo-status
git branch --show-current
git rev-parse HEAD
gh repo view bluetape4k/bluetape-py-workshop \
  --json url,visibility,description,defaultBranchRef,repositoryTopics,hasIssuesEnabled
```

Expected: clean `develop`, `origin/develop` synchronized, public repository,
issues enabled, and the approved description/topics.

- [ ] **Step 2: Confirm the upstream feature gates are still current**

Run:

```bash
gh issue view 21 --repo bluetape4k/bluetape-py --json number,title,state,url
gh issue view 22 --repo bluetape4k/bluetape-py --json number,title,state,url
for issue in 51 54 55 56; do
  gh issue view "$issue" --repo bluetape4k/bluetape-py \
    --json number,title,state,url
done
```

Expected: live issue records are available. Preserve the approved blocked gate
unless the provider issues are all closed and a stable adoption ref exists.

### Task 2: Create milestones and labels

- [ ] **Step 1: Create milestone `0.1.0`**

Run only when an exact-title lookup returns no milestone:

```bash
gh api --method POST repos/bluetape4k/bluetape-py-workshop/milestones \
  -f title='0.1.0' \
  -f description='First runnable bluetape-py workshop lane.'
```

Expected: one open `0.1.0` milestone.

- [ ] **Step 2: Create milestone `0.2.0`**

Run only when an exact-title lookup returns no milestone:

```bash
gh api --method POST repos/bluetape4k/bluetape-py-workshop/milestones \
  -f title='0.2.0' \
  -f description='Upstream-backed web and Redis expansion lane.'
```

Expected: one open `0.2.0` milestone.

- [ ] **Step 3: Create or reconcile structured labels**

Use `gh label create --force` for this exact label set:

| Label | Color | Description |
|---|---|---|
| `type:epic` | `5319e7` | Epic issue grouping related work |
| `type:feature` | `1d76db` | Runnable workshop feature |
| `type:research` | `d4c5f9` | Research and boundary decision |
| `type:chore` | `cfd3d7` | Repository or tooling work |
| `area:foundation` | `0e8a16` | Core validation, logging, and testing |
| `area:async` | `0052cc` | Async and collection workflows |
| `area:cache` | `fbca04` | Local and distributed cache examples |
| `area:serde` | `c2e0c6` | Codec, compression, and serialization |
| `area:testcontainers` | `b60205` | Container-backed integration testing |
| `area:web` | `0366d6` | ASGI and web application boundaries |
| `area:integration` | `e99695` | Cross-package service composition |
| `blocked:upstream` | `d73a4a` | Blocked by an upstream package or release gate |

Expected: all labels exist with exact names, colors, and descriptions. Preserve
the default `documentation` and `enhancement` labels.

### Task 3: Register the roadmap Epic

- [ ] **Step 1: Create the Epic body**

Create `.omx/issues/epic.md` with these sections and facts:

```markdown
## Goal

Maintain the milestone-aligned roadmap for application-shaped Python backend examples built with `bluetape-py`.

## Baseline Policy

- Target Python 3.13+ and use `uv` as dependency and lockfile authority.
- Use exact Git tags or commits for source-only `bluetape-py` distributions until a published package baseline is available.
- Keep examples independently runnable and application-shaped; reusable helpers belong in `bluetape-py`.
- Keep `README.md` and `README.ko.md` synchronized.
- Prove success, failure, empty/boundary, cancellation, timeout, and cleanup behavior when relevant.
- Run Docker-backed checks sequentially and use `bluetape-testcontainers` wrappers where available.

## Learning Path

1. Bootstrap the repository and dependency baseline.
2. Establish validation, logging, and testing in an order intake service.
3. Add deterministic collection transforms and bounded async enrichment.
4. Add local sync and async caching.
5. Add bounded codec, compression, and serde boundaries.
6. Prove Redis test infrastructure without inventing a production provider.
7. Compose the current examples into one framework-neutral order backend.
8. Research the ASGI/FastAPI boundary.
9. Adopt Redis coordination only after its upstream release gate passes.

## Upstream Gates

- ASGI/FastAPI boundary: bluetape-py #21 and #22.
- Redis coordination: bluetape-py #51, #54, #55, and #56.
- PyPI publication remains unavailable until bluetape-py enables it; committed dependencies must not pretend otherwise.

## Child Issues

Child links are added after creation in dependency order.

## Done When

- Every child issue is independently reviewable and carries exact prerequisites.
- Root navigation and bilingual docs remain aligned with implemented examples.
- Deterministic local verification is the default; container-heavy paths are explicit and sequential.
- The integrated backend reuses focused examples without copying reusable library code.
```

- [ ] **Step 2: Create and verify the Epic**

Run:

```bash
gh issue create --repo bluetape4k/bluetape-py-workshop \
  --title '[Epic] Milestone-aligned bluetape-py backend workshop roadmap' \
  --body-file .omx/issues/epic.md \
  --assignee debop \
  --label 'type:epic,documentation,enhancement'
```

Expected: one open Epic, assigned to `debop`, with no milestone because it spans
multiple releases.

### Task 4: Register the `0.1.0` focused issues

For every issue below, create the exact body under `.omx/issues/`, call
`gh issue create` with the listed metadata, then immediately verify title,
body, labels, milestone, assignee, state, and URL using `gh issue view`.

- [ ] **Step 1: Bootstrap issue**

Title: `chore: bootstrap the bluetape-py workshop repository`

Labels: `type:chore`, `documentation`, `area:foundation`

Milestone: `0.1.0`

Body requirements:

- Goal: create the Python 3.13+ `uv` workspace, Ruff, pytest, CI, and authoritative local commands.
- Dependency policy: select an exact Git ref for source-only distributions; local path overrides are not the committed contract.
- Acceptance: `uv sync --locked`, Ruff format/lint, pytest, `git diff --check`, bilingual root README, thin repo-local `AGENTS.md`.
- Non-goal: no domain example implementation.

- [ ] **Step 2: Validated order intake issue**

Title: `feat: add a validated order intake service`

Labels: `type:feature`, `enhancement`, `area:foundation`

Milestone: `0.1.0`

Body requirements:

- Use `bluetape-core`, `bluetape-logging`, and `bluetape-testing`.
- Model a framework-neutral order intake application service.
- Prove valid requests, blank/invalid fields, public exception mapping, request-context reset, log capture, and caller-owned value preservation.
- Add matching English/Korean example README files and root navigation.
- Non-goal: ASGI/FastAPI adapters remain in the research issue.

- [ ] **Step 3: Bounded catalog enrichment issue**

Title: `feat: add a bounded catalog enrichment service`

Labels: `type:feature`, `enhancement`, `area:async`

Milestone: `0.1.0`

Body requirements:

- Use `bluetape-collections` for deterministic grouping/chunking and `bluetape-async` for bounded fan-out.
- Prove required versus optional provider failures, stable result order, timeout, caller cancellation, and task cleanup with bounded tests.
- Depend on the bootstrap issue; reuse foundation validation/logging where useful.
- Add matching README locales and run commands.

- [ ] **Step 4: Cached product catalog issue**

Title: `feat: add a cached product catalog service`

Labels: `type:feature`, `enhancement`, `area:cache`

Milestone: `0.1.0`

Body requirements:

- Use `bluetape-cache` sync and async local TTL loading caches.
- Prove hit, miss, expiry, bounded capacity, loader failure, cancellation, and no global cache state.
- Depend on the bootstrap issue; keep Redis behavior out of scope.
- Add matching README locales and deterministic tests.

- [ ] **Step 5: Bounded payload processing issue**

Title: `feat: add a bounded payload processing service`

Labels: `type:feature`, `enhancement`, `area:serde`

Milestone: `0.1.0`

Body requirements:

- Compose `bluetape-codec`, `bluetape-compression`, and `bluetape-serde` at an explicit trust boundary.
- Prove strict metadata, malformed input, unsupported formats, decompression limits, round trips, and caller-owned input preservation.
- Keep Apache Fory in an explicit trusted-internal optional lane; do not load it in the default example.
- Add matching README locales and deterministic tests.

- [ ] **Step 6: Redis integration testing issue**

Title: `feat: add a Redis-backed integration test workshop`

Labels: `type:feature`, `enhancement`, `area:testcontainers`

Milestone: `0.1.0`

Body requirements:

- Use `bluetape-testcontainers` Redis lifecycle, readiness, and connection details.
- Prove started/unstarted behavior, cleanup, bounded readiness, and sequential Docker validation.
- Keep production Redis cache providers and distributed coordination out of scope.
- Add deterministic non-Docker coverage where practical and matching README locales.

- [ ] **Step 7: Integrated order backend issue**

Title: `feat: compose the foundation examples into an order backend`

Labels: `type:feature`, `enhancement`, `area:integration`

Milestone: `0.1.0`

Body requirements:

- Depend on the validated intake, enrichment, cache, and payload-processing issues.
- Compose their public application boundaries without copying reusable helpers.
- Prove end-to-end success, invalid input, partial provider failure, timeout/cancellation, cache behavior, payload limits, and orderly shutdown.
- Keep the `0.1.0` service framework-neutral; HTTP adoption follows the ASGI/FastAPI research decision.
- Add bilingual architecture/sequence documentation and a diagram only when it reduces cognitive load.

### Task 5: Register the `0.2.0` upstream-aligned issues

- [ ] **Step 1: ASGI/FastAPI research issue**

Title: `research: define the ASGI and FastAPI workshop boundary`

Labels: `type:research`, `documentation`, `area:web`

Milestone: `0.2.0`

Body requirements:

- Link `https://github.com/bluetape4k/bluetape-py/issues/21` and `/22`.
- Decide application-owned versus library-owned request context, error mapping, cancellation/disconnect handling, lifespan resources, and optional framework dependencies.
- Compare direct FastAPI use, a framework-neutral ASGI boundary, and future `bluetape-fastapi` adoption.
- Produce an accepted decision before any framework-specific workshop issue starts.
- Research may proceed while upstream #22 remains open.

- [ ] **Step 2: Redis coordination issue**

Title: `feat: add Redis cache coordination examples`

Labels: `type:feature`, `enhancement`, `area:cache`, `area:integration`, `blocked:upstream`

Milestone: `0.2.0`

Body requirements:

- Link `https://github.com/bluetape4k/bluetape-py/issues/51`, `/54`, `/55`, and `/56`.
- Block implementation until required provider contracts are merged, validated, and available through an exact stable adoption ref.
- Cover distributed load coordination, bounded waits, failure isolation, near-cache invalidation, cancellation, cleanup, and sequential Redis integration tests.
- Do not create workshop-owned Redis provider abstractions.

### Task 6: Link and verify the live roadmap

- [ ] **Step 1: Replace the initial Epic child-link sentence with live links**

Query every issue by its exact title, sort the resulting URLs in approved
dependency order, and edit the Epic body so `## Child Issues` contains a
Markdown task list. Preserve all other Epic sections byte-for-byte.

Expected: nine unique child links and no stale initial child-link sentence.

- [ ] **Step 2: Add live links to the committed design**

Use `apply_patch` to add a `## Live GitHub artifacts` section to
`docs/superpowers/specs/2026-07-12-workshop-roadmap-design.md`. Record the Epic
and all nine child issue URLs in the same dependency order.

Expected: exactly ten unique GitHub issue URLs in the section.

- [ ] **Step 3: Verify live metadata in one report**

Run:

```bash
gh issue list --repo bluetape4k/bluetape-py-workshop --state open --limit 50 \
  --json number,title,labels,milestone,assignees,url
gh api 'repos/bluetape4k/bluetape-py-workshop/milestones?state=open'
gh label list --repo bluetape4k/bluetape-py-workshop --limit 100 \
  --json name,color,description
```

Expected:

- one Epic plus nine child issues;
- every artifact assigned to `debop`;
- seven child issues in `0.1.0`, two in `0.2.0`, Epic without milestone;
- Redis coordination carries `blocked:upstream`;
- ASGI/FastAPI research does not carry `blocked:upstream`;
- all required labels have exact names and metadata.

- [ ] **Step 4: Validate and commit the durable evidence**

Run:

```bash
git diff --check
rg -n 'T[B]D|T[O]DO|F[I]XME|\[f[i]ll' docs/superpowers \
  --glob '*.md'
git status --short
git add docs/superpowers/specs/2026-07-12-workshop-roadmap-design.md \
  docs/superpowers/plans/2026-07-12-workshop-roadmap-registration-plan.md
git commit -m 'docs: register workshop roadmap'
git push origin develop
```

Expected: validation passes, `.omx/` is not tracked, the durable links and
checked plan are committed, and local `develop` matches `origin/develop`.

### Task 7: Stop before example implementation

- [ ] **Step 1: Render the phase DoD**

Report repository URL, commit, Epic and child URLs, milestone/label/assignee
verification, unchecked items, and exact P0/P1 status. Recommend the bootstrap
issue as the first implementation unit.

- [ ] **Step 2: Hold the implementation boundary**

Do not create Python source, dependency metadata, workflows, PRs, releases, or
example branches. Wait for the user's explicit selection of the first issue.
