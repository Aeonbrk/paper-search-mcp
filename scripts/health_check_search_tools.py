from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
from typing import Any, Mapping, Sequence

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import CallToolResult, TextContent
import requests


@dataclass(frozen=True)
class PreflightCase:
    url: str
    headers: Mapping[str, str] | None = None
    expected_statuses: Sequence[int] = (200,)


@dataclass(frozen=True)
class SearchCase:
    source_id: str
    args: dict[str, Any]


@dataclass(frozen=True)
class SearchResult:
    source_id: str
    tool_name: str
    args: dict[str, Any]
    timeout_s: float
    preflight_ok: bool | None
    ok: bool
    count: int | None
    seconds: float | None
    error: str | None
    notes: str | None


DEFAULT_REPO_ROOT = Path(__file__).resolve().parents[1]

SOURCE_LABELS_ZH = {
    "arxiv": "arXiv",
    "pubmed": "PubMed",
    "pmc": "PMC",
    "biorxiv": "bioRxiv",
    "medrxiv": "medRxiv",
    "google_scholar": "Google Scholar（谷歌学术）",
    "iacr": "IACR ePrint",
    "semantic": "Semantic Scholar",
    "crossref": "CrossRef",
}

DEFAULT_SEARCH_CASES: tuple[SearchCase, ...] = (
    SearchCase("arxiv", {"query": "transformer", "max_results": 2}),
    SearchCase("pubmed", {"query": "transformer", "max_results": 2}),
    SearchCase("pmc", {"query": "transformer", "max_results": 2}),
    SearchCase("biorxiv", {"query": "transformer", "max_results": 2, "days": 7}),
    SearchCase("medrxiv", {"query": "covid", "max_results": 2, "days": 7}),
    SearchCase("google_scholar", {"query": "transformer", "max_results": 1}),
    SearchCase("iacr", {"query": "encryption", "max_results": 2}),
    SearchCase("semantic", {"query": "transformer", "max_results": 2}),
    SearchCase("crossref", {"query": "transformer", "max_results": 2}),
)

DEFAULT_PREFLIGHT_CASES: Mapping[str, PreflightCase] = {
    "arxiv": PreflightCase(
        url="http://export.arxiv.org/api/query?search_query=all:transformer&start=0&max_results=1"
    ),
    "pubmed": PreflightCase(
        url="https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=transformer&retmax=1"
    ),
    "pmc": PreflightCase(
        url="https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pmc&term=transformer&retmax=1"
    ),
    "biorxiv": PreflightCase(
        url="https://api.biorxiv.org/details/biorxiv/2025-01-01/2025-01-02/0"
    ),
    "medrxiv": PreflightCase(
        url="https://api.biorxiv.org/details/medrxiv/2025-01-01/2025-01-02/0"
    ),
    "google_scholar": PreflightCase(
        url="https://scholar.google.com/scholar?q=transformer",
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/123.0.0.0 Safari/537.36"
            )
        },
    ),
    "iacr": PreflightCase(url="https://eprint.iacr.org/search?q=encryption"),
    "semantic": PreflightCase(
        url="https://api.semanticscholar.org/graph/v1/paper/search?query=transformer&limit=1"
    ),
    "crossref": PreflightCase(url="https://api.crossref.org/works?query=transformer&rows=1"),
}


def _parse_json_text(text: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Expected JSON tool result, got: {text!r}") from exc


def _count_search_items(result: CallToolResult) -> tuple[int, str | None]:
    if result.isError:
        return 0, "protocol_error"

    if not result.content:
        return 0, None

    papers: list[dict[str, Any]] = []
    for item in result.content:
        if not isinstance(item, TextContent):
            return 0, f"unexpected_content_type:{type(item).__name__}"
        try:
            payload = _parse_json_text(item.text)
        except ValueError:
            return 0, "invalid_json"
        if isinstance(payload, dict):
            papers.append(payload)
            continue
        if isinstance(payload, list):
            if not all(isinstance(entry, dict) for entry in payload):
                return 0, "unexpected_list_payload"
            papers.extend(payload)
            continue
        return 0, "unexpected_payload"

    return len(papers), None


def _tool_to_source_id(tool_name: str) -> str:
    if not tool_name.startswith("search_"):
        return tool_name
    return tool_name[len("search_") :]


def _format_query(args: Mapping[str, Any]) -> str:
    parts = []
    query = args.get("query")
    if query:
        parts.append(f"q={query}")
    if "max_results" in args:
        parts.append(f"n={args.get('max_results')}")
    if "days" in args:
        parts.append(f"days={args.get('days')}")
    return ", ".join(parts) if parts else "-"


def _preflight_http(case: PreflightCase, *, timeout_s: float) -> bool:
    # Keep this intentionally minimal: preflight is a best-effort signal that the
    # upstream is reachable, not a correctness gate.
    response: requests.Response | None = None
    try:
        response = requests.get(
            case.url,
            headers=dict(case.headers) if case.headers is not None else None,
            timeout=timeout_s,
        )
    except requests.RequestException:
        return False
    finally:
        if response is not None:
            response.close()
    return response.status_code in set(int(code) for code in case.expected_statuses)


async def _run_checks(args: argparse.Namespace) -> tuple[str, list[SearchResult]]:
    preflight_results: dict[str, bool] = {}
    if not args.no_preflight:
        for source_id, case in DEFAULT_PREFLIGHT_CASES.items():
            preflight_results[source_id] = _preflight_http(
                case, timeout_s=args.preflight_timeout
            )

    server = StdioServerParameters(
        command=args.server_command,
        args=list(args.server_args),
        cwd=args.repo_root,
    )

    started_at = time.strftime("%Y-%m-%d %H:%M:%S %Z")
    results: list[SearchResult] = []

    async with stdio_client(server) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            available_tools = {tool.name for tool in (await session.list_tools()).tools}
            search_tools = sorted(tool for tool in available_tools if tool.startswith("search_"))

            case_by_source = {case.source_id: case for case in DEFAULT_SEARCH_CASES}
            for tool_name in search_tools:
                source_id = _tool_to_source_id(tool_name)
                search_case = case_by_source.get(
                    source_id,
                    SearchCase(source_id, {"query": args.query, "max_results": args.max_results}),
                )
                tool_args = dict(search_case.args)
                timeout_s = args.timeout_biorxiv if source_id == "biorxiv" else args.timeout
                preflight_ok = preflight_results.get(source_id) if not args.no_preflight else None

                call_started = time.monotonic()
                try:
                    call_result = await asyncio.wait_for(
                        session.call_tool(tool_name, tool_args),
                        timeout=float(timeout_s),
                    )
                except asyncio.TimeoutError:
                    elapsed = time.monotonic() - call_started
                    results.append(
                        SearchResult(
                            source_id=source_id,
                            tool_name=tool_name,
                            args=tool_args,
                            timeout_s=float(timeout_s),
                            preflight_ok=preflight_ok,
                            ok=False,
                            count=0,
                            seconds=round(elapsed, 3),
                            error="timeout",
                            notes=f"超时（>{timeout_s}s）",
                        )
                    )
                    continue
                except Exception as exc:  # noqa: BLE001
                    elapsed = time.monotonic() - call_started
                    results.append(
                        SearchResult(
                            source_id=source_id,
                            tool_name=tool_name,
                            args=tool_args,
                            timeout_s=float(timeout_s),
                            preflight_ok=preflight_ok,
                            ok=False,
                            count=0,
                            seconds=round(elapsed, 3),
                            error=f"exception:{type(exc).__name__}: {exc}",
                            notes="调用抛异常",
                        )
                    )
                    continue

                elapsed = time.monotonic() - call_started
                count, parse_error = _count_search_items(call_result)
                notes: str | None = None
                ok = parse_error is None and count > 0
                if parse_error is not None:
                    notes = "返回格式异常"
                elif count == 0:
                    notes = "返回 0 条（可能是限流/上游变动）"

                results.append(
                    SearchResult(
                        source_id=source_id,
                        tool_name=tool_name,
                        args=tool_args,
                        timeout_s=float(timeout_s),
                        preflight_ok=preflight_ok,
                        ok=ok,
                        count=count,
                        seconds=round(elapsed, 3),
                        error=parse_error,
                        notes=notes,
                    )
                )

    return started_at, results


def _format_preflight(value: bool | None) -> str:
    if value is None:
        return "-"
    return "OK" if value else "FAIL"


def _format_status(row: SearchResult) -> str:
    if row.error == "timeout":
        return "TIMEOUT"
    return "OK" if row.ok else "FAIL"


def _build_markdown(started_at: str, rows: Sequence[SearchResult]) -> str:
    lines = []
    lines.append("# 搜索工具健康检查\n")
    lines.append(f"- 时间：{started_at}")
    lines.append("- 说明：本检查会进行真实网络调用，结果受上游服务、网络与限流影响。")
    lines.append("")
    lines.append("| 来源 | 工具 | 预检 | 查询 | 调用 | 结果数 | 耗时(s) | 备注 |")
    lines.append("|---|---|---|---|---|---:|---:|---|")
    for row in rows:
        label = SOURCE_LABELS_ZH.get(row.source_id, row.source_id)
        tool = f"`{row.tool_name}`"
        preflight = _format_preflight(row.preflight_ok)
        query = _format_query(row.args)
        status = _format_status(row)
        count = "-" if row.count is None else str(row.count)
        seconds = "-" if row.seconds is None else f"{row.seconds:.3f}"
        notes = row.notes or ""
        lines.append(
            f"| {label} | {tool} | {preflight} | {query} | {status} | {count} | {seconds} | {notes} |"
        )

    failed = [row for row in rows if not row.ok]
    if failed:
        lines.append("")
        lines.append(f"## 小结\n\n- 失败/异常：{len(failed)}/{len(rows)}")

    lines.append("")
    return "\n".join(lines)


def _render_with_glow(markdown: str) -> None:
    glow = shutil.which("glow")
    if glow is None:
        sys.stdout.write(markdown)
        return
    subprocess.run([glow, "-"], input=markdown, text=True, check=False)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run a live health check for paper-search-mcp `search_*` tools and render a Chinese Markdown report. "
            "This command performs real network calls and may be flaky due to upstream rate limits."
        )
    )
    parser.add_argument(
        "--repo-root",
        default=str(DEFAULT_REPO_ROOT),
        help="Repo root directory (default: auto-detected).",
    )
    parser.add_argument(
        "--server-command",
        default="uv",
        help="Command used to start the MCP server (default: uv).",
    )
    parser.add_argument(
        "--server-args",
        nargs="+",
        default=["run", "-m", "paper_search_mcp.server"],
        help="Args used to start the MCP server (default: run -m paper_search_mcp.server).",
    )
    parser.add_argument(
        "--query",
        default="transformer",
        help="Fallback query for unknown search tools (default: transformer).",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=2,
        help="Fallback max_results for unknown search tools (default: 2).",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="Per-tool call timeout in seconds (default: 30).",
    )
    parser.add_argument(
        "--timeout-biorxiv",
        type=float,
        default=90.0,
        help="Call timeout for bioRxiv search in seconds (default: 90).",
    )
    parser.add_argument(
        "--no-preflight",
        action="store_true",
        help="Skip upstream preflight HTTP checks.",
    )
    parser.add_argument(
        "--preflight-timeout",
        type=float,
        default=10.0,
        help="Preflight HTTP timeout in seconds (default: 10).",
    )
    output = parser.add_mutually_exclusive_group()
    output.add_argument(
        "--raw",
        action="store_true",
        help="Print raw Markdown instead of rendering with glow.",
    )
    output.add_argument(
        "--json",
        action="store_true",
        help="Emit raw JSON results (no Markdown/glow).",
    )
    parser.add_argument(
        "--output-md",
        help="Optional path to write the Markdown report to disk.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero if any tool check fails.",
    )
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    if not repo_root.exists():
        parser.error(f"--repo-root does not exist: {repo_root}")
    if not repo_root.is_dir():
        parser.error(f"--repo-root must be a directory: {repo_root}")
    args.repo_root = str(repo_root)

    if (
        Path(args.server_command).name == args.server_command
        and shutil.which(args.server_command) is None
    ):
        parser.error(f"--server-command not found on PATH: {args.server_command}")

    if args.max_results < 1:
        parser.error("--max-results must be >= 1")
    if args.timeout <= 0:
        parser.error("--timeout must be > 0")
    if args.timeout_biorxiv <= 0:
        parser.error("--timeout-biorxiv must be > 0")
    if args.preflight_timeout <= 0:
        parser.error("--preflight-timeout must be > 0")

    try:
        started_at, rows = asyncio.run(_run_checks(args))
    except FileNotFoundError as exc:
        print(f"Failed to start MCP server process: {exc}", file=sys.stderr)
        print(
            "Hint: verify `--server-command/--server-args` (default: `uv run -m paper_search_mcp.server`).",
            file=sys.stderr,
        )
        return 2
    except Exception as exc:  # noqa: BLE001
        print(f"Health check failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    if args.json:
        payload = {
            "started_at": started_at,
            "results": [row.__dict__ for row in rows],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        failed = any(not row.ok for row in rows)
        return 1 if args.strict and failed else 0

    markdown = _build_markdown(started_at, rows)
    if args.output_md:
        Path(args.output_md).write_text(markdown, encoding="utf-8")

    if args.raw:
        sys.stdout.write(markdown)
    else:
        if sys.stdout.isatty():
            _render_with_glow(markdown)
        else:
            sys.stdout.write(markdown)

    failed = any(not row.ok for row in rows)
    return 1 if args.strict and failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
