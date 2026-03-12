import os
import shutil
import tempfile
import unittest

import requests

from paper_search_mcp.academic_platforms.sci_hub import SciHubFetcher


LIVE_TESTS_ENABLED = os.getenv("PAPER_SEARCH_LIVE_TESTS") == "1"


def check_sci_hub_accessible():
    try:
        response = requests.get("https://sci-hub.se", timeout=10)
        return response.status_code == 200
    except requests.RequestException:
        return False


class TestSciHubFetcher(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sci_hub_accessible = LIVE_TESTS_ENABLED and check_sci_hub_accessible()

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="sci_hub_test_")
        self.fetcher = SciHubFetcher(output_dir=self.test_dir)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def _require_live_access(self):
        if not LIVE_TESTS_ENABLED:
            self.skipTest("Set PAPER_SEARCH_LIVE_TESTS=1 to run live Sci-Hub tests")
        if not self.sci_hub_accessible:
            self.skipTest("Sci-Hub is not accessible")

    def test_init(self):
        self.assertEqual(self.fetcher.base_url, "https://sci-hub.se")
        self.assertTrue(os.path.exists(self.test_dir))
        self.assertIsNotNone(self.fetcher.session)

    def test_init_custom_url(self):
        custom_fetcher = SciHubFetcher(base_url="https://sci-hub.ru/", output_dir=self.test_dir)
        self.assertEqual(custom_fetcher.base_url, "https://sci-hub.ru")

    def test_download_pdf_empty_query(self):
        self.assertIsNone(self.fetcher.download_pdf(""))
        self.assertIsNone(self.fetcher.download_pdf("   "))

    def test_generate_filename(self):
        class MockResponse:
            def __init__(self, url, content):
                self.url = url
                self.content = content.encode()

        pdf_response = MockResponse("https://example.com/paper.pdf", "fake pdf content")
        filename = self.fetcher._generate_filename(pdf_response, "10.1234/test")
        self.assertTrue(filename.endswith(".pdf"))

        page_response = MockResponse("https://example.com/page", "fake content")
        filename = self.fetcher._generate_filename(page_response, "test-paper")
        self.assertTrue(filename.endswith(".pdf"))
        self.assertIn("test-paper", filename)

    def test_get_direct_url_pdf_url(self):
        pdf_url = "https://example.com/paper.pdf"
        self.assertEqual(self.fetcher._get_direct_url(pdf_url), pdf_url)

    def test_session_headers(self):
        self.assertIn("User-Agent", self.fetcher.session.headers)
        self.assertIn("Mozilla", self.fetcher.session.headers["User-Agent"])

    def test_output_directory_creation(self):
        new_dir = os.path.join(self.test_dir, "subdir", "nested")
        fetcher = SciHubFetcher(output_dir=new_dir)
        self.assertTrue(os.path.exists(new_dir))

    def test_download_pdf_known_doi(self):
        self._require_live_access()
        for doi in [
            "10.1038/nature12373",
            "10.1126/science.1232033",
            "10.1073/pnas.1320040111",
        ]:
            result = self.fetcher.download_pdf(doi)
            if result:
                self.assertTrue(os.path.exists(result))
                self.assertTrue(result.endswith(".pdf"))
                return
        self.skipTest("All Sci-Hub downloads failed (possibly blocked or CAPTCHA)")

    def test_download_pdf_invalid_doi(self):
        self._require_live_access()
        self.assertIsNone(self.fetcher.download_pdf("10.1234/invalid.doi.123456789"))

    def test_get_direct_url_doi(self):
        self._require_live_access()
        for doi in [
            "10.1038/nature12373",
            "10.1126/science.1232033",
            "10.1073/pnas.1320040111",
        ]:
            result = self.fetcher._get_direct_url(doi)
            if result:
                self.assertTrue(result.startswith("http"))
                return

    def test_error_handling(self):
        self._require_live_access()
        result = self.fetcher.download_pdf("this-is-definitely-not-a-valid-doi-or-identifier-12345")
        self.assertIsInstance(result, (str, type(None)))
        self.assertIsNone(self.fetcher.download_pdf(""))


if __name__ == "__main__":
    unittest.main()
