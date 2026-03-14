# Optimize review follow-ups (HTTP backoff + preprint transport)

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

Turn the last review notes into shippable fixes:

- Make `RetryPolicy.backoff_factor` actually affect urllib3 exponential backoff
  (it was previously unused).
- Decide and make explicit how preprint adapters handle proxy environment
  settings (current behavior sets `session.proxies`, but environment proxies
  may still apply unless we explicitly override per request).
- Remove small determinism footguns (capture `now` once for date windows).
- Verify the changes under the repo’s intended toolchain (`uv`, offline tests,
  markdownlint for docs).

Done looks like: targeted unit tests pass, offline test suite remains green,
and docs (if touched) remain markdownlint-clean.

## Progress

- [x] (2026-03-14 16:38 BJT) Confirm scope + proxy policy decision.
- [x] (2026-03-14 16:38 BJT) Implement code + tests for the chosen policy.
- [x] (2026-03-14 16:38 BJT) Run validation and record evidence.
- [x] (2026-03-14 16:38 BJT) Close review notes and summarize outcomes.

## Surprises & Discoveries

- Observation: repo tests are `unittest`-based (no `pytest` usage).
  Evidence: `rg -n "pytest" tests` returns none.
- Observation: requests retry/backoff is implemented via
  `HTTPAdapter(max_retries=Retry(...))`.
  Evidence: requests + urllib3 docs (Context7).

## Decision Log

- Decision: implement configurable backoff growth by subclassing urllib3 `Retry`
  and overriding `get_backoff_time()` + `new()` to preserve the custom factor.
  Rationale: keep urllib3 semantics (redirect rules, jitter support) while
  wiring `RetryPolicy.backoff_factor` into the backoff curve.
  Date/Author: 2026-03-14 / orchestrator
- Decision: Preprint sources respect environment proxies by default. Set
  `PAPER_SEARCH_DISABLE_PROXIES=1` to disable proxies for preprint calls by
  passing `proxies={"http": None, "https": None}` per request.
  Rationale: matches requests defaults while providing an explicit escape hatch
  for environments with misconfigured proxies.
  Date/Author: 2026-03-14 / orchestrator

## Outcomes & Retrospective

Shipped:

- Wired `RetryPolicy.backoff_factor` into urllib3 retry backoff growth while
  keeping urllib3 `Retry` semantics (including redirect history and jitter).
- Preprint sources now respect environment proxies by default. Set
  `PAPER_SEARCH_DISABLE_PROXIES=1` to disable proxies for preprint HTTP calls
  via request-level `proxies={"http": None, "https": None}` overrides.
- Removed a date-window determinism footgun by capturing `now` once when
  computing preprint search windows.
- Updated public docs to reflect the proxy toggle and the separate retry
  backoff knobs.

Notes:

- The offline suite still emits some expected warnings when upstream network
  paths are unavailable (and a feedparser deprecation warning), but the suite
  remains green with skips.

## Context and Orientation

Relevant implementation surfaces:

- `paper_search_mcp/_http.py`: shared requests `Session` construction + urllib3
  retry configuration (via `HTTPAdapter`).
- `tests/test_http.py`: transport regression tests; add coverage for backoff
  growth factor wiring.
- `paper_search_mcp/academic_platforms/_preprint_base.py`: shared bioRxiv /
  medRxiv base; currently sets `session.proxies` (but may still honor env
  proxies) and uses `datetime.now()` twice to compute a search window.
- `tests/test_preprint_base.py`: offline base-class tests for shared preprint
  behavior.

External behavior / docs references used for correctness:

- urllib3 `Retry` backoff: `backoff_factor * (2 ** n)` with optional jitter,
  capped by `backoff_max` (Context7: urllib3 util docs).
- requests `HTTPAdapter(max_retries=Retry(...))` mounting uses longest-prefix
  match; mounting updates session adapter config for that prefix (Context7:
  requests advanced docs).

## Proxy Policy Options (T1)

Pick one default behavior for preprint HTTP calls:

- Option A (selected): Respect environment proxies by default. Add
  `PAPER_SEARCH_DISABLE_PROXIES=1` to disable proxies for preprint calls by
  passing `proxies={"http": None, "https": None}` per request.
- Option B: Disable proxies by default for preprint calls (pass
  `proxies={"http": None, "https": None}` per request). Add
  `PAPER_SEARCH_ENABLE_PROXIES=1` to respect environment proxies again.
- Option C: Disable proxies unconditionally (no override). Avoid unless there
  is a strong operational reason.

Note: setting `session.proxies` alone does not prevent `requests` from
populating proxies from environment variables; use request-level `proxies=...`
or `session.trust_env` when the goal is to control env proxy behavior.

## Task Graph (Dependencies)

### T1: Decide preprint proxy policy (required input)

depends_on: []
reads: [paper_search_mcp/academic_platforms/_preprint_base.py]
writes: []
creates: []
mutex: file:paper_search_mcp/academic_platforms/_preprint_base.py
description: Pick one default proxy policy for the shared preprint base and
  record it as a Decision Log entry; this makes T3 unambiguous.
acceptance: Decision log records Option A (respect env proxies by default) and
  `PAPER_SEARCH_DISABLE_PROXIES=1` as the escape hatch.
validation: n/a
status: done
log: (orchestrator) created task packet.
log: (2026-03-14 16:51 BJT) User selected Option A (respect env proxies) with
  `PAPER_SEARCH_DISABLE_PROXIES=1` escape hatch.
files_changed: (orchestrator) none.

### T2: Wire `RetryPolicy.backoff_factor` into urllib3 backoff growth

depends_on: []
reads: [paper_search_mcp/_http.py, tests/test_http.py]
writes: [paper_search_mcp/_http.py, tests/test_http.py]
creates: []
mutex: file:paper_search_mcp/_http.py
description: Make `RetryPolicy.backoff_factor` control exponential growth while
  keeping urllib3 Retry semantics; add deterministic unit coverage.
acceptance: `RetryPolicy(backoff_base_seconds=1, backoff_factor=3)` yields
  backoff times 0, 3, 9 for the first three consecutive errors (no jitter).
acceptance: Existing HTTP transport tests still pass.
validation: `uv run python -m unittest -q tests.test_http`
status: done
log: (orchestrator) created task packet.
log: (2026-03-14 17:00 BJT) Dispatched to worker Mendel (019ceb93-ee48-73e0-bd34-1f997b31fb9f).
log: (2026-03-14 17:06 BJT) Unittest `tests.test_http` -> OK.
files_changed: paper_search_mcp/_http.py
files_changed: tests/test_http.py

### T3: Implement preprint proxy policy + capture `now` once

depends_on: [T1]
reads: [paper_search_mcp/academic_platforms/_preprint_base.py,
  tests/test_preprint_base.py]
writes: [paper_search_mcp/academic_platforms/_preprint_base.py,
  tests/test_preprint_base.py]
creates: []
mutex: file:paper_search_mcp/academic_platforms/_preprint_base.py
description: Apply the selected proxy policy in `PreprintSearcherBase` and make
  date-window computation deterministic by capturing `now` once.
acceptance: `search()` uses a single captured `now` for `start_date` and
  `end_date` to avoid midnight edge cases.
acceptance: By default, preprint HTTP calls respect environment proxies (no
  explicit `proxies` override is passed).
acceptance: When `PAPER_SEARCH_DISABLE_PROXIES=1`, preprint HTTP calls pass
  `proxies={"http": None, "https": None}` to disable proxies for those calls.
acceptance: The proxy toggle behavior is covered by an offline unit test.
validation: `uv run python -m unittest -q tests.test_preprint_base`
status: done
log: (orchestrator) created task packet.
log: (2026-03-14 17:00 BJT) Dispatched to worker Maxwell (019ceb94-374b-7313-8386-f609ded30da8).
log: (2026-03-14 17:06 BJT) Unittest `tests.test_preprint_base` -> OK.
files_changed: paper_search_mcp/academic_platforms/_preprint_base.py
files_changed: tests/test_preprint_base.py

### T4: Align docs with shipped proxy + backoff behavior

depends_on: [T2, T3]
reads: [README.md, docs/RELIABILITY.md,
  docs/project-specs/adapter-error-handling-policy.md]
writes: [README.md, docs/RELIABILITY.md]
creates: []
mutex: docs:public-docs
description: Ensure docs reflect the selected preprint proxy policy (including
  the override knob) and clarify the two backoff knobs so future reviewers do
  not misread them.
acceptance: Docs describe preprint proxy behavior without implying uniform
  proxy behavior across all sources.
acceptance: Any modified markdown files are markdownlint-clean.
validation: `markdownlint README.md docs/RELIABILITY.md`
status: done
log: (orchestrator) created task packet.
log: (2026-03-14 17:06 BJT) Orchestrator started doc alignment edits.
log: (2026-03-14 17:07 BJT) `markdownlint README.md docs/RELIABILITY.md` -> OK.
files_changed: README.md
files_changed: docs/RELIABILITY.md

### T5: Validate offline suite + record evidence; close out plan

depends_on: [T2, T3, T4]
reads: [pyproject.toml, uv.lock, docs/PLANS.md,
  docs/exec-plans/active/2026-03-14_1636_BJT_review-results-optimization.md]
writes: [docs/PLANS.md,
  docs/exec-plans/active/2026-03-14_1636_BJT_review-results-optimization.md]
creates: [
  docs/exec-plans/completed/2026-03-14_1636_BJT_review-results-optimization.md
]
mutex: file:docs/PLANS.md
description: Run the repo’s standard offline validations (uv sync, compileall,
  unittest discover) and capture evidence in `docs/PLANS.md`; then move this
  ExecPlan to `completed/`.
acceptance: `PAPER_SEARCH_LIVE_TESTS=0 uv run python -m unittest discover -q`
  passes (skips allowed) and evidence is recorded.
acceptance: Working tree is clean (no unstaged changes) after closeout.
validation: `uv sync --locked`
validation: `uv run python -m compileall paper_search_mcp tests`
validation: `PAPER_SEARCH_LIVE_TESTS=0 uv run python -m unittest discover -q`
status: done
log: (orchestrator) created task packet.
log: (2026-03-14 17:07 BJT) Orchestrator started offline validation + closeout.
log: (2026-03-14 17:08 BJT) `uv sync --locked` -> OK.
log: (2026-03-14 17:08 BJT) `compileall paper_search_mcp tests` -> OK.
log: (2026-03-14 17:08 BJT) `unittest discover` (offline) -> OK (skipped=26).
log: (2026-03-14 17:08 BJT) Updated `docs/PLANS.md`; moved ExecPlan.
files_changed: docs/PLANS.md
files_changed: docs/exec-plans/completed/2026-03-14_1636_BJT_review-results-optimization.md

## Plan of Work

1. Complete T1 (proxy policy decision) before touching preprint code.
2. Apply T2 by implementing a small urllib3 `Retry` subclass that:
   - preserves urllib3 history/redirect semantics,
   - uses `RetryPolicy.backoff_base_seconds` as the base delay, and
   - uses `RetryPolicy.backoff_factor` as the exponential growth factor,
   - while keeping jitter support intact (when configured).
3. Apply T3 by implementing the chosen proxy behavior and capturing `now` once.
4. Apply T4 to keep docs aligned with shipped behavior.
5. Run T5 validations and record evidence.

## Concrete Steps

1. From `[repo-root]`, ensure deps are installed:

       uv sync --locked

2. Run targeted unit tests:

       uv run python -m unittest -q tests.test_http tests.test_preprint_base

3. Run offline suite:

       PAPER_SEARCH_LIVE_TESTS=0 uv run python -m unittest discover -q

4. If docs changed, lint:

       markdownlint README.md docs/RELIABILITY.md

## Completion Packet (Workers)

**Status:** `[COMPLETED | FAILED | BLOCKED]`

**Files modified/created:**

- path/to/file.ext

**Acceptance criteria coverage:**

- criterion -> evidence

**Validation performed:**

- command -> result

**Open risks / blockers:**

- notes

**Suggested follow-ups:**

- optional next task or integration note

## Validation and Acceptance

Primary success criteria:

- Transport tests demonstrate the intended backoff curve with the configured
  growth factor.
- Preprint base behavior is explicit, deterministic, and does not regress the
  offline test suite.
- Documentation matches behavior and stays markdownlint-compatible.

## Idempotence and Recovery

- Safe to rerun: `uv sync --locked`, `compileall`, `unittest discover`, and
  markdownlint.
- If a partial download/test artifact is created during future live tests,
  recover by deleting `docs/downloads/` contents (do not commit runtime
  artifacts) and rerunning offline tests.

## Revision Notes

- 2026-03-14 / orchestrator — Created this plan to convert review notes into a
  bounded, parallelizable follow-up.
