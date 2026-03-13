from pathlib import Path
from typing import List
from datetime import datetime, timedelta

import requests
from PyPDF2 import PdfReader

from .._http import DEFAULT_TIMEOUT, RetryPolicy, build_session, request_with_retries
from .._paths import resolve_download_target
from ..paper import Paper
from ._base import PaperSource

class MedRxivSearcher(PaperSource):
    """Searcher for medRxiv papers"""
    BASE_URL = "https://api.biorxiv.org/details/medrxiv"
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

    def search(self, query: str, max_results: int = 10, days: int = 30) -> List[Paper]:
        """
        Search for papers on medRxiv by category within the last N days.

        Args:
            query: Category name to search for (e.g., "cardiovascular medicine").
            max_results: Maximum number of papers to return.
            days: Number of days to look back for papers.

        Returns:
            List of Paper objects matching the category within the specified date range.
        """
        # Calculate date range: last N days
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        # Format category: lowercase and replace spaces with underscores
        category = query.lower().replace(' ', '_')
        
        papers = []
        cursor = 0
        while len(papers) < max_results:
            url = f"{self.BASE_URL}/{start_date}/{end_date}/{cursor}"
            if category:
                url += f"?category={category}"

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
                        date = datetime.strptime(item['date'], '%Y-%m-%d')
                        papers.append(Paper(
                            paper_id=item['doi'],
                            title=item['title'],
                            authors=item['authors'].split('; '),
                            abstract=item['abstract'],
                            url=f"https://www.medrxiv.org/content/{item['doi']}v{item.get('version', '1')}",
                            pdf_url=f"https://www.medrxiv.org/content/{item['doi']}v{item.get('version', '1')}.full.pdf",
                            published_date=date,
                            updated_date=date,
                            source="medrxiv",
                            categories=[item['category']],
                            keywords=[],
                            doi=item['doi']
                        ))
                    except Exception as e:
                        print(f"Error parsing medRxiv entry: {e}")
                if len(collection) < 100:
                    break  # No more results
                cursor += 100
            except (requests.exceptions.RequestException, ValueError) as e:
                print(f"Failed to connect to medRxiv API after {self.max_retries} attempts: {e}")
                break

        return papers[:max_results]

    def download_pdf(self, paper_id: str, save_path: str) -> str:
        """
        Download a PDF for a given paper ID from medRxiv.

        Args:
            paper_id: The DOI of the paper.
            save_path: Directory to save the PDF.

        Returns:
            Path to the downloaded PDF file.
        """
        if not paper_id:
            raise ValueError("Invalid paper_id: paper_id is empty")

        pdf_url = f"https://www.medrxiv.org/content/{paper_id}v1.full.pdf"
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
            paper_id: medRxiv DOI
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
