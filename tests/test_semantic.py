import os
from pathlib import Path
import shutil
import unittest

import requests

from paper_search_mcp.academic_platforms.semantic import SemanticSearcher


LIVE_TESTS_ENABLED = os.getenv("PAPER_SEARCH_LIVE_TESTS") == "1"


def check_semantic_accessible():
    try:
        response = requests.get(
            "https://api.semanticscholar.org/graph/v1/paper/5bbfdf2e62f0508c65ba6de9c72fe2066fd98138",
            timeout=5,
        )
        return response.status_code == 200
    except requests.RequestException:
        return False


class TestSemanticSearcher(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.semantic_accessible = LIVE_TESTS_ENABLED and check_semantic_accessible()

    def setUp(self):
        self.searcher = SemanticSearcher()

    def _require_live_access(self):
        if not LIVE_TESTS_ENABLED:
            self.skipTest("Set PAPER_SEARCH_LIVE_TESTS=1 to run live Semantic Scholar tests")
        if not self.semantic_accessible:
            self.skipTest("Semantic Scholar is not accessible")

    def test_searcher_has_session(self):
        self.assertIsNotNone(self.searcher.session)

    def test_search_basic(self):
        self._require_live_access()
        results = self.searcher.search("secret sharing", max_results=3)
        self.assertIsInstance(results, list)
        self.assertLessEqual(len(results), 3)

    def test_search_with_fetch_details(self):
        self._require_live_access()
        detailed_results = self.searcher.search("cryptography", max_results=2)
        self.assertIsInstance(detailed_results, list)
        self.assertLessEqual(len(detailed_results), 2)

    def test_get_paper_details(self):
        self._require_live_access()
        paper = self.searcher.get_paper_details("5bbfdf2e62f0508c65ba6de9c72fe2066fd98138")
        if paper is not None:
            self.assertEqual(paper.source, "semantic")
            self.assertTrue(paper.title)

    def test_download_pdf_functionality(self):
        self._require_live_access()
        save_path = "test_semantic_live"
        try:
            result = self.searcher.download_pdf(
                "5bbfdf2e62f0508c65ba6de9c72fe2066fd98138",
                save_path,
            )
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
        save_path = "test_semantic_read_live"
        try:
            result = self.searcher.read_paper(
                "5bbfdf2e62f0508c65ba6de9c72fe2066fd98138",
                save_path,
            )
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
