# Design

## Core Design Choices

- Keep one adapter module per source.
- Normalize source output through the shared `Paper` model.
- Keep MCP tool names source-scoped for clarity.
- Prefer explicit capability differences over pretending all sources behave the
  same.

## Consequences

- The repo is easy to extend source-by-source.
- Behavior differs by upstream API quality and rate limits.
- Documentation must stay honest about what each source can really do.
