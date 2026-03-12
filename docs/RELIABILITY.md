# Reliability

## Reliability Model

This project depends on external services for most useful behavior. Reliability
therefore varies by source, and scraping-backed adapters remain less stable
than API-backed adapters.

## Known Reliability Constraints

- APIs can rate-limit, change response formats, or tighten quotas.
- Scraped sources can block requests or change HTML structure without notice.
- PDF download and text extraction may fail even when search succeeds.
- Live-network tests can fail because of upstream behavior rather than a local
  regression.

## Default Acceptance Strategy

Use fast offline checks as the default gate:

- `uv sync --locked`
- `uv run python -m compileall paper_search_mcp tests`
- `uv run python -c "import paper_search_mcp.server as s; print(s.mcp.name)"`
- `uv run python -m unittest discover -q`
- `markdownlint` on changed Markdown

## Live Test Policy

Live integration checks are opt-in:

- set `PAPER_SEARCH_LIVE_TESTS=1`,
- run only the adapter-specific test module you changed,
- expect upstream flake and record that evidence separately from the default
  smoke gate.

## Runtime Notes

- The MCP server now offloads synchronous adapter work to threads and applies a
  bounded concurrency limit.
- This improves responsiveness, but it does not make upstream services more
  reliable. Source-specific caveats still matter.
