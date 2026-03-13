# PMC Source Notes

## Capability Conclusion

- `search_pmc`: supported in v1.
- `download_pmc`: not supported in v1.
- `read_pmc_paper`: not supported in v1.

The repo still reserves all three canonical tool names now. That keeps the MCP
surface stable while making the limitation explicit: search is supported, but
download and read return structured limitation messages instead of pretending
full text is generally available.

## Allowed API Surface for v1

PMC v1 uses NCBI E-utilities only.

- `esearch.fcgi` with `db=pmc` and `retmode=xml` to resolve matching PMCIDs.
- `efetch.fcgi` with `db=pmc` and `retmode=xml` to fetch PMC article XML for
  normalized metadata assembly.

This v1 does not add any other PMC or NCBI integration surface.

## Canonical `paper_id` Contract

- The canonical `paper_id` is the `PMCID` string with the `PMC` prefix.
- Example: `PMC1234567`
- PMID and DOI are secondary identifiers only. They may appear in `doi` or
  `extra`, but they do not replace `paper_id`.

## `download` and `read` Placeholder Contract

`download_pmc` and `read_pmc_paper` are deliberate placeholders in v1.

- They return a string that starts with `LIMITATION:` followed by a single
  space.
- The remainder of the string is a JSON object that follows
  `docs/project-specs/mcp-tool-contract.md`.
- The payload uses `source: "pmc"`, the canonical tool name, the blocked
  capability (`download` or `read`), `supported: false`, and
  `reason: "not_implemented"`.
- The placeholder path is policy, not a transient bug. These tools should
  short-circuit without PMC network access or filesystem writes.

Example shape for `download_pmc`:

```text
LIMITATION: {
  "type": "limitation",
  "source": "pmc",
  "tool": "download_pmc",
  "capability": "download",
  "supported": false,
  "reason": "not_implemented",
  "message": "PMC full-text download is not supported yet in this repo.",
  "paper_id": "PMC1234567"
}
```

Example shape for `read_pmc_paper`:

```text
LIMITATION: {
  "type": "limitation",
  "source": "pmc",
  "tool": "read_pmc_paper",
  "capability": "read",
  "supported": false,
  "reason": "not_implemented",
  "message": "PMC full-text reading is not supported yet in this repo.",
  "paper_id": "PMC1234567"
}
```

## Explicit Non-Goals

- No PMC OA API or OA Web Service integration in this v1.
- No PMC HTML page scraping.
- No new NCBI email, tool, or API-key config knobs.
- No claim that PMC search implies a safe or licensed full-text download path.
