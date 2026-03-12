# Bug / Security / Performance Audit (2026-03-12)

This document captures the most actionable security, runtime, and performance
risks observed in the repository at the time of audit. It is intended to feed
the follow-up implementation tasks in the active ExecPlan while preserving the
public MCP tool surface.

## Audit Metadata

- Date (BJT): 2026-03-12
- Repo revision (git): `cf2697fd04a7b7c1ced0e382ab84f0c214614f83`
- Scope sampled:
  - `paper_search_mcp/server.py`
  - `paper_search_mcp/academic_platforms/*.py`
  - `tests/*.py`
  - `docs/SECURITY.md`, `docs/RELIABILITY.md`

## Public MCP Tool Surface (Snapshot)

Tool names observed from `paper_search_mcp.server:mcp.list_tools()`:

```text
search_arxiv
search_pubmed
search_biorxiv
search_medrxiv
search_google_scholar
search_iacr
download_arxiv
download_pubmed
download_biorxiv
download_medrxiv
download_iacr
read_arxiv_paper
read_pubmed_paper
read_biorxiv_paper
read_medrxiv_paper
read_iacr_paper
search_semantic
download_semantic
read_semantic_paper
search_crossref
get_crossref_paper_by_doi
download_crossref
read_crossref_paper
```

## Executive Summary (Risk-Graded)

Severity legend: **Critical** (exploitable / data loss), **High** (likely
operational failure), **Medium** (quality debt), **Low** (cleanup).

- **Critical**: Untrusted path handling for downloads can write outside an
  intended directory when `save_path` or identifiers are attacker-controlled.
- **High**: Async MCP tools call synchronous network and sleep functions,
  blocking the event loop and reducing responsiveness under concurrent tool
  calls.
- **High**: Several network requests have no timeout and/or do not fail
  explicitly on non-2xx responses, increasing hang / silent-corruption risk.
- **Medium**: Tests default to live-network + large downloads; this is too heavy
  for a default verification gate and introduces flakiness.
- **Medium**: Retry/backoff uses `time.sleep()` (CrossRef, Semantic Scholar),
  which is fine only if the call path is moved off the event loop (thread) or
  replaced with `asyncio.sleep()`.

## Findings

### 1) Path traversal / arbitrary write on download paths (Critical)

#### Why it matters (Finding 1)

Download helpers accept `save_path` and identifier strings (`paper_id`, `doi`,
etc.) from MCP tool parameters. Current implementations build output paths with
string concatenation (for example `f"{save_path}/{paper_id}.pdf"`). If an
attacker can influence these values, they can attempt to write files outside of
the intended download directory (path traversal) or clobber existing files.

#### Affected scope (examples, Finding 1)

- `paper_search_mcp/server.py`: tool functions expose `save_path` directly.
- `paper_search_mcp/academic_platforms/arxiv.py`: `output_file =
  f"{save_path}/{paper_id}.pdf"` without sanitization or directory enforcement.
- `paper_search_mcp/academic_platforms/iacr.py`: builds `filename =
  f"{save_path}/iacr_{paper_id.replace('/', '_')}.pdf"`; `save_path` still
  unbounded.
- `paper_search_mcp/academic_platforms/biorxiv.py`,
  `paper_search_mcp/academic_platforms/medrxiv.py`: replace `/` in DOI but still
  trust `save_path`.
- (Optional/sensitive) `paper_search_mcp/academic_platforms/sci_hub.py` writes
  under a configurable `output_dir` defaulting to `./downloads`.

#### Suggested repair (Finding 1)

- Centralize path handling in one helper (for example `_paths.py`) that:
  - sets a single default download root (per plan: `docs/downloads/`);
  - resolves the requested path (`Path(...).resolve()`) and rejects any target
    not under the allowed root;
  - normalizes filenames (rejects path separators; replaces unsafe characters);
  - creates the directory before writing.
- Treat `save_path` as a *logical* name (or ignore it entirely) unless there is
  a strong reason to accept arbitrary filesystem paths.

#### Suggested validation (Finding 1)

- Add an offline unit test that tries identifiers like `../x`, absolute paths,
  and Windows drive patterns and asserts the final path stays under
  `docs/downloads/`.
- Confirm `download_*` does not create directories outside `docs/downloads/`.

### 2) TLS verification disabled for Sci-Hub fetcher (High)

#### Why it matters (Finding 2)

`verify=False` disables TLS verification and enables trivial MITM attacks.
Even though Sci-Hub is not part of the default supported surface, the code
exists and can be used by developers.

#### Affected scope (Finding 2)

- `paper_search_mcp/academic_platforms/sci_hub.py`: `self.session.get(...,
  verify=False, ...)` in `_get_direct_url()` and `download_pdf()`.

#### Suggested repair (Finding 2)

- Default to `verify=True`. If skipping TLS verification is required for a
  specific environment, make it an explicit opt-in via an environment variable
  (and document the risk).

#### Suggested validation (Finding 2)

- Grep/CI guard: assert `verify=False` does not appear in the Sci-Hub helper by
  default.

### 3) Event-loop blocking due to synchronous I/O in async tools (High)

#### Why it matters (Finding 3)

FastMCP tool functions are declared `async`, but most underlying adapter calls
use synchronous `requests` and even `time.sleep()`. When called directly on the
event loop, this blocks other tool calls and can make the server appear hung.

#### Affected scope (examples, Finding 3)

- `paper_search_mcp/server.py`:
  - `async_search()` creates an `httpx.AsyncClient()` but performs synchronous
    `searcher.search(...)` inside the `async` context.
  - Many tool functions wrap synchronous work in `async` without moving it off
    the event loop.
- `paper_search_mcp/academic_platforms/google_scholar.py`: `time.sleep(...)`
  for random delays.
- `paper_search_mcp/academic_platforms/crossref.py`: `time.sleep(2)` on 429.
- `paper_search_mcp/academic_platforms/semantic.py`: exponential backoff uses
  `time.sleep(...)` during 429 retries.

#### Suggested repair (Finding 3)

- Use `asyncio.to_thread(...)` (or equivalent) in the server wrapper so adapter
  code runs in threads, not on the event loop.
- Add a concurrency limit (semaphore) so a burst of tool calls does not spawn an
  unbounded number of threads / outgoing requests.
- Remove unused `httpx.AsyncClient()` creation where it is not used.

#### Suggested validation (Finding 3)

- Add a cheap offline check that `paper_search_mcp/server.py` does not contain
  `time.sleep`.
- (Optional) Add a concurrency test that runs multiple tool calls and asserts
  they complete without long serial blocking.

### 4) Missing timeouts and weak error handling on network calls (High)

#### Why it matters (Finding 4)

Without explicit timeouts, requests can hang indefinitely. Without
`raise_for_status()` (or equivalent status checks), errors can be silently
treated as successful responses and later parsed or written to disk as garbage.

#### Affected scope (examples, Finding 4)

- `paper_search_mcp/academic_platforms/arxiv.py`:
  - `requests.get(...)` without timeout for API query and PDF download.
  - writes `response.content` to a `.pdf` path without checking status code.
- `paper_search_mcp/academic_platforms/pubmed.py`:
  - `requests.get(...)` without timeout for both search and fetch.
  - XML parsing assumes response is valid XML; failure modes are opaque.
- `paper_search_mcp/academic_platforms/iacr.py`:
  - `self.session.get(...)` without timeout in `search()` and `download_pdf()`.
- `paper_search_mcp/academic_platforms/semantic.py`:
  - `self.session.get(...)` without timeout in `request_api()`.
  - return type is inconsistent (`dict` in signature but often a `Response`).

#### Suggested repair (Finding 4)

- Use explicit timeouts for all requests (connect/read), ideally as a shared
  constant per adapter.
- Standardize on `raise_for_status()` (or equivalent) and return an explicit
  error or empty result on non-2xx.
- Make `SemanticSearcher.request_api()` return a single consistent type:
  either a parsed dict or a `requests.Response` (with clear caller handling).

#### Suggested validation (Finding 4)

- Offline: `python -m compileall` on changed modules.
- Targeted: run the single-adapter live tests only when needed
  (`PAPER_SEARCH_LIVE_TESTS=1 ...`).

### 5) Heavy / flaky default tests (Medium)

#### Why it matters (Finding 5)

Default test discovery should not download many PDFs or depend on scraping
sources. Current defaults pull network data and write to `./downloads`, which is
too heavy for fast verification and increases flake rate.

#### Affected scope (Finding 5)

- `tests/test_server.py`: downloads 10 arXiv PDFs in the default test suite.
- `tests/test.pubmed.py`: filename contains a dot; non-standard naming can
  confuse test discovery patterns.
- Most `tests/test_*.py` appear to be live-network integrations.

#### Suggested repair (Finding 5)

- Split tests into:
  - default offline smoke tests (no network, no downloads);
  - opt-in live tests guarded by `PAPER_SEARCH_LIVE_TESTS=1`.
- Add a small offline test for path normalization logic (see Finding #1).
- Rename `tests/test.pubmed.py` to `tests/test_pubmed.py` for consistency.

#### Suggested validation (Finding 5)

- `uv run python -m unittest discover -q` should not hit the network by default.
- `PAPER_SEARCH_LIVE_TESTS=1 uv run python -m unittest -q tests.test_arxiv`
  should still exercise the live path for targeted changes.

## Notes / Non-Findings (Intentional or Acceptable)

- Source capability is intentionally uneven (see
  `docs/project-specs/source-capability-matrix.md`). The goal is stability and
  honesty about source limits, not perfect uniformity.
- Sci-Hub is optional and sensitive; improvements there should keep it off the
  default advertised surface.
