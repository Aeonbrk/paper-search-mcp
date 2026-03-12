from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence, Tuple

import requests


DEFAULT_CONNECT_TIMEOUT_S = 10.0
DEFAULT_READ_TIMEOUT_S = 30.0
DEFAULT_TIMEOUT: Tuple[float, float] = (DEFAULT_CONNECT_TIMEOUT_S, DEFAULT_READ_TIMEOUT_S)

DEFAULT_USER_AGENT = "paper-search-mcp (requests)"

RETRYABLE_STATUS_CODES = frozenset({429, 500, 502, 503, 504})


def build_session(
    *,
    user_agent: Optional[str] = None,
    headers: Optional[Mapping[str, str]] = None,
) -> requests.Session:
    """
    Create a `requests.Session` with consistent defaults.
    """
    session = requests.Session()
    base_headers: Dict[str, str] = {
        "User-Agent": user_agent or DEFAULT_USER_AGENT,
        "Accept": "*/*",
    }
    if headers:
        base_headers.update(dict(headers))
    session.headers.update(base_headers)
    return session


def backoff_delay_seconds(
    attempt: int,
    *,
    base: float = 1.0,
    factor: float = 2.0,
    max_delay: float = 30.0,
) -> float:
    if attempt <= 0:
        return 0.0
    delay = base * (factor ** (attempt - 1))
    return min(max_delay, delay)


@dataclass(frozen=True)
class RetryPolicy:
    max_retries: int = 3
    retryable_status_codes: Sequence[int] = tuple(RETRYABLE_STATUS_CODES)
    backoff_base_seconds: float = 1.0
    backoff_factor: float = 2.0
    backoff_max_seconds: float = 30.0


def request_with_retries(
    session: requests.Session,
    method: str,
    url: str,
    *,
    timeout: Tuple[float, float] = DEFAULT_TIMEOUT,
    retry_policy: RetryPolicy = RetryPolicy(),
    retry_on_status_codes: Optional[Iterable[int]] = None,
    **kwargs: Any,
) -> requests.Response:
    """
    Make a request with a small, consistent retry/backoff strategy.
    """
    retryable = (
        set(retry_on_status_codes)
        if retry_on_status_codes is not None
        else set(retry_policy.retryable_status_codes)
    )

    last_error: Optional[BaseException] = None
    for attempt in range(retry_policy.max_retries + 1):
        if attempt > 0:
            time.sleep(
                backoff_delay_seconds(
                    attempt,
                    base=retry_policy.backoff_base_seconds,
                    factor=retry_policy.backoff_factor,
                    max_delay=retry_policy.backoff_max_seconds,
                )
            )

        try:
            response = session.request(method, url, timeout=timeout, **kwargs)
        except requests.RequestException as exc:
            last_error = exc
            continue

        if response.status_code in retryable and attempt < retry_policy.max_retries:
            last_error = requests.HTTPError(
                f"Retryable HTTP status {response.status_code}",
                response=response,
            )
            continue

        return response

    if last_error is not None:
        raise last_error
    raise RuntimeError("request_with_retries exhausted without response or exception")


def get_text(
    session: requests.Session,
    url: str,
    *,
    timeout: Tuple[float, float] = DEFAULT_TIMEOUT,
    retry_policy: RetryPolicy = RetryPolicy(),
    raise_for_status: bool = True,
    **kwargs: Any,
) -> str:
    response = request_with_retries(
        session, "GET", url, timeout=timeout, retry_policy=retry_policy, **kwargs
    )
    if raise_for_status:
        response.raise_for_status()
    return response.text


def get_json(
    session: requests.Session,
    url: str,
    *,
    timeout: Tuple[float, float] = DEFAULT_TIMEOUT,
    retry_policy: RetryPolicy = RetryPolicy(),
    raise_for_status: bool = True,
    **kwargs: Any,
) -> Dict[str, Any]:
    response = request_with_retries(
        session, "GET", url, timeout=timeout, retry_policy=retry_policy, **kwargs
    )
    if raise_for_status:
        response.raise_for_status()
    return response.json()

