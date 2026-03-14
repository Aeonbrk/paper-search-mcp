# Performance And Stability Targets

This document defines the first deterministic latency baseline for the
performance and stability optimization pass.

## Scope

The benchmark harness in `scripts/benchmarks/tool_latency_smoke.py` measures
representative public tool paths through `paper_search_mcp/server.py`:

- `search_arxiv`
- `download_arxiv`
- `read_arxiv_paper`

The default benchmark mode is `--dry-run`. It replaces the live arXiv adapter
with a deterministic fake searcher so the harness exercises the MCP wrapper
path without requiring network access or production code changes.

## Baseline Commands

```bash
uv run python scripts/benchmarks/tool_latency_smoke.py --help
uv run python scripts/benchmarks/tool_latency_smoke.py --dry-run --iterations 5
uv run python scripts/benchmarks/tool_latency_smoke.py --live --iterations 3
```

Use `--live` only when you want an observational network sample. Offline
regression checks should stay on `--dry-run`.

## Dry-Run Baseline

The dry-run harness injects fixed adapter-side delays to stabilize the timing
signal around wrapper, thread-hop, and serialization overhead:

- `search_arxiv`: 5 ms synthetic adapter delay
- `download_arxiv`: 8 ms synthetic adapter delay
- `read_arxiv_paper`: 12 ms synthetic adapter delay

Observed dry-run baseline on 2026-03-14 in this repo workspace
(`--iterations 5`):

- `search_arxiv`: observed `p50=5.603 ms`; focus is wrapper and serialization;
  target `p50 <= 20 ms`; failure budget `0`.
- `download_arxiv`: observed `p50=9.739 ms`; focus is wrapper and canonical
  path routing; target `p50 <= 24 ms`; failure budget `0`.
- `read_arxiv_paper`: observed `p50=15.099 ms`; focus is wrapper and canonical
  read routing; target `p50 <= 30 ms`; failure budget `0`.

The observed numbers are the current local reference point. The threshold
values below are the automation guardrails for later regression tests.

## Threshold Keys

These keys are the stable source of truth for offline latency guardrails:

```text
search_arxiv.dry_run.p50_ms_max=20
search_arxiv.dry_run.failures_max=0
download_arxiv.dry_run.p50_ms_max=24
download_arxiv.dry_run.failures_max=0
read_arxiv_paper.dry_run.p50_ms_max=30
read_arxiv_paper.dry_run.failures_max=0
```

## Live-Run Expectations

Live mode is not part of the default offline gate because upstream latency and
availability vary. Use it to compare before/after behavior under the same
network conditions.

- `search_arxiv` should usually stay below 2 s `p50`.
- `download_arxiv` should usually stay below 10 s `p50`.
- `read_arxiv_paper` should usually stay below 12 s `p50`.
- Any transport failure in live mode should be treated separately from a
  no-result search outcome.

## Stability Targets

- Retry and timeout behavior should be consistent per transport family.
- No tool should silently swallow transport failures in the default path.
- Ordinary no-hit searches must still return `[]`, not an error marker.
- Download and read helpers must continue using canonical paths under
  `docs/downloads/`.
