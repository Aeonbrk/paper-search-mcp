# Stabilize And Align Non-Semantic Search Tools

This ExecPlan is a living document. The orchestrator is the single
writer for this file: workers return completion packets; the
orchestrator updates task `status`, `log`, and `files_changed`.

If this work is tracked in `docs/PLANS.md`, keep this file synchronized
with that tracker entry.

## Orchestration

Schema version: 1
Execution mode: multi-agent
Scheduler: waves
Max parallelism: 3
Shared-state policy: orchestrator-only
Plan updates: orchestrator-only
File-scope rule: each task must declare writes/creates; workers must not
write outside without escalation
Write-allowed set: writes ∪ creates

## Purpose / Big Picture

Bring the non-Semantic `search_*` MCP tools back into contract alignment.
The current live probes show three concrete problems: zero-hit searches can
fail at the MCP boundary with `Unexpected response type`, `search_biorxiv`
and `search_medrxiv` do not behave like general search tools, and the live
test surface does not currently pin either failure mode. The goal is to keep
public tool names stable while making non-Semantic search behavior predictable,
query-driven, and regression-tested. Semantic Scholar is explicitly out of
scope for this pass because the user chose to defer API-key-dependent work.

## Progress

- [x] (2026-03-14 00:44 BJT) Capture scope, constraints, and acceptance criteria.
- [x] (2026-03-14 01:11 BJT) Implement the planned changes.
- [x] (2026-03-14 01:14 BJT) Run validation and record evidence.
- [x] (2026-03-14 01:14 BJT) Close review notes and summarize outcomes.

## Surprises & Discoveries

- Observation: direct adapter calls return ordinary empty Python lists for
  no-hit queries, but several MCP tool invocations fail instead of returning an
  empty result.
  Evidence: 2026-03-14 live probes via MCP plus local `uv run python` adapter
  checks showed `arxiv`, `pubmed`, `pmc`, `google_scholar`, `iacr`, and
  `crossref` returning empty lists locally while MCP produced
  `Unexpected response type`.
- Observation: `search_biorxiv` and `search_medrxiv` are implemented as
  category filters over recent papers rather than free-text search.
  Evidence: `paper_search_mcp/academic_platforms/biorxiv.py` and
  `paper_search_mcp/academic_platforms/medrxiv.py` use `?category=...` and
  returned the same recent results for both a real query and a nonsense query.
- Observation: current MCP SDK guidance allows empty structured results and
  also supports explicit `CallToolResult(content=[])` for empty tool outputs.
  Evidence: Context7 lookup for `/modelcontextprotocol/python-sdk` on
  2026-03-14.
- Observation: the documented bioRxiv/medRxiv API surface is still date-range
  oriented and does not publish a true free-text endpoint.
  Evidence: `https://api.biorxiv.org/` lists `details/[server]/[interval]`
  plus optional `category`, and live probes on 2026-03-14 showed bioRxiv
  returning `category=all` for both a plausible and a nonsense category.

## Decision Log

- Decision: exclude Semantic Scholar changes from this plan.
  Rationale: user explicitly deferred Semantic Scholar because it needs an API
  key for reliable work in this environment.
  Date/Author: 2026-03-14 / Codex
- Decision: preserve existing public tool names and make behavior match those
  names instead of narrowing the contract to category-only behavior.
  Rationale: the public surface already advertises `search_biorxiv` and
  `search_medrxiv` as generic search tools, and the user selected the
  true-search direction.
  Date/Author: 2026-03-14 / Codex
- Decision: start with regression tests and protocol evidence before choosing
  the exact empty-result serialization fix.
  Rationale: the adapter layer already returns empty lists, so the bug needs to
  be pinned at the MCP boundary before changing server behavior.
  Date/Author: 2026-03-14 / Codex
- Decision: implement bioRxiv and medRxiv search as bounded metadata retrieval
  plus local query matching.
  Rationale: the public tools are query-driven, but the upstream API does not
  publish a dependable free-text endpoint, and raw category pass-through was
  returning unrelated papers for nonsense queries.
  Date/Author: 2026-03-14 / Codex

## Outcomes & Retrospective

Completed. Non-Semantic search tools now distinguish ordinary no-hit queries
from transport failures across both deterministic adapter tests and the live
MCP smoke path. bioRxiv and medRxiv still expose the same public tool names,
but now implement bounded recent-metadata retrieval plus local query matching
so nonsense queries return `[]` instead of unrelated recent papers. The live
MCP smoke suite now accepts protocol-valid empty search results, and the
bounded reliability pass hardened CrossRef date parsing while adding no-hit
coverage for CrossRef, Google Scholar, and IACR. Semantic Scholar stayed out
of scope in code, tests, and docs apart from explicit scope notes.

## Context and Orientation

`paper_search_mcp/server.py` defines the public FastMCP tool surface and
contains the shared `_search_sync` wrapper used by most search tools.
`paper_search_mcp/academic_platforms/` contains source-specific adapters.
`paper_search_mcp/academic_platforms/biorxiv.py` and
`paper_search_mcp/academic_platforms/medrxiv.py` currently turn the incoming
query into a `category` filter instead of performing free-text search.
`tests/test_mcp_live.py` is the protocol-level live smoke suite for the MCP
surface. `tests/test_server.py` checks tool registration and selected schema
contracts. Source-specific tests such as `tests/test_biorxiv.py`,
`tests/test_medrxiv.py`, `tests/test_crossref.py`, `tests/test_google_scholar.py`,
and `tests/test_iacr.py` cover adapter behavior with a mix of offline fixtures
and opt-in live checks. `docs/project-specs/mcp-tool-contract.md` and
`docs/project-specs/source-capability-matrix.md` define the public search
surface and source-specific expectations.

## Task Graph (Dependencies)

### T1: Pin Deterministic Search Contracts

depends_on: []
reads: [paper_search_mcp/server.py, tests/test_mcp_live.py,
  tests/test_server.py, docs/project-specs/mcp-tool-contract.md]
writes: [tests/test_server.py]
creates: [tests/test_search_contract.py]
mutex: file:tests/test_search_contract.py
description: Add deterministic regression coverage for zero-hit search
  behavior and for the non-Semantic search tool contract before
  changing implementation.
acceptance: There is at least one deterministic server-level or
  adapter-level regression test that makes the expected empty-result
  contract explicit.
acceptance: New tests distinguish ordinary no-hit behavior from
  transport or rate-limit failures without relying on live services.
acceptance: Protocol-level live smoke edits are deferred to T3 so T1
  remains deterministic.
validation: uv run python -m unittest -q tests.test_server tests.test_search_contract
status: done
log: (orchestrator) Deterministic contract pinning stays separate from
  live MCP smoke coverage.
log: (orchestrator) 2026-03-14 00:56 BJT started T1; assigned deterministic
  server-level search-contract coverage with writes limited to
  tests/test_server.py and creates limited to tests/test_search_contract.py.
log: (orchestrator) 2026-03-14 01:00 BJT completed T1; deterministic offline
  contract coverage now pins empty no-hit results and explicit transport or
  rate-limit failure propagation without touching live smoke tests.
files_changed: (orchestrator) /Users/oian/Codes/master/paper-search-mcp/tests/test_server.py
files_changed: (orchestrator) /Users/oian/Codes/master/paper-search-mcp/tests/test_search_contract.py

### T2: Make bioRxiv And medRxiv Real Search Tools

depends_on: [T1]
reads: [paper_search_mcp/academic_platforms/biorxiv.py,
  paper_search_mcp/academic_platforms/medrxiv.py,
  tests/test_biorxiv.py, tests/test_medrxiv.py,
  docs/project-specs/source-capability-matrix.md]
writes: [paper_search_mcp/academic_platforms/biorxiv.py,
  paper_search_mcp/academic_platforms/medrxiv.py,
  tests/test_biorxiv.py, tests/test_medrxiv.py]
creates: [tests/fixtures/biorxiv/search_response.json,
  tests/fixtures/biorxiv/search_empty.json,
  tests/fixtures/medrxiv/search_response.json,
  tests/fixtures/medrxiv/search_empty.json]
mutex: file:paper_search_mcp/academic_platforms/biorxiv.py
description: Replace category-only query handling with true query-driven
  search behavior while keeping the existing `search_biorxiv` and
  `search_medrxiv` tool names stable.
acceptance: A nonsense query returns an empty list instead of unrelated
  recent papers.
acceptance: Deterministic offline tests prove one topical query path and
  one empty-result path for each source.
acceptance: Deterministic tests prove the implementation no longer
  treats the incoming free-text query as a raw category name.
acceptance: Download and read helpers remain untouched apart from any
  helper refactors needed to support search.
validation: uv run python -m unittest -q tests.test_biorxiv tests.test_medrxiv tests.test_search_contract
status: done
log: (orchestrator) User selected the true-search direction for bioRxiv and medRxiv.
log: (orchestrator) 2026-03-14 01:00 BJT started T2; assigned true-search
  adapter rewrite plus offline fixtures/tests with writes limited to
  bioRxiv/medRxiv adapter and test files and creates limited to the declared
  fixture JSON files.
log: (orchestrator) 2026-03-14 01:05 BJT completed T2; bioRxiv and medRxiv
  search now perform bounded metadata fetch plus local query matching, and
  deterministic fixtures prove both topical hits and nonsense-query empty results.
files_changed: (orchestrator) /Users/oian/Codes/master/paper-search-mcp/paper_search_mcp/academic_platforms/biorxiv.py
files_changed: (orchestrator) /Users/oian/Codes/master/paper-search-mcp/paper_search_mcp/academic_platforms/medrxiv.py
files_changed: (orchestrator) /Users/oian/Codes/master/paper-search-mcp/tests/test_biorxiv.py
files_changed: (orchestrator) /Users/oian/Codes/master/paper-search-mcp/tests/test_medrxiv.py
files_changed: (orchestrator) /Users/oian/Codes/master/paper-search-mcp/tests/fixtures/biorxiv/search_response.json
files_changed: (orchestrator) /Users/oian/Codes/master/paper-search-mcp/tests/fixtures/biorxiv/search_empty.json
files_changed: (orchestrator) /Users/oian/Codes/master/paper-search-mcp/tests/fixtures/medrxiv/search_response.json
files_changed: (orchestrator) /Users/oian/Codes/master/paper-search-mcp/tests/fixtures/medrxiv/search_empty.json

### T3: Normalize Empty MCP Search Results

depends_on: [T1]
reads: [paper_search_mcp/server.py, tests/test_mcp_live.py, tests/test_search_contract.py]
writes: [paper_search_mcp/server.py, tests/test_mcp_live.py]
creates: []
mutex: file:paper_search_mcp/server.py
description: Fix the server-side search response path so zero-hit
  non-Semantic searches return protocol-valid empty results instead of
  `Unexpected response type`.
acceptance: `search_arxiv`, `search_pubmed`, `search_pmc`,
  `search_google_scholar`, `search_iacr`, and `search_crossref` all
  produce a valid zero-result response in the MCP smoke path.
acceptance: The chosen return strategy is compatible with current
  FastMCP structured-output guidance for list results or explicit empty
  `CallToolResult` responses.
acceptance: Search tools with positive hits still return the normalized
  paper shape expected by existing callers.
acceptance: Protocol-level live smoke now contains the regression that
  previously belonged to T1.
validation: PAPER_SEARCH_LIVE_TESTS=1 uv run python -m unittest -q tests.test_mcp_live
status: done
log: (orchestrator) Task constrained to non-Semantic search tools only.
log: (orchestrator) 2026-03-14 01:00 BJT started T3; assigned server-side
  empty-result normalization review with writes limited to
  paper_search_mcp/server.py and tests/test_mcp_live.py.
log: (orchestrator) 2026-03-14 01:07 BJT completed T3; live MCP smoke now
  accepts protocol-valid empty search results and passed on the integrated
  workspace with `PAPER_SEARCH_LIVE_TESTS=1 uv run python -m unittest -q tests.test_mcp_live`.
files_changed: (orchestrator) /Users/oian/Codes/master/paper-search-mcp/paper_search_mcp/server.py
files_changed: (orchestrator) /Users/oian/Codes/master/paper-search-mcp/tests/test_mcp_live.py

### T4: Tighten Non-Semantic Search Reliability

depends_on: [T2, T3]
reads: [paper_search_mcp/academic_platforms/google_scholar.py,
  paper_search_mcp/academic_platforms/iacr.py,
  paper_search_mcp/academic_platforms/crossref.py,
  tests/test_crossref.py, tests/test_google_scholar.py, tests/test_iacr.py]
writes: [paper_search_mcp/academic_platforms/google_scholar.py,
  paper_search_mcp/academic_platforms/iacr.py,
  paper_search_mcp/academic_platforms/crossref.py,
  tests/test_crossref.py, tests/test_google_scholar.py, tests/test_iacr.py]
creates: []
mutex: file:paper_search_mcp/academic_platforms/google_scholar.py
description: Apply any small non-Semantic adapter fixes needed to keep
  search behavior deterministic, bounded, and distinguishable from
  empty-result cases after the server-side fix lands.
acceptance: No non-Semantic search adapter relies on exceptions or
  transport quirks to represent an ordinary no-hit query.
acceptance: Adapter tests cover at least one no-hit or low-signal path
  for the sources touched in this task.
acceptance: This task does not change Semantic Scholar behavior,
  configuration, or tests.
acceptance: T4 does not expand into arXiv, PubMed, or PMC cleanup unless
  the plan is explicitly revised first.
validation: uv run python -m unittest -q tests.test_crossref
  tests.test_google_scholar tests.test_iacr tests.test_search_contract
status: done
log: (orchestrator) Reserved for bounded reliability fixes that appear
  after T2 and T3 land.
log: (orchestrator) 2026-03-14 01:08 BJT started T4; focused on bounded
  adapter reliability cleanup and no-hit coverage for CrossRef, Google Scholar,
  and IACR after T2/T3 integration.
log: (orchestrator) 2026-03-14 01:11 BJT completed T4; CrossRef date parsing,
  Google Scholar pagination, and IACR/CrossRef/Google Scholar no-hit coverage
  now keep empty results distinct from transport failures.
files_changed: (orchestrator) /Users/oian/Codes/master/paper-search-mcp/paper_search_mcp/academic_platforms/crossref.py
files_changed: (orchestrator) /Users/oian/Codes/master/paper-search-mcp/paper_search_mcp/academic_platforms/google_scholar.py
files_changed: (orchestrator) /Users/oian/Codes/master/paper-search-mcp/paper_search_mcp/academic_platforms/iacr.py
files_changed: (orchestrator) /Users/oian/Codes/master/paper-search-mcp/tests/test_crossref.py
files_changed: (orchestrator) /Users/oian/Codes/master/paper-search-mcp/tests/test_google_scholar.py
files_changed: (orchestrator) /Users/oian/Codes/master/paper-search-mcp/tests/test_iacr.py

### T5: Update Public Docs To Match Reality

depends_on: [T2, T3, T4]
reads: [README.md, docs/project-specs/mcp-tool-contract.md,
  docs/project-specs/source-capability-matrix.md, docs/PLANS.md]
writes: [README.md, docs/project-specs/mcp-tool-contract.md,
  docs/project-specs/source-capability-matrix.md, docs/PLANS.md]
creates: []
mutex: file:docs/PLANS.md
description: Refresh the durable docs so the maintained search surface,
  no-hit behavior, and Semantic exclusion are all explicit and
  accurate.
acceptance: The docs describe zero-hit search behavior without implying
  transport errors are expected.
acceptance: bioRxiv and medRxiv docs no longer imply category-only
  semantics if implementation changes make them true-search tools.
acceptance: Semantic Scholar remains documented as out of scope for
  this optimization pass, not silently changed.
validation: markdownlint README.md docs/PLANS.md
validation: markdownlint docs/project-specs/mcp-tool-contract.md
validation: markdownlint docs/project-specs/source-capability-matrix.md
status: done
log: (orchestrator) Doc sync must happen after implementation behavior is stable.
log: (orchestrator) 2026-03-14 01:13 BJT started T5; updating public contract
  docs and tracker language to reflect zero-hit behavior, bioRxiv/medRxiv
  query semantics, and Semantic Scholar exclusion.
log: (orchestrator) 2026-03-14 01:14 BJT completed T5; README, tool-contract,
  and capability-matrix docs now describe zero-hit behavior, bounded
  bioRxiv/medRxiv query matching, and unchanged Semantic Scholar scope.
files_changed: (orchestrator) /Users/oian/Codes/master/paper-search-mcp/README.md
files_changed: (orchestrator) /Users/oian/Codes/master/paper-search-mcp/docs/project-specs/mcp-tool-contract.md
files_changed: (orchestrator) /Users/oian/Codes/master/paper-search-mcp/docs/project-specs/source-capability-matrix.md
files_changed: (orchestrator) /Users/oian/Codes/master/paper-search-mcp/docs/PLANS.md

### T6: Validate, Record Evidence, And Close Out

depends_on: [T5]
reads: [docs/PLANS.md, docs/exec-plans/completed/2026-03-14_0044_BJT_search-tool-optimization-nonsemantic.md]
writes: [docs/PLANS.md, docs/exec-plans/completed/2026-03-14_0044_BJT_search-tool-optimization-nonsemantic.md]
creates: []
mutex: file:docs/PLANS.md
description: Run the agreed validation set, record evidence in the
  tracker and ExecPlan, and close any review notes without expanding
  scope into Semantic Scholar.
acceptance: Offline verification passes for touched server, adapter,
  and test modules.
acceptance: Live MCP verification is recorded for the non-Semantic
  search surface, with skips or failures explained precisely.
acceptance: The tracker entry contains concrete evidence and next
  steps, including any intentionally deferred work.
validation: uv run python -m compileall paper_search_mcp tests
validation: uv run python -m unittest -q tests.test_server
validation: uv run python -m unittest -q tests.test_search_contract
validation: uv run python -m unittest -q tests.test_arxiv
validation: uv run python -m unittest -q tests.test_pubmed
validation: uv run python -m unittest -q tests.test_pmc
validation: uv run python -m unittest -q tests.test_biorxiv tests.test_medrxiv
validation: uv run python -m unittest -q tests.test_crossref
  tests.test_google_scholar tests.test_iacr
validation: PAPER_SEARCH_LIVE_TESTS=1 uv run python -m unittest -q tests.test_mcp_live
status: done
log: (orchestrator) Final validation task owned by the orchestrator.
log: (orchestrator) 2026-03-14 01:14 BJT completed T6; offline validation,
  post-T4 live MCP smoke, and markdownlint all passed and the tracker was
  updated with concrete evidence and no remaining in-scope work.
files_changed: (orchestrator) /Users/oian/Codes/master/paper-search-mcp/docs/PLANS.md
files_changed: (orchestrator) /Users/oian/Codes/master/paper-search-mcp/docs/exec-plans/completed/2026-03-14_0044_BJT_search-tool-optimization-nonsemantic.md

## Plan of Work

Start by pinning the deterministic contract with offline tests that
express what a valid zero-hit response looks like for search tools.
Then implement the behavioral correction in two parallel tracks: one
for the bioRxiv and medRxiv adapters so their search tools behave like
actual search, and one for the server-side result path so empty result
sets do not explode at the MCP boundary. After that, apply only the
bounded adapter tune-ups needed for CrossRef, Google Scholar, and IACR,
then update the public docs and rerun the offline and live validation
matrix. Leave Semantic Scholar untouched in code, tests, and docs
beyond explicit scope notes.

## Concrete Steps

1. From `[repo-root]`, run:

       uv run python -m unittest -q tests.test_server

   Expect:

       Existing server registration tests pass.

2. From `[repo-root]`, run:

       PAPER_SEARCH_LIVE_TESTS=1 uv run python -m unittest -q tests.test_mcp_live

   Expect:

       Current live MCP smoke reproduces the non-Semantic search failures or
       skips only when upstream services are unavailable.

3. From `[repo-root]`, after T1 lands, run:

       uv run python -m unittest -q tests.test_search_contract

   Expect:

       A focused regression suite expresses the intended zero-hit contract.

4. From `[repo-root]`, after T2 and T3 land, run:

       uv run python -m unittest -q tests.test_arxiv
       uv run python -m unittest -q tests.test_pubmed
       uv run python -m unittest -q tests.test_pmc
       uv run python -m unittest -q tests.test_biorxiv tests.test_medrxiv
       uv run python -m unittest -q tests.test_server tests.test_search_contract

   Expect:

       Adapter behavior and server-level contract checks pass together,
       with offline proof for the touched query semantics.

5. From `[repo-root]`, at closeout, run:

       uv run python -m compileall paper_search_mcp tests
       uv run python -m unittest -q tests.test_server
       uv run python -m unittest -q tests.test_search_contract
       uv run python -m unittest -q tests.test_arxiv
       uv run python -m unittest -q tests.test_pubmed
       uv run python -m unittest -q tests.test_pmc
       uv run python -m unittest -q tests.test_biorxiv tests.test_medrxiv
       uv run python -m unittest -q tests.test_crossref
       uv run python -m unittest -q tests.test_google_scholar tests.test_iacr
       PAPER_SEARCH_LIVE_TESTS=1 uv run python -m unittest -q tests.test_mcp_live
       markdownlint README.md docs/PLANS.md
       markdownlint docs/project-specs/mcp-tool-contract.md
       markdownlint docs/project-specs/source-capability-matrix.md
       markdownlint docs/exec-plans/completed/2026-03-14_0044_BJT_search-tool-optimization-nonsemantic.md

   Expect:

       Offline checks pass, live MCP results are recorded with source-specific
       skips only where justified, and modified Markdown passes lint.

## Completion Packet (Workers)

**Status:** `[COMPLETED | FAILED | BLOCKED]`

**Files modified/created:**

- [path]

**Acceptance criteria coverage:**

- [criterion] -> [satisfied by]

**Validation performed:**

- [command] -> [result]

**Open risks / blockers:**

- [notes]

**Suggested follow-ups:**

- [optional next task or integration note]

## Validation and Acceptance

Exercise both the offline unit surface and the opt-in live MCP surface. A
successful outcome proves three things: non-Semantic search tools no longer
throw a protocol error on no-hit queries, bioRxiv and medRxiv now behave like
search tools instead of recent category feeds, and the public docs/tests match
those behaviors. Semantic Scholar should remain exactly as before, apart from
any explicit note that it was excluded from this work.

## Idempotence and Recovery

The test commands are safe to rerun. Live probes may be rate-limited or blocked
by third parties, so treat source-specific skips as environmental evidence, not
necessarily regressions. If a server-side return-shape change causes tool-schema
drift or breaks the live smoke path, revert to the last passing contract test
and choose the smallest response-shape fix that satisfies the MCP SDK guidance.
If bioRxiv or medRxiv true-search work proves infeasible against their current
upstream endpoints, stop before shipping and convert the plan into a narrower
docs-plus-explicit-parameter follow-up rather than silently keeping misleading
search behavior.

## Revision Notes

- 2026-03-14 / Codex — Created this plan after live MCP probes identified
  non-Semantic search contract failures and misleading bioRxiv/medRxiv
  behavior.
