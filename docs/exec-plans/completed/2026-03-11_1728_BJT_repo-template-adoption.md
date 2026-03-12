# Adapt repo to lean project-template governance

This ExecPlan is a living document. Keep `Progress`,
`Surprises & Discoveries`, `Decision Log`, and
`Outcomes & Retrospective` current as work proceeds.

If this work is tracked in `docs/PLANS.md`, keep this file synchronized with
that tracker entry.

## Purpose / Big Picture

Adopt the global project template in a lean way that fits this repository's
actual shape: a small Python MCP server with network-heavy adapters, no
frontend, and no repo-local control-plane layer. The work is done when the repo
has durable governance surfaces, docs-first navigation, an honest source
capability matrix, and mechanical verification evidence.

## Progress

- [x] (2026-03-11 17:28 BJT) Capture scope, constraints, and acceptance
  criteria.
- [x] (2026-03-11 17:28 BJT) Implement the planned changes.
- [x] (2026-03-11 17:28 BJT) Run validation and record evidence.
- [x] (2026-03-11 17:28 BJT) Close review notes and summarize outcomes.

## Surprises & Discoveries

- Observation: the repo had only `README.md`, code, tests, and publish config;
  none of the governance surfaces from the template existed yet.
  Evidence: initial repo exploration on 2026-03-11.
- Observation: the test suite is mostly live-network integration rather than a
  deterministic local acceptance gate.
  Evidence: `tests/` calls live arXiv, PubMed, bioRxiv, medRxiv, IACR,
  CrossRef, Google Scholar, Semantic Scholar, and Sci-Hub surfaces.

## Decision Log

- Decision: adopt the template as a lean core, not a placeholder-heavy clone.
  Rationale: the repo is small and should stay legible.
  Date/Author: 2026-03-11 / Codex
- Decision: position the repo as a practical MCP server, not a generalized
  research platform.
  Rationale: matches current code and publish surfaces.
  Date/Author: 2026-03-11 / Codex
- Decision: document Sci-Hub as optional and sensitive rather than a default
  first-class feature.
  Rationale: reduces legal and operational ambiguity while acknowledging the
  existing code.
  Date/Author: 2026-03-11 / Codex

## Outcomes & Retrospective

The repo now has a lean governance spine that matches the global template
without pretending to be a larger system than it is. Root orientation files,
durable `docs/` surfaces, `codemap/` navigation, tracker templates, and a
source capability matrix were added. The MCP runtime surface was preserved.

## Context and Orientation

The runtime entrypoint is `paper_search_mcp/server.py`. Source-specific adapter
logic lives in `paper_search_mcp/academic_platforms/`. The shared output model
is `paper_search_mcp/paper.py`. The current tests under `tests/` are mostly
live integration checks. The repo needs durable docs under `docs/`, root
orientation files, and a `codemap/` navigation layer.

## Task Graph (Dependencies)

This work is linear; no parallel task graph is needed.

## Plan of Work

Create root governance files, add the canonical `docs/` structure that this repo
actually needs, rewrite `README.md` to match the maintained runtime surface, add
`codemap/` navigation, and record the task in `docs/PLANS.md`. Keep runtime
behavior unchanged except for repo hygiene such as ignore rules.

## Concrete Steps

1. From repo root, add the missing governance and documentation surfaces.
2. Rewrite the user-facing docs to reflect actual source capabilities.
3. Add codemap navigation and durable trackers.
4. Run markdown and offline Python verification.
5. Move the completed ExecPlan to `docs/exec-plans/completed/`.

## Validation and Acceptance

Success means:

- changed Markdown passes `markdownlint`,
- Python source imports and compiles offline,
- `README.md`, architecture docs, and capability docs agree,
- the tracker points at a completed ExecPlan with recorded evidence.

## Idempotence and Recovery

- Doc creation and rewrites are safe to rerun.
- If a verification command fails, update the docs or repo hygiene and rerun.
- If the tracker drifts, fix `docs/PLANS.md` and the ExecPlan together.

## Artifacts and Notes

- `markdownlint AGENTS.md ARCHITECTURE.md README.md docs/**/*.md
  codemap/**/*.md` -> pass
- `python3 -m compileall paper_search_mcp tests` -> pass
- `.venv/bin/python -c "import httpx, mcp, paper_search_mcp.server as s;
  print(s.mcp.name)"` -> `paper_search_server`
- `python3 ~/.codex/skills/agent-doc-maintainer/scripts/sync_agents_md.py
  --file ~/.codex/AGENTS.md --check-modular --refresh-inventory --check
  --verify-inventory-age 7 --print-gate` -> output reported `Gate status: PASS`
  while also showing a pending diff for the user's global
  `~/.codex/AGENTS.inventory.md`

## Interfaces and Dependencies

- Stable runtime surfaces:
  - `paper_search_mcp/server.py`
  - `paper_search_mcp/paper.py`
  - `smithery.yaml`
  - `.github/workflows/publish.yml`
- New durable docs:
  - root `AGENTS.md`
  - root `ARCHITECTURE.md`
  - `docs/`
  - `codemap/`

## Revision Notes

- 2026-03-11 / Codex — Created this ExecPlan for the governance migration.
- 2026-03-11 / Codex — Closed the plan after verification and moved it to
  `docs/exec-plans/completed/`.
