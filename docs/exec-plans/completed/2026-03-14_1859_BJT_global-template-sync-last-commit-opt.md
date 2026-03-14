# Sync global project template + optimize last commit

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

Align this repository with the updated global `.codex` project template
(`~/.codex/docs/design-docs/project-template.md`) while keeping the repo's
lean deviations explicit and honest.

Scope includes:

- Sync `docs/design-docs/project-template.md` to the updated global template
  (with repo-specific deviations preserved).
- Migrate navigation from `codemap/reference/CODEBASE_MAP.md` to the canonical
  `docs/CODEBASE_MAP.md` surface.
- Review and optimize the most recent commit ("Add search tools health check")
  with best-practice fixes.
- Amend/squash the last commit after validation (history rewrite).

Non-goals:

- Changing MCP tool names or the runtime identity (`paper_search_server`).
- Expanding adapter features or adding new sources.

## Progress

- [x] (2026-03-14 18:59 BJT) Capture scope, constraints, and acceptance criteria.
- [x] (2026-03-14 22:18 BJT) Implement the planned changes.
- [x] (2026-03-14 22:20 BJT) Run validation and record evidence.
- [x] (2026-03-14 22:26 BJT) Close review notes and summarize outcomes.

## Surprises & Discoveries

- Observation: `codemap/` was deleted in the working tree but still referenced
  by multiple docs.
  Resolution: Migrated navigation to `docs/CODEBASE_MAP.md` and removed
  `codemap/` references outside `docs/exec-plans/**`.

## Decision Log

- Decision: migrate navigation to `docs/CODEBASE_MAP.md`.
  Rationale: matches the updated global project template canonical layout.
  Date/Author: 2026-03-14 / user
- Decision: amend/squash the last commit instead of a follow-up commit.
  Rationale: keep a clean single-commit delta for this tranche of work.
  Date/Author: 2026-03-14 / user
- Decision: keep `docs/generated/` omitted (no codegen pipeline yet).
  Rationale: preserve repo's documented lean deviations.
  Date/Author: 2026-03-14 / orchestrator

## Outcomes & Retrospective

- Synced `docs/design-docs/project-template.md` to the updated global `.codex`
  template structure while keeping this repo’s deliberate omissions explicit.
- Migrated CODEBASE_MAP from `codemap/` to `docs/CODEBASE_MAP.md`, updated all
  primary references, and ensured `codemap/` is not referenced outside
  `docs/exec-plans/**`.
- Tightened `scripts/health_check_search_tools.py` UX and failure modes
  (fail-fast validation + clearer error output) and updated
  `docs/playbooks/validation.md` with stable CLI usage (`--json`, `--strict`,
  `--no-preflight`).
- Ran the offline validation gate (`uv sync`, `markdownlint`, `compileall`,
  offline `unittest discover`).
- Amended the last commit (history rewrite) to keep this tranche as a single
  clean delta.

## Context and Orientation

- Global canonical template: `~/.codex/docs/design-docs/project-template.md`
- Local template adoption doc: `docs/design-docs/project-template.md`
- Current navigation layer (to be migrated): `codemap/reference/CODEBASE_MAP.md`
- Canonical navigation surface (target): `docs/CODEBASE_MAP.md`
- Recent commit under review:
  - `scripts/health_check_search_tools.py`
  - `docs/playbooks/validation.md`

## Task Graph (Dependencies)

### T1: Sync local template adoption doc to updated global template

depends_on: []
reads:
  [~/.codex/docs/design-docs/project-template.md, docs/design-docs/project-template.md]
writes: [docs/design-docs/project-template.md]
creates: []
mutex: file:docs/design-docs/project-template.md
description: Update the repo-local template adoption doc to reflect the updated
  global template while keeping repo-specific deviations explicit (no frontend,
  no docs/generated, no repo-local control plane).
acceptance: `docs/design-docs/project-template.md` matches the global template
  structure and accurately describes the repo's adopted surfaces and
  deviations.
acceptance: The doc references `docs/CODEBASE_MAP.md` (not `codemap/`) for
  navigation.
validation: diff -u ~/.codex/docs/design-docs/project-template.md docs/design-docs/project-template.md
validation: markdownlint docs/design-docs/project-template.md
status: done
log: (orchestrator) created task packet.
log: (2026-03-14 22:18 BJT) Dispatched to worker Dirac
  (019cecb0-1ad5-7e12-90a9-3bf02bbc3058).
log: (2026-03-14 22:18 BJT) `markdownlint docs/design-docs/project-template.md`
  -> OK.
files_changed: docs/design-docs/project-template.md

### T2: Migrate CODEBASE_MAP to canonical docs surface and retire codemap

depends_on: []
reads:
  [AGENTS.md, ARCHITECTURE.md, README.md, codemap/reference/CODEBASE_MAP.md]
writes:
  [
    AGENTS.md,
    ARCHITECTURE.md,
    README.md,
    codemap/index.md,
    codemap/reference/CODEBASE_MAP.md,
  ]
creates: [docs/CODEBASE_MAP.md]
mutex: nav:codemap-migration
description: Create `docs/CODEBASE_MAP.md` from the existing CODEBASE_MAP
  content, update all primary read-order and validation references to point at
  the canonical path, and retire `codemap/` to match the updated global
  template. If `codemap/` is missing in the working tree, source the content
  from git history (`git show HEAD:codemap/reference/CODEBASE_MAP.md`).
acceptance: `docs/CODEBASE_MAP.md` exists and contains the previous CODEBASE_MAP
  content (no information loss).
acceptance: `AGENTS.md`, `ARCHITECTURE.md`, and `README.md` no longer reference
  `codemap/`.
acceptance: `codemap/` is removed from the repo (or reduced to a single minimal
  pointer file if complete removal would break tooling).
validation: rg -n \"codemap/\" AGENTS.md ARCHITECTURE.md README.md
validation: rg -n \"docs/CODEBASE_MAP.md\" AGENTS.md ARCHITECTURE.md README.md
validation: git show HEAD:codemap/reference/CODEBASE_MAP.md |
  diff -u - docs/CODEBASE_MAP.md
validation: markdownlint AGENTS.md ARCHITECTURE.md README.md docs/CODEBASE_MAP.md
status: done
log: (orchestrator) created task packet.
log: (2026-03-14 22:18 BJT) Dispatched to worker Ampere
  (019cecb0-2532-7143-a4ed-97e8e67640c1).
log: (2026-03-14 22:18 BJT) `git show HEAD:codemap/reference/CODEBASE_MAP.md |
  diff -u - docs/CODEBASE_MAP.md` -> OK.
log: (2026-03-14 22:18 BJT) `markdownlint AGENTS.md ARCHITECTURE.md README.md
  docs/CODEBASE_MAP.md` -> OK.
files_changed: docs/CODEBASE_MAP.md
files_changed: AGENTS.md
files_changed: ARCHITECTURE.md
files_changed: README.md
files_changed: codemap/index.md
files_changed: codemap/reference/CODEBASE_MAP.md

### T3: Review and optimize search health-check tooling

depends_on: []
reads: [scripts/health_check_search_tools.py, docs/playbooks/validation.md]
writes: [scripts/health_check_search_tools.py, docs/playbooks/validation.md]
creates: []
mutex: file:scripts/health_check_search_tools.py
description: Improve robustness and best-practice quality of the `search_*`
  health check script (CLI UX, network handling, output consistency), and align
  the validation playbook with the final usage.
acceptance: Script supports `--help` and compiles offline; output modes remain
  stable (`--raw`, `--json`), and `--strict` exit behavior is documented.
acceptance: `docs/playbooks/validation.md` describes how to run the script and
  reiterates that it performs live network calls.
validation: uv run python -m compileall scripts/health_check_search_tools.py
validation: uv run python scripts/health_check_search_tools.py --help
validation: (optional live)
  uv run python scripts/health_check_search_tools.py --json |
  python -m json.tool >/dev/null
validation: markdownlint docs/playbooks/validation.md
status: done
log: (orchestrator) created task packet.
log: (2026-03-14 22:18 BJT) Dispatched to worker Averroes
  (019cecb0-2f2b-71a0-a942-aad02093144b).
log: (2026-03-14 22:18 BJT) `uv run python -m compileall
  scripts/health_check_search_tools.py` -> OK.
log: (2026-03-14 22:18 BJT) `uv run python scripts/health_check_search_tools.py
  --help` -> OK.
log: (2026-03-14 22:18 BJT) `markdownlint docs/playbooks/validation.md` -> OK.
files_changed: scripts/health_check_search_tools.py
files_changed: docs/playbooks/validation.md

### T4: Validate, update trackers, and amend the last commit

depends_on: [T1, T2, T3]
reads: [docs/playbooks/validation.md, docs/PLANS.md]
writes: [docs/PLANS.md, docs/exec-plans/active/2026-03-14_1859_BJT_global-template-sync-last-commit-opt.md]
creates:
  [
    docs/exec-plans/completed/2026-03-14_1859_BJT_global-template-sync-last-commit-opt.md,
  ]
mutex: orchestrator:git-history
description: Run the documented validation sequence, record evidence in
  trackers, amend/squash the last commit (rewrite) with an updated message that
  reflects the final scope, and move this ExecPlan to `completed/`.
acceptance: Offline validation gate passes and evidence is recorded in
  `docs/PLANS.md` and this ExecPlan.
acceptance: `git log -1 --oneline` shows an amended commit message aligned with
  the final scope; force-push risk is acknowledged if the commit was already
  pushed.
acceptance: `codemap/` is not referenced outside `docs/exec-plans/**`.
validation: uv sync --locked
validation: rg -n \"codemap/\" --glob '!docs/exec-plans/**'
validation: find docs -type f -name '*.md' | sort | xargs markdownlint
validation: uv run python -m compileall paper_search_mcp tests scripts
validation: PAPER_SEARCH_LIVE_TESTS=0 uv run python -m unittest discover -q
validation: git status --porcelain
validation: git log -1 --oneline
validation: git show -1 --stat
status: done
log: (orchestrator) created task packet.
log: (2026-03-14 22:19 BJT) Orchestrator started offline validation + closeout.
log: (2026-03-14 22:19 BJT) `uv sync --locked` -> OK.
log: (2026-03-14 22:19 BJT) `rg -n "codemap/" --glob '!docs/exec-plans/**'`
  -> no matches.
log: (2026-03-14 22:19 BJT) `markdownlint AGENTS.md ARCHITECTURE.md README.md`
  -> OK.
log: (2026-03-14 22:19 BJT) `find docs -type f -name '*.md' | sort | xargs
  markdownlint` -> OK.
log: (2026-03-14 22:20 BJT) `uv run python -m compileall paper_search_mcp tests
  scripts` -> OK.
log: (2026-03-14 22:20 BJT) `PAPER_SEARCH_LIVE_TESTS=0 uv run python -m unittest
  discover -q` -> OK (skipped=26).
log: (2026-03-14 22:20 BJT) Note: `git commit --amend` rewrites history
  (changes the commit hash). If this commit was already pushed, a force push
  (`git push --force-with-lease`) is required and downstream consumers must
  rebase/reset to the new hash.
log: (2026-03-14 22:26 BJT) Updated `docs/PLANS.md`; moved ExecPlan to
  `docs/exec-plans/completed/`.
files_changed: docs/PLANS.md
files_changed: docs/exec-plans/completed/2026-03-14_1859_BJT_global-template-sync-last-commit-opt.md

## Plan of Work

1. Update `docs/design-docs/project-template.md` by diffing against the global
   template (`~/.codex/docs/design-docs/project-template.md`) and keeping this
   repo's deviations explicit.
2. Move CODEBASE_MAP content to `docs/CODEBASE_MAP.md` and update all primary
   references (read order + validation commands) to point at the canonical
   path.
3. Review and refine `scripts/health_check_search_tools.py` and the validation
   playbook entry for clarity and robustness.
4. Run the default offline gates plus markdownlint, then amend the last commit.

## Concrete Steps

1. From repo root, confirm current state:

       git status --porcelain
       git log -1 --oneline

2. Apply tasks T1–T3 (workers), then run validation (orchestrator):

       uv sync --locked
       rg -n "codemap/" --glob '!docs/exec-plans/**'
       find docs -type f -name '*.md' | sort | xargs markdownlint
       uv run python -m compileall paper_search_mcp tests scripts
       PAPER_SEARCH_LIVE_TESTS=0 uv run python -m unittest discover -q

3. Amend the last commit (orchestrator):

       git status --porcelain
       git commit --amend

   If already pushed, coordinate a force-push explicitly:

       git push --force-with-lease

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

- `optional next task or integration note`

## Validation and Acceptance

Success means:

- Docs and navigation paths match the updated global template expectations.
- Modified Markdown files are `markdownlint` clean.
- Offline smoke gate passes without relying on live network calls.
- The amended commit message matches the final scope and content.

## Idempotence and Recovery

- Markdown edits are safe to rerun.
- If `git commit --amend` produces an undesired result, recover via
  `git reflog` and resetting to the previous commit.
- If the commit has been pushed, use `--force-with-lease` (never `--force`)
  and only after confirming nobody else built on the old hash.

## Revision Notes

- 2026-03-14 / orchestrator — Created this plan for global template alignment
  and last-commit optimization.
