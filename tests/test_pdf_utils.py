import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock, patch

import requests

from paper_search_mcp._http import RetryPolicy


class FakeResponse:
    def __init__(self, chunks, *, error=None):
        self._chunks = list(chunks)
        self._error = error
        self.chunk_sizes = []

    def raise_for_status(self):
        if self._error is not None:
            raise self._error

    def iter_content(self, chunk_size=1):
        self.chunk_sizes.append(chunk_size)
        for chunk in self._chunks:
            yield chunk


class TestPdfUtils(TestCase):
    def test_download_pdf_file_streams_to_safe_target(self):
        from paper_search_mcp._pdf import DEFAULT_PDF_CHUNK_SIZE, download_pdf_file

        response = FakeResponse([b"abc", b"", b"def"])

        with tempfile.TemporaryDirectory() as temp_dir:
            with patch(
                "paper_search_mcp._pdf.request_with_retries",
                return_value=response,
            ) as request_mock:
                path = download_pdf_file(
                    Mock(),
                    "https://example.test/paper.pdf",
                    filename="../unsafe.pdf",
                    save_path="runs/perf",
                    base_dir=temp_dir,
                    retry_policy=RetryPolicy(max_retries=0),
                )

                self.assertEqual(
                    path.parent,
                    Path(temp_dir).resolve() / "docs" / "downloads" / "runs" / "perf",
                )
                self.assertEqual(path.suffix, ".pdf")
                self.assertEqual(path.read_bytes(), b"abcdef")
        self.assertEqual(response.chunk_sizes, [DEFAULT_PDF_CHUNK_SIZE])
        request_mock.assert_called_once()
        _, kwargs = request_mock.call_args
        self.assertTrue(kwargs["stream"])

    def test_download_pdf_file_wraps_request_failures(self):
        from paper_search_mcp._pdf import PdfDownloadError, download_pdf_file

        with tempfile.TemporaryDirectory() as temp_dir:
            with patch(
                "paper_search_mcp._pdf.request_with_retries",
                side_effect=requests.RequestException("boom"),
            ):
                with self.assertRaises(PdfDownloadError):
                    download_pdf_file(
                        Mock(),
                        "https://example.test/paper.pdf",
                        filename="paper.pdf",
                        save_path="runs/perf",
                        base_dir=temp_dir,
                    )

    def test_download_pdf_file_preserves_existing_file_on_request_failure(self):
        from paper_search_mcp._pdf import PdfDownloadError, download_pdf_file
        from paper_search_mcp._paths import resolve_download_target

        with tempfile.TemporaryDirectory() as temp_dir:
            existing_path = resolve_download_target(
                filename="paper.pdf",
                save_path="runs/perf",
                base_dir=temp_dir,
            ).path
            existing_path.write_bytes(b"cached")

            with patch(
                "paper_search_mcp._pdf.request_with_retries",
                side_effect=requests.RequestException("boom"),
            ):
                with self.assertRaises(PdfDownloadError):
                    download_pdf_file(
                        Mock(),
                        "https://example.test/paper.pdf",
                        filename="paper.pdf",
                        save_path="runs/perf",
                        base_dir=temp_dir,
                    )

            self.assertEqual(existing_path.read_bytes(), b"cached")

    def test_extract_pdf_text_returns_joined_page_text(self):
        from paper_search_mcp._pdf import extract_pdf_text

        reader = SimpleNamespace(
            pages=[
                SimpleNamespace(extract_text=Mock(return_value="Alpha")),
                SimpleNamespace(extract_text=Mock(return_value="Beta\n")),
            ]
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "paper.pdf"
            pdf_path.write_bytes(b"placeholder")
            with patch("paper_search_mcp._pdf.PdfReader", return_value=reader):
                self.assertEqual(extract_pdf_text(pdf_path), "Alpha\nBeta")

    def test_extract_pdf_text_rejects_blank_content(self):
        from paper_search_mcp._pdf import PdfTextExtractionError, extract_pdf_text

        reader = SimpleNamespace(
            pages=[
                SimpleNamespace(extract_text=Mock(return_value="")),
                SimpleNamespace(extract_text=Mock(return_value=None)),
            ]
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "paper.pdf"
            pdf_path.write_bytes(b"placeholder")
            with patch("paper_search_mcp._pdf.PdfReader", return_value=reader):
                with self.assertRaises(PdfTextExtractionError):
                    extract_pdf_text(pdf_path)

    def test_extract_pdf_text_wraps_malformed_pdf_errors(self):
        from paper_search_mcp._pdf import PdfTextExtractionError, extract_pdf_text

        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "broken.pdf"
            pdf_path.write_bytes(b"not-a-pdf")

            with self.assertRaises(PdfTextExtractionError):
                extract_pdf_text(pdf_path)
