# AB: Closeout (merge-ready) + PMC adapter (research + minimal implementation)

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

Do two things in one coordinated pass:

1. **A (Closeout):** turn the current work-in-progress into a merge-ready state
   (docs consistent, validations green, evidence recorded).
2. **B (PMC):** add a new `PMC` (PubMed Central) adapter with a clear capability
   conclusion and deterministic offline tests. For this ExecPlan, v1 scope is
   `search: yes`, `download: no`, `read: no`. Any OA-subset full-text work is a
   follow-up ExecPlan.

Success means:

- The repo can pass offline validation (`PAPER_SEARCH_LIVE_TESTS=0`) and
  `markdownlint` with no manual steps.
- `PMC` has an explicit capability statement (`search/download/read`) in
  `docs/project-specs/source-capability-matrix.md`.
- `PMC` has an adapter module, offline fixtures/tests, tool entries
  (`search_pmc`, `download_pmc`, `read_pmc_paper`), and an updated
  `tests/test_server.py` snapshot. `download_pmc` / `read_pmc_paper` are honest
  placeholders that return explicit limitation messages in the structured format
  defined by `docs/project-specs/mcp-tool-contract.md` (capability remains
  `download: no`, `read: no`).

## Progress

- [x] (2026-03-13 00:17 BJT) Capture scope, constraints, and acceptance criteria.
- [x] (2026-03-13 00:17 BJT) Implement the planned changes.
- [x] (2026-03-13 00:17 BJT) Run validation and record evidence.
- [x] (2026-03-13 00:17 BJT) Close review notes and summarize outcomes.

## Surprises & Discoveries

- Observation: none yet
  Evidence: n/a

## Decision Log

- Decision: Keep closeout changes small and intention-revealing.
  Rationale: reduces review cost for broad, mechanical changes.
  Date/Author: 2026-03-13 / orchestrator
- Decision: For PMC automation, prefer NCBI-supported services only (E-utilities
  first); avoid scraping PMC HTML pages for bulk workflows.
  Rationale: aligns with PMC developer guidance and reduces operational risk.
  Date/Author: 2026-03-13 / orchestrator
- Decision: PMC `download` / `read` support is gated by license/reuse
  constraints; initial delivery may be `search` + metadata/abstract only.
  Rationale: avoid promising full-text behavior that is not universally allowed.
  Date/Author: 2026-03-13 / orchestrator
- Decision: Ship `download_pmc` / `read_pmc_paper` as explicit placeholders that
  return limitation messages; keep the capability matrix as `download: no`,
  `read: no`.
  Rationale: makes limitations obvious while reserving the tool names to avoid
  future breaking changes.
  Date/Author: 2026-03-13 / orchestrator
- Decision: Standardize placeholder limitation messages as `LIMITATION:` + JSON
  (see `docs/project-specs/mcp-tool-contract.md`) and assert it in tests.
  Rationale: gives clients a machine-detectable error surface without changing
  return types.
  Date/Author: 2026-03-13 / orchestrator

## Outcomes & Retrospective

- Added PMC v1 support as `search: yes`, `download: no`, `read: no` with
  explicit capability docs and source notes.
- Implemented `PMCSearcher` plus MCP tools `search_pmc`, `download_pmc`, and
  `read_pmc_paper`; placeholder tools return structured `LIMITATION:` + JSON
  messages and avoid filesystem/network side effects for unsupported paths.
- Added deterministic offline PMC fixtures and tests, updated adapter contract
  coverage, and refreshed the server tool snapshot.
- Completed offline validation (`unittest discover`, targeted PMC tests,
  `compileall`, and `markdownlint`) and recorded evidence in `docs/PLANS.md`.

## Context and Orientation

Key repo surfaces:

- `paper_search_mcp/academic_platforms/*.py`: one adapter per source. All
  adapters share `PaperSource` in `paper_search_mcp/academic_platforms/_base.py`.
- `paper_search_mcp/server.py`: MCP tool registry. Adding a new source requires
  wiring new `@mcp.tool()` functions and updating the tool snapshot test.
- `tests/_offline.py`: offline test helpers that deny outbound network access
  and load deterministic fixtures.
- `tests/test_server.py`: asserts a tool-name snapshot; any tool additions must
  update this expected set.
- `docs/project-specs/source-capability-matrix.md`: the system-of-record for
  `search/download/read` support per maintained source.

PMC constraints to keep explicit:

- Automated retrieval should rely on NCBI/PMC supported services (E-utilities,
  OA APIs, etc.); licenses vary; users remain responsible for compliance.
- Rate limiting matters. Do not add a new NCBI email/tool/api-key config surface
  in this ExecPlan; document the current unsupported state and defer any new
  config work to a follow-up plan.
- Canonical identifier: for this repo, the PMC `paper_id` MUST be the `PMCID`
  string with the `PMC` prefix (example: `PMC1234567`). If additional ids are
  discovered (PMID/DOI), they MUST be treated as secondary fields (`doi` and/or
  `extra`) and MUST NOT replace `paper_id`.
- Placeholder behavior: `download_pmc` / `read_pmc_paper` MUST short-circuit and
  return a `LIMITATION:` + JSON message per `docs/project-specs/mcp-tool-contract.md`
  without any network access or filesystem writes.

## Task Graph (Dependencies)

### T0: Start tracker entry for AB work

depends_on: []
reads: [docs/PLANS.md, docs/TODO.md]
writes: [docs/PLANS.md]
creates: []
mutex: file:docs/PLANS.md
description: Add a new `Active` tracker entry for this ExecPlan and scope AB.
acceptance: `docs/PLANS.md` has an Active entry pointing at this ExecPlan file.
acceptance: Tracker entry includes Difficulty, Rationale, Next steps.
validation: markdownlint docs/PLANS.md
status: done
log: (orchestrator) created task packet.
log: (orchestrator) dispatched to worker `T0-worker`.
log: (orchestrator) worker completed; `docs/PLANS.md` Active tracker entry added
  and `markdownlint docs/PLANS.md` passed.
files_changed: docs/PLANS.md

### T1: Closeout A — make current state merge-ready

depends_on: [T0]
reads: [docs/PLANS.md, docs/TODO.md]
writes: []
creates: []
mutex: closeout:a
description: Run baseline validation. Do not create commits.
acceptance: Offline unit tests pass from `[repo-root]`.
validation: PAPER_SEARCH_LIVE_TESTS=0 uv run python -m unittest discover -q
validation: PAPER_SEARCH_LIVE_TESTS=0 uv run python -m compileall paper_search_mcp
validation: PAPER_SEARCH_LIVE_TESTS=0 uv run python -m compileall tests
status: done
log: (orchestrator) dispatched to worker `T1-worker`.
log: (orchestrator) worker completed; baseline offline validations passed.
files_changed: (orchestrator) none.

### T2: PMC capability conclusion (policy + UX)

depends_on: [T0]
reads: [
  docs/TODO.md,
  docs/project-specs/mcp-tool-contract.md,
  docs/project-specs/source-capability-matrix.md,
  paper_search_mcp/server.py,
  paper_search_mcp/academic_platforms/pubmed.py,
]
writes: [docs/project-specs/source-capability-matrix.md]
creates: [docs/project-specs/source-notes/pmc.md]
mutex: file:docs/project-specs/source-capability-matrix.md
description: Decide and document PMC capability + caveats.
acceptance: Matrix includes a PMC row with `search/download/read` and clear notes.
acceptance: PMC notes doc states which APIs are used and what is avoided.
acceptance: PMC notes doc defines the canonical `paper_id` contract (PMCID with
  `PMC` prefix) and documents that `download`/`read` are placeholders that return
  a `LIMITATION:` + JSON message per tool contract.
acceptance: PMC notes doc explicitly lists v1 allowed endpoints (E-utilities
  `esearch` + `efetch` with `db=pmc`, `retmode=xml`) and explicit non-goals
  (no OA API integration, no PMC HTML scraping, no new NCBI config knobs).
validation: markdownlint docs/project-specs/source-capability-matrix.md
validation: markdownlint docs/project-specs/source-notes/pmc.md
status: done
log: (orchestrator) dispatched to worker `T2-worker`.
log: (orchestrator) worker completed; PMC capability matrix row and source notes
  doc added.
files_changed: docs/project-specs/source-capability-matrix.md
files_changed: docs/project-specs/source-notes/pmc.md

### T3: Implement PMC adapter module

depends_on: [T2]
reads: [
  docs/project-specs/mcp-tool-contract.md,
  paper_search_mcp/_http.py,
  paper_search_mcp/paper.py,
  paper_search_mcp/academic_platforms/_base.py,
  paper_search_mcp/academic_platforms/pubmed.py,
]
writes: []
creates: [paper_search_mcp/academic_platforms/pmc.py]
mutex: file:paper_search_mcp/academic_platforms/pmc.py
description: Implement PMC adapter consistent with `PaperSource`.
acceptance: Adapter supports deterministic `search(query, max_results=10)`.
acceptance: Adapter `download_pdf` / `read_paper` are explicit unsupported stubs
  (they MUST NOT perform network access or filesystem writes).
validation: PAPER_SEARCH_LIVE_TESTS=0 uv run python -m compileall paper_search_mcp
status: done
log: (orchestrator) dispatched to worker `T3-worker`.
log: (orchestrator) worker completed; PMC adapter module created with
  unsupported download/read stubs.
files_changed: paper_search_mcp/academic_platforms/pmc.py

### T4: Wire PMC into MCP server tool surface

depends_on: [T3]
reads: [
  paper_search_mcp/server.py,
  docs/project-specs/mcp-tool-contract.md,
  README.md,
]
writes: [
  paper_search_mcp/server.py,
  docs/project-specs/mcp-tool-contract.md,
  README.md,
]
creates: []
mutex: file:paper_search_mcp/server.py
description: Add `search_pmc`, `download_pmc`, `read_pmc_paper` tools; keep
  semantics consistent (`download`/`read` return structured limitation messages
  per tool contract).
acceptance: `paper_search_mcp.server` imports cleanly and registers
  `search_pmc`, `download_pmc`, `read_pmc_paper`.
acceptance: `download_pmc` / `read_pmc_paper` return `LIMITATION:` + JSON
  limitation messages per tool contract.
acceptance: `download_pmc` / `read_pmc_paper` short-circuit (no network access,
  no filesystem writes; do not call `_canonical_save_path`).
acceptance: README + tool contract reflect shipped PMC tool surface.
validation: PAPER_SEARCH_LIVE_TESTS=0 uv run python -m compileall paper_search_mcp
validation: markdownlint README.md docs/project-specs/mcp-tool-contract.md
status: done
log: (orchestrator) dispatched to worker `T4-worker`.
log: (orchestrator) worker completed; PMC tools wired in server and surface docs
  updated.
files_changed: paper_search_mcp/server.py
files_changed: docs/project-specs/mcp-tool-contract.md
files_changed: README.md

### T5: PMC offline fixtures + adapter tests

depends_on: [T4]
reads: [tests/_offline.py, tests/test_adapter_contract.py]
writes: [tests/test_pmc.py, tests/test_adapter_contract.py]
creates: [tests/fixtures/pmc/esearch.xml, tests/fixtures/pmc/efetch.xml]
mutex: file:tests/test_pmc.py
description: Add deterministic offline PMC fixture tests.
acceptance: `tests.test_pmc` uses `OfflineTestCase` and fixture-backed mocks
  (no real network access).
acceptance: `tests.test_pmc` asserts `download_pmc` / `read_pmc_paper` return a
  `LIMITATION:` + JSON limitation message per tool contract and validates by
  parsing JSON (not raw string equality).
acceptance: `tests.test_pmc` asserts placeholder tools do not create
  `docs/downloads/` as a side effect.
acceptance: PMC is added to ADAPTER_SPECS and passes contract test.
validation: PAPER_SEARCH_LIVE_TESTS=0 uv run python -m unittest -q tests.test_pmc
validation: PAPER_SEARCH_LIVE_TESTS=0 uv run python -m unittest -q tests.test_adapter_contract
status: done
log: (orchestrator) dispatched to worker `T5-worker`.
log: (orchestrator) worker completed; PMC offline fixtures/tests added and
  adapter contract updated.
files_changed: tests/test_pmc.py
files_changed: tests/test_adapter_contract.py
files_changed: tests/fixtures/pmc/esearch.xml
files_changed: tests/fixtures/pmc/efetch.xml

### T6: Update server tool snapshot test

depends_on: [T4]
reads: [tests/test_server.py]
writes: [tests/test_server.py]
creates: []
mutex: file:tests/test_server.py
description: Update tool snapshot to include `search_pmc`, `download_pmc`,
  `read_pmc_paper`.
acceptance: Snapshot remains order-insensitive (set membership, not ordering).
acceptance: Tool snapshot test passes with PMC included.
validation: PAPER_SEARCH_LIVE_TESTS=0 uv run python -m unittest -q tests.test_server
status: done
log: (orchestrator) dispatched to worker `T6-worker`.
log: (orchestrator) worker completed; server tool snapshot now includes PMC tool
  trio.
files_changed: tests/test_server.py

### T7: Orchestrator validation + evidence recording

depends_on: [T1, T2, T4, T5, T6]
reads: [paper_search_mcp/**/*.py, tests/**/*.py, docs/**/*.md]
writes: [docs/PLANS.md]
creates: []
mutex: file:docs/PLANS.md
description: Run repo-wide offline validation and record evidence.
acceptance: Offline `unittest discover -q` passes.
acceptance: `compileall` and `markdownlint` pass.
acceptance: `docs/PLANS.md` evidence is updated with concrete command transcripts.
validation: PAPER_SEARCH_LIVE_TESTS=0 uv run python -m unittest discover -q
validation: PAPER_SEARCH_LIVE_TESTS=0 uv run python -m compileall paper_search_mcp
validation: PAPER_SEARCH_LIVE_TESTS=0 uv run python -m compileall tests
validation: markdownlint README.md docs/**/*.md
status: done
log: (orchestrator) started integration validation and evidence capture.
log: (orchestrator) offline `unittest discover`, `compileall`, and
  `markdownlint` passed; tracker evidence updated in `docs/PLANS.md`.
files_changed: docs/PLANS.md

### T8: Closeout — move ExecPlan to completed + finalize tracker

depends_on: [T7]
reads: [
  docs/PLANS.md,
  docs/exec-plans/active/2026-03-13_0017_BJT_ab-closeout-pmc-adapter.md,
]
writes: [
  docs/PLANS.md,
  docs/exec-plans/active/2026-03-13_0017_BJT_ab-closeout-pmc-adapter.md,
]
creates: [
  docs/exec-plans/completed/2026-03-13_0017_BJT_ab-closeout-pmc-adapter.md,
]
mutex: plan-closeout
description: Orchestrator-only. Move plan to `completed/`; mark tracker done.
acceptance: `docs/exec-plans/active/` no longer contains this plan file.
acceptance: `docs/PLANS.md` marks the tracker completed with evidence.
validation: markdownlint docs/PLANS.md
validation: markdownlint docs/exec-plans/completed/2026-03-13_0017_BJT_ab-closeout-pmc-adapter.md
validation: test ! -f docs/exec-plans/active/2026-03-13_0017_BJT_ab-closeout-pmc-adapter.md
validation: test -f docs/exec-plans/completed/2026-03-13_0017_BJT_ab-closeout-pmc-adapter.md
status: done
log: (orchestrator) started plan closeout and tracker finalization.
log: (orchestrator) moved ExecPlan to completed and marked tracker completed.
log: (orchestrator) `markdownlint` and active/completed file existence checks
  passed for closeout.
files_changed: docs/PLANS.md
files_changed: docs/exec-plans/active/2026-03-13_0017_BJT_ab-closeout-pmc-adapter.md
files_changed: docs/exec-plans/completed/2026-03-13_0017_BJT_ab-closeout-pmc-adapter.md

## Plan of Work

- Start by creating a tracker entry (T0) so this work is visible and reviewable.
- In parallel, run closeout validations (T1) while deciding PMC scope and docs
  (T2).
- Implement the PMC adapter module (T3), then wire it into the MCP server (T4).
- Add deterministic fixtures + tests (T5) and update server tool snapshot (T6).
- Run full offline validation and update `docs/PLANS.md` evidence (T7).
- Close the plan by moving this ExecPlan into `docs/exec-plans/completed/` and
  marking the tracker completed (T8).

## Concrete Steps

1. From `[repo-root]`, run:

       uv sync --locked

2. Validate offline:

       PAPER_SEARCH_LIVE_TESTS=0 uv run python -m compileall paper_search_mcp
       PAPER_SEARCH_LIVE_TESTS=0 uv run python -m compileall tests
       PAPER_SEARCH_LIVE_TESTS=0 uv run python -m unittest discover -q

   Expect:

       OK (skipped=...)

3. Validate docs:

       markdownlint README.md docs/**/*.md

4. Validate PMC specifically (after implementation):

       PAPER_SEARCH_LIVE_TESTS=0 uv run python -m unittest -q tests.test_pmc
       PAPER_SEARCH_LIVE_TESTS=0 uv run python -m unittest -q tests.test_adapter_contract
       PAPER_SEARCH_LIVE_TESTS=0 uv run python -m unittest -q tests.test_server

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

- `optional follow-up`

## Validation and Acceptance

Baseline (must be offline):

- `PAPER_SEARCH_LIVE_TESTS=0 uv run python -m compileall paper_search_mcp tests`
- `PAPER_SEARCH_LIVE_TESTS=0 uv run python -m compileall tests`
- `PAPER_SEARCH_LIVE_TESTS=0 uv run python -m unittest discover -q`
- `markdownlint README.md docs/**/*.md`

PMC specifics:

- `PAPER_SEARCH_LIVE_TESTS=0 uv run python -m unittest -q tests.test_pmc`
- `PAPER_SEARCH_LIVE_TESTS=0 uv run python -m unittest -q tests.test_server`

## Idempotence and Recovery

- Test and lint commands are safe to rerun.
- If PMC implementation scope changes mid-flight, keep T2 (capability decision)
  as the source of truth and update dependent tasks accordingly.
- Do not create commits as part of this ExecPlan. Keep git-history work as a
  separate follow-up.

## Revision Notes

- 2026-03-13 / orchestrator — Created this plan to execute A (closeout) and B (PMC)
  concurrently with a dependency-aware task graph.
