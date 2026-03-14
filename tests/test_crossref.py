import os
import unittest
from unittest import mock

import requests

from paper_search_mcp.academic_platforms.crossref import CrossRefSearcher
from tests._offline import OfflineTestCase, read_fixture_json


LIVE_TESTS_ENABLED = os.getenv("PAPER_SEARCH_LIVE_TESTS") == "1"


def check_api_accessible():
    try:
        response = requests.get("https://api.crossref.org/works?sample=1", timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False


class TestCrossRefSearcher(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.api_accessible = LIVE_TESTS_ENABLED and check_api_accessible()

    def setUp(self):
        self.searcher = CrossRefSearcher()

    def _require_live_access(self):
        if not LIVE_TESTS_ENABLED:
            self.skipTest("Set PAPER_SEARCH_LIVE_TESTS=1 to run live CrossRef tests")
        if not self.api_accessible:
            self.skipTest("CrossRef API is not accessible")

    def test_search(self):
        self._require_live_access()
        papers = self.searcher.search("machine learning", max_results=5)
        self.assertTrue(len(papers) > 0)
        self.assertTrue(papers[0].title)

    def test_search_with_filters(self):
        self._require_live_access()
        papers = self.searcher.search(
            "artificial intelligence",
            max_results=3,
            filter="from-pub-date:2020,has-full-text:true",
        )
        self.assertGreaterEqual(len(papers), 0)

    def test_get_paper_by_doi(self):
        self._require_live_access()
        paper = self.searcher.get_paper_by_doi("10.1038/nature12373")
        if paper is not None:
            self.assertEqual(paper.doi, "10.1038/nature12373")
            self.assertTrue(paper.title)

    def test_get_paper_by_invalid_doi(self):
        self._require_live_access()
        paper = self.searcher.get_paper_by_doi("10.1234/invalid.doi.123456789")
        self.assertIsNone(paper)

    def test_download_pdf_not_supported(self):
        with self.assertRaises(NotImplementedError):
            self.searcher.download_pdf("10.1038/nature12373", "./downloads")

    def test_read_paper_not_supported(self):
        message = self.searcher.read_paper("10.1038/nature12373")
        self.assertIn("CrossRef papers cannot be read directly", message)
        self.assertIn("metadata and abstracts are available", message)

    def test_user_agent_header(self):
        self.assertIn("paper-search-mcp", self.searcher.session.headers.get("User-Agent", ""))
        self.assertIn("mailto:", self.searcher.session.headers.get("User-Agent", ""))


class TestCrossRefSearcherOffline(OfflineTestCase):
    def test_search_offline_fixture(self):
        searcher = CrossRefSearcher()
        response = mock.Mock()
        response.raise_for_status = mock.Mock()
        response.json.return_value = read_fixture_json("crossref", "works_search.json")

        with mock.patch(
            "paper_search_mcp.academic_platforms.crossref.request_with_retries",
            return_value=response,
        ) as mock_request:
            papers = searcher.search("threshold cryptography", max_results=2)

        self.assertEqual(mock_request.call_count, 1)
        self.assertEqual(len(papers), 2)

        first = papers[0]
        self.assertEqual(first.source, "crossref")
        self.assertEqual(first.paper_id, "10.1000/crossref.one")
        self.assertEqual(first.doi, "10.1000/crossref.one")
        self.assertEqual(first.title, "Offline CrossRef Paper One")
        self.assertEqual(first.authors, ["Alice Doe", "Bob Smith"])
        self.assertEqual(first.categories, ["journal-article"])

        serialized = first.to_dict()
        for key in [
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
        ]:
            self.assertIn(key, serialized)
        self.assertEqual(serialized["source"], "crossref")

    def test_search_returns_empty_list_for_no_hit_response(self):
        searcher = CrossRefSearcher()
        response = mock.Mock()
        response.raise_for_status = mock.Mock()
        response.json.return_value = {"message": {"items": []}}

        with mock.patch(
            "paper_search_mcp.academic_platforms.crossref.request_with_retries",
            return_value=response,
        ):
            papers = searcher.search("no such paper", max_results=2)

        self.assertEqual(papers, [])

    def test_search_propagates_transport_failures(self):
        searcher = CrossRefSearcher()

        with mock.patch(
            "paper_search_mcp.academic_platforms.crossref.request_with_retries",
            side_effect=requests.RequestException("crossref unavailable"),
        ):
            with self.assertRaisesRegex(requests.RequestException, "crossref unavailable"):
                searcher.search("network failure", max_results=2)

    def test_extract_date_normalizes_partial_or_zero_month_day(self):
        searcher = CrossRefSearcher()

        published = searcher._extract_date(
            {"published": {"date-parts": [[2024, 0, 0]]}},
            "published",
        )
        issued = searcher._extract_date(
            {"issued": {"date-parts": [[2023, 2, 31]]}},
            "issued",
        )

        self.assertEqual(published, searcher._extract_date({"published": {"date-parts": [[2024]]}}, "published"))
        self.assertEqual(published, searcher._extract_date({"published": {"date-parts": [["2024", "0"]]}}, "published"))
        self.assertEqual(published.year, 2024)
        self.assertEqual(published.month, 1)
        self.assertEqual(published.day, 1)
        self.assertEqual(issued, searcher._extract_date({"issued": {"date-parts": [[2023, 2, 28]]}}, "issued"))


if __name__ == "__main__":
    unittest.main()
