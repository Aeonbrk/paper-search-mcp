# Local Project Template Adoption

This repo adopts the global project template as a lean default, not a maximal
copy.

## Canonical Layout Reference

The canonical layout is defined by the maintainer's global template. This repo
implements the parts that materially improve legibility for a small Python MCP
server:

- root `AGENTS.md`
- root `ARCHITECTURE.md`
- `codemap/`
- `docs/PLANS.md`
- `docs/exec-plans/`
- `docs/design-docs/`
- `docs/project-specs/`
- `docs/references/`
- `docs/playbooks/`
- `docs/DESIGN.md`
- `docs/PROJECT_SENSE.md`
- `docs/QUALITY_SCORE.md`
- `docs/RELIABILITY.md`
- `docs/SECURITY.md`

## Deliberate Deviations

### Omitted surfaces

- `FRONTEND.md` is omitted because the repo has no frontend surface.
- `docs/generated/` is omitted because there is no codegen or generated-doc
  pipeline.
- Repo-local control-plane files are omitted because orchestration policy lives
  in the global Codex environment, not this package.

### Repo-specific emphasis

- Source capability differences are first-class and documented under
  `docs/project-specs/source-capability-matrix.md`.
- Offline verification is the default acceptance gate for documentation changes.
- `codemap/` exists to speed up orientation for a small but source-diverse code
  base.
