# ExecPlan Template

Use this to seed a new ExecPlan. Keep the live plan self-contained, and save it
with a timestamp-first filename such as
`docs/exec-plans/active/YYYY-MM-DD_HHMM_BJT_slug.md`. When the work is closed,
move or copy the final record to
`docs/exec-plans/completed/YYYY-MM-DD_HHMM_BJT_slug.md`.

## Copy-Paste Starter

```md
# [Short, action-oriented description]

This ExecPlan is a living document. Keep `Progress`,
`Surprises & Discoveries`, `Decision Log`, and
`Outcomes & Retrospective` current as work proceeds.

If you intend to execute with parallel subagents, seed from
`docs/exec-plans/execplan_swarm_template.md` instead of this
single-agent template.

If this work is tracked in `docs/PLANS.md`, keep this file synchronized
with that tracker entry.

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
  Rationale: provide a self-contained implementation guide
  Date/Author: YYYY-MM-DD / [name]

## Outcomes & Retrospective

Summarize what shipped, what did not, and what was learned. Compare the
result to the purpose above.

## Context and Orientation

Describe the current state as if the reader knows nothing about this
repository. Name the important files by full path. Define any
non-obvious term before using it.

## Task Graph (Dependencies)

Use this section when parallel work or staged dependencies matter. If
the work is linear, say so plainly:
`This work is linear; no parallel task graph is needed.`

- id: T1
  name: Example task
  depends_on: []
  paths:
  - path/to/file
  acceptance:
  - Example acceptance criterion
  validation:
  - example command

## Plan of Work

Describe the intended edits in prose. For each change, name the file,
the relevant function or section, and the reason for the edit.

## Concrete Steps

List the exact commands to run, where to run them, and the short expected output.

1. From `[repo-root]`, run:

       [command]

   Expect:

       [short transcript]

## Validation and Acceptance

Describe how to exercise the change and what success looks like. Prefer
behavior-based acceptance over vague completion statements.

## Idempotence and Recovery

State which steps are safe to rerun, what can fail partway through, and
how to recover or roll back safely.

## Artifacts and Notes

Keep only the shortest evidence that proves progress or correctness.

## Interfaces and Dependencies

Name the interfaces, modules, services, libraries, or generated
artifacts that must exist when the milestone is complete. Be specific
about names and paths.

## Revision Notes

- YYYY-MM-DD / [name] — Created or revised this plan because [reason].
```
