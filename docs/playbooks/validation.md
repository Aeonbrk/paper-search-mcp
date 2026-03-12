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

Use live-network tests only when an adapter changed:

```bash
PAPER_SEARCH_LIVE_TESTS=1 uv run python -m unittest -q tests.test_arxiv
PAPER_SEARCH_LIVE_TESTS=1 uv run python -m unittest -q tests.test_semantic
```

Rules:

- run the narrowest module that matches the changed adapter,
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
