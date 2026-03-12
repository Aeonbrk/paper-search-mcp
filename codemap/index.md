# Codemap

Use this folder for docs-first orientation before broad source exploration.

## Recommended read order

1. `codemap/reference/CODEBASE_MAP.md`
2. `ARCHITECTURE.md`
3. `docs/project-specs/mcp-tool-contract.md`
4. `docs/project-specs/source-capability-matrix.md`

## What codemap owns

- navigation context,
- file and subsystem summaries,
- entrypoint guidance.

It does not replace the durable guidance in `docs/`.

## Local retrieval

- Prefer `code-index` for local code and docs retrieval.
  - On repo entry or repo-root change: call `set_project_path`.
  - Use shallow index search first.
  - Call `build_deep_index` before symbol-level work.
  - After edits: call `refresh_index` before trusting results.
- If `code-index` is not available, use `rg`.
