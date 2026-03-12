# Upstream and Services Reference

## Repository lineage

- Current Git remote points at `Aeonbrk/paper-search-mcp`.
- The repo remains compatible with the upstream runtime identity:
  `paper-search-mcp` and `paper_search_mcp`.

## Distribution surfaces

- `pyproject.toml` — package metadata and dependencies
- `smithery.yaml` — Smithery launch metadata
- `.github/workflows/publish.yml` — tag-driven PyPI publish workflow

## External services

- arXiv API
- PubMed eUtils
- bioRxiv API
- medRxiv API
- Google Scholar web pages
- IACR ePrint Archive web pages
- Semantic Scholar API
- CrossRef API

## Operational reminder

Changes in these external services can change repo behavior without any local
code change. Keep `docs/project-specs/source-capability-matrix.md` and
`docs/RELIABILITY.md` aligned with reality.
