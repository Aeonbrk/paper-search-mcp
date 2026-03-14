from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence, Tuple

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


DEFAULT_CONNECT_TIMEOUT_S = 10.0
DEFAULT_READ_TIMEOUT_S = 30.0
DEFAULT_TIMEOUT: Tuple[float, float] = (DEFAULT_CONNECT_TIMEOUT_S, DEFAULT_READ_TIMEOUT_S)

DEFAULT_USER_AGENT = "paper-search-mcp (requests)"
DEFAULT_POOL_CONNECTIONS = 10
DEFAULT_POOL_MAXSIZE = 10
DEFAULT_ALLOWED_RETRY_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})

RETRYABLE_STATUS_CODES = frozenset({429, 500, 502, 503, 504})


@dataclass(frozen=True)
class RetryPolicy:
    max_retries: int = 3
    retryable_status_codes: Sequence[int] = tuple(RETRYABLE_STATUS_CODES)
    backoff_base_seconds: float = 1.0
    backoff_factor: float = 2.0
    backoff_max_seconds: float = 30.0
    allowed_methods: Sequence[str] = tuple(DEFAULT_ALLOWED_RETRY_METHODS)


@dataclass(frozen=True)
class TransportConfig:
    retry_policy: RetryPolicy
    retry_on_status_codes: Tuple[int, ...]
    pool_connections: int
    pool_maxsize: int
    pool_block: bool


class TransportError(requests.RequestException):
    def __init__(
        self,
        *,
        method: str,
        url: str,
        attempts: int,
        timeout: Tuple[float, float],
        cause: requests.RequestException,
    ) -> None:
        message = (
            f"{method.upper()} {url} failed after {attempts} attempt(s) "
            f"with timeout={timeout}: {cause}"
        )
        super().__init__(
            message,
            request=getattr(cause, "request", None),
            response=getattr(cause, "response", None),
        )
        self.method = method.upper()
        self.url = url
        self.attempts = attempts
        self.timeout = timeout


def _normalize_retry_status_codes(
    retry_policy: RetryPolicy,
    retry_on_status_codes: Optional[Iterable[int]] = None,
) -> Tuple[int, ...]:
    source = (
        retry_policy.retryable_status_codes
        if retry_on_status_codes is None
        else retry_on_status_codes
    )
    return tuple(dict.fromkeys(int(code) for code in source))


def _build_retry(
    retry_policy: RetryPolicy,
    retry_on_status_codes: Optional[Iterable[int]] = None,
) -> Retry:
    retryable_status_codes = _normalize_retry_status_codes(
        retry_policy, retry_on_status_codes
    )
    return Retry(
        total=retry_policy.max_retries,
        connect=retry_policy.max_retries,
        read=retry_policy.max_retries,
        status=retry_policy.max_retries if retryable_status_codes else 0,
        other=retry_policy.max_retries,
        allowed_methods=frozenset(
            method.upper() for method in retry_policy.allowed_methods
        ),
        status_forcelist=retryable_status_codes,
        backoff_factor=retry_policy.backoff_base_seconds,
        backoff_max=retry_policy.backoff_max_seconds,
        raise_on_status=False,
        respect_retry_after_header=True,
    )


def configure_session_transport(
    session: requests.Session,
    *,
    retry_policy: RetryPolicy = RetryPolicy(),
    retry_on_status_codes: Optional[Iterable[int]] = None,
    pool_connections: int = DEFAULT_POOL_CONNECTIONS,
    pool_maxsize: int = DEFAULT_POOL_MAXSIZE,
    pool_block: bool = False,
) -> requests.Session:
    transport_config = TransportConfig(
        retry_policy=retry_policy,
        retry_on_status_codes=_normalize_retry_status_codes(
            retry_policy, retry_on_status_codes
        ),
        pool_connections=pool_connections,
        pool_maxsize=pool_maxsize,
        pool_block=pool_block,
    )
    current_config = getattr(session, "_paper_search_transport_config", None)
    if current_config == transport_config:
        return session

    adapter = HTTPAdapter(
        max_retries=_build_retry(retry_policy, transport_config.retry_on_status_codes),
        pool_connections=pool_connections,
        pool_maxsize=pool_maxsize,
        pool_block=pool_block,
    )
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    setattr(session, "_paper_search_transport_config", transport_config)
    return session


def build_session(
    *,
    user_agent: Optional[str] = None,
    headers: Optional[Mapping[str, str]] = None,
    retry_policy: RetryPolicy = RetryPolicy(),
    retry_on_status_codes: Optional[Iterable[int]] = None,
    pool_connections: int = DEFAULT_POOL_CONNECTIONS,
    pool_maxsize: int = DEFAULT_POOL_MAXSIZE,
    pool_block: bool = False,
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
    return configure_session_transport(
        session,
        retry_policy=retry_policy,
        retry_on_status_codes=retry_on_status_codes,
        pool_connections=pool_connections,
        pool_maxsize=pool_maxsize,
        pool_block=pool_block,
    )


def request_with_retries(
    session: requests.Session,
    method: str,
    url: str,
    *,
    timeout: Tuple[float, float] = DEFAULT_TIMEOUT,
    retry_policy: Optional[RetryPolicy] = None,
    retry_on_status_codes: Optional[Iterable[int]] = None,
    **kwargs: Any,
) -> requests.Response:
    """
    Make a request with a consistent retry/pooling configuration.
    """
    transport_config = getattr(session, "_paper_search_transport_config", None)
    effective_retry_policy = (
        retry_policy
        if retry_policy is not None
        else (
            transport_config.retry_policy
            if isinstance(transport_config, TransportConfig)
            else RetryPolicy()
        )
    )
    pool_connections = (
        transport_config.pool_connections
        if isinstance(transport_config, TransportConfig)
        else DEFAULT_POOL_CONNECTIONS
    )
    pool_maxsize = (
        transport_config.pool_maxsize
        if isinstance(transport_config, TransportConfig)
        else DEFAULT_POOL_MAXSIZE
    )
    pool_block = (
        transport_config.pool_block
        if isinstance(transport_config, TransportConfig)
        else False
    )

    configure_session_transport(
        session,
        retry_policy=effective_retry_policy,
        retry_on_status_codes=retry_on_status_codes,
        pool_connections=pool_connections,
        pool_maxsize=pool_maxsize,
        pool_block=pool_block,
    )
    try:
        return session.request(method, url, timeout=timeout, **kwargs)
    except requests.RequestException as exc:
        raise TransportError(
            method=method,
            url=url,
            attempts=effective_retry_policy.max_retries + 1,
            timeout=timeout,
            cause=exc,
        ) from exc


def get_text(
    session: requests.Session,
    url: str,
    *,
    timeout: Tuple[float, float] = DEFAULT_TIMEOUT,
    retry_policy: Optional[RetryPolicy] = None,
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
    retry_policy: Optional[RetryPolicy] = None,
    raise_for_status: bool = True,
    **kwargs: Any,
) -> Dict[str, Any]:
    response = request_with_retries(
        session, "GET", url, timeout=timeout, retry_policy=retry_policy, **kwargs
    )
    if raise_for_status:
        response.raise_for_status()
    return response.json()
