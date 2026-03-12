# ExecPlan Swarm Template

Use this to seed a multi-agent ExecPlan intended for dependency-aware parallel
execution. Keep the live plan self-contained, and save it with a timestamp-first
filename such as `docs/exec-plans/active/YYYY-MM-DD_HHMM_BJT_slug.md`. When the
work is closed, move or copy the final record to
`docs/exec-plans/completed/YYYY-MM-DD_HHMM_BJT_slug.md`.

Planning rule: if two tasks' `writes` or `creates` overlap on any path, they
must share a `mutex` label unless a `depends_on` chain already prevents
parallelism.

## Copy-Paste Starter

```md
# [Short, action-oriented description]

This ExecPlan is a living document. The orchestrator is the single
writer for this file: workers return completion packets; the
orchestrator updates task `status`, `log`, and `files_changed`.

If this work is tracked in `docs/PLANS.md`, keep this file synchronized
with that tracker entry.

## Orchestration

Schema version: 1
Execution mode: multi-agent
Scheduler: rolling_pool | waves
Max parallelism: 12
Shared-state policy: orchestrator-only
Plan updates: orchestrator-only
File-scope rule: each task must declare writes/creates; workers must not
write outside without escalation
Write-allowed set: writes ∪ creates

## Purpose / Big Picture

State what changes for the user or maintainer, why it matters, and how
someone can tell the work is done.

## Progress

- [ ] (YYYY-MM-DD HH:MM BJT) Capture scope, constraints, and acceptance criteria.
- [ ] (YYYY-MM-DD HH:MM BJT) Implement the planned changes.
- [ ] (YYYY-MM-DD HH:MM BJT) Run validation and record evidence.
- [ ] (YYYY-MM-DD HH:MM BJT) Close review notes and summarize outcomes.

## Surprises & Discoveries

- Observation: none yet
  Evidence: n/a

## Decision Log

- Decision: initial ExecPlan created
  Rationale: provide a self-contained multi-agent implementation guide
  Date/Author: YYYY-MM-DD / [name]

## Outcomes & Retrospective

Summarize what shipped, what did not, and what was learned. Compare the
result to the purpose above.

## Context and Orientation

Describe the current state as if the reader knows nothing about this
repository. Name the important files by full path. Define any
non-obvious term before using it.

## Task Graph (Dependencies)

Each task is a heading `### T<n>: <Name>`. Under each task, use flat field lines
with repo-relative paths.

### T1: Example task

depends_on: []
reads: [path/to/input.md]
writes: [path/to/output.md]
creates: []
mutex: file:path/to/output.md
description: One sentence describing what this task does and why.
acceptance: Example acceptance criterion.
validation: Example validation command.
status: planned
log: (orchestrator) created task packet.
files_changed: (orchestrator) none.

### T2: Example follow-up task

depends_on: [T1]
writes: []
creates: [path/to/new_file.md]
mutex: file:path/to/new_file.md
description: One sentence describing what this task does and why.
acceptance: Example acceptance criterion.
validation: Example validation command.
status: planned

## Plan of Work

Describe the intended edits in prose. For each change, name the file,
the relevant function or section, and the reason for the edit.

## Concrete Steps

List the exact commands to run, where to run them, and the short expected output.

1. From `[repo-root]`, run:

       [command]

   Expect:

       [short transcript]

## Completion Packet (Workers)

**Status:** `[COMPLETED | FAILED | BLOCKED]`

**Files modified/created:**
- <path>

**Acceptance criteria coverage:**
- <criterion> -> <how it is satisfied>

**Validation performed:**
- <command> -> <result>

**Open risks / blockers:**
- <notes>

**Suggested follow-ups:**
- <optional next task or integration note>

## Validation and Acceptance

Describe how to exercise the change and what success looks like.

## Idempotence and Recovery

State which steps are safe to rerun, what can fail partway through, and
how to recover or roll back safely.

## Revision Notes

- YYYY-MM-DD / [name] — Created or revised this plan because [reason].
```
