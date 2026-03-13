# Source Capability Matrix

This matrix documents the maintained behavior of each source adapter.
Update it whenever source behavior changes.

## Supported MCP sources

- **arXiv** — search: yes; download: yes; read: yes; notes: API-backed,
  explicit timeouts, and downloads/reads land under `docs/downloads/`.
- **PubMed** — search: yes; download: no; read: no; notes: metadata and
  abstracts only.
- **PMC** — search: yes; download: no; read: no; notes: v1 uses NCBI
  E-utilities only (`esearch` + `efetch` with `db=pmc`, `retmode=xml`);
  canonical `paper_id` is a `PMCID` with the `PMC` prefix; `download_pmc`
  and `read_pmc_paper` stay as structured limitation placeholders. See
  `docs/project-specs/source-notes/pmc.md`.
- **bioRxiv** — search: yes; download: yes; read: yes; notes: API-backed,
  but PDF and text behavior still depend on remote availability; downloads
  write under `docs/downloads/`.
- **medRxiv** — search: yes; download: yes; read: yes; notes: similar
  operational profile to bioRxiv; downloads write under `docs/downloads/`.
- **Google Scholar** — search: yes; download: no; read: no; notes:
  supported with caveats because it is scraping-based and can be blocked.
- **IACR ePrint Archive** — search: yes; download: yes; read: yes;
  notes: search and detail scraping depend on current site structure; downloads
  write under `docs/downloads/`.
- **Semantic Scholar** — search: yes; download: yes; read: yes; notes:
  better with `SEMANTIC_SCHOLAR_API_KEY`; otherwise more rate-limit risk;
  downloads write under `docs/downloads/`.
- **CrossRef** — search: yes; download: no; read: no; notes:
  metadata-oriented and does not provide direct full-text delivery.

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
