# Security

## Security Posture

This repo is a networked connector. Its main risks come from untrusted upstream
services, downloaded PDFs, and accidental exposure of local filesystem paths or
credentials.

## Current Controls

- Download and read flows are confined to `docs/downloads/`.
- MCP download/read tools always use the canonical `docs/downloads/` root
  instead of trusting arbitrary filesystem locations.
- Shared path helpers fold `downloads/` and `docs/downloads/` prefixes into the
  canonical root so callers do not accidentally create nested
  `docs/downloads/docs/downloads/...` paths.
- Maintained adapters now use explicit timeouts and clearer HTTP failure
  handling on their default paths.

## Rules

- Keep API keys out of the repo. Use environment variables such as
  `SEMANTIC_SCHOLAR_API_KEY`.
- Do not commit downloaded PDFs or runtime ledgers.
- Treat downloaded documents as untrusted input.
- Keep source-specific legal and operational caveats explicit.

## Sensitive Surface

Sci-Hub-related code exists in the repo, but it is not part of the default
supported surface.

- Do not advertise it in the main README or capability matrix as a normal path.
- Any future work on that helper should include legal, operational, and
  documentation review.
- Do not silently reintroduce insecure transport shortcuts or uncontrolled
  write paths on that path.

## Validation Hooks

- `uv run python -m unittest -q tests.test_paths`
- `uv run python -m unittest discover -q`
