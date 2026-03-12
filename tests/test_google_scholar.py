import os
import unittest

import requests

from paper_search_mcp.academic_platforms.google_scholar import GoogleScholarSearcher


LIVE_TESTS_ENABLED = os.getenv("PAPER_SEARCH_LIVE_TESTS") == "1"


def check_scholar_accessible():
    try:
        response = requests.get("https://scholar.google.com", timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False


class TestGoogleScholarSearcher(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scholar_accessible = LIVE_TESTS_ENABLED and check_scholar_accessible()

    def setUp(self):
        self.searcher = GoogleScholarSearcher()

    def _require_live_access(self):
        if not LIVE_TESTS_ENABLED:
            self.skipTest("Set PAPER_SEARCH_LIVE_TESTS=1 to run live Google Scholar tests")
        if not self.scholar_accessible:
            self.skipTest("Google Scholar is not accessible")

    def test_search(self):
        self._require_live_access()
        papers = self.searcher.search("machine learning", max_results=5)
        self.assertTrue(len(papers) > 0)
        self.assertTrue(papers[0].title)

    def test_stable_paper_id(self):
        paper_id = self.searcher._stable_paper_id(
            url="https://example.com/paper",
            title="Example Paper",
            authors=["Ada Lovelace"],
        )
        self.assertTrue(paper_id.startswith("gs_"))
        self.assertEqual(
            paper_id,
            self.searcher._stable_paper_id(
                url="https://example.com/paper",
                title="Example Paper",
                authors=["Ada Lovelace"],
            ),
        )

    def test_download_pdf_not_supported(self):
        with self.assertRaises(NotImplementedError):
            self.searcher.download_pdf("some_id", "./downloads")

    def test_read_paper_not_supported(self):
        message = self.searcher.read_paper("some_id")
        self.assertIn("Google Scholar doesn't support direct paper reading", message)


if __name__ == "__main__":
    unittest.main()
