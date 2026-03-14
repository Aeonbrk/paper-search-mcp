# Optimize Paper Search Runtime Quality

This ExecPlan is a living document. The orchestrator is the single
writer for this file: workers return completion packets; the
orchestrator updates task `status`, `log`, and `files_changed`.

If this work is tracked in `docs/PLANS.md`, keep this file synchronized
with that tracker entry.

## Orchestration

Schema version: 1
Execution mode: multi-agent
Scheduler: waves
Max parallelism: 4
Shared-state policy: orchestrator-only
Plan updates: orchestrator-only
File-scope rule: each task must declare writes/creates; workers must not
write outside without escalation
Write-allowed set: writes ∪ creates

## Purpose / Big Picture

Improve `paper-search-mcp` in three dimensions without changing its
public runtime identity or MCP tool names:

1. Performance: reduce avoidable latency, repeated setup work, and
   unnecessary network churn.
2. Stability: normalize retry/error behavior and remove silent failures.
3. Maintainability: shrink duplication, centralize shared logic, and
   keep tests/docs aligned with behavior.

Done means the server keeps the current public tool surface, but the
internals are cleaner, better tested offline, and operationally safer
under transient upstream failures.

## Progress

- [x] (2026-03-14 14:09 BJT) Capture scope, constraints, and acceptance criteria.
- [x] (2026-03-14 14:36 BJT) Implement the planned changes.
- [x] (2026-03-14 14:58 BJT) Run validation and record evidence.
- [x] (2026-03-14 15:00 BJT) Close review notes and summarize outcomes.

## Surprises & Discoveries

- Observation: adapters mix multiple request patterns (`session.get` in
  several places, `request_with_retries` elsewhere), which creates
  inconsistent retry and timeout behavior.
  Evidence: `paper_search_mcp/academic_platforms/*.py` review on
  2026-03-14.
- Observation: `biorxiv.py` and `medrxiv.py` are near-identical, so
  every bugfix currently has to be mirrored manually.
  Evidence: direct `diff -u` between both files on 2026-03-14.
- Observation: several code paths still use `print(...)` plus broad
  `except Exception`, reducing observability and hiding failure causes.
  Evidence: `rg -n "print\\(|except Exception" paper_search_mcp`.
- Observation: MCP entrypoint logic in `server.py` is repetitive, which
  increases drift risk between tool behaviors over time.
  Evidence: repeated wrappers in `paper_search_mcp/server.py`.
- Observation: upstream `requests` guidance favors `Session` reuse plus
  `HTTPAdapter`/`Retry` for pooled, resilient requests.
  Evidence: Context7 `/psf/requests` docs lookup on 2026-03-14.
- Observation: MCP Python SDK guidance supports simple decorated tool
  handlers; blocking I/O remains safe when isolated from event-loop
  critical paths.
  Evidence: Context7 `/modelcontextprotocol/python-sdk` lookup on
  2026-03-14.
- Observation: PDF text extraction can return empty output or fail on
  malformed files; explicit guardrails are recommended.
  Evidence: Context7 `/websites/pypdf_readthedocs_io_en` lookup on
  2026-03-14.

## Decision Log

- Decision: keep a strict compatibility boundary for MCP tool names and
  high-level contracts while refactoring internals.
  Rationale: user asked for quality optimization, not API redesign.
  Date/Author: 2026-03-14 / Codex
- Decision: introduce shared HTTP and PDF utility layers before adapter
  refactors.
  Rationale: this gives one reliability/perf foundation that all
  adapters can adopt consistently.
  Date/Author: 2026-03-14 / Codex
- Decision: run adapter refactors in parallel by source family
  (API-backed, scraping-backed, preprint pair) with disjoint write sets.
  Rationale: maximize swarm throughput while avoiding file conflicts.
  Date/Author: 2026-03-14 / Codex
- Decision: keep Sci-Hub outside the default optimization surface unless
  explicitly requested.
  Rationale: repo policy marks it optional and sensitive.
  Date/Author: 2026-03-14 / Codex

## Outcomes & Retrospective

Completed. The runtime now has shared HTTP and PDF utility baselines,
centralized server dispatch wrappers, and reduced duplication for the
bioRxiv/medRxiv path. Offline regression coverage now includes
transport policy behavior and deterministic performance smoke checks.
Durable docs were synchronized with the new reliability/performance
guardrails and canonical path behavior.

## Context and Orientation

`paper_search_mcp/server.py` is the FastMCP entrypoint and tool
registration surface. `paper_search_mcp/_http.py` is the shared HTTP
utility baseline. `paper_search_mcp/academic_platforms/` contains one
adapter per source, with notable duplication between
`biorxiv.py`/`medrxiv.py`. `paper_search_mcp/_paths.py` centralizes safe
download path handling. `tests/` contains offline contract tests plus
opt-in live checks. Durable contracts live under
`docs/project-specs/`, while `docs/PLANS.md` tracks accepted multi-step
work.

## Task Graph (Dependencies)

### T1: Baseline Targets And Perf Harness

depends_on: []
reads: [README.md, ARCHITECTURE.md, docs/playbooks/validation.md, tests/test_mcp_live.py]
writes: [docs/project-specs/performance-stability-targets.md]
creates: [scripts/benchmarks/tool_latency_smoke.py]
mutex: file:docs/project-specs/performance-stability-targets.md
description: Define measurable latency/error targets and add a small
  reproducible benchmark harness to quantify before/after impact.
acceptance: Baseline and target metrics are documented for at least
  `search`, `download`, and `read` representative paths.
acceptance: Benchmark script is deterministic enough for local
  comparison runs and does not require changing production code.
acceptance: Benchmark script provides a `--dry-run` mode that exercises
  the execution path without requiring network calls.
validation: uv run python scripts/benchmarks/tool_latency_smoke.py --help
validation: uv run python scripts/benchmarks/tool_latency_smoke.py
  --dry-run --iterations 1
status: done
log: (orchestrator) task packet created.
log: (2026-03-14 14:28 BJT) Completed by subagent; benchmark harness and
  target spec added with dry-run validation passing.
files_changed: (orchestrator) none.
files_changed: docs/project-specs/performance-stability-targets.md
files_changed: scripts/benchmarks/tool_latency_smoke.py

### T2: Harden Shared HTTP Client Layer

depends_on: [T1]
reads: [paper_search_mcp/_http.py, paper_search_mcp/academic_platforms/arxiv.py,
  paper_search_mcp/academic_platforms/pubmed.py, paper_search_mcp/academic_platforms/pmc.py]
writes: [paper_search_mcp/_http.py]
creates: [tests/test_http.py]
mutex: file:paper_search_mcp/_http.py
description: Upgrade shared HTTP utilities to consistent session
  configuration, retry semantics, and clearer transport error handling.
acceptance: Shared session setup supports pooled connections and
  retry/backoff policy configuration aligned with `requests` guidance.
acceptance: Callers can opt into consistent retryable status codes
  without duplicating retry code in adapters.
acceptance: New unit tests pin timeout/retry behavior and failure
  propagation.
validation: uv run python -m unittest -q tests.test_http
status: done
log: (orchestrator) task packet created.
log: (2026-03-14 14:31 BJT) Completed by subagent; shared HTTP session
  transport hardened and tests added.
files_changed: (orchestrator) none.
files_changed: paper_search_mcp/_http.py
files_changed: tests/test_http.py

### T3: Add Shared PDF Download/Extraction Utilities

depends_on: [T1]
reads: [paper_search_mcp/academic_platforms/arxiv.py, paper_search_mcp/academic_platforms/biorxiv.py,
  paper_search_mcp/academic_platforms/medrxiv.py, paper_search_mcp/academic_platforms/iacr.py,
  paper_search_mcp/academic_platforms/semantic.py, paper_search_mcp/_paths.py,
  tests/test_paths.py]
writes: []
creates: [paper_search_mcp/_pdf.py, tests/test_pdf_utils.py]
mutex: file:paper_search_mcp/_pdf.py
description: Create reusable helpers for streamed PDF downloads and
  robust text extraction with explicit failure signaling.
acceptance: Shared helper supports large-file-safe streaming writes and
  consistent return/exception behavior.
acceptance: Text extraction path handles empty or malformed PDFs without
  silent success.
acceptance: PDF helper integration preserves canonical safe-write routing
  under `docs/downloads/`.
acceptance: Unit tests cover happy path and malformed/empty edge cases.
validation: uv run python -m unittest -q tests.test_pdf_utils
validation: uv run python -m unittest -q tests.test_paths
status: done
log: (orchestrator) task packet created.
log: (2026-03-14 14:31 BJT) Completed by subagent; shared PDF
  download/extraction utilities and tests added.
files_changed: (orchestrator) none.
files_changed: paper_search_mcp/_pdf.py
files_changed: tests/test_pdf_utils.py

### T4: Refactor Server Dispatch And Error Policy

depends_on: [T1]
reads: [paper_search_mcp/server.py, docs/project-specs/mcp-tool-contract.md, tests/test_server.py,
  tests/test_search_contract.py]
writes: [paper_search_mcp/server.py, tests/test_server.py, tests/test_search_contract.py]
creates: []
mutex: file:paper_search_mcp/server.py
description: Reduce wrapper duplication in `server.py` and enforce
  consistent tool-level error propagation semantics.
acceptance: Search/download/read tool wrappers use a centralized dispatch
  pattern with no behavior drift across sources.
acceptance: Unsupported capability responses remain contract-compatible.
acceptance: Server tests pin the updated dispatch behavior.
validation: uv run python -m unittest -q tests.test_server tests.test_search_contract
status: done
log: (orchestrator) task packet created.
log: (2026-03-14 14:31 BJT) Completed by subagent; centralized server
  dispatch and error-policy tests updated.
files_changed: (orchestrator) none.
files_changed: paper_search_mcp/server.py
files_changed: tests/test_server.py
files_changed: tests/test_search_contract.py

### T5: API-Backed Adapter Reliability Pass

depends_on: [T2, T3]
reads: [paper_search_mcp/academic_platforms/arxiv.py, paper_search_mcp/academic_platforms/pubmed.py,
  paper_search_mcp/academic_platforms/pmc.py, paper_search_mcp/academic_platforms/crossref.py,
  paper_search_mcp/academic_platforms/semantic.py]
writes: [paper_search_mcp/academic_platforms/arxiv.py, paper_search_mcp/academic_platforms/pubmed.py,
  paper_search_mcp/academic_platforms/pmc.py, paper_search_mcp/academic_platforms/crossref.py,
  paper_search_mcp/academic_platforms/semantic.py, tests/test_arxiv.py, tests/test_pubmed.py,
  tests/test_pmc.py, tests/test_crossref.py, tests/test_semantic.py]
creates: []
mutex: file:paper_search_mcp/academic_platforms/arxiv.py
description: Migrate API-backed sources to shared HTTP/PDF utilities and
  remove ad hoc error handling and print-based diagnostics.
acceptance: Target adapters no longer rely on direct `session.get`
  boilerplate where shared helpers apply.
acceptance: Exception handling is explicit and source-appropriate, with
  logging instead of print statements.
acceptance: Existing contracts for empty results and unsupported actions
  remain intact.
validation: uv run python -m unittest -q tests.test_arxiv
  tests.test_pubmed tests.test_pmc tests.test_crossref tests.test_semantic
status: done
log: (orchestrator) task packet created.
log: (2026-03-14 14:34 BJT) Completed by subagent; API-backed adapters
  migrated to shared HTTP/PDF flows with updated tests.
files_changed: (orchestrator) none.
files_changed: paper_search_mcp/academic_platforms/arxiv.py
files_changed: paper_search_mcp/academic_platforms/pubmed.py
files_changed: paper_search_mcp/academic_platforms/pmc.py
files_changed: paper_search_mcp/academic_platforms/semantic.py
files_changed: tests/test_arxiv.py
files_changed: tests/test_pubmed.py
files_changed: tests/test_pmc.py
files_changed: tests/test_semantic.py

### T6: Scraping Adapter Stability And Throughput Pass

depends_on: [T2, T3]
reads: [paper_search_mcp/academic_platforms/google_scholar.py, paper_search_mcp/academic_platforms/iacr.py,
  tests/test_google_scholar.py, tests/test_iacr.py, tests/fixtures/iacr/search.html]
writes: [paper_search_mcp/academic_platforms/google_scholar.py, paper_search_mcp/academic_platforms/iacr.py,
  tests/test_google_scholar.py, tests/test_iacr.py]
creates: [tests/fixtures/google_scholar/search_no_results.html,
  tests/fixtures/google_scholar/search_partial_results.html,
  tests/fixtures/iacr/search_partial.html]
mutex: file:paper_search_mcp/academic_platforms/google_scholar.py
description: Tighten parsing guards, request pacing, and fallback logic
  for scraping-driven sources where upstream HTML instability is common.
acceptance: No-hit behavior stays deterministic and distinct from
  transport failures.
acceptance: Detail-fetch behavior remains bounded and does not degrade
  search latency unexpectedly.
acceptance: Adapter tests cover at least one degraded/partial-parse path
  per touched source using deterministic fixtures.
validation: uv run python -m unittest -q tests.test_google_scholar tests.test_iacr
status: done
log: (orchestrator) task packet created.
log: (2026-03-14 14:34 BJT) Completed by subagent; scraping adapters
  hardened for partial pages and bounded detail-fetch.
files_changed: (orchestrator) none.
files_changed: paper_search_mcp/academic_platforms/google_scholar.py
files_changed: paper_search_mcp/academic_platforms/iacr.py
files_changed: tests/test_google_scholar.py
files_changed: tests/test_iacr.py
files_changed: tests/fixtures/google_scholar/search_no_results.html
files_changed: tests/fixtures/google_scholar/search_partial_results.html
files_changed: tests/fixtures/iacr/search_partial.html

### T7: Deduplicate bioRxiv/medRxiv Core

depends_on: [T2, T3]
reads: [paper_search_mcp/academic_platforms/biorxiv.py, paper_search_mcp/academic_platforms/medrxiv.py,
  tests/test_biorxiv.py, tests/test_medrxiv.py]
writes: [paper_search_mcp/academic_platforms/biorxiv.py, paper_search_mcp/academic_platforms/medrxiv.py,
  tests/test_biorxiv.py, tests/test_medrxiv.py]
creates: [paper_search_mcp/academic_platforms/_preprint_base.py, tests/test_preprint_base.py]
mutex: file:paper_search_mcp/academic_platforms/_preprint_base.py
description: Extract shared preprint search/download/read behavior into a
  single internal base utility to remove mirrored logic.
acceptance: Shared preprint behavior lives in one place and source
  modules keep only source-specific constants.
acceptance: Existing search contract behavior for both sources remains
  unchanged.
acceptance: New focused unit tests cover the shared helper behavior.
validation: uv run python -m unittest -q tests.test_biorxiv tests.test_medrxiv tests.test_preprint_base
status: done
log: (orchestrator) task packet created.
log: (2026-03-14 14:34 BJT) Completed by subagent; shared preprint base
  extracted and bioRxiv/medRxiv deduplicated.
files_changed: (orchestrator) none.
files_changed: paper_search_mcp/academic_platforms/_preprint_base.py
files_changed: paper_search_mcp/academic_platforms/biorxiv.py
files_changed: paper_search_mcp/academic_platforms/medrxiv.py
files_changed: tests/test_biorxiv.py
files_changed: tests/test_medrxiv.py
files_changed: tests/test_preprint_base.py

### T8: Add Reliability And Performance Regression Suite

depends_on: [T4, T5, T6, T7]
reads: [tests/test_adapter_contract.py, tests/test_search_contract.py,
  docs/project-specs/performance-stability-targets.md]
writes: [tests/test_adapter_contract.py, tests/test_search_contract.py]
creates: [tests/test_http_resilience.py, tests/test_performance_smoke.py]
mutex: file:tests/test_performance_smoke.py
description: Add deterministic regression tests for retry semantics,
  failure handling, and lightweight performance guardrails.
acceptance: New tests fail on retry regression, silent exception
  swallowing, or major latency regressions in local smoke scenarios.
acceptance: Latency regression checks use explicit threshold keys defined
  in `docs/project-specs/performance-stability-targets.md`.
acceptance: Suite remains offline by default and compatible with current
  CI/offline gate.
validation: uv run python -m unittest -q tests.test_http_resilience
  tests.test_performance_smoke tests.test_adapter_contract
  tests.test_search_contract
status: done
log: (orchestrator) task packet created.
log: (2026-03-14 14:36 BJT) Completed by subagent; reliability/perf
  regression tests added and offline validation passed.
files_changed: (orchestrator) none.
files_changed: tests/test_adapter_contract.py
files_changed: tests/test_search_contract.py
files_changed: tests/test_http_resilience.py
files_changed: tests/test_performance_smoke.py

### T9: Docs And Codemap Synchronization

depends_on: [T1, T5, T6, T7, T8]
reads: [README.md, ARCHITECTURE.md, docs/PROJECT_SENSE.md,
  docs/project-specs/mcp-tool-contract.md, docs/project-specs/source-capability-matrix.md,
  codemap/reference/CODEBASE_MAP.md]
writes: [README.md, ARCHITECTURE.md, docs/PROJECT_SENSE.md,
  docs/project-specs/mcp-tool-contract.md, docs/project-specs/source-capability-matrix.md,
  codemap/reference/CODEBASE_MAP.md]
creates: [docs/project-specs/adapter-error-handling-policy.md]
mutex: file:docs/project-specs/mcp-tool-contract.md
description: Update durable docs to match the refactored runtime and make
  operational guardrails explicit for maintainers.
acceptance: Public docs describe stable tool behavior while explaining
  new internal reliability/performance guardrails.
acceptance: Capability matrix remains explicit about uneven source
  support and sensitive optional surfaces.
acceptance: Codemap reflects new shared utility modules and adapter
  ownership boundaries.
validation: markdownlint README.md ARCHITECTURE.md docs/PROJECT_SENSE.md
validation: markdownlint docs/project-specs/mcp-tool-contract.md
  docs/project-specs/source-capability-matrix.md
  docs/project-specs/adapter-error-handling-policy.md
validation: markdownlint codemap/reference/CODEBASE_MAP.md
status: done
log: (orchestrator) task packet created.
files_changed: (orchestrator) none.
log: (2026-03-14 14:52 BJT) Completed by orchestrator; docs and codemap
  synchronized with reliability/performance guardrails.
log: `markdownlint README.md ARCHITECTURE.md docs/PROJECT_SENSE.md` passed.
log: `markdownlint docs/project-specs/mcp-tool-contract.md
  docs/project-specs/source-capability-matrix.md
  docs/project-specs/adapter-error-handling-policy.md` passed.
log: `markdownlint codemap/reference/CODEBASE_MAP.md` passed.
files_changed: README.md
files_changed: ARCHITECTURE.md
files_changed: docs/PROJECT_SENSE.md
files_changed: docs/project-specs/mcp-tool-contract.md
files_changed: docs/project-specs/source-capability-matrix.md
files_changed: docs/project-specs/adapter-error-handling-policy.md
files_changed: codemap/reference/CODEBASE_MAP.md

### T10: Full Validation, Tracker Update, And Closeout

depends_on: [T9]
reads: [docs/PLANS.md, docs/exec-plans/active/2026-03-14_1409_BJT_paper-search-perf-stability-maintainability.md]
writes: [docs/PLANS.md, docs/exec-plans/active/2026-03-14_1409_BJT_paper-search-perf-stability-maintainability.md]
creates: []
mutex: file:docs/PLANS.md
description: Run the full agreed validation matrix, record evidence,
  update tracker fields, and produce final execution notes.
acceptance: All modified Python modules compile successfully.
acceptance: Offline unit tests pass with explicit reporting for any
  intentional skips.
acceptance: `docs/PLANS.md` entry is updated with execution evidence and
  next-step state.
acceptance: This ExecPlan is updated in lockstep with final
  `status`/`log`/`files_changed` and validation evidence.
validation: uv sync --locked
validation: uv run python -m compileall paper_search_mcp tests
validation: uv run python -c "import paper_search_mcp.server as s; print(s.mcp.name)"
validation: uv run python -m unittest discover -q
validation: markdownlint README.md ARCHITECTURE.md docs/PROJECT_SENSE.md docs/PLANS.md
validation: find docs -type f -name '*.md' | sort | xargs markdownlint
validation: find codemap -type f -name '*.md' | sort | xargs markdownlint
status: done
log: (orchestrator) task packet created.
log: (2026-03-14 14:59 BJT) Completed by orchestrator; full validation
  matrix passed and tracker synchronized.
log: `uv sync --locked` passed.
log: `uv run python -m compileall paper_search_mcp tests` passed.
log: `uv run python -c "import paper_search_mcp.server as s; print(s.mcp.name)"`
  printed `paper_search_server`.
log: `uv run python -m unittest discover -q` passed with
  `OK (skipped=26)`.
log: `markdownlint README.md ARCHITECTURE.md docs/PROJECT_SENSE.md
  docs/PLANS.md` passed.
log: `find docs -type f -name '*.md' | sort | xargs markdownlint` passed.
log: `find codemap -type f -name '*.md' | sort | xargs markdownlint`
  passed.
files_changed: (orchestrator) none.
files_changed: docs/PLANS.md
files_changed: docs/exec-plans/active/2026-03-14_1409_BJT_paper-search-perf-stability-maintainability.md

## Plan of Work

Wave 1 lays the foundation with measurable targets plus shared utility
upgrades (`T1` to `T4`). Wave 2 executes parallel adapter migrations by
source family (`T5`, `T6`, `T7`) with disjoint write scopes. Wave 3 adds
cross-cutting regression coverage (`T8`), synchronizes durable docs
(`T9`), then runs full validation and records evidence (`T10`).

The implementation strategy is deliberately stability-first: keep tool
contracts and source capability boundaries intact while improving how the
code gets there.

## Concrete Steps

1. From `[repo-root]`, run:

       TZ=Asia/Shanghai date +"%Y-%m-%d_%H%M_BJT"

   Expect:

       A timestamp used in the active ExecPlan filename.

2. From `[repo-root]`, run:

       uv sync --locked

   Expect:

       Dependency environment is aligned with `uv.lock`.

3. From `[repo-root]`, run:

       uv run python -m unittest -q tests.test_server tests.test_search_contract

   Expect:

       Baseline server contract tests pass before refactor waves start.

4. From `[repo-root]`, run after each wave:

       uv run python -m compileall paper_search_mcp tests

   Expect:

       No syntax/import regressions from parallel edits.

5. From `[repo-root]`, run at final closeout:

       uv run python -m unittest discover -q

   Expect:

       Offline default suite passes.

## Completion Packet (Workers)

**Status:** `[COMPLETED | FAILED | BLOCKED]`

**Files modified/created:**

- [path]

**Acceptance criteria coverage:**

- [criterion] -> [how it is satisfied]

**Validation performed:**

- [command] -> [result]

**Open risks / blockers:**

- [notes]

**Suggested follow-ups:**

- [optional next task or integration note]

## Validation and Acceptance

Primary acceptance is offline deterministic validation plus compile/import
health. Live-network validation is optional and should only be run for
the specific adapters touched when upstream availability is stable.

## Idempotence and Recovery

Most steps are safe to rerun: tests, compile checks, and markdown lint.
If a wave partially lands, recover by rerunning that wave’s tests first,
then continue forward; avoid cross-wave rollback unless a contract break
is proven. Maintain one orchestrator writer for `docs/PLANS.md` and this
ExecPlan to avoid tracker drift.

## Revision Notes

- 2026-03-14 / Codex — Created initial swarm ExecPlan for performance,
  stability, and maintainability optimization.
