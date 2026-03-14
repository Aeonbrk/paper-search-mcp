import unittest
from unittest import mock

import requests

from paper_search_mcp._http import (
    DEFAULT_ALLOWED_RETRY_METHODS,
    RetryPolicy,
    TransportError,
    build_session,
    request_with_retries,
)


class TestHttpHelpers(unittest.TestCase):
    def test_build_session_sets_headers_pooling_and_retry_policy(self):
        retry_policy = RetryPolicy(
            max_retries=4,
            retryable_status_codes=(429, 503),
            backoff_base_seconds=0.25,
            backoff_max_seconds=3.0,
        )

        session = build_session(
            user_agent="custom-agent/1.0",
            headers={"X-Test": "1"},
            retry_policy=retry_policy,
            pool_connections=5,
            pool_maxsize=7,
            pool_block=True,
        )

        self.assertEqual(session.headers["User-Agent"], "custom-agent/1.0")
        self.assertEqual(session.headers["X-Test"], "1")
        self.assertEqual(session.headers["Accept"], "*/*")

        for prefix in ("http://", "https://"):
            adapter = session.get_adapter(prefix)
            retry = adapter.max_retries
            self.assertEqual(adapter._pool_connections, 5)
            self.assertEqual(adapter._pool_maxsize, 7)
            self.assertTrue(adapter._pool_block)
            self.assertEqual(retry.total, 4)
            self.assertEqual(retry.connect, 4)
            self.assertEqual(retry.read, 4)
            self.assertEqual(set(retry.status_forcelist), {429, 503})
            self.assertEqual(
                set(retry.allowed_methods), set(DEFAULT_ALLOWED_RETRY_METHODS)
            )
            self.assertEqual(retry.backoff_factor, 0.25)
            self.assertEqual(retry.backoff_max, 3.0)
            self.assertFalse(retry.raise_on_status)

    def test_retry_policy_backoff_factor_is_applied_to_backoff_time(self):
        retry_policy = RetryPolicy(
            max_retries=10,
            backoff_base_seconds=1.0,
            backoff_factor=3.0,
            backoff_max_seconds=60.0,
        )
        session = build_session(retry_policy=retry_policy)
        retry = session.get_adapter("https://").max_retries

        retry = retry.increment(
            method="GET",
            url="https://example.test/retry",
            error=Exception("boom"),
        )
        self.assertEqual(retry.get_backoff_time(), 0.0)

        retry = retry.increment(
            method="GET",
            url="https://example.test/retry",
            error=Exception("boom"),
        )
        self.assertEqual(retry.get_backoff_time(), 3.0)

        retry = retry.increment(
            method="GET",
            url="https://example.test/retry",
            error=Exception("boom"),
        )
        self.assertEqual(retry.get_backoff_time(), 9.0)

    def test_request_with_retries_preserves_pooling_and_applies_status_override(self):
        session = build_session(
            retry_policy=RetryPolicy(max_retries=1, retryable_status_codes=(429,)),
            pool_connections=3,
            pool_maxsize=9,
        )
        response = mock.Mock()

        with mock.patch.object(session, "request", return_value=response) as mock_request:
            returned = request_with_retries(
                session,
                "GET",
                "https://example.test/search",
                timeout=(1.5, 2.5),
                retry_policy=RetryPolicy(max_retries=2, retryable_status_codes=(503,)),
                retry_on_status_codes=(503, 504),
                params={"q": "graph"},
            )

        self.assertIs(returned, response)
        mock_request.assert_called_once_with(
            "GET",
            "https://example.test/search",
            timeout=(1.5, 2.5),
            params={"q": "graph"},
        )
        adapter = session.get_adapter("https://")
        retry = adapter.max_retries
        self.assertEqual(adapter._pool_connections, 3)
        self.assertEqual(adapter._pool_maxsize, 9)
        self.assertEqual(retry.total, 2)
        self.assertEqual(set(retry.status_forcelist), {503, 504})

    def test_request_with_retries_reuses_session_retry_policy_by_default(self):
        session = build_session(
            retry_policy=RetryPolicy(
                max_retries=5, retryable_status_codes=(429, 503)
            ),
            pool_connections=4,
            pool_maxsize=8,
        )
        response = mock.Mock()

        with mock.patch.object(session, "request", return_value=response):
            request_with_retries(
                session,
                "GET",
                "https://example.test/defaults",
            )

        adapter = session.get_adapter("https://")
        retry = adapter.max_retries
        self.assertEqual(adapter._pool_connections, 4)
        self.assertEqual(adapter._pool_maxsize, 8)
        self.assertEqual(retry.total, 5)
        self.assertEqual(set(retry.status_forcelist), {429, 503})

    def test_request_with_retries_wraps_transport_failures(self):
        session = build_session()

        with mock.patch.object(
            session, "request", side_effect=requests.Timeout("timed out")
        ):
            with self.assertRaises(TransportError) as context:
                request_with_retries(
                    session,
                    "GET",
                    "https://example.test/failure",
                    timeout=(1.0, 5.0),
                    retry_policy=RetryPolicy(max_retries=2),
                )

        error = context.exception
        self.assertIsInstance(error.__cause__, requests.Timeout)
        self.assertEqual(error.method, "GET")
        self.assertEqual(error.url, "https://example.test/failure")
        self.assertEqual(error.attempts, 3)
        self.assertIn("timed out", str(error))
        self.assertIn("https://example.test/failure", str(error))


if __name__ == "__main__":
    unittest.main()
