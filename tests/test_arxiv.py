import os
import unittest

from paper_search_mcp.academic_platforms.arxiv import ArxivSearcher


LIVE_TESTS_ENABLED = os.getenv("PAPER_SEARCH_LIVE_TESTS") == "1"


class TestArxivSearcher(unittest.TestCase):
    def test_search(self):
        if not LIVE_TESTS_ENABLED:
            self.skipTest("Set PAPER_SEARCH_LIVE_TESTS=1 to run live arXiv tests")

        searcher = ArxivSearcher()
        papers = searcher.search("machine learning", max_results=10)
        self.assertEqual(len(papers), 10)
        self.assertTrue(papers[0].title)


if __name__ == "__main__":
    unittest.main()
