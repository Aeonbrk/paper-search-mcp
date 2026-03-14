from datetime import datetime
import logging
from typing import List
from xml.etree import ElementTree as ET

import requests

from .._http import DEFAULT_TIMEOUT, build_session, request_with_retries
from ..paper import Paper
from ._base import PaperSource

logger = logging.getLogger(__name__)


class PubMedSearcher(PaperSource):
    """Searcher for PubMed papers"""
    SEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    FETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

    def __init__(self):
        self.session = build_session()
        self.timeout = DEFAULT_TIMEOUT

    def search(self, query: str, max_results: int = 10) -> List[Paper]:
        search_params = {
            'db': 'pubmed',
            'term': query,
            'retmax': max_results,
            'retmode': 'xml'
        }
        search_root = self._get_xml(
            self.SEARCH_URL,
            search_params,
            description="search results",
        )
        if search_root is None:
            return []

        ids = [node.text for node in search_root.findall(".//Id") if node.text]
        if not ids:
            return []
        
        fetch_params = {
            'db': 'pubmed',
            'id': ','.join(ids),
            'retmode': 'xml'
        }
        fetch_root = self._get_xml(
            self.FETCH_URL,
            fetch_params,
            description="article details",
        )
        if fetch_root is None:
            return []

        papers = []
        for article in fetch_root.findall('.//PubmedArticle'):
            try:
                pmid_node = article.find(".//PMID")
                title_node = article.find(".//ArticleTitle")
                year_node = article.find(".//PubDate/Year")
                if pmid_node is None or title_node is None or year_node is None:
                    continue

                pmid = pmid_node.text or ""
                title = title_node.text or ""

                authors = []
                for author in article.findall(".//Author"):
                    last = author.findtext("LastName") or ""
                    initials = author.findtext("Initials") or ""
                    name = f"{last} {initials}".strip()
                    if name:
                        authors.append(name)

                abstract_node = article.find(".//AbstractText")
                abstract = abstract_node.text if abstract_node is not None and abstract_node.text else ""

                pub_date = year_node.text or ""
                published = datetime.strptime(pub_date, "%Y")

                doi_node = article.find('.//ELocationID[@EIdType="doi"]')
                doi = doi_node.text if doi_node is not None and doi_node.text else ""
                papers.append(Paper(
                    paper_id=pmid,
                    title=title,
                    authors=authors,
                    abstract=abstract,
                    url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                    pdf_url='',  # PubMed 无直接 PDF
                    published_date=published,
                    updated_date=published,
                    source='pubmed',
                    categories=[],
                    keywords=[],
                    doi=doi
                ))
            except (AttributeError, TypeError, ValueError) as exc:
                logger.warning("Error parsing PubMed article: %s", exc)
        return papers

    def _get_xml(
        self,
        url: str,
        params: dict[str, object],
        *,
        description: str,
    ) -> ET.Element | None:
        try:
            response = request_with_retries(
                self.session,
                "GET",
                url,
                params=params,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.warning("Error fetching PubMed %s: %s", description, exc)
            return None

        try:
            return ET.fromstring(response.content)
        except ET.ParseError as exc:
            logger.warning("Error parsing PubMed %s XML: %s", description, exc)
            return None

    def download_pdf(self, paper_id: str, save_path: str) -> str:
        """Attempt to download a paper's PDF from PubMed.

        Args:
            paper_id: PubMed ID (PMID)
            save_path: Directory to save the PDF

        Returns:
            str: Error message indicating PDF download is not supported
        
        Raises:
            NotImplementedError: Always raises this error as PubMed doesn't provide direct PDF access
        """
        message = ("PubMed does not provide direct PDF downloads. "
                  "Please use the paper's DOI or URL to access the publisher's website.")
        raise NotImplementedError(message)

    def read_paper(self, paper_id: str, save_path: str = "./downloads") -> str:
        """Attempt to read and extract text from a PubMed paper.

        Args:
            paper_id: PubMed ID (PMID)
            save_path: Directory for potential PDF storage (unused)

        Returns:
            str: Error message indicating PDF reading is not supported
        """
        message = ("PubMed papers cannot be read directly through this tool. "
                  "Only metadata and abstracts are available through PubMed's API. "
                  "Please use the paper's DOI or URL to access the full text on the publisher's website.")
        return message

if __name__ == "__main__":
    # 测试 PubMedSearcher 的功能
    searcher = PubMedSearcher()
    
    # 测试搜索功能
    print("Testing search functionality...")
    query = "machine learning"
    max_results = 5
    try:
        papers = searcher.search(query, max_results=max_results)
        print(f"Found {len(papers)} papers for query '{query}':")
        for i, paper in enumerate(papers, 1):
            print(f"{i}. {paper.title}")
            print(f"   Authors: {', '.join(paper.authors)}")
            print(f"   DOI: {paper.doi}")
            print(f"   URL: {paper.url}\n")
    except Exception as e:
        print(f"Error during search: {e}")
    
    # 测试 PDF 下载功能（会返回不支持的提示）
    if papers:
        print("\nTesting PDF download functionality...")
        paper_id = papers[0].paper_id
        try:
            pdf_path = searcher.download_pdf(paper_id, "./downloads")
        except NotImplementedError as e:
            print(f"Expected error: {e}")
    
    # 测试论文阅读功能（会返回不支持的提示）
    if papers:
        print("\nTesting paper reading functionality...")
        paper_id = papers[0].paper_id
        try:
            message = searcher.read_paper(paper_id)
            print(f"Response: {message}")
        except Exception as e:
            print(f"Error during paper reading: {e}")
