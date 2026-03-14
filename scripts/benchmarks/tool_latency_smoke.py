from __future__ import annotations

import argparse
import asyncio
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
import json
import statistics
import time
from typing import Any, Callable, Iterator
from unittest.mock import patch

from paper_search_mcp import server
from paper_search_mcp._paths import resolve_download_target
from paper_search_mcp.paper import Paper


DEFAULT_ITERATIONS = 5
DEFAULT_WARMUP = 1
DEFAULT_QUERY = "transformer"
DEFAULT_PAPER_ID = "1706.03762"
DRY_RUN_DELAYS = {
    "search_arxiv": 0.005,
    "download_arxiv": 0.008,
    "read_arxiv_paper": 0.012,
}


@dataclass(frozen=True)
class BenchmarkCase:
    tool_name: str
    description: str
    invoke: Callable[[], Any]


class DryRunArxivSearcher:
    def search(self, query: str, max_results: int = 10, **_: Any) -> list[Paper]:
        time.sleep(DRY_RUN_DELAYS["search_arxiv"])
        return [
            Paper(
                paper_id=f"dry-run-{index}",
                title=f"Dry Run Result {index}",
                authors=["Benchmark Harness"],
                abstract=f"Deterministic result for query={query}",
                doi="",
                published_date=datetime(2024, 1, 1),
                pdf_url="https://example.invalid/paper.pdf",
                url="https://example.invalid/paper",
                source="arxiv",
            )
            for index in range(min(max_results, 2))
        ]

    def download_pdf(self, paper_id: str, save_path: str) -> str:
        time.sleep(DRY_RUN_DELAYS["download_arxiv"])
        target = resolve_download_target(filename=f"{paper_id}.pdf", save_path=save_path)
        return str(target.path)

    def read_paper(self, paper_id: str, save_path: str = "./downloads") -> str:
        time.sleep(DRY_RUN_DELAYS["read_arxiv_paper"])
        resolve_download_target(filename=f"{paper_id}.pdf", save_path=save_path)
        return f"dry-run extracted text for {paper_id}"


def _build_cases(query: str, paper_id: str) -> list[BenchmarkCase]:
    return [
        BenchmarkCase(
            tool_name="search_arxiv",
            description="Search representative query path",
            invoke=lambda: server.search_arxiv(query=query, max_results=3),
        ),
        BenchmarkCase(
            tool_name="download_arxiv",
            description="Download representative paper path",
            invoke=lambda: server.download_arxiv(paper_id=paper_id, save_path="./downloads"),
        ),
        BenchmarkCase(
            tool_name="read_arxiv_paper",
            description="Read representative paper path",
            invoke=lambda: server.read_arxiv_paper(paper_id=paper_id, save_path="./downloads"),
        ),
    ]


def _summarize_result(value: Any) -> str:
    if isinstance(value, list):
        return f"list[{len(value)}]"
    if isinstance(value, str):
        return f"str[{len(value)}]"
    return type(value).__name__


@contextmanager
def _dry_run_patches(enabled: bool) -> Iterator[None]:
    if not enabled:
        yield
        return

    with patch.object(server, "ArxivSearcher", DryRunArxivSearcher):
        yield


async def _run_case(case: BenchmarkCase, iterations: int, warmup: int) -> dict[str, Any]:
    for _ in range(warmup):
        await case.invoke()

    timings_ms: list[float] = []
    failures = 0
    result_summary = ""

    for _ in range(iterations):
        started = time.perf_counter()
        try:
            result = await case.invoke()
        except Exception as exc:  # pragma: no cover - only hit in live failure cases
            failures += 1
            result_summary = f"{type(exc).__name__}: {exc}"
        else:
            timings_ms.append((time.perf_counter() - started) * 1000.0)
            result_summary = _summarize_result(result)

    if not timings_ms:
        raise RuntimeError(f"{case.tool_name} produced no successful iterations")

    return {
        "tool_name": case.tool_name,
        "description": case.description,
        "iterations": iterations,
        "failures": failures,
        "result_summary": result_summary,
        "min_ms": round(min(timings_ms), 3),
        "p50_ms": round(statistics.median(timings_ms), 3),
        "mean_ms": round(statistics.fmean(timings_ms), 3),
        "max_ms": round(max(timings_ms), 3),
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run a deterministic latency smoke benchmark for representative "
            "paper-search MCP tool paths."
        )
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="Use a deterministic fake arXiv adapter and avoid network calls.",
    )
    mode.add_argument(
        "--live",
        action="store_true",
        help="Run against the real adapter implementation and live network.",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=DEFAULT_ITERATIONS,
        help=f"Measured iterations per tool (default: {DEFAULT_ITERATIONS}).",
    )
    parser.add_argument(
        "--warmup",
        type=int,
        default=DEFAULT_WARMUP,
        help=f"Warmup iterations per tool before timing (default: {DEFAULT_WARMUP}).",
    )
    parser.add_argument(
        "--query",
        default=DEFAULT_QUERY,
        help=f"Representative search query (default: {DEFAULT_QUERY!r}).",
    )
    parser.add_argument(
        "--paper-id",
        default=DEFAULT_PAPER_ID,
        help=f"Representative paper id for download/read (default: {DEFAULT_PAPER_ID!r}).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the benchmark report as JSON.",
    )
    return parser


def _print_table(report: dict[str, Any]) -> None:
    print(f"mode={report['mode']} iterations={report['iterations']} warmup={report['warmup']}")
    print("tool_name           p50_ms   mean_ms  min_ms   max_ms   failures  result")
    for result in report["results"]:
        print(
            f"{result['tool_name']:<18}"
            f"{result['p50_ms']:>8.3f}  "
            f"{result['mean_ms']:>7.3f}  "
            f"{result['min_ms']:>6.3f}  "
            f"{result['max_ms']:>6.3f}  "
            f"{result['failures']:>8}  "
            f"{result['result_summary']}"
        )


async def _amain(args: argparse.Namespace) -> int:
    dry_run = args.dry_run or not args.live
    cases = _build_cases(query=args.query, paper_id=args.paper_id)

    with _dry_run_patches(dry_run):
        results = [
            await _run_case(case, iterations=args.iterations, warmup=args.warmup)
            for case in cases
        ]

    report = {
        "mode": "dry-run" if dry_run else "live",
        "iterations": args.iterations,
        "warmup": args.warmup,
        "results": results,
    }

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        _print_table(report)

    return 1 if any(result["failures"] for result in results) else 0


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    if args.iterations < 1:
        parser.error("--iterations must be >= 1")
    if args.warmup < 0:
        parser.error("--warmup must be >= 0")
    return asyncio.run(_amain(args))


if __name__ == "__main__":
    raise SystemExit(main())
