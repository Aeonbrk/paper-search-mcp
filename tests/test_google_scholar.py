import os
import unittest
from unittest import mock

import requests

from paper_search_mcp.academic_platforms.google_scholar import GoogleScholarSearcher
from tests._offline import read_fixture_text


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

    def test_search_returns_empty_list_when_page_has_no_results(self):
        response = mock.Mock()
        response.raise_for_status = mock.Mock()
        response.text = read_fixture_text("google_scholar", "search_no_results.html")

        with (
            mock.patch(
                "paper_search_mcp.academic_platforms.google_scholar.request_with_retries",
                return_value=response,
            ) as mock_request,
            mock.patch("paper_search_mcp.academic_platforms.google_scholar.time.sleep"),
        ):
            papers = self.searcher.search("no hits expected", max_results=3)

        self.assertEqual(papers, [])
        mock_request.assert_called_once()

    def test_search_stops_after_partial_page_without_extra_request(self):
        response = mock.Mock()
        response.raise_for_status = mock.Mock()
        response.text = read_fixture_text("google_scholar", "search_partial_results.html")

        with (
            mock.patch(
                "paper_search_mcp.academic_platforms.google_scholar.request_with_retries",
                return_value=response,
            ) as mock_request,
            mock.patch("paper_search_mcp.academic_platforms.google_scholar.time.sleep") as mock_sleep,
        ):
            papers = self.searcher.search("partial page", max_results=15)

        self.assertEqual(len(papers), 1)
        self.assertEqual(papers[0].title, "Offline Scholar Paper One")
        mock_request.assert_called_once()
        mock_sleep.assert_not_called()

    def test_search_propagates_transport_failures(self):
        with mock.patch(
            "paper_search_mcp.academic_platforms.google_scholar.request_with_retries",
            side_effect=requests.RequestException("scholar unavailable"),
        ):
            with self.assertRaisesRegex(requests.RequestException, "scholar unavailable"):
                self.searcher.search("network failure", max_results=2)


if __name__ == "__main__":
    unittest.main()
