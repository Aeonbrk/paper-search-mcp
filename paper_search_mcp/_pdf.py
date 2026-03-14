from __future__ import annotations

from pathlib import Path
from typing import Optional

import requests
from PyPDF2 import PdfReader

from ._http import DEFAULT_TIMEOUT, RetryPolicy, request_with_retries
from ._paths import PathLike, resolve_download_target


DEFAULT_PDF_CHUNK_SIZE = 1024 * 64


class PdfDownloadError(RuntimeError):
    """Raised when a PDF cannot be downloaded safely."""


class PdfTextExtractionError(RuntimeError):
    """Raised when a PDF cannot be parsed into non-empty text."""


def download_pdf_file(
    session: requests.Session,
    url: str,
    *,
    filename: str,
    save_path: Optional[str] = None,
    base_dir: Optional[PathLike] = None,
    timeout=DEFAULT_TIMEOUT,
    retry_policy: RetryPolicy = RetryPolicy(),
    chunk_size: int = DEFAULT_PDF_CHUNK_SIZE,
    **request_kwargs,
) -> Path:
    target = resolve_download_target(
        filename=filename,
        save_path=save_path,
        base_dir=base_dir,
    )
    response = None
    started_write = False

    try:
        response = request_with_retries(
            session,
            "GET",
            url,
            timeout=timeout,
            retry_policy=retry_policy,
            stream=True,
            **request_kwargs,
        )
        response.raise_for_status()
        with target.path.open("wb") as handle:
            started_write = True
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    handle.write(chunk)
    except (OSError, requests.RequestException) as exc:
        if started_write:
            _remove_partial_file(target.path)
        raise PdfDownloadError(f"Failed to download PDF from {url}: {exc}") from exc
    finally:
        if response is not None and hasattr(response, "close"):
            response.close()

    return target.path


def extract_pdf_text(pdf_path: PathLike) -> str:
    path = Path(pdf_path)

    try:
        reader = PdfReader(str(path))
    except Exception as exc:
        raise PdfTextExtractionError(
            f"Failed to open PDF for text extraction: {path}"
        ) from exc

    page_text = []
    for index, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception as exc:
            raise PdfTextExtractionError(
                f"Failed to extract text from page {index} in {path}"
            ) from exc
        stripped = text.strip()
        if stripped:
            page_text.append(stripped)

    if not page_text:
        raise PdfTextExtractionError(f"PDF contains no extractable text: {path}")

    return "\n".join(page_text)


def _remove_partial_file(path: Path) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        return
