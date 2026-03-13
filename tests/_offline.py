from __future__ import annotations

from contextlib import ExitStack, contextmanager
import json
from pathlib import Path
import socket
from typing import Any, Iterator
import unittest
from unittest.mock import patch


FIXTURES_ROOT = Path(__file__).resolve().parent / "fixtures"


class NetworkAccessDenied(AssertionError):
    pass


def fixture_path(*parts: str) -> Path:
    if not parts:
        raise ValueError("fixture_path() requires at least one path segment")

    candidate = (FIXTURES_ROOT.joinpath(*parts)).resolve()
    root = FIXTURES_ROOT.resolve()

    if root not in candidate.parents and candidate != root:
        raise ValueError(f"Fixture path escapes fixtures root: {candidate}")

    if not candidate.exists():
        joined = "/".join(parts)
        raise FileNotFoundError(
            f"Missing fixture: {joined}. Expected at {candidate}. "
            "If you're adding a new offline test, store fixtures under tests/fixtures/."
        )

    return candidate


def read_fixture_text(*parts: str, encoding: str = "utf-8") -> str:
    return fixture_path(*parts).read_text(encoding=encoding)


def read_fixture_bytes(*parts: str) -> bytes:
    return fixture_path(*parts).read_bytes()


def read_fixture_json(*parts: str) -> Any:
    return json.loads(read_fixture_text(*parts))


class _DeniedSocket:
    def __init__(self, *args: object, **kwargs: object) -> None:
        self._args = args
        self._kwargs = kwargs

    def settimeout(self, _timeout: object) -> None:
        return None

    def setsockopt(self, *_args: object, **_kwargs: object) -> None:
        return None

    def setblocking(self, _flag: object) -> None:
        return None

    def close(self) -> None:
        return None

    def fileno(self) -> int:
        return -1

    def connect(self, address: object) -> None:
        raise NetworkAccessDenied(f"Outbound network disabled for offline tests (connect): {address}")

    def connect_ex(self, address: object) -> int:
        raise NetworkAccessDenied(f"Outbound network disabled for offline tests (connect_ex): {address}")

    def __enter__(self) -> "_DeniedSocket":
        return self

    def __exit__(
        self,
        _exc_type: object,
        _exc: object,
        _tb: object,
    ) -> bool:
        self.close()
        return False


@contextmanager
def deny_network() -> Iterator[None]:
    def _deny(*_args: object, **_kwargs: object) -> None:
        raise NetworkAccessDenied("Outbound network disabled for offline tests")

    with ExitStack() as stack:
        stack.enter_context(patch("socket.socket", _DeniedSocket))
        stack.enter_context(patch("socket.create_connection", _deny))
        stack.enter_context(patch("socket.getaddrinfo", _deny))

        try:
            import urllib3.util.connection as urllib3_connection
        except Exception:
            urllib3_connection = None

        if urllib3_connection is not None:
            stack.enter_context(patch.object(urllib3_connection, "create_connection", _deny))

        yield


class OfflineTestCase(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        self._offline_exit_stack = ExitStack()
        self._offline_exit_stack.enter_context(deny_network())

    def tearDown(self) -> None:
        self._offline_exit_stack.close()
        super().tearDown()

