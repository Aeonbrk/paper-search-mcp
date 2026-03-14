# Project Template (Local Adoption)

This repository adopts the global `.codex` project template as a lean default,
not a maximal copy.

Global source of truth:

- `~/.codex/docs/design-docs/project-template.md`

## Directory Layout

The directory layout below describes the canonical template. This repo adopts a
subset; see "Local Adoption" and "Deliberate Deviations" for specifics.

```text
AGENTS.md                # Local agent invariants and policy overrides
ARCHITECTURE.md          # Core architecture, ownership, and system orientation
docs/
├── CODEBASE_MAP.md      # Structural navigation artifact
├── PLANS.md             # Durable tracker for accepted multi-step work
├── design-docs/
│   ├── index.md
│   └── ...
├── exec-plans/
│   ├── active/                    # In-progress plans (task is live)
│   ├── completed/                 # Closed plans (task is finished)
│   ├── plans_template.md          # Starter template for PLANS.md
│   ├── execplan_template.md       # Single-agent task starter template
│   ├── execplan_swarm_template.md # Multi-agent starter for parallel execution
│   └── tech-debt-tracker.md       # Durable debt log independent of active tasks
├── generated/
│   └── ...                        # Versioned, machine-produced schema/API docs
├── project-specs/
│   ├── index.md
│   └── ...
├── references/
│   ├── index.md
│   └── ...
├── DESIGN.md
├── FRONTEND.md          # Only for projects which have frontend workflow
├── PROJECT_SENSE.md
├── QUALITY_SCORE.md     # Domain-graded rubric
│                        # (Date/Domain/Grade/Evidence/Next action)
├── RELIABILITY.md
└── SECURITY.md

```

## Filesystem Lifecycle Semantics

Directory paths inherently convey task states. Agents must determine the
lifecycle stage of an artifact by inspecting its path:

- **`docs/exec-plans/active/`**: The task is currently in progress. The plan is
  a living document actively being updated by the orchestrator.
- **`docs/exec-plans/completed/`**: The task is finished. The plan serves as a
  historical, retrospective artifact.
- **`docs/generated/`**: The content is machine-produced derived from another
  source of truth. Do not hand-edit; regenerate instead.
- **`docs/CODEBASE_MAP.md`**: A structural navigation map designed for docs-first
  exploration. It is not a secondary knowledge base.

## Governance & Customization Contract

Treat this layout as the strict default for `.codex` repositories. If a
repository must deviate from this structure, the following rules apply:

- **Explicit declaration:** If a surface is intentionally omitted or
  substituted, the local `AGENTS.md` or `ARCHITECTURE.md` MUST explicitly
  declare the deviation.
- **Link integrity:** You MUST adjust the local read order and strictly avoid
  leaving live links to absent surfaces.
- **Template seeding:** When bootstrapping `docs/PLANS.md`, strictly copy only
  the `## Copy-Paste Starter` content from `docs/exec-plans/plans_template.md`.
- **ExecPlan creation:** When creating a new ExecPlan, strictly copy only the
  `## Copy-Paste Starter` content from `docs/exec-plans/execplan_template.md`
  (single-agent) or `docs/exec-plans/execplan_swarm_template.md` (parallel
  subagent work).

## Usage Guidance

- **Keep root files minimal:** Reserve `AGENTS.md` for strict policy/invariants
  and `ARCHITECTURE.md` for high-level system orientation.
- **Centralize tracking:** Keep the durable, high-level task tracker
  exclusively in `docs/PLANS.md`.
- **Manage executable plans:** Confine all long-form executable plans to
  `docs/exec-plans/`. Ensure in-progress plans in `docs/exec-plans/active/` are
  linked directly from `docs/PLANS.md`.
- **Distribute domain knowledge:** Store durable, domain-specific guidance
  across `docs/design-docs/`, `docs/project-specs/`, and `docs/references/`.
- **Enforce layouts:** Do not maintain compatibility shims or redirects for
  canonical doc paths once this stricter layout is adopted. Add mechanical
  enforcement checks alongside the structure.

## Local Adoption

This repo implements the subset that materially improves legibility for a small
Python MCP server:

- Root: `AGENTS.md`, `ARCHITECTURE.md`
- Navigation: `docs/CODEBASE_MAP.md`
- Trackers: `docs/PLANS.md`, `docs/exec-plans/`
- Durable docs: `docs/design-docs/`, `docs/project-specs/`, `docs/references/`,
  `docs/playbooks/`
- Core orientation/rubrics: `docs/DESIGN.md`, `docs/PROJECT_SENSE.md`,
  `docs/QUALITY_SCORE.md`, `docs/RELIABILITY.md`, `docs/SECURITY.md`

## Deliberate Deviations

This repo intentionally omits or substitutes some template surfaces:

- `docs/FRONTEND.md` is omitted because the repo has no frontend workflow.
- `docs/generated/` is omitted because there is no code generation or
  generated-doc pipeline.
- Repo-local control-plane registry/orchestration files are omitted because the
  authored control plane lives in the maintainer's global Codex environment,
  not this package.

## Repo-Specific Emphasis

- Source capability differences are first-class and documented under
  `docs/project-specs/source-capability-matrix.md`.
- Offline verification is the default acceptance gate for documentation changes.
