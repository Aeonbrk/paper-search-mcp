import importlib
import unittest
from unittest import mock

import requests

from paper_search_mcp._http import RETRYABLE_STATUS_CODES, RetryPolicy, TransportError, request_with_retries


SESSION_BACKED_ADAPTER_SPECS = (
    ("arxiv", "paper_search_mcp.academic_platforms.arxiv", "ArxivSearcher"),
    ("pubmed", "paper_search_mcp.academic_platforms.pubmed", "PubMedSearcher"),
    ("pmc", "paper_search_mcp.academic_platforms.pmc", "PMCSearcher"),
    ("biorxiv", "paper_search_mcp.academic_platforms.biorxiv", "BioRxivSearcher"),
    ("medrxiv", "paper_search_mcp.academic_platforms.medrxiv", "MedRxivSearcher"),
    (
        "google_scholar",
        "paper_search_mcp.academic_platforms.google_scholar",
        "GoogleScholarSearcher",
    ),
    ("iacr", "paper_search_mcp.academic_platforms.iacr", "IACRSearcher"),
    ("semantic", "paper_search_mcp.academic_platforms.semantic", "SemanticSearcher"),
    ("crossref", "paper_search_mcp.academic_platforms.crossref", "CrossRefSearcher"),
)


class TestHttpResilience(unittest.TestCase):
    def test_session_backed_adapters_share_retryable_status_policy(self):
        expected_status_codes = set(RETRYABLE_STATUS_CODES)

        for source_id, module_path, class_name in SESSION_BACKED_ADAPTER_SPECS:
            with self.subTest(source=source_id):
                module = importlib.import_module(module_path)
                adapter_cls = getattr(module, class_name)
                adapter = adapter_cls()

                transport_config = getattr(adapter.session, "_paper_search_transport_config", None)
                self.assertIsNotNone(transport_config)
                self.assertEqual(
                    set(transport_config.retry_on_status_codes),
                    expected_status_codes,
                )

    def test_request_with_retries_reports_attempt_budget_from_retry_policy(self):
        module = importlib.import_module("paper_search_mcp.academic_platforms.arxiv")
        searcher = module.ArxivSearcher()

        with mock.patch.object(
            searcher.session,
            "request",
            side_effect=requests.Timeout("benchmark timeout"),
        ):
            with self.assertRaises(TransportError) as context:
                request_with_retries(
                    searcher.session,
                    "GET",
                    "https://example.test/arxiv",
                    timeout=searcher.timeout,
                    retry_policy=RetryPolicy(max_retries=4),
                )

        error = context.exception
        self.assertEqual(error.attempts, 5)
        self.assertEqual(error.method, "GET")
        self.assertIn("benchmark timeout", str(error))


if __name__ == "__main__":
    unittest.main()
