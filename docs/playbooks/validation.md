# Validation Playbook

## Default Sequence

1. Run `uv sync --locked` to align the environment with `uv.lock`.
2. Run `markdownlint` on changed Markdown.
3. Run `uv run python -m compileall paper_search_mcp tests`.
4. Run `uv run python -c "import paper_search_mcp.server as s; print(s.mcp.name)"`.
5. Run `uv run python -m unittest discover -q`.

## Offline Smoke Gate

`uv run python -m unittest discover -q` is the default test gate.

- It must stay offline by default.
- It must not download PDFs.
- Path-safety checks live in `tests/test_paths.py`.

## Live Tests

Use live-network tests only when an adapter changed or when you need the
protocol-level MCP smoke suite:

```bash
PAPER_SEARCH_LIVE_TESTS=1 uv run python -m unittest -q tests.test_arxiv
PAPER_SEARCH_LIVE_TESTS=1 uv run python -m unittest -q tests.test_semantic
PAPER_SEARCH_LIVE_TESTS=1 uv run python -m unittest -q tests.test_mcp_live
```

Optional: quick status table for all `search_*` tools:

```bash
uv run python scripts/health_check_search_tools.py
uv run python scripts/health_check_search_tools.py --raw > /tmp/search_health.md
uv run python scripts/health_check_search_tools.py --json | \
  python -m json.tool >/dev/null
uv run python scripts/health_check_search_tools.py --strict
uv run python scripts/health_check_search_tools.py --no-preflight
```

If `glow` is installed, the script renders Markdown via `glow` when stdout is a
TTY.

Notes:

- This script performs live network calls and may flake due to upstream rate
  limits, scraping defenses, or transient outages.
- `--json` emits machine-readable output; `--raw` prints Markdown without
  rendering via `glow`.
- `--strict` exits non-zero if any tool check fails (useful for automation).

Rules:

- run the narrowest module that matches the changed adapter,
- `tests.test_mcp_live` is opt-in and does not replace the default offline gate,
- expect upstream flake for scraping-heavy sources,
- clean up any temporary `docs/downloads/` subdirectories created by ad hoc
  live tests.

## Docker Validation

If `Dockerfile` or `.dockerignore` changed, also run:

```bash
docker build -t paper-search-mcp .
docker run --rm paper-search-mcp python -c \
  "from paper_search_mcp.server import mcp; print(mcp.name)"
```

## Portability Note

Shell glob expansion for commands like `docs/**/*.md` is shell-dependent. On
shells that do not expand `**`, quote the glob or pass explicit file paths.
