# Paper Search MCP

`paper-search-mcp` is a Python FastMCP server for searching academic papers
across multiple sources and, when the source permits it, downloading PDFs or
extracting text.

![PyPI](https://img.shields.io/pypi/v/paper-search-mcp.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
[![smithery badge](https://smithery.ai/badge/@openags/paper-search-mcp)](https://smithery.ai/server/@openags/paper-search-mcp)

## What this repo is for

- Expose paper-search tools through the Model Context Protocol.
- Normalize source results through a shared `Paper` model.
- Keep source-specific capabilities explicit instead of pretending every source
  works the same way.
- Keep error handling deterministic and source-appropriate across adapters.

For the maintained repo shape and capability boundaries, start with:

- `ARCHITECTURE.md`
- `docs/PROJECT_SENSE.md`
- `docs/project-specs/mcp-tool-contract.md`
- `docs/project-specs/source-capability-matrix.md`
- `docs/TODO.md`

## Supported sources

The repo currently ships search support for:

- arXiv
- PubMed
- PMC
- bioRxiv
- medRxiv
- Google Scholar
- IACR ePrint Archive
- Semantic Scholar
- CrossRef

Support is intentionally uneven:

- some sources are metadata-only,
- PMC currently ships as metadata search plus placeholder download/read tools,
- some support PDF download,
- some also support text extraction from downloaded PDFs,
- scraping-based sources are more fragile than API-backed sources.
- ordinary no-hit search queries return empty results instead of transport
  errors.
- supported tool paths now share centralized HTTP retry/timeout policy and
  canonical download routing under `docs/downloads/`.
- bioRxiv/medRxiv preprint calls respect environment proxies by default. Set
  `PAPER_SEARCH_DISABLE_PROXIES=1` to disable proxies for preprint calls only.

See `docs/project-specs/source-capability-matrix.md` for the current source
matrix.

Two source families need extra context:

- `search_biorxiv` and `search_medrxiv` stay query-driven at the MCP surface,
  but the upstream API does not expose a documented free-text endpoint. The
  repo now fetches a bounded recent metadata window and applies local matching
  so nonsense queries return `[]` instead of unrelated recent papers.
- bioRxiv and medRxiv now share a single internal preprint base so reliability
  fixes land in one place.
- Semantic Scholar remains on the same public tool surface, but now uses the
  shared PDF helper path used by other download/read adapters.

Sci-Hub-related code exists in the repo, but it is not part of the default
supported surface.

Supported download/read helpers write under `docs/downloads/`.

Operational guardrails live in:

- `docs/project-specs/performance-stability-targets.md`
- `docs/project-specs/adapter-error-handling-policy.md`

## Quick start

### Run from this repo with `uv`

```bash
uv run -m paper_search_mcp.server
```

### Install through Smithery

```bash
npx -y @smithery/cli install @openags/paper-search-mcp --client claude
```

### Claude Desktop configuration

Add a server entry to your Claude Desktop config:

```json
{
  "mcpServers": {
    "paper_search_server": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/path/to/paper-search-mcp",
        "-m",
        "paper_search_mcp.server"
      ],
      "env": {
        "SEMANTIC_SCHOLAR_API_KEY": ""
      }
    }
  }
}
```

`SEMANTIC_SCHOLAR_API_KEY` is optional. Without it, Semantic Scholar requests
use unauthenticated access with lower rate limits.

## Development

```bash
uv sync --locked
uv run -m paper_search_mcp.server
```

Default verification for runtime or doc changes:

```bash
uv sync --locked
markdownlint AGENTS.md ARCHITECTURE.md README.md docs/**/*.md
uv run python -m compileall paper_search_mcp tests
uv run python -c "import paper_search_mcp.server as s; print(s.mcp.name)"
uv run python -m unittest discover -q
```

Targeted reliability/performance checks:

```bash
uv run python -m unittest -q tests.test_http tests.test_pdf_utils
uv run python -m unittest -q tests.test_http_resilience tests.test_performance_smoke
uv run python scripts/benchmarks/tool_latency_smoke.py --dry-run --iterations 3
```

If your shell does not expand `**`, quote the globs or pass explicit file lists
to `markdownlint`.

Targeted live tests are opt-in:

```bash
PAPER_SEARCH_LIVE_TESTS=1 uv run python -m unittest -q tests.test_arxiv
```

See `docs/playbooks/validation.md` for the repo's validation flow and
`docs/playbooks/release.md` for release steps.

## Repo map

- `paper_search_mcp/server.py` — FastMCP entrypoint and tool registration
- `paper_search_mcp/academic_platforms/` — source adapters
- `paper_search_mcp/paper.py` — normalized paper schema
- `tests/` — offline smoke tests plus opt-in live adapter checks
- `docs/` — durable repo guidance
- `docs/CODEBASE_MAP.md` — code navigation map

## Demo

![Demo](docs/images/demo.png)

## License

This project is licensed under the MIT License. See `LICENSE`.
