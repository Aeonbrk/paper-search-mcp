import os
from pathlib import Path
import shutil
import unittest

import requests

from paper_search_mcp.academic_platforms.iacr import IACRSearcher


LIVE_TESTS_ENABLED = os.getenv("PAPER_SEARCH_LIVE_TESTS") == "1"


def check_iacr_accessible():
    try:
        response = requests.get("https://eprint.iacr.org", timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False


class TestIACRSearcher(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.iacr_accessible = LIVE_TESTS_ENABLED and check_iacr_accessible()

    def setUp(self):
        self.searcher = IACRSearcher()

    def _require_live_access(self):
        if not LIVE_TESTS_ENABLED:
            self.skipTest("Set PAPER_SEARCH_LIVE_TESTS=1 to run live IACR tests")
        if not self.iacr_accessible:
            self.skipTest("IACR is not accessible")

    def test_searcher_has_session(self):
        self.assertIsNotNone(self.searcher.session)

    def test_search_basic(self):
        self._require_live_access()
        results = self.searcher.search("secret sharing", max_results=3)
        self.assertIsInstance(results, list)
        self.assertLessEqual(len(results), 3)

    def test_search_with_fetch_details(self):
        self._require_live_access()
        detailed_results = self.searcher.search("cryptography", max_results=2, fetch_details=True)
        compact_results = self.searcher.search("cryptography", max_results=2, fetch_details=False)
        self.assertIsInstance(detailed_results, list)
        self.assertIsInstance(compact_results, list)
        self.assertLessEqual(len(detailed_results), 2)
        self.assertLessEqual(len(compact_results), 2)

    def test_get_paper_details(self):
        self._require_live_access()
        paper = self.searcher.get_paper_details("2009/101")
        if paper is not None:
            self.assertEqual(paper.paper_id, "2009/101")
            self.assertEqual(paper.source, "iacr")
            self.assertTrue(paper.title)

    def test_download_pdf_functionality(self):
        self._require_live_access()
        save_path = "test_iacr_live"
        try:
            result = self.searcher.download_pdf("2009/101", save_path)
            self.assertIsInstance(result, str)
            if not result.startswith("Error") and not result.startswith("Failed"):
                self.assertTrue(os.path.exists(result))
                self.assertTrue(result.endswith(".pdf"))
        finally:
            output_dir = Path("docs/downloads") / save_path
            if output_dir.exists():
                shutil.rmtree(output_dir, ignore_errors=True)

    def test_read_paper_functionality(self):
        self._require_live_access()
        save_path = "test_iacr_read_live"
        try:
            result = self.searcher.read_paper("2009/101", save_path)
            self.assertIsInstance(result, str)
            if "Error" not in result and len(result) > 100:
                self.assertIn("Title:", result)
                self.assertIn("PDF downloaded to:", result)
                self.assertIn("--- Page", result)
        finally:
            output_dir = Path("docs/downloads") / save_path
            if output_dir.exists():
                shutil.rmtree(output_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
