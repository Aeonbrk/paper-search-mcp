# PLANS

`docs/PLANS.md` tracks accepted multi-step work. Keep it concise. Put long-form
detail in `docs/exec-plans/`.

## Tracker Contract

- Required fields: `Status`, `Difficulty`, `Rationale`, `ExecPlan`,
  `Evidence`, `Next steps`, `Last updated`
- Optional field: `Mode` as `single_agent | swarm_waves | super_swarm`
- Record difficulty as `score=<n> level=<Simple|Medium|Complex>`.
- For `Medium` and `Complex`, include rationale inline on the `Difficulty` line
  as `rationale="..."`.
- If `ExecPlan` points under `docs/exec-plans/`, that file must already exist.
- Use timestamp-first Beijing-time filenames, for example
  `docs/exec-plans/active/YYYY-MM-DD_HHMM_BJT_slug.md`.

## Active

- None.

## Completed

### 统一 uv + bug/perf + 文档补齐

- Status: completed
- Mode: super_swarm
- Difficulty: score=12 level=Complex
  rationale="Touches Docker build, core server runtime, multiple adapters,
  tests, and durable docs while preserving the public MCP surface."
- Rationale: Align uv workflows, fix high-impact security/runtime issues,
  improve responsiveness, and keep docs truthful and actionable.
- ExecPlan:
  `docs/exec-plans/completed/2026-03-12_0008_BJT_uv-bugs-perf-docs.md`
- Evidence: Audit doc updated; `uv sync --locked` passed; `docker build -t
  paper-search-mcp .` passed; `docker run --rm paper-search-mcp python -c
  "from paper_search_mcp.server import mcp; print(mcp.name)"` printed
  `paper_search_server`; `markdownlint README.md $(find docs -type f -name
  '*.md' | sort)` passed; `uv run python -m compileall paper_search_mcp tests`
  passed; `uv run python -c "import paper_search_mcp.server as s;
  print(s.mcp.name)"` printed `paper_search_server`; `uv run python -m unittest
  discover -q` returned `OK (skipped=25)`.
- Next steps: none; T12 stays deferred unless explicitly needed.
- Last updated: 2026-03-12

### Adapt repo to project template

- Status: completed
- Mode: single_agent
- Difficulty: score=6 level=Medium
  rationale="Touches repo-wide governance, documentation, navigation, and
  verification surfaces without changing the MCP runtime contract."
- Rationale: Adopt the global template in a lean way that matches this repo.
- ExecPlan:
  `docs/exec-plans/completed/2026-03-11_1728_BJT_repo-template-adoption.md`
- Evidence: `markdownlint` passed; `python3 -m compileall paper_search_mcp tests`
  passed; `.venv/bin/python -c "import httpx, mcp, paper_search_mcp.server as
  s; print(s.mcp.name)"` printed `paper_search_server`.
- Next steps: none
- Last updated: 2026-03-11
