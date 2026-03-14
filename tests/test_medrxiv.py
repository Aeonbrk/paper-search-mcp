import os
from pathlib import Path
import shutil
import unittest
from unittest import mock

import requests

from paper_search_mcp.academic_platforms.medrxiv import MedRxivSearcher
from tests._offline import OfflineTestCase, read_fixture_json


LIVE_TESTS_ENABLED = os.getenv("PAPER_SEARCH_LIVE_TESTS") == "1"


def check_api_accessible():
    try:
        response = requests.get("https://api.medrxiv.org/details/medrxiv/0/1", timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False


class TestMedRxivSearcher(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.api_accessible = LIVE_TESTS_ENABLED and check_api_accessible()

    def setUp(self):
        self.searcher = MedRxivSearcher()

    def _require_live_access(self):
        if not LIVE_TESTS_ENABLED:
            self.skipTest("Set PAPER_SEARCH_LIVE_TESTS=1 to run live medRxiv tests")
        if not self.api_accessible:
            self.skipTest("medRxiv API is not accessible")

    def test_search(self):
        self._require_live_access()
        papers = self.searcher.search("machine learning", max_results=10)
        self.assertTrue(len(papers) > 0)
        self.assertTrue(papers[0].title)

    def test_download_and_read(self):
        self._require_live_access()
        papers = self.searcher.search("machine learning", max_results=1)
        if not papers:
            self.skipTest("No papers found for testing download")

        save_path = "test_medrxiv_live"
        try:
            pdf_path = self.searcher.download_pdf(papers[0].paper_id, save_path)
            self.assertTrue(os.path.exists(pdf_path))
            text_content = self.searcher.read_paper(papers[0].paper_id, save_path)
            self.assertTrue(len(text_content) > 0)
        finally:
            output_dir = Path("docs/downloads") / save_path
            if output_dir.exists():
                shutil.rmtree(output_dir, ignore_errors=True)


class TestMedRxivSearcherOffline(OfflineTestCase):
    def test_search_offline_matches_free_text_without_category_parameter(self):
        searcher = MedRxivSearcher()
        response = mock.Mock()
        response.raise_for_status = mock.Mock()
        response.json.return_value = read_fixture_json("medrxiv", "search_response.json")
        requested_urls = []

        def fake_request(*args, **kwargs):
            requested_urls.append(args[2])
            return response

        with mock.patch(
            "paper_search_mcp.academic_platforms.medrxiv.request_with_retries",
            side_effect=fake_request,
        ) as mock_request:
            papers = searcher.search("long covid antibody", max_results=3)

        self.assertEqual(mock_request.call_count, 1)
        self.assertEqual(len(papers), 1)
        self.assertEqual(
            papers[0].title,
            "Long COVID antibody signatures after mild infection",
        )
        self.assertEqual(papers[0].categories, ["infectious diseases"])
        self.assertEqual(papers[0].source, "medrxiv")
        self.assertNotIn("?category=", requested_urls[0])

    def test_search_offline_returns_empty_for_nonsense_query(self):
        searcher = MedRxivSearcher()
        response = mock.Mock()
        response.raise_for_status = mock.Mock()
        response.json.return_value = read_fixture_json("medrxiv", "search_empty.json")

        with mock.patch(
            "paper_search_mcp.academic_platforms.medrxiv.request_with_retries",
            return_value=response,
        ) as mock_request:
            papers = searcher.search("orbital penguin entropy", max_results=3)

        self.assertEqual(mock_request.call_count, 1)
        self.assertEqual(papers, [])


if __name__ == "__main__":
    unittest.main()
