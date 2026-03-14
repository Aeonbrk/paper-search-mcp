# Source Capability Matrix

This matrix documents the maintained behavior of each source adapter.
Update it whenever source behavior changes.

## Supported MCP sources

- **arXiv** — search: yes; download: yes; read: yes; notes: API-backed,
  explicit timeout/retry policy via shared HTTP helpers, and downloads/reads
  land under `docs/downloads/`.
- **PubMed** — search: yes; download: no; read: no; notes: metadata and
  abstracts only.
- **PMC** — search: yes; download: no; read: no; notes: v1 uses NCBI
  E-utilities only (`esearch` + `efetch` with `db=pmc`, `retmode=xml`);
  canonical `paper_id` is a `PMCID` with the `PMC` prefix; `download_pmc`
  and `read_pmc_paper` stay as structured limitation placeholders. See
  `docs/project-specs/source-notes/pmc.md`.
- **bioRxiv** — search: yes; download: yes; read: yes; notes: API-backed,
  but the upstream API does not publish a documented free-text search endpoint;
  this repo performs bounded recent-metadata retrieval plus local query
  matching so nonsense queries return `[]`; runtime behavior is now centralized
  with medRxiv in a shared preprint base; PDF and text behavior still depend on
  remote availability; downloads write under `docs/downloads/`.
- **medRxiv** — search: yes; download: yes; read: yes; notes: similar
  operational profile to bioRxiv, including bounded recent-metadata retrieval
  plus local query matching because the public API does not publish a
  documented free-text search endpoint; runtime behavior is centralized with
  bioRxiv in the shared preprint base; downloads write under `docs/downloads/`.
- **Google Scholar** — search: yes; download: no; read: no; notes:
  supported with caveats because it is scraping-based and can be blocked;
  ordinary no-hit queries return `[]`, while transport failures stay distinct;
  degraded short pages now terminate deterministically to avoid wasted retries.
- **IACR ePrint Archive** — search: yes; download: yes; read: yes;
  notes: search and detail scraping depend on current site structure; ordinary
  no-hit queries return `[]`; detail-fetch effort is bounded per search call to
  avoid latency blowups; downloads write under `docs/downloads/`.
- **Semantic Scholar** — search: yes; download: yes; read: yes; notes:
  better with `SEMANTIC_SCHOLAR_API_KEY`; otherwise more rate-limit risk;
  runtime PDF handling now uses shared download/extraction helpers; downloads
  write under `docs/downloads/`.
- **CrossRef** — search: yes; download: no; read: no; notes:
  metadata-oriented and does not provide direct full-text delivery; ordinary
  no-hit queries return `[]`, while request failures stay distinct.

## Optional and Sensitive Surface

- **Sci-Hub** — not on the default MCP surface; legacy helper only; treat it
  as optional and sensitive even though code and tests exist in the repo.

## Interpretation Rules

- `Supported` means the source is part of the maintained MCP surface.
- `Supported with caveats` means the source is exposed, but reliability depends
  heavily on third-party blocking or scraping stability.
- `Optional and sensitive` means the code exists, but should not be
  treated as a default advertised feature.
- For maintained download/read helpers, the canonical write location is
  `docs/downloads/`.
- Shared operational guardrails for retries and failure signaling are documented
  in `docs/project-specs/adapter-error-handling-policy.md`.
