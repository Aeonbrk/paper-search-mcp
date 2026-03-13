# Ship Release Safely With CI Gates

This ExecPlan is a living document. The orchestrator is the single
writer for this file: workers return completion packets; the
orchestrator updates task `status`, `log`, and `files_changed`.

If this work is tracked in `docs/PLANS.md`, keep this file synchronized
with that tracker entry.

## Orchestration

Schema version: 1
Execution mode: multi-agent
Scheduler: waves
Max parallelism: 6
Shared-state policy: orchestrator-only
Plan updates: orchestrator-only
File-scope rule: each task must declare writes/creates; workers must not
write outside without escalation
Write-allowed set: writes ∪ creates

## Purpose / Big Picture

Ship a new PyPI release that includes the PMC adapter work, while reducing the
chance of publishing a broken build by:

- adding an offline unit-test gate to the PyPI publish workflow, and
- adding a PR/push CI workflow that runs the same offline gate.

Done looks like:

- `.github/workflows/publish.yml` runs offline tests before building/publishing,
- a new CI workflow runs on `push`/`pull_request` and executes the offline gate,
- the package version is bumped (default: `0.1.3` -> `0.1.4`) and tagged as
  `v0.1.4`,
- local validation evidence is recorded (commands + results).

Assumptions (explicit):

- Version bump target is `0.1.4` (patch bump); if you prefer `0.2.0`, update the
  version and tag steps accordingly.
- Offline gate is `PAPER_SEARCH_LIVE_TESTS=0 python -m unittest discover -q`.
- GitHub Actions uses `pip install -e .` for test gating (pip-parity); local
  validation continues to use `uv sync --locked` as documented in
  `docs/playbooks/validation.md`.

## Progress

- [x] (2026-03-13 15:25 BJT) Capture scope, constraints, and acceptance criteria.
- [x] (2026-03-13 15:25 BJT) Implement the planned changes.
- [x] (2026-03-13 15:25 BJT) Run validation and record evidence.
- [ ] (2026-03-13 15:25 BJT) Close review notes and summarize outcomes.

## Surprises & Discoveries

- Observation: `uv sync --locked` failed after bumping `pyproject.toml` version
  until `uv lock` refreshed `uv.lock` to match (`paper-search-mcp v0.1.3 ->
  v0.1.4`).
  Evidence: `uv sync --locked` reported lockfile out of date; `uv lock` printed
  `Updated paper-search-mcp v0.1.3 -> v0.1.4`, and the next `uv sync --locked`
  succeeded.

## Decision Log

- Decision: proceed with both publish-gating and CI workflow
  Rationale: publish workflow is tag-triggered and should fail fast; CI prevents
  regressions landing on `main`.
  Date/Author: 2026-03-13 / Codex

- Decision: default version bump is `0.1.4`
  Rationale: pre-1.0 versioning; patch bump is sufficient for shipping PMC search
  and offline fixtures with minimal downstream disruption.
  Date/Author: 2026-03-13 / Codex

## Outcomes & Retrospective

Summarize what shipped, what did not, and what was learned. Compare the
result to the purpose above.

## Context and Orientation

Key repo surfaces involved in this change:

- `pyproject.toml`: PyPI version metadata (`[project].version`).
- `.github/workflows/publish.yml`: tag-triggered PyPI publish workflow.
- `docs/playbooks/release.md`: documented release checklist.
- `docs/playbooks/validation.md`: default local validation sequence; offline gate.
- `uv.lock`: local dependency lockfile used by `uv sync --locked`.
- `tests/`: unit tests; live-network tests are gated by `PAPER_SEARCH_LIVE_TESTS`.

## Task Graph (Dependencies)

### T1: Track This Work In docs/PLANS.md

depends_on: []
reads: [
  docs/PLANS.md,
  docs/exec-plans/active/2026-03-13_1525_BJT_release-safety-ci-gates.md,
]
writes: [docs/PLANS.md]
creates: []
mutex: file:docs/PLANS.md
description: Add an `Active` tracker entry so this ExecPlan is discoverable and
  stays synchronized with the system-of-record tracker.
acceptance: `docs/PLANS.md` includes this ExecPlan under `## Active` with all
  required fields.
validation: rg -n "2026-03-13_1525_BJT_release-safety-ci-gates\\.md" docs/PLANS.md
status: done
log: (orchestrator) created task packet.
log: (orchestrator) added `## Active` tracker entry in `docs/PLANS.md` for this
  ExecPlan (required fields present).
files_changed: docs/PLANS.md

### T2: Add Offline Test Gate To Publish Workflow

depends_on: []
reads: [.github/workflows/publish.yml]
writes: [.github/workflows/publish.yml]
creates: []
mutex: file:.github/workflows/publish.yml
description: Ensure the tag-triggered PyPI publish workflow runs offline checks
  before build/publish.
acceptance: The workflow runs offline unit tests
  (`PAPER_SEARCH_LIVE_TESTS=0 python -m unittest discover -q`) before
  `python -m build`.
acceptance: Publishing is blocked if unit tests fail.
validation: python - <<'PY'
import pathlib
text = pathlib.Path(".github/workflows/publish.yml").read_text()
assert "PAPER_SEARCH_LIVE_TESTS=0" in text
assert "python -m unittest discover -q" in text
assert text.index("python -m unittest discover -q") < text.index("python -m build")
print("publish.yml: offline test gate present and runs before build")
PY
status: done
log: (orchestrator) added `pip install -e .` plus an offline gate step running
  `compileall` and `unittest discover -q` before `python -m build`.
log: (orchestrator) validated gate presence + ordering via local Python snippet.
files_changed: .github/workflows/publish.yml

### T3: Add CI Workflow For Offline Gate (PR/Push)

depends_on: []
reads: []
writes: []
creates: [.github/workflows/ci.yml]
mutex: file:.github/workflows/ci.yml
description: Add a lightweight CI workflow that runs the offline gate on
  `push`/`pull_request` before tagging a release.
acceptance: CI triggers on `pull_request` and `push` to `main`.
acceptance: CI runs offline unit tests
  (`PAPER_SEARCH_LIVE_TESTS=0 python -m unittest discover -q`).
validation: python - <<'PY'
import pathlib
text = pathlib.Path(".github/workflows/ci.yml").read_text()
assert "pull_request" in text
assert "push" in text
assert "branches" in text and "main" in text
assert "PAPER_SEARCH_LIVE_TESTS=0" in text
assert "python -m unittest discover -q" in text
print("ci.yml: triggers and offline test gate present")
PY
status: done
log: (orchestrator) created PR/push CI workflow running offline `compileall`
  and `unittest discover -q`.
log: (orchestrator) validated workflow triggers + gate presence via local Python
  snippet.
files_changed: .github/workflows/ci.yml

### T4: Bump Package Version

depends_on: []
reads: [pyproject.toml, docs/playbooks/release.md, uv.lock]
writes: [pyproject.toml, uv.lock]
creates: []
mutex: file:pyproject.toml
description: Update `[project].version` to match the next release tag (default
  `v0.1.4`).
acceptance: `pyproject.toml` version equals `0.1.4`.
acceptance: `uv sync --locked` does not require updating `uv.lock` after the
  version bump.
validation: python - <<'PY'
import pathlib, re
text = pathlib.Path("pyproject.toml").read_text()
m = re.search(
    r'^version\\s*=\\s*\"([0-9]+\\.[0-9]+\\.[0-9]+)\"\\s*$',
    text,
    re.M,
)
assert m, "missing [project].version"
assert m.group(1) == "0.1.4", f"expected 0.1.4, got {m.group(1)}"
print("pyproject.toml: version is 0.1.4")
PY
status: done
log: (orchestrator) bumped `[project].version` from `0.1.3` to `0.1.4`.
log: (orchestrator) refreshed `uv.lock` via `uv lock` (expected after version
  metadata changes).
log: (orchestrator) validated version via local Python snippet.
files_changed: pyproject.toml
files_changed: uv.lock

### T5: Update Release Playbook To Mention CI/Test Gates

depends_on: [T2, T3, T4]
reads: [
  docs/playbooks/release.md,
  .github/workflows/publish.yml,
  .github/workflows/ci.yml,
]
writes: [docs/playbooks/release.md]
creates: []
mutex: file:docs/playbooks/release.md
description: Keep the documented release checklist consistent with the new
  publish-gating and CI workflows.
acceptance: `docs/playbooks/release.md` instructs to wait for CI to be green
  before tagging a release.
acceptance: `docs/playbooks/release.md` mentions the publish workflow runs tests
  before build/publish.
validation: markdownlint docs/playbooks/release.md
status: done
log: (orchestrator) updated the checklist to require green `CI` before tagging
  and to mention publish runs offline checks before build/publish.
log: (orchestrator) markdownlint `docs/playbooks/release.md` passed.
files_changed: docs/playbooks/release.md

### T6: Local Validation (Offline, Full Default Sequence)

depends_on: [T2, T3, T4, T5]
reads: [docs/playbooks/validation.md]
writes: []
creates: []
description: Run the documented validation sequence locally and capture pass/fail
  evidence.
acceptance: The full default validation sequence from
  `docs/playbooks/validation.md` passes.
validation: uv sync --locked
validation: markdownlint README.md \
  $(find docs -type f -name '*.md' | sort)
validation: uv run python -m compileall paper_search_mcp tests
validation: uv run python -c \
  "import paper_search_mcp.server as s; print(s.mcp.name)"
validation: PAPER_SEARCH_LIVE_TESTS=0 uv run python -m unittest discover -q
status: done
log: (orchestrator) Passed: uv sync --locked (after refreshing uv.lock).
log: (orchestrator) Passed: markdownlint on README.md + docs/*.md.
log: (orchestrator) Passed: uv run python -m compileall paper_search_mcp tests.
log: (orchestrator) Printed MCP name: paper_search_server.
log: (orchestrator) Passed: offline unittest discover -q (OK, skipped=25).

### T7: Commit And Push (No Tag Yet)

depends_on: [T1, T6]
reads: [
  .github/workflows/publish.yml,
  .github/workflows/ci.yml,
  pyproject.toml,
  uv.lock,
  docs/playbooks/release.md,
  docs/PLANS.md,
]
writes: [.git/]
creates: []
mutex: repo:git-state
description: Stage only intended files, commit, and push to `origin/main` so CI
  can run before tagging.
acceptance: The commit contains only the planned release-safety changes.
acceptance: `origin/main` points at the new commit and the workspace is clean
  after pushing.
validation: git status -sb
validation: git diff --name-only
validation: git diff --name-only --cached
status: planned

### T8: Verify CI Is Green On The Pushed Commit

depends_on: [T7]
reads: []
writes: []
creates: []
description: Confirm the PR/push CI workflow is green on the pushed commit before
  tagging a release.
acceptance: GitHub Actions CI run for the pushed commit is green.
validation: (manual) GitHub Actions UI shows the `CI` workflow succeeded for the
  commit on `main`.
status: planned

### T9: Tag And Push Release Tag

depends_on: [T8]
reads: []
writes: [.git/]
creates: [.git/refs/tags/v0.1.4]
mutex: repo:git-state
description: Tag `v0.1.4` on the verified commit and push the tag to trigger
  PyPI publish.
acceptance: Local tag `v0.1.4` points at the intended commit.
acceptance: Remote tag `v0.1.4` exists on `origin`.
validation: git show-ref --tags v0.1.4
validation: git ls-remote --tags origin v0.1.4
status: planned

### T10: Verify Publish Workflow And PyPI Release

depends_on: [T9]
reads: []
writes: []
creates: []
description: Confirm the publish workflow succeeded and the release is available
  on PyPI.
acceptance: GitHub Actions `Publish to PyPI` workflow is green for tag `v0.1.4`.
acceptance: PyPI has version `0.1.4` available for `paper-search-mcp`.
validation: (manual) GitHub Actions UI shows the tag workflow succeeded and PyPI
  lists version 0.1.4.
status: planned

## Plan of Work

1. Track this work in `docs/PLANS.md` so it is visible and stays synchronized.
2. Add a test gate to `.github/workflows/publish.yml` so publishing blocks on
   offline unit tests.
3. Add `.github/workflows/ci.yml` so PR/push CI runs the offline gate
   automatically.
4. Bump `pyproject.toml` version to the next release version (default `0.1.4`).
5. Update `docs/playbooks/release.md` so the checklist mentions CI and publish
   gates.
6. Run the full local validation sequence from `docs/playbooks/validation.md`.
7. Commit and push to `origin/main` (no tag yet), wait for CI to go green, then
   tag and push `v0.1.4`.
8. Verify publish workflow and PyPI release availability.

## Concrete Steps

1. From `[repo-root]`, update `docs/PLANS.md` `## Active` section to include:

   - Status / Difficulty / Rationale / ExecPlan / Evidence / Next steps /
     Last updated.

2. From `[repo-root]`, edit `.github/workflows/publish.yml` to run:

       pip install -e .
       PAPER_SEARCH_LIVE_TESTS=0 python -m compileall paper_search_mcp tests
       PAPER_SEARCH_LIVE_TESTS=0 python -m unittest discover -q

   before:

       python -m build

3. From `[repo-root]`, create `.github/workflows/ci.yml` that:

   - checks out the repo
   - sets up Python (>= 3.10)
   - installs the package (`pip install -e .`)
   - runs `PAPER_SEARCH_LIVE_TESTS=0 python -m compileall paper_search_mcp tests`
   - runs `PAPER_SEARCH_LIVE_TESTS=0 python -m unittest discover -q`

4. From `[repo-root]`, bump `pyproject.toml` version to the intended release
   value (default `0.1.4`).

   If `uv sync --locked` fails after the bump, refresh `uv.lock`:

       uv lock

5. Update `docs/playbooks/release.md` to mention:

   - do not tag until `CI` is green on the pushed commit,
   - publish workflow runs offline tests before build/publish.

6. Run the local validation sequence from `docs/playbooks/validation.md`:

       uv sync --locked
       markdownlint README.md \
         $(find docs -type f -name '*.md' | sort)
       uv run python -m compileall paper_search_mcp tests
       uv run python -c "import paper_search_mcp.server as s; print(s.mcp.name)"
       uv run python -m unittest discover -q

7. Commit and push (no tag yet). Before staging, confirm you are not sweeping
   unrelated changes:

       git status -sb
       git diff --name-only

   Stage only intended paths:

       git add pyproject.toml \
         uv.lock \
         .github/workflows/publish.yml \
         .github/workflows/ci.yml \
         docs/playbooks/release.md \
         docs/PLANS.md \
         docs/exec-plans/active/2026-03-13_1525_BJT_release-safety-ci-gates.md

   Commit and push:

       git commit -m "Release: add CI + publish test gate"
       git push

8. Verify CI is green for the pushed commit on `main` (GitHub Actions UI).

9. Tag and push the tag:

       git tag v0.1.4
       git push origin v0.1.4

   Expect: GitHub Actions `Publish to PyPI` workflow runs on the tag and blocks
   on the offline test gate if anything is broken.

## Completion Packet (Workers)

**Status:** `[COMPLETED | FAILED | BLOCKED]`

**Files modified/created:**

- `path/to/file`

**Acceptance criteria coverage:**

- `criterion` -> `how it is satisfied`

**Validation performed:**

- `command` -> `result`

**Open risks / blockers:**

- `notes`

**Suggested follow-ups:**

- `optional follow-up`

## Validation and Acceptance

- CI shows green on PR/push for the offline gate.
- CI is green on the pushed `main` commit before tagging.
- Tagging `v0.1.4` triggers publish, which runs tests before building/publishing.
- Publish workflow is green and PyPI shows version `0.1.4`.

## Idempotence and Recovery

- Safe to rerun: unit tests, `compileall`, CI runs, and re-tagging a new version
  (do not move an existing tag on a published release).
- If publish fails: fix on `main`, bump version, and tag a new version.

## Revision Notes

- 2026-03-13 / Codex — Created this plan to ship PMC support with safer release
  gates.
- 2026-03-13 / Codex — Revised after plan review: added `docs/PLANS.md` tracking,
  split commit/tag steps behind CI verification, and tightened validation.
