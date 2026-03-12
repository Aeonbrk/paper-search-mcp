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
- Adapts source searchers into serialized MCP responses

### `paper_search_mcp/paper.py`

- Defines the normalized `Paper` dataclass
- Owns the serialized response contract used by MCP tools

### `paper_search_mcp/academic_platforms/`

- `arxiv.py` — arXiv adapter
- `pubmed.py` — PubMed metadata adapter
- `biorxiv.py` — bioRxiv adapter
- `medrxiv.py` — medRxiv adapter
- `google_scholar.py` — Google Scholar scraping adapter
- `iacr.py` — IACR search, detail, download, and read adapter
- `semantic.py` — Semantic Scholar API adapter
- `crossref.py` — CrossRef metadata adapter
- `sci_hub.py` — legacy optional helper, not on the default MCP surface

## Tests

- `tests/test_server.py` — basic server-level integration behavior
- `tests/test_*.py` — mostly live-network adapter checks
- Test suite currently mixes smoke and integration concerns

## Durable docs

- `docs/project-specs/` — public behavior and source matrix
- `docs/playbooks/` — validation and release workflows
- `docs/exec-plans/` — durable implementation tracking
- `docs/references/` — upstream and service references

## First places to edit

- Add or change tool behavior: `paper_search_mcp/server.py`
- Add or change a source: `paper_search_mcp/academic_platforms/`
- Change the response schema: `paper_search_mcp/paper.py`
- Update capability docs after behavior changes:
  `docs/project-specs/source-capability-matrix.md`
