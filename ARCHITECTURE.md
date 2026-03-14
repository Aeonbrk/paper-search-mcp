# Architecture

`paper-search-mcp` is a small Python package that exposes paper-search tools
through FastMCP. The repo is intentionally network-first: most useful behavior
depends on live upstream services rather than local data.

## Read Order

1. `README.md` for user entrypoints and setup.
2. `docs/PROJECT_SENSE.md` for repo intent and boundaries.
3. `docs/project-specs/mcp-tool-contract.md` for the public MCP surface.
4. `docs/project-specs/source-capability-matrix.md` for source-specific limits.
5. `codemap/reference/CODEBASE_MAP.md` for code navigation.

## System Shape

### Runtime entrypoint

- `paper_search_mcp/server.py` creates the FastMCP server.
- The server exposes one tool family per paper source.
- Tool names are source-scoped and currently stable.
- Search/download/read wrappers now go through centralized dispatch helpers with
  a bounded concurrency semaphore.
- MCP wrapper paths force canonical writes under `docs/downloads/`.

### Adapter layer

- `paper_search_mcp/academic_platforms/` contains one adapter module per source.
- Shared HTTP transport behavior is centralized in `paper_search_mcp/_http.py`.
- Shared streamed PDF download and extraction behavior is centralized in
  `paper_search_mcp/_pdf.py`.
- bioRxiv and medRxiv now share `academic_platforms/_preprint_base.py`.
- Adapter quality still varies by upstream API stability and site behavior.

### Normalized paper model

- `paper_search_mcp/paper.py` defines the shared `Paper` dataclass.
- MCP tools serialize results through `Paper.to_dict()`.
- The serialized shape is a compatibility surface for downstream clients.

### Validation layer

- `tests/` now includes deterministic offline regression coverage for transport
  policy, adapter contracts, and performance smoke thresholds.
- Optional live checks remain opt-in and scoped to targeted adapters.
- Offline checks (`compileall`, contract tests, and smoke tests) are the
  default acceptance gate.

## Design Constraints

- The repo optimizes for breadth of source support over perfect uniformity.
- Some sources are metadata-only, some permit PDF download, and some can also
  extract text from downloaded PDFs.
- No-hit search behavior must remain deterministic (`[]`) and separate from
  transport/runtime failures.
- Unsupported capabilities must stay explicit instead of silently degrading.
- External services may rate-limit, change HTML structure, or block scraping.
- The repo should document these differences instead of hiding them.

## Negative Space

The repo does not currently include:

- a frontend or web app,
- persistent storage,
- generated API documentation,
- repo-local control-plane orchestration,
- fully deterministic offline fixtures for every single adapter path.

Those omissions are part of the current architecture, not missing polish.
