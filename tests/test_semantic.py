import os
from pathlib import Path
import shutil
import unittest
from unittest import mock

import requests

from paper_search_mcp.academic_platforms.semantic import SemanticSearcher
from tests._offline import OfflineTestCase, read_fixture_json


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
        finally:
            output_dir = Path("docs/downloads") / save_path
            if output_dir.exists():
                shutil.rmtree(output_dir, ignore_errors=True)


class TestSemanticSearcherOffline(OfflineTestCase):
    def test_search_offline_fixture(self):
        searcher = SemanticSearcher()
        fixture = read_fixture_json("semantic", "paper_search.json")

        with mock.patch.object(searcher, "request_api", return_value=fixture) as mock_request:
            papers = searcher.search("secret sharing", max_results=2)

        mock_request.assert_called_once()
        self.assertEqual(len(papers), 2)

        first = papers[0]
        self.assertEqual(first.paper_id, "sem_one")
        self.assertEqual(first.title, "Offline Semantic Paper One")
        self.assertEqual(first.authors, ["Alice Example", "Bob Example"])
        self.assertEqual(first.source, "semantic")
        self.assertEqual(first.doi, "10.1000/semantic.one")
        self.assertEqual(first.categories, ["Computer Science", "Mathematics"])
        self.assertEqual(first.pdf_url, "https://example.org/semantic-one.pdf")

        second = papers[1]
        self.assertEqual(second.paper_id, "sem_two")
        self.assertEqual(second.pdf_url, "https://arxiv.org/pdf/2503.54321v1")

        serialized = first.to_dict()
        self.assertEqual(serialized["source"], "semantic")
        self.assertEqual(serialized["categories"], "Computer Science; Mathematics")
        self.assertEqual(serialized["doi"], "10.1000/semantic.one")

    def test_download_pdf_uses_shared_pdf_helper(self):
        searcher = SemanticSearcher()
        paper = mock.Mock(paper_id="sem_one", pdf_url="https://example.org/semantic-one.pdf")

        with (
            mock.patch.object(searcher, "get_paper_details", return_value=paper),
            mock.patch(
                "paper_search_mcp.academic_platforms.semantic.download_pdf_file",
                return_value=Path("docs/downloads/offline/semantic_sem_one.pdf"),
            ) as mock_download,
        ):
            result = searcher.download_pdf("sem_one", "offline")

        self.assertEqual(result, "docs/downloads/offline/semantic_sem_one.pdf")
        mock_download.assert_called_once()

    def test_read_paper_uses_shared_extraction_helper(self):
        searcher = SemanticSearcher()
        paper = mock.Mock(
            paper_id="sem_one",
            pdf_url="https://example.org/semantic-one.pdf",
            title="Offline Semantic Paper One",
            authors=["Alice Example", "Bob Example"],
            published_date="2025-03-01",
            url="https://example.org/semantic-one",
        )

        with (
            mock.patch.object(searcher, "get_paper_details", return_value=paper),
            mock.patch.object(
                searcher,
                "_download_pdf_file",
                return_value="docs/downloads/offline/semantic_sem_one.pdf",
            ),
            mock.patch(
                "paper_search_mcp.academic_platforms.semantic.extract_pdf_text",
                return_value="semantic text body",
            ) as mock_extract,
        ):
            result = searcher.read_paper("sem_one", "offline")

        self.assertIn("Title: Offline Semantic Paper One", result)
        self.assertIn("PDF downloaded to: docs/downloads/offline/semantic_sem_one.pdf", result)
        self.assertTrue(result.endswith("semantic text body"))
        mock_extract.assert_called_once_with("docs/downloads/offline/semantic_sem_one.pdf")


if __name__ == "__main__":
    unittest.main()
