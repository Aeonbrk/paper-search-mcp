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

### Release: CI + publish test gates + version bump

- Status: active
- Mode: swarm_waves
- Difficulty: score=6 level=Medium
  rationale="Touches GitHub Actions workflows plus the release/tagging flow;
  bounded but affects publishing safety."
- Rationale: Ship PMC support safely by gating PyPI publish on offline tests and
  adding CI coverage for the same gate.
- ExecPlan:
  `docs/exec-plans/active/2026-03-13_1525_BJT_release-safety-ci-gates.md`
- Evidence: `.github/workflows/publish.yml` gated on offline tests; new
  `.github/workflows/ci.yml` added; `pyproject.toml` bumped to `0.1.4`;
  `uv sync --locked` passed; `markdownlint README.md $(find docs -type f -name
  '*.md' | sort)` passed; `PAPER_SEARCH_LIVE_TESTS=0 uv run python -m unittest
  discover -q` passed (`OK (skipped=25)`).
- Next steps: Commit and push to `origin/main`, verify the `CI` workflow is
  green on that commit, then tag and push `v0.1.4` and verify publish + PyPI.
- Last updated: 2026-03-13

## Completed

### AB: Closeout (merge-ready) + PMC adapter (research + minimal implementation)

- Status: completed
- Mode: super_swarm
- Difficulty: score=8 level=Medium
  rationale="Combines merge-readiness closeout with a new source adapter and
  shared docs/tests updates while keeping public MCP names and capability claims
  stable."
- Rationale: Close out current work to merge-ready and add PMC v1 support with
  honest capability boundaries.
- ExecPlan:
  `docs/exec-plans/completed/2026-03-13_0017_BJT_ab-closeout-pmc-adapter.md`
- Evidence: `uv sync --locked` passed; `PAPER_SEARCH_LIVE_TESTS=0 uv run python
  -m compileall paper_search_mcp` passed; `PAPER_SEARCH_LIVE_TESTS=0 uv run
  python -m compileall tests` passed; `PAPER_SEARCH_LIVE_TESTS=0 uv run python
  -m unittest discover -q` passed with `OK (skipped=25)`; `markdownlint
  README.md docs/**/*.md` passed; `PAPER_SEARCH_LIVE_TESTS=0 uv run python -m
  unittest -q tests.test_pmc tests.test_adapter_contract tests.test_server`
  passed; ExecPlan moved from `active/` to `completed/`.
- Next steps: none
- Last updated: 2026-03-13

### P0: Offline fixtures + adapter interface convergence

- Status: completed
- Mode: super_swarm
- Difficulty: score=9 level=Medium
  rationale="Touches several adapters plus deterministic fixtures/tests while
  preserving the MCP tool surface; mostly mechanical but broad."
- Rationale: Implement `docs/TODO.md` P0 items so adapter expansion does not
  erode testability and maintainability.
- ExecPlan:
  `docs/exec-plans/completed/2026-03-12_2208_BJT_p0-offline-fixtures-adapter-interface.md`
- Evidence: `PAPER_SEARCH_LIVE_TESTS=0 uv run python -m unittest -q
  tests.test_arxiv tests.test_pubmed tests.test_crossref tests.test_semantic
  tests.test_iacr` passed; `PAPER_SEARCH_LIVE_TESTS=0 uv run python -m
  compileall paper_search_mcp` passed; `PAPER_SEARCH_LIVE_TESTS=0 uv run python
  -m compileall tests` passed; `env -u PAPER_SEARCH_LIVE_TESTS uv run python -m
  unittest discover -q` passed; `rg -n "class PaperSource"
  paper_search_mcp/academic_platforms/*.py` returns only `_base.py`;
  markdownlint passed for the execplan and fixture README.
- Next steps: none
- Last updated: 2026-03-12

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
