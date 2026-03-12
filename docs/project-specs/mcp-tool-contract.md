# MCP Tool Contract

This repo exposes a source-scoped FastMCP tool surface from
`paper_search_mcp/server.py`.

## Naming pattern

- `search_<source>` returns normalized paper metadata.
- `download_<source>` downloads a paper PDF when the source supports it.
- `read_<source>_paper` returns extracted text or a source-specific limitation
  message.
- `get_crossref_paper_by_doi` is the one source-specific lookup helper that does
  not follow the search/download/read triad.

## Current tool groups

### Search

- `search_arxiv`
- `search_pubmed`
- `search_biorxiv`
- `search_medrxiv`
- `search_google_scholar`
- `search_iacr`
- `search_semantic`
- `search_crossref`

### Download

- `download_arxiv`
- `download_pubmed`
- `download_biorxiv`
- `download_medrxiv`
- `download_iacr`
- `download_semantic`
- `download_crossref`

### Read

- `read_arxiv_paper`
- `read_pubmed_paper`
- `read_biorxiv_paper`
- `read_medrxiv_paper`
- `read_iacr_paper`
- `read_semantic_paper`
- `read_crossref_paper`

### Lookup

- `get_crossref_paper_by_doi`

## Normalized search result shape

Search and lookup tools serialize `Paper` objects through `Paper.to_dict()`.
Clients should expect these keys:

- `paper_id`
- `title`
- `authors`
- `abstract`
- `doi`
- `published_date`
- `pdf_url`
- `url`
- `source`
- `updated_date`
- `categories`
- `keywords`
- `citations`
- `references`
- `extra`

## Compatibility notes

- `authors`, `categories`, `keywords`, and `references` are serialized as
  semicolon-delimited strings, not JSON arrays.
- Date fields are serialized as ISO 8601 strings when present.
- `extra` is currently serialized as an opaque string via `str(self.extra)`,
  not as a structured JSON object.
- Capability differences belong in the source matrix, not in tool naming.
