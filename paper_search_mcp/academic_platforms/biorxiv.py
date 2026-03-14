from pathlib import Path
import re
from datetime import datetime, timedelta
from typing import List

import requests
from PyPDF2 import PdfReader

from .._http import DEFAULT_TIMEOUT, RetryPolicy, build_session, request_with_retries
from .._paths import resolve_download_target
from ..paper import Paper
from ._base import PaperSource

class BioRxivSearcher(PaperSource):
    """Searcher for bioRxiv papers"""
    BASE_URL = "https://api.biorxiv.org/details/biorxiv"
    SEARCH_PAGE_SIZE = 100
    MAX_SEARCH_PAGES = 5
    PDF_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/91.0.4472.124 Safari/537.36"
        )
    }

    def __init__(self):
        self.session = build_session(headers=self.PDF_HEADERS)
        self.session.proxies = {'http': None, 'https': None}
        self.timeout = 30
        self.max_retries = 3

    def _retry_policy(self) -> RetryPolicy:
        return RetryPolicy(max_retries=max(self.max_retries - 1, 0))

    def _pdf_target(self, paper_id: str, save_path: str):
        return resolve_download_target(filename=f"{paper_id}.pdf", save_path=save_path)

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
            url=f"https://www.biorxiv.org/content/{doi}v{version}",
            pdf_url=f"https://www.biorxiv.org/content/{doi}v{version}.full.pdf",
            published_date=date,
            updated_date=date,
            source="biorxiv",
            categories=[item["category"]],
            keywords=[],
            doi=doi,
        )

    def search(self, query: str, max_results: int = 10, days: int = 30) -> List[Paper]:
        """
        Search recent bioRxiv metadata for papers matching a free-text query.

        Args:
            query: Free-text query to match against recent paper metadata.
            max_results: Maximum number of papers to return.
            days: Number of days to look back for papers.

        Returns:
            List of Paper objects matching the query within the specified date range.
        """
        normalized_query = self._normalize_search_text(query)
        query_terms = [term for term in normalized_query.split() if term]
        if not query_terms:
            return []

        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        matches = []
        seen_paper_ids = set()
        cursor = 0
        pages_fetched = 0
        while pages_fetched < self.MAX_SEARCH_PAGES:
            url = f"{self.BASE_URL}/{start_date}/{end_date}/{cursor}"
            try:
                response = request_with_retries(
                    self.session,
                    "GET",
                    url,
                    timeout=DEFAULT_TIMEOUT,
                    retry_policy=self._retry_policy(),
                )
                response.raise_for_status()
                data = response.json()
                collection = data.get('collection', [])
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
                    except Exception as e:
                        print(f"Error parsing bioRxiv entry: {e}")
                pages_fetched += 1
                if len(collection) < self.SEARCH_PAGE_SIZE:
                    break  # No more results
                cursor += self.SEARCH_PAGE_SIZE
            except (requests.exceptions.RequestException, ValueError) as e:
                print(f"Failed to connect to bioRxiv API after {self.max_retries} attempts: {e}")
                break

        matches.sort(
            key=lambda match: (match[0], match[1].published_date),
            reverse=True,
        )
        return [paper for _, paper in matches[:max_results]]

    def download_pdf(self, paper_id: str, save_path: str) -> str:
        """
        Download a PDF for a given paper ID from bioRxiv.

        Args:
            paper_id: The DOI of the paper.
            save_path: Directory to save the PDF.

        Returns:
            Path to the downloaded PDF file.
        """
        if not paper_id:
            raise ValueError("Invalid paper_id: paper_id is empty")

        pdf_url = f"https://www.biorxiv.org/content/{paper_id}v1.full.pdf"
        target = self._pdf_target(paper_id, save_path)
        try:
            response = request_with_retries(
                self.session,
                "GET",
                pdf_url,
                headers=self.PDF_HEADERS,
                timeout=DEFAULT_TIMEOUT,
                retry_policy=self._retry_policy(),
            )
            response.raise_for_status()
            target.path.write_bytes(response.content)
            return str(target.path)
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to download PDF after {self.max_retries} attempts: {e}") from e
    
    def read_paper(self, paper_id: str, save_path: str = "./downloads") -> str:
        """
        Read a paper and convert it to text format.
        
        Args:
            paper_id: bioRxiv DOI
            save_path: Directory where the PDF is/will be saved
            
        Returns:
            str: The extracted text content of the paper
        """
        pdf_path = self._pdf_target(paper_id, save_path).path
        if not pdf_path.exists():
            pdf_path = Path(self.download_pdf(paper_id, save_path))
        
        try:
            reader = PdfReader(pdf_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            print(f"Error reading PDF for paper {paper_id}: {e}")
            return ""
