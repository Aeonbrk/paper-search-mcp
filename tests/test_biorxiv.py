import os
from pathlib import Path
import shutil
import unittest

import requests

from paper_search_mcp.academic_platforms.biorxiv import BioRxivSearcher


LIVE_TESTS_ENABLED = os.getenv("PAPER_SEARCH_LIVE_TESTS") == "1"


def check_api_accessible():
    try:
        response = requests.get("https://api.biorxiv.org/details/biorxiv/0/1", timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False


class TestBioRxivSearcher(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.api_accessible = LIVE_TESTS_ENABLED and check_api_accessible()

    def setUp(self):
        self.searcher = BioRxivSearcher()

    def _require_live_access(self):
        if not LIVE_TESTS_ENABLED:
            self.skipTest("Set PAPER_SEARCH_LIVE_TESTS=1 to run live bioRxiv tests")
        if not self.api_accessible:
            self.skipTest("bioRxiv API is not accessible")

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

        save_path = "test_biorxiv_live"
        try:
            pdf_path = self.searcher.download_pdf(papers[0].paper_id, save_path)
            self.assertTrue(os.path.exists(pdf_path))
            text_content = self.searcher.read_paper(papers[0].paper_id, save_path)
            self.assertTrue(len(text_content) > 0)
        finally:
            output_dir = Path("docs/downloads") / save_path
            if output_dir.exists():
                shutil.rmtree(output_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
