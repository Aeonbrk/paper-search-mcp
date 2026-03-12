import os
import unittest

import requests

from paper_search_mcp.academic_platforms.crossref import CrossRefSearcher


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


if __name__ == "__main__":
    unittest.main()
