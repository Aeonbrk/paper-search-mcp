# paper_search_mcp/server.py
import asyncio
from typing import Any, Callable, Dict, List, Optional, Type

from mcp.server.fastmcp import FastMCP

from .academic_platforms.arxiv import ArxivSearcher
from .academic_platforms.pubmed import PubMedSearcher
from .academic_platforms.pmc import PMCSearcher
from .academic_platforms.biorxiv import BioRxivSearcher
from .academic_platforms.medrxiv import MedRxivSearcher
from .academic_platforms.google_scholar import GoogleScholarSearcher
from .academic_platforms.iacr import IACRSearcher
from .academic_platforms.semantic import SemanticSearcher
from .academic_platforms.crossref import CrossRefSearcher

# from .academic_platforms.hub import SciHubSearcher
from ._paths import resolve_download_target

# Initialize MCP server
mcp = FastMCP("paper_search_server")

_MAX_CONCURRENT_TOOL_CALLS = 8
_TOOL_SEMAPHORE = asyncio.Semaphore(_MAX_CONCURRENT_TOOL_CALLS)


_CANONICAL_SAVE_PATH = "docs/downloads"


def _canonical_save_path(_: str) -> str:
    resolve_download_target(filename="paper.pdf", save_path=_CANONICAL_SAVE_PATH)
    return _CANONICAL_SAVE_PATH


async def _run_sync(callable_: Callable[..., Any], /, *args: Any, **kwargs: Any) -> Any:
    async with _TOOL_SEMAPHORE:
        return await asyncio.to_thread(callable_, *args, **kwargs)


def _serialize_search_results(papers: Optional[List[Any]]) -> List[Dict]:
    if not papers:
        return []
    return [paper.to_dict() for paper in papers]


def _search_sync(
    searcher_cls: Type[Any], query: str, max_results: int, kwargs: Optional[Dict[str, Any]] = None
) -> List[Dict]:
    searcher = searcher_cls()
    if kwargs:
        papers = searcher.search(query, max_results=max_results, **kwargs)
    else:
        papers = searcher.search(query, max_results=max_results)
    return _serialize_search_results(papers)


def _download_sync(searcher_cls: Type[Any], paper_id: str, save_path: str) -> str:
    save_dir = _canonical_save_path(save_path)
    searcher = searcher_cls()
    return searcher.download_pdf(paper_id, save_dir)


def _read_sync(searcher_cls: Type[Any], paper_id: str, save_path: str) -> str:
    save_dir = _canonical_save_path(save_path)
    searcher = searcher_cls()
    return searcher.read_paper(paper_id, save_dir)


# Tool definitions
@mcp.tool()
async def search_arxiv(query: str, max_results: int = 10) -> List[Dict]:
    """Search academic papers from arXiv.

    Args:
        query: Search query string (e.g., 'machine learning').
        max_results: Maximum number of papers to return (default: 10).
    Returns:
        List of paper metadata in dictionary format.
    """
    return await _run_sync(_search_sync, ArxivSearcher, query, max_results)


@mcp.tool()
async def search_pubmed(query: str, max_results: int = 10) -> List[Dict]:
    """Search academic papers from PubMed.

    Args:
        query: Search query string (e.g., 'machine learning').
        max_results: Maximum number of papers to return (default: 10).
    Returns:
        List of paper metadata in dictionary format.
    """
    return await _run_sync(_search_sync, PubMedSearcher, query, max_results)


@mcp.tool()
async def search_pmc(query: str, max_results: int = 10) -> List[Dict]:
    """Search academic papers from PubMed Central (PMC).

    Args:
        query: Search query string (e.g., 'machine learning').
        max_results: Maximum number of papers to return (default: 10).
    Returns:
        List of paper metadata in dictionary format.
    """
    return await _run_sync(_search_sync, PMCSearcher, query, max_results)


@mcp.tool()
async def search_biorxiv(query: str, max_results: int = 10) -> List[Dict]:
    """Search academic papers from bioRxiv.

    Args:
        query: Search query string (e.g., 'machine learning').
        max_results: Maximum number of papers to return (default: 10).
    Returns:
        List of paper metadata in dictionary format.
    """
    return await _run_sync(_search_sync, BioRxivSearcher, query, max_results)


@mcp.tool()
async def search_medrxiv(query: str, max_results: int = 10) -> List[Dict]:
    """Search academic papers from medRxiv.

    Args:
        query: Search query string (e.g., 'machine learning').
        max_results: Maximum number of papers to return (default: 10).
    Returns:
        List of paper metadata in dictionary format.
    """
    return await _run_sync(_search_sync, MedRxivSearcher, query, max_results)


@mcp.tool()
async def search_google_scholar(query: str, max_results: int = 10) -> List[Dict]:
    """Search academic papers from Google Scholar.

    Args:
        query: Search query string (e.g., 'machine learning').
        max_results: Maximum number of papers to return (default: 10).
    Returns:
        List of paper metadata in dictionary format.
    """
    return await _run_sync(_search_sync, GoogleScholarSearcher, query, max_results)


@mcp.tool()
async def search_iacr(
    query: str, max_results: int = 10, fetch_details: bool = True
) -> List[Dict]:
    """Search academic papers from IACR ePrint Archive.

    Args:
        query: Search query string (e.g., 'cryptography', 'secret sharing').
        max_results: Maximum number of papers to return (default: 10).
        fetch_details: Whether to fetch detailed information for each paper (default: True).
    Returns:
        List of paper metadata in dictionary format.
    """
    def _search_iacr_sync() -> List[Dict]:
        searcher = IACRSearcher()
        papers = searcher.search(query, max_results, fetch_details)
        return _serialize_search_results(papers)

    return await _run_sync(_search_iacr_sync)


@mcp.tool()
async def download_arxiv(paper_id: str, save_path: str = "./downloads") -> str:
    """Download PDF of an arXiv paper.

    Args:
        paper_id: arXiv paper ID (e.g., '2106.12345').
        save_path: Compatibility parameter. MCP tools always write under
            `docs/downloads`; custom values do not change the output directory.
    Returns:
        Path to the downloaded PDF file.
    """
    return await _run_sync(_download_sync, ArxivSearcher, paper_id, save_path)


@mcp.tool()
async def download_pubmed(paper_id: str, save_path: str = "./downloads") -> str:
    """Attempt to download PDF of a PubMed paper.

    Args:
        paper_id: PubMed ID (PMID).
        save_path: Compatibility parameter. MCP tools always write under
            `docs/downloads`; custom values do not change the output directory.
    Returns:
        str: Message indicating that direct PDF download is not supported.
    """
    try:
        return await _run_sync(_download_sync, PubMedSearcher, paper_id, save_path)
    except NotImplementedError as e:
        return str(e)


@mcp.tool()
async def download_pmc(paper_id: str, save_path: str = "./downloads") -> str:
    """Return the PMC download limitation message.

    Args:
        paper_id: PMC ID (PMCID, for example `PMC1234567`).
        save_path: Compatibility parameter. PMC v1 ignores this value because
            download is not supported.
    Returns:
        `LIMITATION:` + JSON limitation message.
    """
    del save_path
    searcher = PMCSearcher()
    return await _run_sync(searcher.download_pdf, paper_id, "")


@mcp.tool()
async def download_biorxiv(paper_id: str, save_path: str = "./downloads") -> str:
    """Download PDF of a bioRxiv paper.

    Args:
        paper_id: bioRxiv DOI.
        save_path: Compatibility parameter. MCP tools always write under
            `docs/downloads`; custom values do not change the output directory.
    Returns:
        Path to the downloaded PDF file.
    """
    return await _run_sync(_download_sync, BioRxivSearcher, paper_id, save_path)


@mcp.tool()
async def download_medrxiv(paper_id: str, save_path: str = "./downloads") -> str:
    """Download PDF of a medRxiv paper.

    Args:
        paper_id: medRxiv DOI.
        save_path: Compatibility parameter. MCP tools always write under
            `docs/downloads`; custom values do not change the output directory.
    Returns:
        Path to the downloaded PDF file.
    """
    return await _run_sync(_download_sync, MedRxivSearcher, paper_id, save_path)


@mcp.tool()
async def download_iacr(paper_id: str, save_path: str = "./downloads") -> str:
    """Download PDF of an IACR ePrint paper.

    Args:
        paper_id: IACR paper ID (e.g., '2009/101').
        save_path: Compatibility parameter. MCP tools always write under
            `docs/downloads`; custom values do not change the output directory.
    Returns:
        Path to the downloaded PDF file.
    """
    return await _run_sync(_download_sync, IACRSearcher, paper_id, save_path)


@mcp.tool()
async def read_arxiv_paper(paper_id: str, save_path: str = "./downloads") -> str:
    """Read and extract text content from an arXiv paper PDF.

    Args:
        paper_id: arXiv paper ID (e.g., '2106.12345').
        save_path: Compatibility parameter. MCP tools always use
            `docs/downloads`; custom values do not change the read/download
            directory.
    Returns:
        str: The extracted text content of the paper.
    """
    try:
        return await _run_sync(_read_sync, ArxivSearcher, paper_id, save_path)
    except Exception as e:
        print(f"Error reading paper {paper_id}: {e}")
        return ""


@mcp.tool()
async def read_pubmed_paper(paper_id: str, save_path: str = "./downloads") -> str:
    """Read and extract text content from a PubMed paper.

    Args:
        paper_id: PubMed ID (PMID).
        save_path: Compatibility parameter. MCP tools always use
            `docs/downloads`; custom values do not change the read/download
            directory.
    Returns:
        str: Message indicating that direct paper reading is not supported.
    """
    return await _run_sync(_read_sync, PubMedSearcher, paper_id, save_path)


@mcp.tool()
async def read_pmc_paper(paper_id: str, save_path: str = "./downloads") -> str:
    """Return the PMC read limitation message.

    Args:
        paper_id: PMC ID (PMCID, for example `PMC1234567`).
        save_path: Compatibility parameter. PMC v1 ignores this value because
            read is not supported.
    Returns:
        `LIMITATION:` + JSON limitation message.
    """
    del save_path
    searcher = PMCSearcher()
    return await _run_sync(searcher.read_paper, paper_id, "")


@mcp.tool()
async def read_biorxiv_paper(paper_id: str, save_path: str = "./downloads") -> str:
    """Read and extract text content from a bioRxiv paper PDF.

    Args:
        paper_id: bioRxiv DOI.
        save_path: Compatibility parameter. MCP tools always use
            `docs/downloads`; custom values do not change the read/download
            directory.
    Returns:
        str: The extracted text content of the paper.
    """
    try:
        return await _run_sync(_read_sync, BioRxivSearcher, paper_id, save_path)
    except Exception as e:
        print(f"Error reading paper {paper_id}: {e}")
        return ""


@mcp.tool()
async def read_medrxiv_paper(paper_id: str, save_path: str = "./downloads") -> str:
    """Read and extract text content from a medRxiv paper PDF.

    Args:
        paper_id: medRxiv DOI.
        save_path: Compatibility parameter. MCP tools always use
            `docs/downloads`; custom values do not change the read/download
            directory.
    Returns:
        str: The extracted text content of the paper.
    """
    try:
        return await _run_sync(_read_sync, MedRxivSearcher, paper_id, save_path)
    except Exception as e:
        print(f"Error reading paper {paper_id}: {e}")
        return ""


@mcp.tool()
async def read_iacr_paper(paper_id: str, save_path: str = "./downloads") -> str:
    """Read and extract text content from an IACR ePrint paper PDF.

    Args:
        paper_id: IACR paper ID (e.g., '2009/101').
        save_path: Compatibility parameter. MCP tools always use
            `docs/downloads`; custom values do not change the read/download
            directory.
    Returns:
        str: The extracted text content of the paper.
    """
    try:
        return await _run_sync(_read_sync, IACRSearcher, paper_id, save_path)
    except Exception as e:
        print(f"Error reading paper {paper_id}: {e}")
        return ""


@mcp.tool()
async def search_semantic(query: str, year: Optional[str] = None, max_results: int = 10) -> List[Dict]:
    """Search academic papers from Semantic Scholar.

    Args:
        query: Search query string (e.g., 'machine learning').
        year: Optional year filter (e.g., '2019', '2016-2020', '2010-', '-2015').
        max_results: Maximum number of papers to return (default: 10).
    Returns:
        List of paper metadata in dictionary format.
    """
    kwargs: Dict[str, Any] = {}
    if year is not None:
        kwargs["year"] = year
    return await _run_sync(_search_sync, SemanticSearcher, query, max_results, kwargs)


@mcp.tool()
async def download_semantic(paper_id: str, save_path: str = "./downloads") -> str:
    """Download PDF of a Semantic Scholar paper.    

    Args:
        paper_id: Semantic Scholar paper ID, Paper identifier in one of the following formats:
            - Semantic Scholar ID (e.g., "649def34f8be52c8b66281af98ae884c09aef38b")
            - DOI:<doi> (e.g., "DOI:10.18653/v1/N18-3011")
            - ARXIV:<id> (e.g., "ARXIV:2106.15928")
            - MAG:<id> (e.g., "MAG:112218234")
            - ACL:<id> (e.g., "ACL:W12-3903")
            - PMID:<id> (e.g., "PMID:19872477")
            - PMCID:<id> (e.g., "PMCID:2323736")
            - URL:<url> (e.g., "URL:https://arxiv.org/abs/2106.15928v1")
        save_path: Compatibility parameter. MCP tools always write under
            `docs/downloads`; custom values do not change the output directory.
    Returns:
        Path to the downloaded PDF file.
    """ 
    return await _run_sync(_download_sync, SemanticSearcher, paper_id, save_path)


@mcp.tool()
async def read_semantic_paper(paper_id: str, save_path: str = "./downloads") -> str:
    """Read and extract text content from a Semantic Scholar paper. 

    Args:
        paper_id: Semantic Scholar paper ID, Paper identifier in one of the following formats:
            - Semantic Scholar ID (e.g., "649def34f8be52c8b66281af98ae884c09aef38b")
            - DOI:<doi> (e.g., "DOI:10.18653/v1/N18-3011")
            - ARXIV:<id> (e.g., "ARXIV:2106.15928")
            - MAG:<id> (e.g., "MAG:112218234")
            - ACL:<id> (e.g., "ACL:W12-3903")
            - PMID:<id> (e.g., "PMID:19872477")
            - PMCID:<id> (e.g., "PMCID:2323736")
            - URL:<url> (e.g., "URL:https://arxiv.org/abs/2106.15928v1")
        save_path: Compatibility parameter. MCP tools always use
            `docs/downloads`; custom values do not change the read/download
            directory.
    Returns:
        str: The extracted text content of the paper.
    """
    try:
        return await _run_sync(_read_sync, SemanticSearcher, paper_id, save_path)
    except Exception as e:
        print(f"Error reading paper {paper_id}: {e}")
        return ""


@mcp.tool()
async def search_crossref(
    query: str,
    max_results: int = 10,
    filter: Optional[str] = None,
    sort: Optional[str] = None,
    order: Optional[str] = None,
) -> List[Dict]:
    """Search academic papers from CrossRef database.
    
    CrossRef is a scholarly infrastructure organization that provides 
    persistent identifiers (DOIs) for scholarly content and metadata.
    It's one of the largest citation databases covering millions of 
    academic papers, journals, books, and other scholarly content.

    Args:
        query: Search query string (e.g., 'machine learning', 'climate change').
        max_results: Maximum number of papers to return (default: 10, max: 1000).
        filter: CrossRef filter string
            (e.g., 'has-full-text:true,from-pub-date:2020').
        sort: Sort field ('relevance', 'published', 'updated', 'deposited', etc.).
        order: Sort order ('asc' or 'desc').
    Returns:
        List of paper metadata in dictionary format.
        
    Examples:
        # Basic search
        search_crossref("deep learning", 20)
        
        # Search with filters
        search_crossref("climate change", 10, filter="from-pub-date:2020,has-full-text:true")
        
        # Search sorted by publication date
        search_crossref("neural networks", 15, sort="published", order="desc")
    """
    search_kwargs = {
        key: value
        for key, value in {
            "filter": filter,
            "sort": sort,
            "order": order,
        }.items()
        if value is not None
    }
    return await _run_sync(_search_sync, CrossRefSearcher, query, max_results, search_kwargs)


@mcp.tool()
async def get_crossref_paper_by_doi(doi: str) -> Dict:
    """Get a specific paper from CrossRef by its DOI.

    Args:
        doi: Digital Object Identifier (e.g., '10.1038/nature12373').
    Returns:
        Paper metadata in dictionary format, or empty dict if not found.
        
    Example:
        get_crossref_paper_by_doi("10.1038/nature12373")
    """
    def _get_crossref_paper_by_doi_sync() -> Dict:
        searcher = CrossRefSearcher()
        paper = searcher.get_paper_by_doi(doi)
        return paper.to_dict() if paper else {}

    return await _run_sync(_get_crossref_paper_by_doi_sync)


@mcp.tool()
async def download_crossref(paper_id: str, save_path: str = "./downloads") -> str:
    """Attempt to download PDF of a CrossRef paper.

    Args:
        paper_id: CrossRef DOI (e.g., '10.1038/nature12373').
        save_path: Compatibility parameter. MCP tools always write under
            `docs/downloads`; custom values do not change the output directory.
    Returns:
        str: Message indicating that direct PDF download is not supported.
        
    Note:
        CrossRef is a citation database and doesn't provide direct PDF downloads.
        Use the DOI to access the paper through the publisher's website.
    """
    try:
        return await _run_sync(_download_sync, CrossRefSearcher, paper_id, save_path)
    except NotImplementedError as e:
        return str(e)


@mcp.tool()
async def read_crossref_paper(paper_id: str, save_path: str = "./downloads") -> str:
    """Attempt to read and extract text content from a CrossRef paper.

    Args:
        paper_id: CrossRef DOI (e.g., '10.1038/nature12373').
        save_path: Compatibility parameter. MCP tools always use
            `docs/downloads`; custom values do not change the read/download
            directory.
    Returns:
        str: Message indicating that direct paper reading is not supported.
        
    Note:
        CrossRef is a citation database and doesn't provide direct paper content.
        Use the DOI to access the paper through the publisher's website.
    """
    return await _run_sync(_read_sync, CrossRefSearcher, paper_id, save_path)


if __name__ == "__main__":
    mcp.run(transport="stdio")
