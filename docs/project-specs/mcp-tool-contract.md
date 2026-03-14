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

## Search contract

- Search tools are query-driven unless a source-specific note says otherwise.
- An ordinary no-hit query returns zero papers, not a transport error.
- For direct Python calls in this repo, that means `[]`.
- At the MCP boundary, current FastMCP and Python SDK clients may surface the
  same zero-hit result either as an empty structured result or as
  `CallToolResult(content=[])`. Both are valid no-result outcomes.
- Transport failures, blocking, or rate limits are not part of the no-hit
  contract. Those cases may still surface as errors.

## Source-specific search notes

- `search_biorxiv` and `search_medrxiv` remain free-text search tools at the
  public surface. Because the upstream API does not publish a documented
  free-text endpoint, this repo implements them by fetching a bounded recent
  metadata window and applying local query matching.
- `search_crossref`, `search_google_scholar`, and `search_iacr` treat no-hit
  searches as empty results and keep transport failures distinct from that
  outcome.

## Limitation message format (hard contract)

Some sources do not support `download` and/or `read` capabilities. In those
cases, the tool returns a limitation message as a `str` (not an exception).

To keep this machine-detectable and testable, any newly added tool (and any tool
intentionally shipped as a placeholder) MUST return a structured limitation
message in the following format:

- Prefix: the string MUST start with `LIMITATION:` followed by a single space.
- Payload: the remainder of the string MUST be a JSON object.

Parsing rules:

- After removing the exact prefix `LIMITATION:` plus a single space, the
  remainder MUST be parseable by `json.loads` as a JSON object.
- Producers MUST NOT append trailing prose after the JSON (whitespace is fine).
- Consumers MUST parse the JSON payload; they MUST NOT rely on exact whitespace,
  indentation, or key ordering.

Schema (JSON keys):

- `type`: MUST be `limitation`
- `source`: source id (e.g., `pmc`)
- `tool`: tool name (e.g., `download_pmc`)
- `capability`: MUST be `download` or `read`
- `supported`: MUST be `false`
- `reason`: stable reason code. For v1 in this repo it MUST be one of:
  `not_implemented`, `unsupported_by_source`, `license_restricted`
- `message`: human-readable explanation
- `paper_id`: OPTIONAL, the input `paper_id`
- `docs`: OPTIONAL list of doc paths that explain the limitation (example:
  `docs/project-specs/source-capability-matrix.md`)

Examples:

```text
LIMITATION: {
  "type": "limitation",
  "source": "pmc",
  "tool": "download_pmc",
  "capability": "download",
  "supported": false,
  "reason": "not_implemented",
  "message": "PMC full-text download is not supported yet in this repo.",
  "paper_id": "PMC123456",
  "docs": ["docs/project-specs/source-capability-matrix.md"]
}
```

```text
LIMITATION: {
  "type": "limitation",
  "source": "pmc",
  "tool": "read_pmc_paper",
  "capability": "read",
  "supported": false,
  "reason": "not_implemented",
  "message": "PMC full-text reading is not supported yet in this repo.",
  "paper_id": "PMC123456",
  "docs": ["docs/project-specs/source-capability-matrix.md"]
}
```

Notes:

- Existing tools may still return free-form strings until migrated; only the
  above format is considered stable for automation.

## Current tool groups

### Search

- `search_arxiv`
- `search_pubmed`
- `search_pmc`
- `search_biorxiv`
- `search_medrxiv`
- `search_google_scholar`
- `search_iacr`
- `search_semantic`
- `search_crossref`

### Download

- `download_arxiv`
- `download_pubmed`
- `download_pmc`
- `download_biorxiv`
- `download_medrxiv`
- `download_iacr`
- `download_semantic`
- `download_crossref`

### Read

- `read_arxiv_paper`
- `read_pubmed_paper`
- `read_pmc_paper`
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
- PMC v1 ships the full tool trio, but `download_pmc` and `read_pmc_paper`
  are explicit placeholders that return the structured limitation format above.
