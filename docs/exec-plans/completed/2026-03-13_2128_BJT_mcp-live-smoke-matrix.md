# Add Live MCP Protocol Smoke Matrix (Opt-in)

This ExecPlan is a living document. The orchestrator is the single
writer for this file: workers return completion packets; the
orchestrator updates task `status`, `log`, and `files_changed`.

If this work is tracked in `docs/PLANS.md`, keep this file synchronized
with that tracker entry.

## Orchestration

Schema version: 1
Execution mode: multi-agent
Scheduler: rolling_pool
Max parallelism: 12
Shared-state policy: orchestrator-only
Plan updates: orchestrator-only
File-scope rule: each task must declare writes/creates; workers must not
write outside without escalation
Write-allowed set: writes ∪ creates

## Purpose / Big Picture

Add a permanent, opt-in "live MCP smoke matrix" that tests this repo's MCP
server through the real MCP protocol boundary (stdio), instead of only importing
`paper_search_mcp.server` and calling `mcp.list_tools()` in-process.

Done looks like:

- a new `tests/test_mcp_live.py` exists and is gated by `PAPER_SEARCH_LIVE_TESTS=1`,
- the test suite launches the server with `uv run -m paper_search_mcp.server`,
  connects via `mcp.client.stdio`, and calls tools via `ClientSession`,
- the suite covers every registered tool at least once (or skips source-local
  cases when upstreams are unavailable),
- `docs/playbooks/validation.md` documents how to run the new opt-in live MCP
  suite,
- default offline validation remains unchanged and stays offline by default.

## Progress

- [x] (2026-03-13 22:01 BJT) Capture scope, constraints, and acceptance criteria.
- [x] (2026-03-13 22:21 BJT) Implement the planned changes.
- [x] (2026-03-13 22:26 BJT) Run validation and record evidence.
- [x] (2026-03-13 22:27 BJT) Close review notes and summarize outcomes.

## Surprises & Discoveries

- Observation: MCP `call_tool()` returns `TextContent.text` blocks, so tests
  must parse tool outputs from text, not assume Python values.
  Evidence: local stdio client run successfully returned JSON strings for
  search tools and `LIMITATION:` strings for PMC placeholder tools.

- Observation: Server-side save paths are canonicalized to `docs/downloads`,
  so tests must clean up by deleting returned file paths (not by assuming a
  per-test subdirectory).
  Evidence: `paper_search_mcp.server:_canonical_save_path()` ignores user input.

- Observation: a skipped full-text live case can still leave a PDF behind
  unless cleanup runs from a `finally` block after the download step.
  Evidence: `tests/test_mcp_live.py` now always restores `docs/downloads/`
  to its pre-test snapshot, and final validation ended with
  `remaining_download_files= []`.

## Decision Log

- Decision: ship the MCP protocol suite as opt-in live tests
  Rationale: repo default gate stays offline; upstream services are flaky.
  Date/Author: 2026-03-13 / Codex

- Decision: preflight per source and skip source-local cases when upstream is
  unavailable
  Rationale: reduces noise while still exercising the MCP protocol boundary.
  Date/Author: 2026-03-13 / Codex

## Outcomes & Retrospective

Shipped:

- `tests/_mcp_live.py` adds stdio-session, parsing, preflight, and safe cleanup
  helpers for protocol-level live tests.
- `tests/test_mcp_live.py` adds an opt-in live MCP smoke matrix that exercises
  the registered tool surface over stdio and tolerates upstream flake via
  source-local skips.
- `docs/playbooks/validation.md` now documents the live suite without changing
  the default offline gate.

What did not change:

- The default validation gate stays offline.
- The MCP runtime surface, tool names, and source capability claims stay
  unchanged.

What was learned:

- FastMCP stdio results are text-first at the client boundary, so protocol
  tests must parse `TextContent.text`.
- Cleanup must be resilient to skipped live cases after a download succeeds.
- CrossRef live responses can log parser warnings without breaking the protocol
  smoke suite; this remains a follow-up quality issue rather than a blocker for
  the new matrix.

## Context and Orientation

This repo exposes a FastMCP server at `paper_search_mcp/server.py` and runs it
with stdio transport:

- `uv run -m paper_search_mcp.server`

Existing tests confirm tool registration in-process:

- `tests/test_server.py` calls `asyncio.run(server.mcp.list_tools())`.

This plan adds a protocol-level suite:

- it launches the real server process (`uv run -m ...`),
- it connects over stdio using the official MCP Python SDK client APIs,
- it calls tools using `ClientSession.call_tool(...)`,
- it parses tool responses from `CallToolResult.content[...].text`.

Tool surface and response contracts:

- Tool names and patterns are documented in `docs/project-specs/mcp-tool-contract.md`.
- Source capabilities (search/download/read supported or not) are documented in
  `docs/project-specs/source-capability-matrix.md`.
- Some tools are expected to return structured limitation messages:
  `LIMITATION:` + JSON (not exceptions).

## Task Graph (Dependencies)

### T1: Track This Work In docs/PLANS.md

depends_on: []
reads: [
  docs/PLANS.md,
  docs/exec-plans/active/2026-03-13_2128_BJT_mcp-live-smoke-matrix.md,
]
writes: [docs/PLANS.md]
creates: []
mutex: file:docs/PLANS.md
description: Add an `Active` tracker entry so this ExecPlan is discoverable and
  stays synchronized with the system-of-record tracker.
acceptance: `docs/PLANS.md` includes this ExecPlan under `## Active` with all
  required fields.
validation: rg -n "2026-03-13_2128_BJT_mcp-live-smoke-matrix\\.md" docs/PLANS.md
status: done
log: (orchestrator) created task packet.
log: (orchestrator) 2026-03-13 22:01 BJT launched worker.
log: (orchestrator) 2026-03-13 22:04 BJT validated `docs/PLANS.md` active
  tracker entry and `rg -n "2026-03-13_2128_BJT_mcp-live-smoke-matrix\\.md"
  docs/PLANS.md`.
files_changed: `docs/PLANS.md`

### T2: Add Shared MCP Live Test Helpers

depends_on: []
reads: [
  docs/project-specs/mcp-tool-contract.md,
  docs/project-specs/source-capability-matrix.md,
  paper_search_mcp/server.py,
  tests/test_server.py,
]
writes: []
creates: [tests/_mcp_live.py]
mutex: file:tests/_mcp_live.py
description: Add a small helper module for starting a stdio MCP client session,
  preflighting upstream reachability, and parsing `TextContent.text` results.
acceptance: Helper exposes a single `async` entrypoint to open a stdio
  `ClientSession` against `uv run -m paper_search_mcp.server`.
acceptance: Helper exposes parsing helpers for: JSON tool results and
  `LIMITATION:` + JSON payloads.
acceptance: Helper exposes safe cleanup utilities for files returned by
  download tools under `docs/downloads/`.
validation: uv run python -m compileall tests/_mcp_live.py
validation: uv run python -c "import tests._mcp_live as m; print(m.__name__)"
status: done
log: (orchestrator) 2026-03-13 22:01 BJT launched worker.
log: (orchestrator) 2026-03-13 22:06 BJT validated helper module with
  `uv run python -m compileall tests/_mcp_live.py` and import smoke.
files_changed: `tests/_mcp_live.py`

### T3: Add Live MCP Smoke Matrix Tests

depends_on: [T2]
reads: [
  docs/project-specs/mcp-tool-contract.md,
  docs/project-specs/source-capability-matrix.md,
  paper_search_mcp/server.py,
  tests/test_server.py,
  tests/_mcp_live.py,
]
writes: []
creates: [tests/test_mcp_live.py]
mutex: file:tests/test_mcp_live.py
description: Add a permanent, opt-in unittest module that covers every
  registered MCP tool by calling it over stdio using `ClientSession.call_tool`.
acceptance: Test module skips unless `PAPER_SEARCH_LIVE_TESTS=1`.
acceptance: Test module verifies `initialize` + `list_tools` over stdio and
  asserts the registered tool set matches `tests/test_server.py`.
acceptance: For each source marked `search: yes` in
  `docs/project-specs/source-capability-matrix.md`, call `search_*` over MCP and
  parse normalized JSON results.
acceptance: For each source marked `download: yes` and `read: yes` in
  `docs/project-specs/source-capability-matrix.md`, call the corresponding tools
  with valid IDs, validate output shape, and delete any returned files under
  `docs/downloads/`.
acceptance: For sources whose matrix indicates download/read is not supported
  but whose tools are registered (PubMed, CrossRef), assert a non-file
  unsupported result and verify `docs/downloads/` is unchanged.
acceptance: Placeholder limitation tools (`download_pmc`, `read_pmc_paper`)
  return `LIMITATION:` + JSON per `docs/project-specs/mcp-tool-contract.md`.
acceptance: Upstream flake handling uses preflight reachability checks; when a
  source is unavailable, only that source's test(s) are skipped.
validation: PAPER_SEARCH_LIVE_TESTS=0 uv run python -m unittest -q tests.test_server
validation: PAPER_SEARCH_LIVE_TESTS=1 uv run python -m unittest -q tests.test_mcp_live
status: done
log: (orchestrator) 2026-03-13 22:06 BJT launched worker after T2 completed.
log: (orchestrator) 2026-03-13 22:15 BJT took ownership of T3 locally after
  worker validation stalled; reviewed `tests/test_mcp_live.py`.
log: (orchestrator) 2026-03-13 22:19 BJT validated with
  `PAPER_SEARCH_LIVE_TESTS=0 uv run python -m unittest -q tests.test_server
  tests.test_mcp_live` and `PAPER_SEARCH_LIVE_TESTS=1 uv run python -m
  unittest -q tests.test_mcp_live` (`OK`, `skipped=3`).
files_changed: `tests/test_mcp_live.py`

### T4: Document The Live MCP Suite In Validation Playbook

depends_on: [T3]
reads: [docs/playbooks/validation.md, tests/test_mcp_live.py]
writes: [docs/playbooks/validation.md]
creates: []
mutex: file:docs/playbooks/validation.md
description: Update the validation playbook to include the new opt-in live MCP
  smoke command.
acceptance: `docs/playbooks/validation.md` includes
  `PAPER_SEARCH_LIVE_TESTS=1 uv run python -m unittest -q tests.test_mcp_live`.
acceptance: The playbook continues to state the default gate is offline.
validation: markdownlint docs/playbooks/validation.md
validation: rg -n \
  "PAPER_SEARCH_LIVE_TESTS=1 uv run python -m unittest -q" \
  "tests\\.test_mcp_live" \
  docs/playbooks/validation.md
status: done
log: (orchestrator) 2026-03-13 22:20 BJT launched worker after T3 completed.
log: (orchestrator) 2026-03-13 22:21 BJT validated `docs/playbooks/validation.md`
  with `markdownlint` and `rg -n` checks for the new live command and offline
  gate wording.
files_changed: `docs/playbooks/validation.md`

### T5: Run Validation And Record Evidence

depends_on: [T1, T3, T4]
reads: [
  docs/playbooks/validation.md,
  docs/exec-plans/active/2026-03-13_2128_BJT_mcp-live-smoke-matrix.md,
]
writes: [docs/exec-plans/active/2026-03-13_2128_BJT_mcp-live-smoke-matrix.md]
creates: []
mutex: plan:2026-03-13_2128_BJT_mcp-live-smoke-matrix
description: Run default offline validation and the opt-in live MCP suite,
  recording evidence in this ExecPlan (command + short transcript).
acceptance: Default offline gate remains green.
acceptance: Live MCP suite runs successfully when upstreams are available and
  reports skips when upstreams are unavailable.
validation: uv sync --locked
validation: markdownlint README.md \
  $(find docs -type f -name '*.md' | sort)
validation: uv run python -m compileall paper_search_mcp tests
validation: uv run python -c \
  "import paper_search_mcp.server as s; print(s.mcp.name)"
validation: PAPER_SEARCH_LIVE_TESTS=0 uv run python -m unittest discover -q
validation: PAPER_SEARCH_LIVE_TESTS=1 uv run python -m unittest -q tests.test_mcp_live
status: done
log: (orchestrator) 2026-03-13 22:21 BJT started full validation and evidence capture.
log: (orchestrator) 2026-03-13 22:23 BJT first validation pass succeeded with
  uv sync --locked; markdownlint README.md $(find docs -type f -name '*.md' |
  sort); uv run python -m compileall paper_search_mcp tests; uv run python -c
  "import paper_search_mcp.server as s; print(s.mcp.name)";
  PAPER_SEARCH_LIVE_TESTS=0 uv run python -m unittest discover -q
  -> OK (skipped=26); PAPER_SEARCH_LIVE_TESTS=1 uv run python -m unittest -q
  tests.test_mcp_live -> OK (skipped=4).
log: (orchestrator) 2026-03-13 22:24 BJT found a leftover semantic PDF under
  `docs/downloads/` after a skipped live full-text case, patched
  `tests/test_mcp_live.py` to guarantee cleanup in `finally`, deleted the stray
  file, and reran validation.
log: (orchestrator) 2026-03-13 22:26 BJT final validation pass succeeded with
  uv sync --locked; markdownlint README.md $(find docs -type f -name '*.md' |
  sort); uv run python -m compileall paper_search_mcp tests; uv run python -c
  "import paper_search_mcp.server as s; print(s.mcp.name)";
  PAPER_SEARCH_LIVE_TESTS=0 uv run python -m unittest discover -q
  -> OK (skipped=26); PAPER_SEARCH_LIVE_TESTS=1 uv run python -m unittest -q
  tests.test_mcp_live -> OK (skipped=4); final download-root check reported
  remaining_download_files= [].
files_changed: `docs/exec-plans/completed/2026-03-13_2128_BJT_mcp-live-smoke-matrix.md`
files_changed: `tests/test_mcp_live.py`

## Plan of Work

1. Track this plan in `docs/PLANS.md`.
2. Add a minimal helper module (`tests/_mcp_live.py`) that knows how to:
   - start a stdio MCP session using `StdioServerParameters` and `stdio_client`,
   - call tools and extract `TextContent.text`,
   - parse JSON and `LIMITATION:` payloads,
   - delete downloaded files under `docs/downloads/` by returned path.
3. Add `tests/test_mcp_live.py`:
   - gate on `PAPER_SEARCH_LIVE_TESTS=1`,
   - per-source preflight checks (requests + small timeout),
   - per-source MCP tool calls to cover all registered tools,
   - safe cleanup of any downloaded PDFs created by the run.
4. Update `docs/playbooks/validation.md` to document the new opt-in command.
5. Run validation and record evidence.

## Concrete Steps

1. From `[repo-root]`, run:

       uv sync --locked

2. Run offline checks:

       uv run python -m compileall paper_search_mcp tests
       uv run python -c "import paper_search_mcp.server as s; print(s.mcp.name)"
       PAPER_SEARCH_LIVE_TESTS=0 uv run python -m unittest discover -q

3. Run the live MCP matrix:

       PAPER_SEARCH_LIVE_TESTS=1 uv run python -m unittest -q tests.test_mcp_live

   Expect:

   - at least the stdio initialize + tool snapshot tests pass,
   - source-local tests may skip if an upstream is down or blocked.

## Completion Packet (Workers)

__Status:__ `[COMPLETED | FAILED | BLOCKED]`

__Files modified/created:__

- `path/to/file`

__Acceptance criteria coverage:__

- `criterion` -> `how it is satisfied`

__Validation performed:__

- `command` -> `result`

__Open risks / blockers:__

- `notes`

__Suggested follow-ups:__

- `optional follow-up`

## Validation and Acceptance

- Default offline gate stays stable (`PAPER_SEARCH_LIVE_TESTS=0`).
- Live MCP suite is opt-in and covers every registered tool over stdio.
- Live suite does not leave PDFs behind under `docs/downloads/`.

## Idempotence and Recovery

- Safe to rerun: offline unit tests, `markdownlint`, and the live MCP suite.
- If a live source flakes: re-run; if persistent, improve preflight checks to
  skip source-local cases until the upstream recovers.

## Revision Notes

- 2026-03-13 / Codex — Created this plan to add protocol-level MCP smoke
  coverage for all registered tools.
- 2026-03-13 / Codex — Completed implementation, documented the live suite, and
  tightened cleanup so the live matrix leaves `docs/downloads/` clean.
