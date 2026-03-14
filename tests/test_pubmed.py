import os
import unittest
from unittest import mock

import requests

from paper_search_mcp.academic_platforms.pubmed import PubMedSearcher
from tests._offline import OfflineTestCase, read_fixture_text


LIVE_TESTS_ENABLED = os.getenv("PAPER_SEARCH_LIVE_TESTS") == "1"


class TestPubMedSearcher(unittest.TestCase):
    def setUp(self):
        self.searcher = PubMedSearcher()

    def test_search(self):
        if not LIVE_TESTS_ENABLED:
            self.skipTest("Set PAPER_SEARCH_LIVE_TESTS=1 to run live PubMed tests")

        papers = self.searcher.search("machine learning", max_results=10)
        self.assertEqual(len(papers), 10)
        self.assertTrue(papers[0].title)

    def test_pdf_unsupported(self):
        with self.assertRaises(NotImplementedError):
            self.searcher.download_pdf("12345678", "./downloads")

    def test_read_paper_message(self):
        message = self.searcher.read_paper("12345678")
        self.assertIn("PubMed papers cannot be read directly", message)


class TestPubMedSearcherOffline(OfflineTestCase):
    def test_search_offline_fixture(self):
        searcher = PubMedSearcher()

        search_response = mock.Mock()
        search_response.content = read_fixture_text("pubmed", "esearch.xml").encode("utf-8")
        search_response.raise_for_status = mock.Mock()

        fetch_response = mock.Mock()
        fetch_response.content = read_fixture_text("pubmed", "efetch.xml").encode("utf-8")
        fetch_response.raise_for_status = mock.Mock()

        with mock.patch(
            "paper_search_mcp.academic_platforms.pubmed.request_with_retries",
            side_effect=[search_response, fetch_response],
        ) as mock_request:
            papers = searcher.search("secret sharing", max_results=2)

        self.assertEqual(mock_request.call_count, 2)
        mock_request.assert_any_call(
            searcher.session,
            "GET",
            searcher.SEARCH_URL,
            params={
                "db": "pubmed",
                "term": "secret sharing",
                "retmax": 2,
                "retmode": "xml",
            },
            timeout=searcher.timeout,
        )
        mock_request.assert_any_call(
            searcher.session,
            "GET",
            searcher.FETCH_URL,
            params={
                "db": "pubmed",
                "id": "12345678,87654321",
                "retmode": "xml",
            },
            timeout=searcher.timeout,
        )

        self.assertEqual(len(papers), 2)

        first = papers[0]
        self.assertEqual(first.paper_id, "12345678")
        self.assertEqual(first.title, "Offline PubMed Paper One")
        self.assertEqual(first.authors, ["Doe J", "Smith A"])
        self.assertEqual(first.abstract, "Deterministic fixture abstract for PubMed paper one.")
        self.assertEqual(first.source, "pubmed")
        self.assertEqual(first.doi, "10.1000/pubmed.one")
        self.assertEqual(first.url, "https://pubmed.ncbi.nlm.nih.gov/12345678/")

        second = papers[1]
        self.assertEqual(second.paper_id, "87654321")
        self.assertEqual(second.title, "Offline PubMed Paper Two")
        self.assertEqual(second.authors, ["Lee B"])
        self.assertEqual(second.doi, "")

        serialized = first.to_dict()
        self.assertEqual(serialized["paper_id"], "12345678")
        self.assertEqual(serialized["source"], "pubmed")
        self.assertEqual(serialized["doi"], "10.1000/pubmed.one")

    def test_search_returns_empty_list_for_transport_failure(self):
        searcher = PubMedSearcher()

        with mock.patch(
            "paper_search_mcp.academic_platforms.pubmed.request_with_retries",
            side_effect=requests.RequestException("pubmed unavailable"),
        ):
            papers = searcher.search("network fault", max_results=2)

        self.assertEqual(papers, [])


if __name__ == "__main__":
    unittest.main()
