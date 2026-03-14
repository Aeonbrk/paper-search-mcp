from __future__ import annotations

import asyncio
from dataclasses import dataclass
import os
from pathlib import Path
import re
from typing import Any
import unittest

from mcp.types import CallToolResult, TextContent

from tests._mcp_live import (
    DOWNLOADS_ROOT,
    cleanup_download_file,
    open_live_mcp_session,
    parse_json_text,
    parse_limitation_tool_result,
    preflight_http,
    tool_result_text,
)


LIVE_TESTS_ENABLED = os.getenv("PAPER_SEARCH_LIVE_TESTS") == "1"
REPO_ROOT = Path(__file__).resolve().parents[1]
CAPABILITY_MATRIX_PATH = REPO_ROOT / "docs" / "project-specs" / "source-capability-matrix.md"

EXPECTED_TOOL_NAMES = {
    "search_arxiv",
    "search_pubmed",
    "search_biorxiv",
    "search_medrxiv",
    "search_google_scholar",
    "search_iacr",
    "download_arxiv",
    "download_pubmed",
    "download_biorxiv",
    "download_medrxiv",
    "download_iacr",
    "read_arxiv_paper",
    "read_pubmed_paper",
    "read_biorxiv_paper",
    "read_medrxiv_paper",
    "read_iacr_paper",
    "search_semantic",
    "download_semantic",
    "read_semantic_paper",
    "search_crossref",
    "search_pmc",
    "get_crossref_paper_by_doi",
    "download_crossref",
    "download_pmc",
    "read_crossref_paper",
    "read_pmc_paper",
}

NORMALIZED_PAPER_KEYS = {
    "paper_id",
    "title",
    "authors",
    "abstract",
    "doi",
    "published_date",
    "pdf_url",
    "url",
    "source",
    "updated_date",
    "categories",
    "keywords",
    "citations",
    "references",
    "extra",
}

SOURCE_LABEL_TO_ID = {
    "arXiv": "arxiv",
    "PubMed": "pubmed",
    "PMC": "pmc",
    "bioRxiv": "biorxiv",
    "medRxiv": "medrxiv",
    "Google Scholar": "google_scholar",
    "IACR ePrint Archive": "iacr",
    "Semantic Scholar": "semantic",
    "CrossRef": "crossref",
}

SEARCH_CASES = {
    "arxiv": {"query": "transformer", "max_results": 2},
    "pubmed": {"query": "transformer", "max_results": 2},
    "pmc": {"query": "transformer", "max_results": 2},
    "biorxiv": {"query": "transformer", "max_results": 2},
    "medrxiv": {"query": "covid", "max_results": 2},
    "google_scholar": {"query": "transformer", "max_results": 1},
    "iacr": {"query": "encryption", "max_results": 2},
    "semantic": {"query": "transformer", "max_results": 2},
    "crossref": {"query": "transformer", "max_results": 2},
}

NO_HIT_SEARCH_QUERY = "qzjxkvmrptnqlwyyhbcd20260314 vfsnkmptzqwyxrdh"
NO_HIT_SEARCH_CASES = {
    source_id: {"query": NO_HIT_SEARCH_QUERY, "max_results": 1}
    for source_id in (
        "arxiv",
        "pubmed",
        "pmc",
        "google_scholar",
        "iacr",
        "crossref",
    )
}

PREFLIGHT_CASES = {
    "arxiv": {
        "url": "http://export.arxiv.org/api/query?search_query=all:transformer&start=0&max_results=1",
    },
    "pubmed": {
        "url": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=transformer&retmax=1",
    },
    "pmc": {
        "url": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pmc&term=transformer&retmax=1",
    },
    "biorxiv": {
        "url": "https://api.biorxiv.org/details/biorxiv/2025-01-01/2025-01-02/0",
    },
    "medrxiv": {
        "url": "https://api.biorxiv.org/details/medrxiv/2025-01-01/2025-01-02/0",
    },
    "google_scholar": {
        "url": "https://scholar.google.com/scholar?q=transformer",
        "headers": {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/123.0.0.0 Safari/537.36"
            )
        },
    },
    "iacr": {
        "url": "https://eprint.iacr.org/search?q=encryption",
    },
    "semantic": {
        "url": "https://api.semanticscholar.org/graph/v1/paper/search?query=transformer&limit=1",
    },
    "crossref": {
        "url": "https://api.crossref.org/works?query=transformer&rows=1",
    },
}

FULLTEXT_FALLBACK_IDS = {
    "arxiv": "1706.03762",
    "semantic": "ARXIV:1706.03762",
}

LIMITATION_SOURCES = {"pmc"}
SEARCH_SOURCE_IDS = tuple(SEARCH_CASES)
FULLTEXT_SOURCE_IDS = ("arxiv", "biorxiv", "medrxiv", "iacr", "semantic")
NONFILE_UNSUPPORTED_SOURCE_IDS = ("pubmed", "crossref")
ZERO_HIT_SEARCH_SOURCE_IDS = tuple(NO_HIT_SEARCH_CASES)


@dataclass(frozen=True)
class SourceCapability:
    label: str
    source_id: str
    search: bool
    download: bool
    read: bool


SOURCE_CAPABILITIES: dict[str, SourceCapability] | None = None


def setUpModule() -> None:
    if not LIVE_TESTS_ENABLED:
        raise unittest.SkipTest("Set PAPER_SEARCH_LIVE_TESTS=1 to run live MCP smoke tests")
    _assert_capability_matrix_matches_expected()


def _load_source_capabilities() -> dict[str, SourceCapability]:
    pattern = re.compile(
        r"^- \*\*(?P<label>.+?)\*\* .*?search: (?P<search>yes|no); "
        r"download: (?P<download>yes|no); read: (?P<read>yes|no);"
    )
    capabilities: dict[str, SourceCapability] = {}
    for line in CAPABILITY_MATRIX_PATH.read_text(encoding="utf-8").splitlines():
        match = pattern.match(line)
        if match is None:
            continue
        label = match.group("label")
        source_id = SOURCE_LABEL_TO_ID.get(label)
        if source_id is None:
            continue
        capabilities[source_id] = SourceCapability(
            label=label,
            source_id=source_id,
            search=match.group("search") == "yes",
            download=match.group("download") == "yes",
            read=match.group("read") == "yes",
        )

    missing_sources = set(SOURCE_LABEL_TO_ID.values()) - set(capabilities)
    if missing_sources:
        raise RuntimeError(
            f"Failed to parse source capabilities for: {sorted(missing_sources)}"
        )
    return capabilities


def _get_source_capabilities() -> dict[str, SourceCapability]:
    global SOURCE_CAPABILITIES
    if SOURCE_CAPABILITIES is None:
        SOURCE_CAPABILITIES = _load_source_capabilities()
    return SOURCE_CAPABILITIES


def _assert_capability_matrix_matches_expected() -> None:
    capabilities = _get_source_capabilities()
    search_sources = {
        source_id for source_id, capability in capabilities.items() if capability.search
    }
    fulltext_sources = {
        source_id
        for source_id, capability in capabilities.items()
        if capability.download and capability.read
    }
    unsupported_sources = {
        source_id
        for source_id, capability in capabilities.items()
        if not capability.download
        and not capability.read
        and source_id not in LIMITATION_SOURCES
        and {f"download_{source_id}", f"read_{source_id}_paper"} <= EXPECTED_TOOL_NAMES
    }

    if search_sources != set(SEARCH_SOURCE_IDS):
        raise RuntimeError(
            "Live search test source set drifted from the capability matrix: "
            f"expected {sorted(SEARCH_SOURCE_IDS)}, got {sorted(search_sources)}"
        )
    if fulltext_sources != set(FULLTEXT_SOURCE_IDS):
        raise RuntimeError(
            "Live full-text test source set drifted from the capability matrix: "
            f"expected {sorted(FULLTEXT_SOURCE_IDS)}, got {sorted(fulltext_sources)}"
        )
    if unsupported_sources != set(NONFILE_UNSUPPORTED_SOURCE_IDS):
        raise RuntimeError(
            "Live unsupported-source set drifted from the capability matrix: "
            f"expected {sorted(NONFILE_UNSUPPORTED_SOURCE_IDS)}, "
            f"got {sorted(unsupported_sources)}"
        )


def _snapshot_downloads() -> set[Path]:
    if not DOWNLOADS_ROOT.exists():
        return set()
    return {path.resolve() for path in DOWNLOADS_ROOT.rglob("*") if path.is_file()}


def _tool_name(prefix: str, source_id: str) -> str:
    if prefix == "read":
        return f"read_{source_id}_paper"
    return f"{prefix}_{source_id}"


def _download_path_from_text(text: str) -> Path | None:
    candidate_text = text.strip()
    if not candidate_text or candidate_text.startswith("LIMITATION:"):
        return None
    candidate = Path(candidate_text)
    if not candidate.is_absolute():
        return None
    resolved = candidate.resolve()
    if DOWNLOADS_ROOT not in resolved.parents:
        return None
    return resolved


def _json_items(result: CallToolResult) -> list[dict[str, Any]]:
    if result.isError:
        raise AssertionError(f"Tool returned protocol error: {result}")
    if not result.content:
        raise AssertionError("Expected at least one content block")

    papers: list[dict[str, Any]] = []
    for item in result.content:
        if not isinstance(item, TextContent):
            raise AssertionError(f"Expected text content, got {type(item).__name__}")
        payload = parse_json_text(item.text)
        if not isinstance(payload, dict):
            raise AssertionError("Expected at least one JSON object payload")
        papers.append(payload)
    if not papers:
        raise AssertionError("Expected at least one JSON object payload")
    return papers


def _search_items(result: CallToolResult) -> list[dict[str, Any]]:
    if result.isError:
        raise AssertionError(f"Tool returned protocol error: {result}")
    if not result.content:
        return []

    papers: list[dict[str, Any]] = []
    for item in result.content:
        if not isinstance(item, TextContent):
            raise AssertionError(f"Expected text content, got {type(item).__name__}")
        payload = parse_json_text(item.text)
        if isinstance(payload, dict):
            papers.append(payload)
            continue
        if isinstance(payload, list):
            if not all(isinstance(paper, dict) for paper in payload):
                raise AssertionError("Expected JSON object payloads")
            papers.extend(payload)
            continue
        raise AssertionError("Expected JSON object or list payload")
    return papers


class TestPaperSearchServerLive(unittest.TestCase):
    maxDiff = None
    _availability_cache: dict[str, bool] = {}

    @classmethod
    def _source_is_available(cls, source_id: str) -> bool:
        if source_id not in cls._availability_cache:
            preflight = PREFLIGHT_CASES[source_id]
            cls._availability_cache[source_id] = preflight_http(
                preflight["url"],
                headers=preflight.get("headers"),
            )
        return cls._availability_cache[source_id]

    def _require_source(self, source_id: str) -> None:
        if not self._source_is_available(source_id):
            self.skipTest(f"{source_id} upstream preflight is unavailable")

    def _assert_paper(self, paper: dict[str, Any], *, source_id: str) -> None:
        self.assertTrue(
            NORMALIZED_PAPER_KEYS <= set(paper),
            f"Missing normalized paper keys for {source_id}: {paper}",
        )
        self.assertEqual(paper["source"], source_id)
        self.assertTrue(paper["paper_id"], paper)
        self.assertIsInstance(paper["title"], str)
        self.assertIsInstance(paper["authors"], str)
        self.assertIn("source", paper)

    def _run(self, coroutine: Any) -> Any:
        return asyncio.run(coroutine)

    async def _search_papers(
        self,
        session: Any,
        source_id: str,
    ) -> list[dict[str, Any]]:
        result = await session.call_tool(_tool_name("search", source_id), SEARCH_CASES[source_id])
        papers = _search_items(result)
        self.assertTrue(papers, f"{source_id} search returned no papers")
        for paper in papers:
            self._assert_paper(paper, source_id=source_id)
        return papers

    async def _assert_no_hit_search(
        self,
        session: Any,
        source_id: str,
    ) -> None:
        result = await session.call_tool(
            _tool_name("search", source_id),
            NO_HIT_SEARCH_CASES[source_id],
        )
        papers = _search_items(result)
        self.assertEqual(papers, [], f"{source_id} no-hit query returned unexpected papers")

    def _pick_paper_id(self, source_id: str, papers: list[dict[str, Any]], *, require_pdf: bool) -> str:
        for paper in papers:
            if not paper.get("paper_id"):
                continue
            if require_pdf and not paper.get("pdf_url"):
                continue
            return str(paper["paper_id"])

        fallback_id = FULLTEXT_FALLBACK_IDS.get(source_id)
        if fallback_id is not None:
            return fallback_id
        self.skipTest(f"{source_id} search did not return a suitable paper id")

    def test_initialize_and_list_tools_over_stdio(self) -> None:
        async def run() -> None:
            async with open_live_mcp_session() as session:
                response = await session.list_tools()
                tool_names = {tool.name for tool in response.tools}
                self.assertEqual(tool_names, EXPECTED_TOOL_NAMES)

        self._run(run())

    def test_crossref_lookup_uses_live_doi(self) -> None:
        self._require_source("crossref")

        async def run() -> None:
            async with open_live_mcp_session() as session:
                papers = await self._search_papers(session, "crossref")
                doi = next((paper.get("doi") for paper in papers if paper.get("doi")), None)
                self.assertIsNotNone(doi, "crossref search returned no DOI values")
                assert doi is not None
                result = await session.call_tool("get_crossref_paper_by_doi", {"doi": doi})
                payload = _json_items(result)
                self.assertEqual(len(payload), 1)
                self._assert_paper(payload[0], source_id="crossref")
                self.assertEqual(payload[0]["doi"], doi)

        self._run(run())

    def test_pmc_limitation_tools_return_structured_payloads(self) -> None:
        self._require_source("pmc")

        async def run() -> None:
            before = _snapshot_downloads()
            async with open_live_mcp_session() as session:
                papers = await self._search_papers(session, "pmc")
                paper_id = self._pick_paper_id("pmc", papers, require_pdf=False)

                download_result = await session.call_tool("download_pmc", {"paper_id": paper_id})
                read_result = await session.call_tool("read_pmc_paper", {"paper_id": paper_id})

                self.assertFalse(download_result.isError, download_result)
                self.assertFalse(read_result.isError, read_result)

                download_payload = parse_limitation_tool_result(download_result)
                read_payload = parse_limitation_tool_result(read_result)

                self.assertEqual(download_payload["type"], "limitation")
                self.assertEqual(download_payload["tool"], "download_pmc")
                self.assertEqual(download_payload["capability"], "download")
                self.assertFalse(download_payload["supported"])
                self.assertEqual(download_payload["source"], "pmc")
                self.assertEqual(download_payload["paper_id"], paper_id)

                self.assertEqual(read_payload["type"], "limitation")
                self.assertEqual(read_payload["tool"], "read_pmc_paper")
                self.assertEqual(read_payload["capability"], "read")
                self.assertFalse(read_payload["supported"])
                self.assertEqual(read_payload["source"], "pmc")
                self.assertEqual(read_payload["paper_id"], paper_id)

            self.assertSetEqual(_snapshot_downloads(), before)

        self._run(run())


def _make_search_test(source_id: str):
    def test(self: TestPaperSearchServerLive) -> None:
        self._require_source(source_id)

        async def run() -> None:
            async with open_live_mcp_session() as session:
                await self._search_papers(session, source_id)

        self._run(run())

    test.__name__ = f"test_search_{source_id}_returns_normalized_json"
    return test


def _make_zero_hit_search_test(source_id: str):
    def test(self: TestPaperSearchServerLive) -> None:
        self._require_source(source_id)

        async def run() -> None:
            async with open_live_mcp_session() as session:
                await self._assert_no_hit_search(session, source_id)

        self._run(run())

    test.__name__ = f"test_search_{source_id}_returns_empty_result_for_no_hit_query"
    return test


def _make_fulltext_test(source_id: str):
    def test(self: TestPaperSearchServerLive) -> None:
        self._require_source(source_id)

        async def run() -> None:
            before = _snapshot_downloads()
            download_path: Path | None = None
            try:
                async with open_live_mcp_session() as session:
                    papers = await self._search_papers(session, source_id)
                    paper_id = self._pick_paper_id(source_id, papers, require_pdf=True)

                    download_result = await session.call_tool(
                        _tool_name("download", source_id),
                        {"paper_id": paper_id},
                    )
                    self.assertFalse(download_result.isError, download_result)
                    self.assertTrue(download_result.content, f"{source_id} download returned no content")
                    download_text = tool_result_text(download_result).strip()
                    self.assertFalse(
                        download_text.startswith("Error"),
                        f"{source_id} download returned error text: {download_text}",
                    )
                    download_path = _download_path_from_text(download_text)
                    self.assertIsNotNone(download_path, download_text)
                    assert download_path is not None
                    self.assertTrue(download_path.exists(), download_path)

                    read_result = await session.call_tool(
                        _tool_name("read", source_id),
                        {"paper_id": paper_id},
                    )
                    self.assertFalse(read_result.isError, read_result)
                    self.assertTrue(read_result.content, f"{source_id} read returned no content")
                    read_text = tool_result_text(read_result).strip()
                    self.assertTrue(read_text, f"{source_id} read returned empty text")
                    self.assertFalse(
                        read_text.startswith("Error"),
                        f"{source_id} read returned error text: {read_text}",
                    )

                after = _snapshot_downloads()
                self.assertSetEqual(after - before, {download_path})
            finally:
                if download_path is not None and download_path.exists():
                    self.assertTrue(cleanup_download_file(download_path))
                self.assertSetEqual(_snapshot_downloads(), before)

        self._run(run())

    test.__name__ = f"test_{source_id}_download_and_read_over_stdio"
    return test


def _make_unsupported_test(source_id: str):
    def test(self: TestPaperSearchServerLive) -> None:
        self._require_source(source_id)

        async def run() -> None:
            before = _snapshot_downloads()
            async with open_live_mcp_session() as session:
                papers = await self._search_papers(session, source_id)
                paper_id = self._pick_paper_id(source_id, papers, require_pdf=False)

                download_result = await session.call_tool(
                    _tool_name("download", source_id),
                    {"paper_id": paper_id},
                )
                read_result = await session.call_tool(
                    _tool_name("read", source_id),
                    {"paper_id": paper_id},
                )

                self.assertFalse(download_result.isError, download_result)
                self.assertFalse(read_result.isError, read_result)

                download_text = tool_result_text(download_result).strip()
                read_text = tool_result_text(read_result).strip()

                self.assertIsNone(_download_path_from_text(download_text), download_text)
                self.assertIsNone(_download_path_from_text(read_text), read_text)
                self.assertTrue(download_text)
                self.assertTrue(read_text)

            self.assertSetEqual(_snapshot_downloads(), before)

        self._run(run())

    test.__name__ = f"test_{source_id}_unsupported_download_and_read_leave_downloads_unchanged"
    return test


for _source_id in SEARCH_SOURCE_IDS:
    setattr(
        TestPaperSearchServerLive,
        f"test_search_{_source_id}_returns_normalized_json",
        _make_search_test(_source_id),
    )

for _source_id in ZERO_HIT_SEARCH_SOURCE_IDS:
    setattr(
        TestPaperSearchServerLive,
        f"test_search_{_source_id}_returns_empty_result_for_no_hit_query",
        _make_zero_hit_search_test(_source_id),
    )

for _source_id in FULLTEXT_SOURCE_IDS:
    setattr(
        TestPaperSearchServerLive,
        f"test_{_source_id}_download_and_read_over_stdio",
        _make_fulltext_test(_source_id),
    )

for _source_id in NONFILE_UNSUPPORTED_SOURCE_IDS:
    setattr(
        TestPaperSearchServerLive,
        f"test_{_source_id}_unsupported_download_and_read_leave_downloads_unchanged",
        _make_unsupported_test(_source_id),
    )


if __name__ == "__main__":
    unittest.main()
