from __future__ import annotations

from datetime import datetime, timedelta
import os
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
    def test_search_captures_now_once_for_date_window(self):
        searcher = DummyPreprintSearcher()
        fixed_now = datetime(2026, 3, 14, 0, 0, 1)

        class CountingDateTime:
            calls = 0

            @classmethod
            def now(cls):
                cls.calls += 1
                if cls.calls > 1:
                    raise AssertionError("datetime.now() called more than once")
                return fixed_now

        response = mock.Mock()
        response.raise_for_status = mock.Mock()
        response.json.return_value = {"collection": []}

        days = 7
        expected_end = fixed_now.strftime("%Y-%m-%d")
        expected_start = (fixed_now - timedelta(days=days)).strftime("%Y-%m-%d")
        expected_url = f"{searcher.BASE_URL}/{expected_start}/{expected_end}/0"

        def _assert_url(url: str):
            self.assertEqual(url, expected_url)
            return response

        with mock.patch(
            "paper_search_mcp.academic_platforms._preprint_base.datetime",
            CountingDateTime,
        ):
            with mock.patch.object(searcher, "_request", side_effect=_assert_url):
                papers = searcher.search("immune", max_results=1, days=days)

        self.assertEqual(papers, [])
        self.assertEqual(CountingDateTime.calls, 1)

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

    def test_proxy_toggle_disables_proxies_per_request(self):
        searcher = DummyPreprintSearcher()

        response = mock.Mock()
        response.raise_for_status = mock.Mock()
        response.json.return_value = {"collection": []}

        with mock.patch(
            "paper_search_mcp.academic_platforms._preprint_base.request_with_retries",
            return_value=response,
        ) as mock_request:
            papers = searcher.search("immune", max_results=1, days=1)

        self.assertEqual(papers, [])
        self.assertNotIn("proxies", mock_request.call_args.kwargs)

        with mock.patch.dict(os.environ, {"PAPER_SEARCH_DISABLE_PROXIES": "1"}):
            with mock.patch(
                "paper_search_mcp.academic_platforms._preprint_base.request_with_retries",
                return_value=response,
            ) as mock_request_disabled:
                papers = searcher.search("immune", max_results=1, days=1)

            self.assertEqual(papers, [])
            self.assertEqual(
                mock_request_disabled.call_args.kwargs["proxies"],
                {"http": None, "https": None},
            )

        expected_pdf_path = Path("docs/downloads/unit/10.1000/test.pdf")
        with mock.patch(
            "paper_search_mcp.academic_platforms._preprint_base.download_pdf_file",
            return_value=expected_pdf_path,
        ) as mock_download:
            result = searcher._download(
                "https://www.example.org/content/10.1000/testv1.full.pdf",
                "10.1000/test",
                "unit",
            )

        self.assertEqual(result, expected_pdf_path)
        self.assertNotIn("proxies", mock_download.call_args.kwargs)

        with mock.patch.dict(os.environ, {"PAPER_SEARCH_DISABLE_PROXIES": "1"}):
            with mock.patch(
                "paper_search_mcp.academic_platforms._preprint_base.download_pdf_file",
                return_value=expected_pdf_path,
            ) as mock_download_disabled:
                result = searcher._download(
                    "https://www.example.org/content/10.1000/testv1.full.pdf",
                    "10.1000/test",
                    "unit",
                )

            self.assertEqual(result, expected_pdf_path)
            self.assertEqual(
                mock_download_disabled.call_args.kwargs["proxies"],
                {"http": None, "https": None},
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
