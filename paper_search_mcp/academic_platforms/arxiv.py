from datetime import datetime
import logging
from pathlib import Path
from typing import List

import feedparser
import requests

from .._http import DEFAULT_TIMEOUT, RetryPolicy, build_session, request_with_retries
from .._paths import resolve_download_target
from .._pdf import PdfDownloadError, PdfTextExtractionError, download_pdf_file, extract_pdf_text
from ..paper import Paper
from ._base import PaperSource

logger = logging.getLogger(__name__)


class ArxivSearcher(PaperSource):
    """Searcher for arXiv papers"""
    BASE_URL = "http://export.arxiv.org/api/query"

    def __init__(self):
        self.session = build_session()
        self.timeout = DEFAULT_TIMEOUT
        self.retry_policy = RetryPolicy(max_retries=2, backoff_base_seconds=1.0)

    def search(self, query: str, max_results: int = 10) -> List[Paper]:
        params = {
            'search_query': query,
            'max_results': max_results,
            'sortBy': 'submittedDate',
            'sortOrder': 'descending'
        }
        try:
            response = request_with_retries(
                self.session,
                "GET",
                self.BASE_URL,
                params=params,
                timeout=self.timeout,
                retry_policy=self.retry_policy,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.warning("Error fetching arXiv results for %r: %s", query, exc)
            return []
        feed = feedparser.parse(response.content)
        papers = []
        for entry in feed.entries:
            try:
                authors = [author.name for author in getattr(entry, "authors", [])]
                published = datetime.strptime(entry.published, '%Y-%m-%dT%H:%M:%SZ')
                updated = datetime.strptime(entry.updated, '%Y-%m-%dT%H:%M:%SZ')
                pdf_url = next(
                    (
                        link.href
                        for link in getattr(entry, "links", [])
                        if getattr(link, "type", "") == 'application/pdf'
                    ),
                    '',
                )
                papers.append(Paper(
                    paper_id=entry.id.split('/')[-1],
                    title=entry.title,
                    authors=authors,
                    abstract=entry.summary,
                    url=entry.id,
                    pdf_url=pdf_url,
                    published_date=published,
                    updated_date=updated,
                    source='arxiv',
                    categories=[tag.term for tag in getattr(entry, "tags", [])],
                    keywords=[],
                    doi=entry.get('arxiv_doi', entry.get('doi', ''))
                ))
            except (AttributeError, KeyError, TypeError, ValueError) as exc:
                logger.warning(
                    "Error parsing arXiv entry %r: %s",
                    getattr(entry, "id", "<unknown>"),
                    exc,
                )
        return papers

    def download_pdf(self, paper_id: str, save_path: str) -> str:
        pdf_url = f"https://arxiv.org/pdf/{paper_id}.pdf"
        try:
            target_path = download_pdf_file(
                self.session,
                pdf_url,
                filename=f"{paper_id}.pdf",
                save_path=save_path,
                timeout=self.timeout,
                retry_policy=self.retry_policy,
            )
        except PdfDownloadError as exc:
            raise RuntimeError(
                f"Failed to download arXiv PDF for {paper_id}: {exc}"
            ) from exc

        return str(target_path)

    def read_paper(self, paper_id: str, save_path: str = "./downloads") -> str:
        """Read a paper and convert it to text format.
        
        Args:
            paper_id: arXiv paper ID
            save_path: Directory where the PDF is/will be saved
            
        Returns:
            str: The extracted text content of the paper
        """
        target = resolve_download_target(filename=f"{paper_id}.pdf", save_path=save_path)
        pdf_path = target.path
        if not pdf_path.exists():
            pdf_path = Path(self.download_pdf(paper_id, save_path))

        try:
            return extract_pdf_text(pdf_path)
        except PdfTextExtractionError as exc:
            raise RuntimeError(
                f"Failed to read arXiv PDF for {paper_id}: {exc}"
            ) from exc

if __name__ == "__main__":
    # 测试 ArxivSearcher 的功能
    searcher = ArxivSearcher()
    
    # 测试搜索功能
    print("Testing search functionality...")
    query = "machine learning"
    max_results = 5
    try:
        papers = searcher.search(query, max_results=max_results)
        print(f"Found {len(papers)} papers for query '{query}':")
        for i, paper in enumerate(papers, 1):
            print(f"{i}. {paper.title} (ID: {paper.paper_id})")
    except Exception as e:
        print(f"Error during search: {e}")
    
    # 测试 PDF 下载功能
    if papers:
        print("\nTesting PDF download functionality...")
        paper_id = papers[0].paper_id
        save_path = "./downloads"  # 确保此目录存在
        try:
            Path(save_path).mkdir(parents=True, exist_ok=True)
            pdf_path = searcher.download_pdf(paper_id, save_path)
            print(f"PDF downloaded successfully: {pdf_path}")
        except Exception as e:
            print(f"Error during PDF download: {e}")

    # 测试论文阅读功能
    if papers:
        print("\nTesting paper reading functionality...")
        paper_id = papers[0].paper_id
        try:
            text_content = searcher.read_paper(paper_id)
            print(f"\nFirst 500 characters of the paper content:")
            print(text_content[:500] + "...")
            print(f"\nTotal length of extracted text: {len(text_content)} characters")
        except Exception as e:
            print(f"Error during paper reading: {e}")
