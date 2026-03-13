# P0: Offline fixtures + adapter interface convergence

This ExecPlan is a living document. The orchestrator is the single
writer for this file: workers return completion packets; the
orchestrator updates task `status`, `log`, and `files_changed`.

If this work is tracked in `docs/PLANS.md`, keep this file synchronized
with that tracker entry.

## Orchestration

Schema version: 1
Execution mode: multi-agent
Scheduler: waves
Max parallelism: 10
Shared-state policy: orchestrator-only
Plan updates: orchestrator-only
File-scope rule: each task must declare writes/creates; workers must not
write outside without escalation
Write-allowed set: writes ∪ creates

## Purpose / Big Picture

Ship the `docs/TODO.md` P0 items:

1. Add deterministic, offline fixture/contract tests for the main adapters
   (`arxiv`, `pubmed`, `crossref`, `semantic`, `iacr`).
2. Converge the shared adapter interface so we stop duplicating the same
   `PaperSource` skeleton per module.

Success means:

- `uv run python -m unittest discover -q` remains offline by default.
- Each of the five adapters above has at least one offline test that validates
  parsing/serialization without touching the network.
- Maintained adapters share one explicit interface/protocol (and the duplicated
  `class PaperSource` definitions are removed from modules on the default
  surface).

## Progress

- [x] (2026-03-12 22:09 BJT) Capture scope, constraints, and acceptance.
- [x] (2026-03-12 23:09 BJT) Implement the planned changes.
- [x] (2026-03-12 23:11 BJT) Run validation and record evidence.
- [x] (2026-03-12 23:13 BJT) Close review notes and summarize outcomes.

## Surprises & Discoveries

- Observation: Worker retries hit `Too many open files (os error 24)`.
  Evidence: blocked completion packets for T3/T5/T8/T9 retries.
- Observation: Local fallback execution unblocked completion quickly.
  Evidence: All tasks reached `status: done` and validations passed at 23:11 BJT.

## Decision Log

- Decision: Prefer `unittest.mock` + fixture files; do not add new test deps.
  Rationale: keep default verification lightweight and dependency-free.
  Date/Author: 2026-03-12 / orchestrator
- Decision: Interface convergence is “one shared protocol + delete duplicates”,
  not a full adapter rewrite.
  Rationale: reduce maintenance cost with minimal behavior-change risk.
  Date/Author: 2026-03-12 / orchestrator

## Outcomes & Retrospective

Implemented offline fixtures/tests for arXiv, PubMed, CrossRef, Semantic, and
IACR, plus a shared `PaperSource` base in `_base.py`. Removed duplicate
`PaperSource` definitions from maintained adapters and preserved live-test
gates. Offline validation and markdownlint both passed.

## Context and Orientation

Relevant repo surfaces:

- `docs/TODO.md` defines the P0 asks (offline fixtures + interface convergence).
- `paper_search_mcp/academic_platforms/*.py` contains one adapter per source.
  Many modules currently duplicate a local `PaperSource` base class.
- `paper_search_mcp/paper.py` defines the normalized `Paper` model; MCP tools
  serialize via `Paper.to_dict()`.
- `tests/test_*.py` are mostly opt-in live tests; by default they should not hit
  the network.

Offline fixture strategy:

- Store small, representative upstream responses in `tests/fixtures/{source}/`.
- In tests, patch the narrowest call site that prevents network access
  (`Session.get`, `request_with_retries`, or an adapter method like
  `request_api`), then call the real `search()` and assert on the produced
  `Paper` objects and `to_dict()` shape.

## Task Graph (Dependencies)

### T0: Offline-test helpers (deny network + fixture loader)

depends_on: []
reads: [docs/TODO.md, tests/test_*.py]
writes: [tests/_offline.py, tests/test_adapter_contract.py]
creates: [tests/fixtures/README.md]
mutex: file:tests/_offline.py
description: Add offline helpers (fixtures + deny-network + contract test).
acceptance: Offline tests fail fast on outbound sockets while reading fixtures.
acceptance: New contract test enforces adapter interface invariants offline.
validation: uv run python -m compileall tests
validation: uv run python -m unittest -q tests.test_adapter_contract
status: done
log: (orchestrator) created task packet.
log: (2026-03-12 22:40 BJT) launched worker for T0.
log: (2026-03-12 22:50 BJT) worker completed.
log: (2026-03-12 22:50 BJT) validations passed:
log: (`compileall tests`, `tests.test_adapter_contract`).
files_changed: tests/_offline.py
files_changed: tests/test_adapter_contract.py
files_changed: tests/fixtures/README.md

### T1: Add shared adapter interface module

depends_on: []
reads: [docs/TODO.md, paper_search_mcp/academic_platforms/*.py]
writes: [paper_search_mcp/academic_platforms/_base.py]
creates: []
mutex: file:paper_search_mcp/academic_platforms/_base.py
description: Define one shared adapter protocol/ABC; remove duplicates.
acceptance: `_base.py` is importable and documents the adapter contract.
validation: uv run python -m compileall paper_search_mcp
status: done
log: (orchestrator) created task packet.
log: (2026-03-12 22:40 BJT) launched worker for T1.
log: (2026-03-12 22:50 BJT) worker completed.
log: (2026-03-12 22:50 BJT) validation passed:
log: (`compileall paper_search_mcp`).
files_changed: paper_search_mcp/academic_platforms/_base.py

### T2: arXiv - remove duplicate base + add offline fixture test

depends_on: [T0, T1]
reads: [
  paper_search_mcp/academic_platforms/arxiv.py,
  tests/_offline.py,
  tests/test_arxiv.py,
]
writes: [paper_search_mcp/academic_platforms/arxiv.py, tests/test_arxiv.py]
creates: [tests/fixtures/arxiv/search_response.xml]
mutex: adapter:arxiv
description: Import shared `PaperSource`; add offline Atom-feed fixture test.
acceptance: Offline arXiv test passes and fails if it attempts network access.
validation: uv run python -m unittest -q tests.test_arxiv
status: done
log: (2026-03-12 22:50 BJT) launched worker for T2.
log: (2026-03-12 22:58 BJT) worker completed and packet accepted.
log: (2026-03-12 23:11 BJT) validation passed (`tests.test_arxiv`).
files_changed: paper_search_mcp/academic_platforms/arxiv.py
files_changed: tests/test_arxiv.py
files_changed: tests/fixtures/arxiv/search_response.xml

### T3: PubMed - remove duplicate base + add offline fixture test

depends_on: [T0, T1]
reads: [
  paper_search_mcp/academic_platforms/pubmed.py,
  tests/_offline.py,
  tests/test_pubmed.py,
]
writes: [paper_search_mcp/academic_platforms/pubmed.py, tests/test_pubmed.py]
creates: [tests/fixtures/pubmed/esearch.xml, tests/fixtures/pubmed/efetch.xml]
mutex: adapter:pubmed
description: Import shared base; add offline PubMed fixture test.
acceptance: Offline PubMed test passes and fails if it attempts network access.
validation: uv run python -m unittest -q tests.test_pubmed
status: done
log: (2026-03-12 22:50 BJT) launched worker for T3.
log: (2026-03-12 23:00 BJT) worker retry blocked by OS FD limit.
log: (2026-03-12 23:09 BJT) orchestrator completed task locally.
log: (2026-03-12 23:11 BJT) validation passed (`tests.test_pubmed`).
files_changed: paper_search_mcp/academic_platforms/pubmed.py
files_changed: tests/test_pubmed.py
files_changed: tests/fixtures/pubmed/esearch.xml
files_changed: tests/fixtures/pubmed/efetch.xml

### T4: CrossRef - remove duplicate base + add offline fixture test

depends_on: [T0, T1]
reads: [
  paper_search_mcp/academic_platforms/crossref.py,
  tests/_offline.py,
  tests/test_crossref.py,
]
writes: [
  paper_search_mcp/academic_platforms/crossref.py,
  tests/test_crossref.py,
]
creates: [tests/fixtures/crossref/works_search.json]
mutex: adapter:crossref
description: Import shared base; add offline CrossRef JSON fixture test.
acceptance: New offline CrossRef test passes and asserts `to_dict()` keys.
validation: uv run python -m unittest -q tests.test_crossref
status: done
log: (2026-03-12 22:50 BJT) launched worker for T4.
log: (2026-03-12 23:09 BJT) orchestrator completed task locally.
log: (2026-03-12 23:11 BJT) validation passed (`tests.test_crossref`).
files_changed: paper_search_mcp/academic_platforms/crossref.py
files_changed: tests/test_crossref.py
files_changed: tests/fixtures/crossref/works_search.json

### T5: Semantic Scholar - remove duplicate base + add offline fixture test

depends_on: [T0, T1]
reads: [
  paper_search_mcp/academic_platforms/semantic.py,
  tests/_offline.py,
  tests/test_semantic.py,
]
writes: [
  paper_search_mcp/academic_platforms/semantic.py,
  tests/test_semantic.py,
]
creates: [tests/fixtures/semantic/paper_search.json]
mutex: adapter:semantic
description: Import shared base; add offline Semantic JSON fixture test.
acceptance: New offline Semantic test passes and validates normalized fields.
validation: uv run python -m unittest -q tests.test_semantic
status: done
log: (2026-03-12 22:50 BJT) launched worker for T5.
log: (2026-03-12 22:57 BJT) worker blocked by OS FD limit.
log: (2026-03-12 23:09 BJT) orchestrator completed task locally.
log: (2026-03-12 23:11 BJT) validation passed (`tests.test_semantic`).
files_changed: paper_search_mcp/academic_platforms/semantic.py
files_changed: tests/test_semantic.py
files_changed: tests/fixtures/semantic/paper_search.json

### T6: IACR - remove duplicate base + add offline fixture test

depends_on: [T0, T1]
reads: [
  paper_search_mcp/academic_platforms/iacr.py,
  tests/_offline.py,
  tests/test_iacr.py,
]
writes: [paper_search_mcp/academic_platforms/iacr.py, tests/test_iacr.py]
creates: [tests/fixtures/iacr/search.html]
mutex: adapter:iacr
description: Import shared `PaperSource`; add offline IACR HTML fixture test.
acceptance: New offline IACR test passes and asserts `to_dict()` keys.
validation: uv run python -m unittest -q tests.test_iacr
status: done
log: (2026-03-12 22:50 BJT) launched worker for T6.
log: (2026-03-12 23:09 BJT) orchestrator completed task locally.
log: (2026-03-12 23:11 BJT) validation passed (`tests.test_iacr`).
files_changed: paper_search_mcp/academic_platforms/iacr.py
files_changed: tests/test_iacr.py
files_changed: tests/fixtures/iacr/search.html

### T7: bioRxiv - remove duplicate base

depends_on: [T1]
reads: [paper_search_mcp/academic_platforms/biorxiv.py]
writes: [paper_search_mcp/academic_platforms/biorxiv.py]
creates: []
mutex: adapter:biorxiv
description: Replace module-local `PaperSource` with an import from `_base.py`.
acceptance: bioRxiv adapter imports cleanly and has no local `PaperSource`.
validation: uv run python -m compileall paper_search_mcp
status: done
log: (2026-03-12 22:50 BJT) launched worker for T7.
log: (2026-03-12 23:09 BJT) orchestrator completed task locally.
log: (2026-03-12 23:11 BJT) compileall passed for `paper_search_mcp`.
files_changed: paper_search_mcp/academic_platforms/biorxiv.py

### T8: medRxiv - remove duplicate base

depends_on: [T1]
reads: [paper_search_mcp/academic_platforms/medrxiv.py]
writes: [paper_search_mcp/academic_platforms/medrxiv.py]
creates: []
mutex: adapter:medrxiv
description: Replace module-local `PaperSource` with an import from `_base.py`.
acceptance: medRxiv adapter imports cleanly and has no local `PaperSource`.
validation: uv run python -m compileall paper_search_mcp
status: done
log: (2026-03-12 22:50 BJT) launched worker for T8.
log: (2026-03-12 22:56 BJT) worker blocked by OS FD limit.
log: (2026-03-12 23:09 BJT) orchestrator completed task locally.
log: (2026-03-12 23:11 BJT) compileall passed for `paper_search_mcp`.
files_changed: paper_search_mcp/academic_platforms/medrxiv.py

### T9: Google Scholar - remove duplicate base

depends_on: [T1]
reads: [paper_search_mcp/academic_platforms/google_scholar.py]
writes: [paper_search_mcp/academic_platforms/google_scholar.py]
creates: []
mutex: adapter:google_scholar
description: Replace module-local `PaperSource` with an import from `_base.py`.
acceptance: Google Scholar imports cleanly and has no local `PaperSource`.
validation: uv run python -m compileall paper_search_mcp
status: done
log: (2026-03-12 22:50 BJT) launched worker for T9.
log: (2026-03-12 22:57 BJT) worker blocked by OS FD limit.
log: (2026-03-12 23:09 BJT) orchestrator completed task locally.
log: (2026-03-12 23:11 BJT) compileall passed for `paper_search_mcp`.
files_changed: paper_search_mcp/academic_platforms/google_scholar.py

### T10: Orchestrator integration + repo-wide validation

depends_on: [T2, T3, T4, T5, T6, T7, T8, T9]
reads: [paper_search_mcp/academic_platforms/*.py, tests/*.py, tests/fixtures/**]
writes: []
creates: []
mutex: validation:repo
description: Run repo-wide offline validation and record evidence.
acceptance: `unittest discover -q` passes offline; no duplicate `PaperSource`.
validation: env -u PAPER_SEARCH_LIVE_TESTS uv run python -m unittest discover -q
validation: uv run python -m compileall paper_search_mcp
validation: PAPER_SEARCH_LIVE_TESTS=0 uv run python -m compileall tests
status: done
log: (2026-03-12 23:11 BJT) compileall passed for `paper_search_mcp`.
log: (2026-03-12 23:11 BJT) compileall passed for `tests`.
log: (2026-03-12 23:11 BJT) `unittest discover -q` passed offline.
log: (2026-03-12 23:11 BJT) confirmed no duplicate adapter `PaperSource`.
files_changed: (orchestrator) none.

## Plan of Work

Wave 1:

- T1 lands first (shared interface module).

Wave 2 (parallel):

- T2–T9 apply the interface import per adapter and add offline fixtures/tests
  for the five main adapters.

Wave 3:

- T10 runs the offline verification suite and writes down evidence.

## Concrete Steps

1. From `[repo-root]`, run:

       uv sync --locked

2. Implement tasks in waves (see Task Graph).

3. From `[repo-root]`, run:

       PAPER_SEARCH_LIVE_TESTS=0 uv run python -m compileall paper_search_mcp
       PAPER_SEARCH_LIVE_TESTS=0 uv run python -m compileall tests
       PAPER_SEARCH_LIVE_TESTS=0 uv run python -m unittest discover -q

   Expect:

       OK (skipped=...)

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

- `PAPER_SEARCH_LIVE_TESTS=0 uv run python -m compileall paper_search_mcp`
- `PAPER_SEARCH_LIVE_TESTS=0 uv run python -m compileall tests`
- `PAPER_SEARCH_LIVE_TESTS=0 uv run python -m unittest discover -q`

Targeted per-adapter checks:

- `uv run python -m unittest -q tests.test_arxiv`
- `uv run python -m unittest -q tests.test_pubmed`
- `uv run python -m unittest -q tests.test_crossref`
- `uv run python -m unittest -q tests.test_semantic`
- `uv run python -m unittest -q tests.test_iacr`

## Idempotence and Recovery

- Tests and `compileall` are safe to rerun.
- If an adapter refactor breaks a live-only test, keep the offline test intact
  and gate the live test behind `PAPER_SEARCH_LIVE_TESTS=1` as before.

## Revision Notes

- 2026-03-12 / orchestrator — Created this plan for `docs/TODO.md` P0 work.
