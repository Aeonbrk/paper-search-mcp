"""
Shared adapter contract for `paper_search_mcp.academic_platforms`.

This module defines the single, shared interface that all academic-platform
adapters/searchers SHOULD implement. It exists to avoid duplicating a local
`PaperSource` skeleton in every adapter module, and to give tests one stable
place to import the contract from.

Contract (high-level):
  - `search(query, max_results: int = 10, **kwargs) -> list[Paper]`
  - `download_pdf(paper_id, save_path) -> str`
  - `read_paper(paper_id, save_path: str = "./downloads") -> str`

Design notes:
  - The contract is intentionally small and behavior-preserving: adapters may
    still choose how they do networking, parsing, error handling, and retries.
  - Return values are normalized via the `Paper` model (`paper_search_mcp.paper`).
  - This module must remain importable without any third-party dependencies.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, List, TYPE_CHECKING

if TYPE_CHECKING:
    from ..paper import Paper

__all__ = ["PaperSource"]


class PaperSource(ABC):
    """
    Shared abstract base class for paper sources/adapters.

    Implementations are expected to:
      - Perform a query against a source and return a list of normalized
        `Paper` objects. The shared search signature includes
        `max_results: int = 10`; implementations may also accept
        source-specific keyword arguments.
      - Optionally download a PDF to a local path, returning that path as `str`.
      - Optionally read/convert a paper to a text representation. The shared
        compatibility signature keeps `save_path="./downloads"`.

    Adapters currently vary in how they handle errors (some raise, some return
    empty values). That behavior is intentionally NOT standardized here to keep
    the runtime surface stable; convergence happens module-by-module.
    """

    @abstractmethod
    def search(
        self,
        query: str,
        max_results: int = 10,
        **kwargs: Any,
    ) -> List["Paper"]:
        """Search for papers matching `query` and return normalized results."""
        raise NotImplementedError

    @abstractmethod
    def download_pdf(self, paper_id: str, save_path: str) -> str:
        """
        Download a paper's PDF into `save_path`.

        Returns:
            str: Filesystem path to the downloaded PDF.
        """

        raise NotImplementedError

    @abstractmethod
    def read_paper(self, paper_id: str, save_path: str = "./downloads") -> str:
        """
        Read a paper and return extracted text.

        Implementations may download the PDF first if it is not present locally.
        """

        raise NotImplementedError
