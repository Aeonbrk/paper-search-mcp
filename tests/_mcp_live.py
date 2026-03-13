from __future__ import annotations

from collections.abc import AsyncIterator, Iterable, Mapping, Sequence
from contextlib import asynccontextmanager
import json
from os import PathLike
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import CallToolResult, TextContent
import requests


REPO_ROOT = Path(__file__).resolve().parents[1]
DOWNLOADS_ROOT = (REPO_ROOT / "docs" / "downloads").resolve()
LIMITATION_PREFIX = "LIMITATION: "
SERVER_COMMAND = "uv"
SERVER_ARGS = ["run", "-m", "paper_search_mcp.server"]


@asynccontextmanager
async def open_live_mcp_session() -> AsyncIterator[ClientSession]:
    server = StdioServerParameters(
        command=SERVER_COMMAND,
        args=SERVER_ARGS,
        cwd=str(REPO_ROOT),
    )
    async with stdio_client(server) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            yield session


def preflight_http(
    url: str,
    *,
    timeout: float = 5.0,
    headers: Mapping[str, str] | None = None,
    expected_statuses: Sequence[int] = (200,),
) -> bool:
    try:
        response = requests.get(
            url,
            headers=dict(headers) if headers is not None else None,
            timeout=timeout,
        )
    except requests.RequestException:
        return False

    return response.status_code in set(expected_statuses)


def tool_result_text(result: CallToolResult) -> str:
    texts: list[str] = []
    for item in result.content:
        if not isinstance(item, TextContent):
            raise AssertionError(f"Expected text content, got {type(item).__name__}")
        texts.append(item.text)

    if not texts:
        raise AssertionError("Expected at least one TextContent block")

    return "\n".join(texts)


def parse_json_text(text: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise AssertionError(f"Expected JSON tool result, got: {text!r}") from exc


def parse_json_tool_result(result: CallToolResult) -> Any:
    return parse_json_text(tool_result_text(result))


def parse_limitation_text(text: str) -> dict[str, Any]:
    if not text.startswith(LIMITATION_PREFIX):
        raise AssertionError(f"Expected limitation result with prefix {LIMITATION_PREFIX!r}")

    payload = parse_json_text(text[len(LIMITATION_PREFIX):])
    if not isinstance(payload, dict):
        raise AssertionError("Expected limitation payload to decode to a JSON object")

    return payload


def parse_limitation_tool_result(result: CallToolResult) -> dict[str, Any]:
    return parse_limitation_text(tool_result_text(result))


def cleanup_download_file(path: str | PathLike[str]) -> bool:
    resolved = _resolve_download_file(path)
    if not resolved.exists():
        return False
    if not resolved.is_file():
        raise ValueError(f"Cleanup target is not a file: {resolved}")

    resolved.unlink()
    _prune_empty_download_dirs(resolved.parent)
    return True


def cleanup_download_files(paths: Iterable[str | PathLike[str]]) -> list[Path]:
    removed: list[Path] = []
    for path in paths:
        resolved = _resolve_download_file(path)
        if not resolved.exists():
            continue
        if cleanup_download_file(resolved):
            removed.append(resolved)
    return removed


def _resolve_download_file(path: str | PathLike[str]) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = (REPO_ROOT / candidate).resolve()
    else:
        candidate = candidate.resolve()

    if candidate == DOWNLOADS_ROOT or DOWNLOADS_ROOT not in candidate.parents:
        raise ValueError(f"Cleanup path must stay under {DOWNLOADS_ROOT}: {candidate}")

    return candidate


def _prune_empty_download_dirs(start: Path) -> None:
    current = start
    while current != DOWNLOADS_ROOT and DOWNLOADS_ROOT in current.parents:
        try:
            current.rmdir()
        except OSError:
            return
        current = current.parent


__all__ = [
    "DOWNLOADS_ROOT",
    "LIMITATION_PREFIX",
    "SERVER_ARGS",
    "SERVER_COMMAND",
    "cleanup_download_file",
    "cleanup_download_files",
    "open_live_mcp_session",
    "parse_json_text",
    "parse_json_tool_result",
    "parse_limitation_text",
    "parse_limitation_tool_result",
    "preflight_http",
    "tool_result_text",
]
