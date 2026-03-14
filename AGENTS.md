# Repository AGENTS

This repository adopts the global `.codex` governance pack in a lean form that
fits a small Python MCP package.

## Read Here First

1. `README.md`
2. `ARCHITECTURE.md`
3. `docs/PROJECT_SENSE.md`
4. `docs/project-specs/source-capability-matrix.md`
5. `docs/CODEBASE_MAP.md`
6. `docs/PLANS.md`

## Local Invariants

- Keep this repo positioned as a practical Python MCP server for paper search,
  metadata retrieval, and source-specific download/read helpers.
- Preserve public runtime identity unless a task explicitly changes it:
  `paper-search-mcp`, `paper_search_mcp`, Smithery metadata, and existing MCP
  tool names stay stable.
- Treat `docs/` as the durable system of record for repo-specific guidance.
- Treat `docs/CODEBASE_MAP.md` as the durable navigation surface.
- Treat `runtime/run_ledger/` and `downloads/` as local runtime artifacts only;
  do not commit their contents.
- Keep source-by-source caveats explicit. Do not document every adapter as if it
  has the same capability or reliability.
- Keep Sci-Hub out of the default supported surface. If it is mentioned, frame
  it as optional and sensitive legacy functionality with legal and operational
  caveats.

## Template Deviations

This repo intentionally omits some surfaces from the canonical project template.
Those omissions are deliberate, not accidental:

- No `FRONTEND.md`: the repo has no frontend surface.
- No `docs/generated/`: there is no generated API/schema doc pipeline yet.
- No repo-local control-plane registry or orchestration config: those belong to
  the maintainer's global Codex environment, not this package.

## Working Rules

- Prefer concise docs that help a maintainer or agent act immediately.
- Keep Markdown compatible with `markdownlint`.
- Validate documentation changes mechanically before handoff.
- For local code and docs retrieval, follow the global `code-index` workflow
  (`set_project_path` on repo entry; shallow search first; `build_deep_index`
  before symbol-level work; `refresh_index` after edits). If `code-index` is not
  available, use `rg`.
- For any writing output intended for humans, use `writing-clearly-and-concisely`
  then `humanizer` (English) or `humanizer-zh` (Chinese) before finalizing.
- When changing AGENTS or related governance docs, run the required global
  `agent-doc-maintainer` completion gate from the user instructions.
