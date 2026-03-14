# Adapter Error Handling Policy

This document defines runtime guardrails for adapter reliability work.
It complements `mcp-tool-contract.md` by describing internal behavior that
must remain consistent across sources.

## Scope

- Applies to source adapters under `paper_search_mcp/academic_platforms/`.
- Applies to shared transport and PDF helpers:
  - `paper_search_mcp/_http.py`
  - `paper_search_mcp/_pdf.py`
- Applies to MCP wrapper dispatch in `paper_search_mcp/server.py`.

## Core Rules

- Preserve public tool names and capability boundaries.
- Keep ordinary no-hit searches deterministic (`[]`), not error markers.
- Keep transport/runtime failures distinct from no-hit outcomes.
- Prefer explicit limitation responses for unsupported capabilities.
- Route maintained download/read writes under `docs/downloads/`.

## Transport Policy

- Build and reuse sessions through shared HTTP helpers.
- Use shared retry policy defaults for retryable status codes:
  `429`, `500`, `502`, `503`, `504`.
- Keep bounded connect/read timeouts on network paths.
- Raise wrapped transport errors (`TransportError`) for terminal failures.

## PDF Policy

- Use shared streamed download helpers for PDF writes.
- Clean up partial output files when streamed writes fail.
- Use shared extraction helpers for read paths where contract-compatible.
- Treat malformed or empty PDFs as explicit failures internally.

## MCP Dispatch Policy

- Use centralized search/download/read dispatch wrappers.
- For supported operations, propagate runtime failures.
- For unsupported operations, return source-appropriate limitation responses.
- Keep wrapper-level save-path handling compatibility-only; canonical writes stay
  under `docs/downloads/`.

## Logging Policy

- Use module loggers for runtime warnings and recoverable parse failures.
- Avoid `print(...)` in runtime request/parse paths.
- Keep warning messages source-specific enough for diagnosis.

## Source-Specific Compatibility Notes

- PMC `download` and `read` remain explicit placeholders and return structured
  limitation payloads.
- PubMed and CrossRef `download`/`read` remain unsupported and return explicit
  unsupported messages.
- bioRxiv and medRxiv share a common preprint base implementation; source
  modules keep source constants and identity-specific behavior.

## Validation Expectations

- Unit tests should pin retry policy behavior and failure propagation.
- Unit tests should cover malformed/empty PDF extraction behavior.
- Regression tests should verify no-hit/search contracts and unsupported
  capability behavior.
- Performance smoke checks should read thresholds from
  `performance-stability-targets.md` and run offline by default.
