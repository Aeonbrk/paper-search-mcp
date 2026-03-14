# Project Sense

`paper-search-mcp` is a practical connector layer between LLM/MCP clients and a
small set of academic paper sources.

## What This Repo Is

- A Python FastMCP server.
- A normalized paper metadata interface.
- A set of source adapters with uneven but useful capabilities.
- A lightweight package that can run locally, through Smithery, or via a Python
  environment.

## What This Repo Is Not

- A general research workflow platform.
- A publisher-licensed full-text platform.
- A frontend application.
- A stable abstraction over every scholarly source on the internet.

## Current Aim

Make the repo easy to understand, safe to operate, and honest about source
limits while preserving the existing MCP runtime surface.

## Current Operational Priorities

- Keep the public MCP tool names and high-level behavior stable.
- Improve internal reliability through shared HTTP and PDF utility layers.
- Keep no-hit behavior deterministic (`[]`) and distinct from transport errors.
- Preserve canonical download/read routing under `docs/downloads/`.
- Expand deterministic offline regression coverage before relying on live checks.
