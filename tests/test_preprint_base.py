from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest import mock

from paper_search_mcp._pdf import PdfTextExtractionError
from paper_search_mcp.academic_platforms._preprint_base import PreprintSearcherBase
from tests._offline import OfflineTestCase


class DummyPreprintSearcher(PreprintSearcherBase):
    SOURCE_NAME = "dummy"
    BASE_URL = "https://api.example.org/details/dummy"
    CONTENT_BASE_URL = "https://www.example.org/content"


class TestPreprintSearcherBase(OfflineTestCase):
    def test_search_uses_shared_scoring_and_source_specific_urls(self):
        searcher = DummyPreprintSearcher()
        response = mock.Mock()
        response.raise_for_status = mock.Mock()
        response.json.return_value = {
            "collection": [
                {
                    "doi": "10.1000/alpha",
                    "title": "Immune atlas for lung repair",
                    "abstract": "A single cell immune atlas for repair.",
                    "authors": "Ada Lovelace; Grace Hopper",
                    "category": "immunology",
                    "date": "2026-01-02",
                    "version": "2",
                },
                {
                    "doi": "10.1000/alpha",
                    "title": "Immune atlas duplicate",
                    "abstract": "duplicate",
                    "authors": "Ada Lovelace",
                    "category": "immunology",
                    "date": "2026-01-01",
                    "version": "1",
                },
            ]
        }

        with mock.patch.object(searcher, "_request", return_value=response) as mock_request:
            papers = searcher.search("immune atlas", max_results=5)

        self.assertEqual(mock_request.call_count, 1)
        self.assertEqual(len(papers), 1)
        self.assertEqual(papers[0].source, "dummy")
        self.assertEqual(papers[0].url, "https://www.example.org/content/10.1000/alphav2")
        self.assertEqual(
            papers[0].pdf_url,
            "https://www.example.org/content/10.1000/alphav2.full.pdf",
        )

    def test_download_pdf_delegates_to_shared_download_helper(self):
        searcher = DummyPreprintSearcher()
        expected_path = Path("docs/downloads/unit/10.1000/test.pdf")

        with mock.patch.object(searcher, "_download", return_value=expected_path) as mock_download:
            result = searcher.download_pdf("10.1000/test", "unit")

        self.assertEqual(result, str(expected_path))
        mock_download.assert_called_once_with(
            "https://www.example.org/content/10.1000/testv1.full.pdf",
            "10.1000/test",
            "unit",
        )

    def test_read_paper_returns_empty_string_when_extraction_fails(self):
        searcher = DummyPreprintSearcher()
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "10.1000" / "test.pdf"
            pdf_path.parent.mkdir(parents=True, exist_ok=True)
            pdf_path.write_bytes(b"%PDF-1.4\n")

            with mock.patch.object(searcher, "_pdf_target") as mock_target:
                mock_target.return_value.path = pdf_path
                with mock.patch.object(
                    searcher,
                    "_extract_text",
                    side_effect=PdfTextExtractionError("bad pdf"),
                ):
                    with self.assertLogs(
                        __name__,
                        level="WARNING",
                    ):
                        result = searcher.read_paper("10.1000/test", temp_dir)

        self.assertEqual(result, "")


if __name__ == "__main__":
    unittest.main()
