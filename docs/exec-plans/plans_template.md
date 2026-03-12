# PLANS Template

Use this to seed `docs/PLANS.md`. Keep entries short. Put long-form detail in
the linked ExecPlan.

## Copy-Paste Starter

```md
# PLANS

`docs/PLANS.md` tracks accepted multi-step work. Keep it concise. Put
long-form detail in `docs/exec-plans/`.

## Tracker Contract

- Required fields: `Status`, `Difficulty`, `Rationale`, `ExecPlan`,
  `Evidence`, `Next steps`, `Last updated`
- Optional field: `Mode` as `single_agent | swarm_waves | super_swarm`
- Record difficulty as `score=<n> level=<Simple|Medium|Complex>`.
- For `Medium` and `Complex`, include rationale inline on the `Difficulty`
  line as `rationale="..."`.
- If `ExecPlan` points under `docs/exec-plans/`, that file must already exist.
- Use timestamp-first Beijing-time filenames, for example
  `docs/exec-plans/active/YYYY-MM-DD_HHMM_BJT_slug.md`.

## Active

- No active tracked tasks.

<!-- Replace the line above with entries like this:
### <Task title>

- Status: planned | in_progress | blocked
- Mode: single_agent
- Difficulty: score=<n> level=Simple
- Rationale: <one-line reason>
- ExecPlan: `docs/exec-plans/active/YYYY-MM-DD_HHMM_BJT_slug.md`
- Evidence: <short proof point>
- Next steps: <next concrete action>
- Last updated: YYYY-MM-DD
-->

## Completed

- No completed tracked tasks.

<!-- Move finished entries here:
### <Task title>

- Status: completed
- Difficulty: score=<n> level=Medium rationale="<why this is not Simple>"
- Rationale: <one-line reason>
- ExecPlan: `docs/exec-plans/completed/YYYY-MM-DD_HHMM_BJT_slug.md`
- Evidence: <validation or review note>
- Next steps: none | <follow-up item>
- Last updated: YYYY-MM-DD
-->
```
