from __future__ import annotations

from datetime import datetime, timedelta
import logging
import os
from pathlib import Path
import re
from typing import List

import requests

from .._http import DEFAULT_TIMEOUT, RetryPolicy, build_session, request_with_retries
from .._paths import resolve_download_target
from .._pdf import (
    PdfDownloadError,
    PdfTextExtractionError,
    download_pdf_file,
    extract_pdf_text,
)
from ..paper import Paper
from ._base import PaperSource


class PreprintSearcherBase(PaperSource):
    SEARCH_PAGE_SIZE = 100
    MAX_SEARCH_PAGES = 5
    PDF_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/91.0.4472.124 Safari/537.36"
        )
    }

    SOURCE_NAME = ""
    BASE_URL = ""
    CONTENT_BASE_URL = ""
    DISABLE_PROXIES_ENV = "PAPER_SEARCH_DISABLE_PROXIES"

    def __init__(self):
        self.session = build_session(headers=self.PDF_HEADERS)
        self.timeout = 30
        self.max_retries = 3

    @property
    def logger(self) -> logging.Logger:
        return logging.getLogger(self.__class__.__module__)

    def _proxy_request_kwargs(self) -> dict:
        if os.getenv(self.DISABLE_PROXIES_ENV) != "1":
            return {}
        return {"proxies": {"http": None, "https": None}}

    def _retry_policy(self) -> RetryPolicy:
        return RetryPolicy(max_retries=max(self.max_retries - 1, 0))

    def _pdf_target(self, paper_id: str, save_path: str):
        return resolve_download_target(filename=f"{paper_id}.pdf", save_path=save_path)

    def _request(self, url: str) -> requests.Response:
        return request_with_retries(
            self.session,
            "GET",
            url,
            timeout=DEFAULT_TIMEOUT,
            retry_policy=self._retry_policy(),
            **self._proxy_request_kwargs(),
        )

    def _download(self, url: str, paper_id: str, save_path: str) -> Path:
        return download_pdf_file(
            self.session,
            url,
            filename=f"{paper_id}.pdf",
            save_path=save_path,
            timeout=DEFAULT_TIMEOUT,
            retry_policy=self._retry_policy(),
            headers=self.PDF_HEADERS,
            **self._proxy_request_kwargs(),
        )

    def _extract_text(self, pdf_path: Path) -> str:
        return extract_pdf_text(pdf_path)

    @staticmethod
    def _normalize_search_text(value: str) -> str:
        return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()

    def _score_item(self, item: dict, normalized_query: str, query_terms: List[str]) -> int:
        fields = {
            "title": self._normalize_search_text(item.get("title", "")),
            "abstract": self._normalize_search_text(item.get("abstract", "")),
            "category": self._normalize_search_text(item.get("category", "")),
            "authors": self._normalize_search_text(item.get("authors", "")),
            "doi": self._normalize_search_text(item.get("doi", "")),
        }
        combined = " ".join(fields.values())
        if not combined or any(term not in combined for term in query_terms):
            return 0

        score = len(query_terms)
        if normalized_query and normalized_query in combined:
            score += 2
        if normalized_query and normalized_query in fields["title"]:
            score += 4
        if normalized_query and normalized_query in fields["abstract"]:
            score += 2
        if normalized_query and normalized_query in fields["category"]:
            score += 1
        if normalized_query and normalized_query in fields["authors"]:
            score += 1
        return score

    def _paper_from_item(self, item: dict) -> Paper:
        date = datetime.strptime(item["date"], "%Y-%m-%d")
        version = item.get("version", "1")
        doi = item["doi"]
        return Paper(
            paper_id=doi,
            title=item["title"],
            authors=item["authors"].split("; "),
            abstract=item["abstract"],
            url=f"{self.CONTENT_BASE_URL}/{doi}v{version}",
            pdf_url=f"{self.CONTENT_BASE_URL}/{doi}v{version}.full.pdf",
            published_date=date,
            updated_date=date,
            source=self.SOURCE_NAME,
            categories=[item["category"]],
            keywords=[],
            doi=doi,
        )

    def _pdf_url(self, paper_id: str) -> str:
        return f"{self.CONTENT_BASE_URL}/{paper_id}v1.full.pdf"

    def search(self, query: str, max_results: int = 10, days: int = 30) -> List[Paper]:
        normalized_query = self._normalize_search_text(query)
        query_terms = [term for term in normalized_query.split() if term]
        if not query_terms:
            return []

        now = datetime.now()
        end_date = now.strftime("%Y-%m-%d")
        start_date = (now - timedelta(days=days)).strftime("%Y-%m-%d")

        matches = []
        seen_paper_ids = set()
        cursor = 0
        pages_fetched = 0
        while pages_fetched < self.MAX_SEARCH_PAGES:
            url = f"{self.BASE_URL}/{start_date}/{end_date}/{cursor}"
            try:
                response = self._request(url)
                response.raise_for_status()
                collection = response.json().get("collection", [])
                for item in collection:
                    try:
                        score = self._score_item(item, normalized_query, query_terms)
                        if score <= 0:
                            continue

                        paper = self._paper_from_item(item)
                        if paper.paper_id in seen_paper_ids:
                            continue

                        matches.append((score, paper))
                        seen_paper_ids.add(paper.paper_id)
                    except Exception as exc:
                        self.logger.warning(
                            "Failed to parse %s entry: %s",
                            self.SOURCE_NAME,
                            exc,
                        )
                pages_fetched += 1
                if len(collection) < self.SEARCH_PAGE_SIZE:
                    break
                cursor += self.SEARCH_PAGE_SIZE
            except (requests.RequestException, ValueError) as exc:
                self.logger.warning(
                    "Failed to query %s after %s attempts: %s",
                    self.SOURCE_NAME,
                    self.max_retries,
                    exc,
                )
                break

        matches.sort(key=lambda match: (match[0], match[1].published_date), reverse=True)
        return [paper for _, paper in matches[:max_results]]

    def download_pdf(self, paper_id: str, save_path: str) -> str:
        if not paper_id:
            raise ValueError("Invalid paper_id: paper_id is empty")

        try:
            return str(self._download(self._pdf_url(paper_id), paper_id, save_path))
        except PdfDownloadError as exc:
            raise Exception(
                f"Failed to download PDF after {self.max_retries} attempts: {exc}"
            ) from exc

    def read_paper(self, paper_id: str, save_path: str = "./downloads") -> str:
        pdf_path = self._pdf_target(paper_id, save_path).path
        if not pdf_path.exists():
            pdf_path = Path(self.download_pdf(paper_id, save_path))

        try:
            return self._extract_text(pdf_path)
        except PdfTextExtractionError as exc:
            self.logger.warning("Failed to read %s PDF for %s: %s", self.SOURCE_NAME, paper_id, exc)
            return ""
