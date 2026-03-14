import unittest
from unittest import mock

from paper_search_mcp import server
from tests._offline import OfflineTestCase


NON_SEMANTIC_SEARCH_CASES = (
    {
        "tool_name": "search_arxiv",
        "searcher_attr": "ArxivSearcher",
        "call_kwargs": {},
        "expected_args": ("no hits expected",),
        "expected_kwargs": {"max_results": 3},
    },
    {
        "tool_name": "search_pubmed",
        "searcher_attr": "PubMedSearcher",
        "call_kwargs": {},
        "expected_args": ("no hits expected",),
        "expected_kwargs": {"max_results": 3},
    },
    {
        "tool_name": "search_pmc",
        "searcher_attr": "PMCSearcher",
        "call_kwargs": {},
        "expected_args": ("no hits expected",),
        "expected_kwargs": {"max_results": 3},
    },
    {
        "tool_name": "search_biorxiv",
        "searcher_attr": "BioRxivSearcher",
        "call_kwargs": {},
        "expected_args": ("no hits expected",),
        "expected_kwargs": {"max_results": 3},
    },
    {
        "tool_name": "search_medrxiv",
        "searcher_attr": "MedRxivSearcher",
        "call_kwargs": {},
        "expected_args": ("no hits expected",),
        "expected_kwargs": {"max_results": 3},
    },
    {
        "tool_name": "search_google_scholar",
        "searcher_attr": "GoogleScholarSearcher",
        "call_kwargs": {},
        "expected_args": ("no hits expected",),
        "expected_kwargs": {"max_results": 3},
    },
    {
        "tool_name": "search_iacr",
        "searcher_attr": "IACRSearcher",
        "call_kwargs": {"fetch_details": False},
        "expected_args": ("no hits expected", 3, False),
        "expected_kwargs": {},
    },
    {
        "tool_name": "search_crossref",
        "searcher_attr": "CrossRefSearcher",
        "call_kwargs": {
            "filter": "from-pub-date:2020",
            "sort": "published",
            "order": "desc",
        },
        "expected_args": ("no hits expected",),
        "expected_kwargs": {
            "max_results": 3,
            "filter": "from-pub-date:2020",
            "sort": "published",
            "order": "desc",
        },
    },
)

READ_PROPAGATION_CASES = (
    {
        "tool_name": "read_arxiv_paper",
        "searcher_attr": "ArxivSearcher",
    },
    {
        "tool_name": "read_biorxiv_paper",
        "searcher_attr": "BioRxivSearcher",
    },
    {
        "tool_name": "read_medrxiv_paper",
        "searcher_attr": "MedRxivSearcher",
    },
    {
        "tool_name": "read_iacr_paper",
        "searcher_attr": "IACRSearcher",
    },
    {
        "tool_name": "read_semantic_paper",
        "searcher_attr": "SemanticSearcher",
    },
)

UNSUPPORTED_DOWNLOAD_CASES = (
    {
        "tool_name": "download_pubmed",
        "searcher_attr": "PubMedSearcher",
        "message": "PubMed download unsupported",
    },
    {
        "tool_name": "download_crossref",
        "searcher_attr": "CrossRefSearcher",
        "message": "CrossRef download unsupported",
    },
)

SUPPORTED_DOWNLOAD_PROPAGATION_CASES = (
    {
        "tool_name": "download_arxiv",
        "searcher_attr": "ArxivSearcher",
    },
    {
        "tool_name": "download_biorxiv",
        "searcher_attr": "BioRxivSearcher",
    },
    {
        "tool_name": "download_medrxiv",
        "searcher_attr": "MedRxivSearcher",
    },
    {
        "tool_name": "download_iacr",
        "searcher_attr": "IACRSearcher",
    },
    {
        "tool_name": "download_semantic",
        "searcher_attr": "SemanticSearcher",
    },
)


async def _immediate_run(callable_, /, *args, **kwargs):
    return callable_(*args, **kwargs)


class TestSearchContract(OfflineTestCase):
    def test_nonsemantic_search_tools_return_empty_lists_for_no_hit_queries(self):
        for case in NON_SEMANTIC_SEARCH_CASES:
            calls = []

            class NoHitSearcher:
                def search(self, *args, **kwargs):
                    calls.append((args, kwargs))
                    return []

            tool = getattr(server, case["tool_name"])

            with self.subTest(tool=case["tool_name"]):
                with (
                    mock.patch.object(server, case["searcher_attr"], NoHitSearcher),
                    mock.patch("paper_search_mcp.server._run_sync", new=_immediate_run),
                ):
                    result = self._run_without_event_loop(
                        tool(query="no hits expected", max_results=3, **case["call_kwargs"])
                    )

                self.assertEqual(result, [])
                self.assertEqual(calls, [(case["expected_args"], case["expected_kwargs"])])

    def test_search_crossref_propagates_transport_failures(self):
        class TransportFailureSearcher:
            def search(self, *args, **kwargs):
                raise RuntimeError("transport unavailable")

        with (
            mock.patch.object(server, "CrossRefSearcher", TransportFailureSearcher),
            mock.patch("paper_search_mcp.server._run_sync", new=_immediate_run),
        ):
            with self.assertRaisesRegex(RuntimeError, "transport unavailable"):
                self._run_without_event_loop(
                    server.search_crossref(query="network fault", max_results=2)
                )

    def test_search_pubmed_propagates_rate_limit_failures(self):
        class RateLimitedSearcher:
            def search(self, *args, **kwargs):
                raise RuntimeError("429 Too Many Requests")

        with (
            mock.patch.object(server, "PubMedSearcher", RateLimitedSearcher),
            mock.patch("paper_search_mcp.server._run_sync", new=_immediate_run),
        ):
            with self.assertRaisesRegex(RuntimeError, "429 Too Many Requests"):
                self._run_without_event_loop(
                    server.search_pubmed(query="rate limited", max_results=2)
                )

    def test_supported_read_tools_propagate_runtime_failures(self):
        for case in READ_PROPAGATION_CASES:
            class BrokenReader:
                def read_paper(self, *args, **kwargs):
                    raise RuntimeError("paper read failed")

            tool = getattr(server, case["tool_name"])

            with self.subTest(tool=case["tool_name"]):
                with (
                    mock.patch.object(server, case["searcher_attr"], BrokenReader),
                    mock.patch("paper_search_mcp.server._run_sync", new=_immediate_run),
                ):
                    with self.assertRaisesRegex(RuntimeError, "paper read failed"):
                        self._run_without_event_loop(
                            tool(paper_id="paper-id", save_path="./downloads")
                        )

    def test_unsupported_download_tools_return_limitation_messages(self):
        for case in UNSUPPORTED_DOWNLOAD_CASES:
            class UnsupportedDownloader:
                def download_pdf(self, *args, **kwargs):
                    raise NotImplementedError(case["message"])

            tool = getattr(server, case["tool_name"])

            with self.subTest(tool=case["tool_name"]):
                with (
                    mock.patch.object(server, case["searcher_attr"], UnsupportedDownloader),
                    mock.patch("paper_search_mcp.server._run_sync", new=_immediate_run),
                ):
                    result = self._run_without_event_loop(
                        tool(paper_id="paper-id", save_path="./downloads")
                    )

                self.assertEqual(result, case["message"])

    def test_supported_download_tools_propagate_runtime_failures(self):
        for case in SUPPORTED_DOWNLOAD_PROPAGATION_CASES:
            class BrokenDownloader:
                def download_pdf(self, *args, **kwargs):
                    raise RuntimeError("paper download failed")

            tool = getattr(server, case["tool_name"])

            with self.subTest(tool=case["tool_name"]):
                with (
                    mock.patch.object(server, case["searcher_attr"], BrokenDownloader),
                    mock.patch("paper_search_mcp.server._run_sync", new=_immediate_run),
                ):
                    with self.assertRaisesRegex(RuntimeError, "paper download failed"):
                        self._run_without_event_loop(
                            tool(paper_id="paper-id", save_path="./downloads")
                        )

    def _run_without_event_loop(self, coroutine):
        try:
            coroutine.send(None)
        except StopIteration as stop:
            return stop.value

        coroutine.close()
        self.fail("Coroutine yielded unexpectedly while offline")


if __name__ == "__main__":
    unittest.main()
