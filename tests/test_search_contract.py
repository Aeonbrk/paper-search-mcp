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

    def _run_without_event_loop(self, coroutine):
        try:
            coroutine.send(None)
        except StopIteration as stop:
            return stop.value

        coroutine.close()
        self.fail("Coroutine yielded unexpectedly while offline")


if __name__ == "__main__":
    unittest.main()
