from typing import List, Optional
from datetime import datetime
from math import ceil
import hashlib
import requests
from bs4 import BeautifulSoup
import time
import random
from ..paper import Paper
from .._http import DEFAULT_TIMEOUT, RetryPolicy, build_session, request_with_retries
from ._base import PaperSource
import logging

logger = logging.getLogger(__name__)

class GoogleScholarSearcher(PaperSource):
    """Custom implementation of Google Scholar paper search"""
    
    SCHOLAR_URL = "https://scholar.google.com/scholar"
    BROWSERS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
    ]

    def __init__(self):
        self._setup_session()

    def _setup_session(self):
        """Initialize session with random user agent"""
        self.session = build_session(
            user_agent=random.choice(self.BROWSERS),
            headers={
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "en-US,en;q=0.9",
            },
        )

    def _stable_paper_id(self, *, url: str, title: str, authors: List[str]) -> str:
        basis = url.strip()
        if not basis:
            basis = f"{title}|{'|'.join(a.strip() for a in authors if a.strip())}"
        digest = hashlib.sha256(basis.encode("utf-8")).hexdigest()[:16]
        return f"gs_{digest}"

    def _extract_year(self, text: str) -> Optional[int]:
        """Extract year from publication info"""
        for word in text.split():
            if word.isdigit() and 1900 <= int(word) <= datetime.now().year:
                return int(word)
        return None

    def _parse_paper(self, item) -> Optional[Paper]:
        """Parse single paper entry from HTML"""
        try:
            # Extract main paper elements
            title_elem = item.find('h3', class_='gs_rt')
            info_elem = item.find('div', class_='gs_a')
            abstract_elem = item.find('div', class_='gs_rs')

            if not title_elem or not info_elem:
                return None

            # Process title and URL
            title = title_elem.get_text(strip=True).replace('[PDF]', '').replace('[HTML]', '')
            link = title_elem.find('a', href=True)
            url = link['href'] if link else ''

            # Process author info
            info_text = info_elem.get_text()
            authors = [a.strip() for a in info_text.split('-')[0].split(',')]
            year = self._extract_year(info_text)

            # Create paper object
            return Paper(
                paper_id=self._stable_paper_id(url=url, title=title, authors=authors),
                title=title,
                authors=authors,
                abstract=abstract_elem.get_text() if abstract_elem else "",
                url=url,
                pdf_url="",
                published_date=datetime(year, 1, 1) if year else None,
                updated_date=None,
                source="google_scholar",
                categories=[],
                keywords=[],
                doi="",
                citations=0
            )
        except Exception as e:
            logger.warning(f"Failed to parse paper: {e}")
            return None

    def search(self, query: str, max_results: int = 10) -> List[Paper]:
        """
        Search Google Scholar with custom parameters
        """
        papers = []
        start = 0
        results_per_page = min(10, max_results)
        max_pages = max(1, ceil(max_results / results_per_page))
        retry_policy = RetryPolicy(
            max_retries=2,
            backoff_base_seconds=1.0,
            backoff_factor=2.0,
            backoff_max_seconds=8.0,
        )

        for _ in range(max_pages):
            # Construct search parameters
            params = {
                'q': query,
                'start': start,
                'hl': 'en',
                'as_sdt': '0,5'  # Include articles and citations
            }

            # Keep a small delay only for follow-up pages.
            if start > 0:
                time.sleep(random.uniform(1.0, 3.0))

            response = request_with_retries(
                self.session,
                "GET",
                self.SCHOLAR_URL,
                params=params,
                timeout=DEFAULT_TIMEOUT,
                retry_policy=retry_policy,
            )
            response.raise_for_status()

            # Parse results
            soup = BeautifulSoup(response.text, 'html.parser')
            results = soup.find_all('div', class_='gs_ri')

            if not results:
                break

            # Process each result
            for item in results:
                if len(papers) >= max_results:
                    break

                paper = self._parse_paper(item)
                if paper:
                    papers.append(paper)

            if len(papers) >= max_results:
                break

            start += results_per_page

        return papers[:max_results]

    def download_pdf(self, paper_id: str, save_path: str) -> str:
        """
        Google Scholar doesn't support direct PDF downloads
        
        Raises:
            NotImplementedError: Always raises this error
        """
        raise NotImplementedError(
            "Google Scholar doesn't provide direct PDF downloads. "
            "Please use the paper URL to access the publisher's website."
        )

    def read_paper(self, paper_id: str, save_path: str = "./downloads") -> str:
        """
        Google Scholar doesn't support direct paper reading
        
        Returns:
            str: Message indicating the feature is not supported
        """
        return (
            "Google Scholar doesn't support direct paper reading. "
            "Please use the paper URL to access the full text on the publisher's website."
        )

if __name__ == "__main__":
    # Test Google Scholar searcher
    searcher = GoogleScholarSearcher()
    
    print("Testing search functionality...")
    query = "machine learning"
    max_results = 5
    
    try:
        papers = searcher.search(query, max_results=max_results)
        print(f"\nFound {len(papers)} papers for query '{query}':")
        for i, paper in enumerate(papers, 1):
            print(f"\n{i}. {paper.title}")
            print(f"   Authors: {', '.join(paper.authors)}")
            print(f"   Citations: {paper.citations}")
            print(f"   URL: {paper.url}")
    except Exception as e:
        print(f"Error during search: {e}")
