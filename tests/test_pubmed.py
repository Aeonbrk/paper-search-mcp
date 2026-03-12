import os
import unittest

from paper_search_mcp.academic_platforms.pubmed import PubMedSearcher


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


if __name__ == "__main__":
    unittest.main()
