# Codebase Map

## Root surfaces

- `README.md` — user entrypoint
- `AGENTS.md` — repo-local invariants and read order
- `ARCHITECTURE.md` — system shape and negative space
- `pyproject.toml` — packaging metadata and dependencies
- `smithery.yaml` — Smithery start command
- `.github/workflows/publish.yml` — release automation

## Runtime package

### `paper_search_mcp/server.py`

- Creates the FastMCP server named `paper_search_server`
- Registers the public MCP tools
- Uses centralized search/download/read dispatch wrappers
- Enforces canonical MCP download/read routing under `docs/downloads/`

### Shared utilities

- `paper_search_mcp/_http.py` — shared session, retry, pooling, and transport
  error helpers
- `paper_search_mcp/_pdf.py` — shared streamed PDF download and text extraction
  helpers
- `paper_search_mcp/_paths.py` — canonical safe path routing for downloads

### `paper_search_mcp/paper.py`

- Defines the normalized `Paper` dataclass
- Owns the serialized response contract used by MCP tools

### `paper_search_mcp/academic_platforms/`

- `arxiv.py` — arXiv adapter
- `pubmed.py` — PubMed metadata adapter
- `biorxiv.py` — bioRxiv adapter
- `medrxiv.py` — medRxiv adapter
- `_preprint_base.py` — shared base for bioRxiv/medRxiv behavior
- `google_scholar.py` — Google Scholar scraping adapter
- `iacr.py` — IACR search, detail, download, and read adapter
- `semantic.py` — Semantic Scholar API adapter
- `crossref.py` — CrossRef metadata adapter
- `sci_hub.py` — legacy optional helper, not on the default MCP surface

## Tests

- `tests/test_server.py` — server dispatch and unsupported fallback behavior
- `tests/test_search_contract.py` — no-hit and failure-propagation contracts
- `tests/test_http.py` and `tests/test_http_resilience.py` — shared transport
  config and retry behavior
- `tests/test_pdf_utils.py` — shared streamed PDF/download extraction behavior
- `tests/test_performance_smoke.py` — offline latency smoke thresholds
- `tests/test_preprint_base.py` — shared bioRxiv/medRxiv base behavior
- `tests/test_*.py` — source-level unit and optional live checks

## Durable docs

- `docs/project-specs/` — public behavior, source matrix, reliability policy,
  and perf/stability targets
- `docs/playbooks/` — validation and release workflows
- `docs/exec-plans/` — durable implementation tracking
- `docs/references/` — upstream and service references

## First places to edit

- Add or change tool behavior: `paper_search_mcp/server.py`
- Add or change shared transport/PDF behavior:
  `paper_search_mcp/_http.py` and `paper_search_mcp/_pdf.py`
- Add or change a source: `paper_search_mcp/academic_platforms/`
- Change the response schema: `paper_search_mcp/paper.py`
- Update capability docs after behavior changes:
  `docs/project-specs/source-capability-matrix.md`
