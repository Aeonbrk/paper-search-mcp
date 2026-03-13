from __future__ import annotations

import json
from datetime import datetime
from typing import Iterable, List, Optional
from xml.etree import ElementTree as ET

import requests

from .._http import DEFAULT_TIMEOUT, build_session
from ..paper import Paper
from ._base import PaperSource

__all__ = ["PMCSearcher"]


class PMCSearcher(PaperSource):
    """Searcher for PubMed Central metadata via NCBI E-utilities."""

    SEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    FETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    LIMITATION_DOCS = [
        "docs/project-specs/source-capability-matrix.md",
        "docs/project-specs/source-notes/pmc.md",
    ]
    MONTH_NUMBERS = {
        "jan": 1,
        "january": 1,
        "feb": 2,
        "february": 2,
        "mar": 3,
        "march": 3,
        "apr": 4,
        "april": 4,
        "may": 5,
        "jun": 6,
        "june": 6,
        "jul": 7,
        "july": 7,
        "aug": 8,
        "august": 8,
        "sep": 9,
        "sept": 9,
        "september": 9,
        "oct": 10,
        "october": 10,
        "nov": 11,
        "november": 11,
        "dec": 12,
        "december": 12,
    }

    def __init__(self) -> None:
        self.session = build_session()
        self.timeout = DEFAULT_TIMEOUT

    def search(self, query: str, max_results: int = 10) -> List[Paper]:
        search_params = {
            "db": "pmc",
            "term": query,
            "retmax": max_results,
            "retmode": "xml",
        }

        search_root = self._get_xml(self.SEARCH_URL, search_params)
        if search_root is None:
            return []

        raw_ids = [node.text.strip() for node in search_root.findall(".//IdList/Id") if node.text]
        if not raw_ids:
            return []

        canonical_ids = [self._canonical_pmcid(raw_id) for raw_id in raw_ids]
        fetch_root = self._get_xml(
            self.FETCH_URL,
            {
                "db": "pmc",
                "id": ",".join(raw_ids),
                "retmode": "xml",
            },
        )
        if fetch_root is None:
            return []

        paper_by_id = {}
        for article in fetch_root.findall(".//article"):
            paper = self._parse_article(article)
            if paper is not None:
                paper_by_id[paper.paper_id] = paper

        return [paper_by_id[paper_id] for paper_id in canonical_ids if paper_id in paper_by_id]

    def download_pdf(self, paper_id: str, save_path: str) -> str:
        del save_path
        return self._limitation_message(
            tool="download_pmc",
            capability="download",
            paper_id=paper_id,
            message="PMC full-text download is not supported yet in this repo.",
        )

    def read_paper(self, paper_id: str, save_path: str = "./downloads") -> str:
        del save_path
        return self._limitation_message(
            tool="read_pmc_paper",
            capability="read",
            paper_id=paper_id,
            message="PMC full-text reading is not supported yet in this repo.",
        )

    def _get_xml(self, url: str, params: dict[str, object]) -> Optional[ET.Element]:
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
        except requests.RequestException:
            return None

        try:
            return ET.fromstring(response.content)
        except ET.ParseError:
            return None

    def _parse_article(self, article: ET.Element) -> Optional[Paper]:
        article_meta = article.find("./front/article-meta")
        if article_meta is None:
            return None

        pmcid = self._find_pmcid(article_meta)
        if not pmcid:
            return None

        title = self._find_text(article_meta, "./title-group/article-title")
        if not title:
            title = self._find_text(article_meta, "./title-group")

        authors = self._extract_authors(article_meta)
        abstract = self._extract_abstract(article_meta)
        doi = self._find_article_id(article_meta, "doi") or ""
        pmid = self._find_article_id(article_meta, "pmid") or ""
        published_date = self._extract_date(article_meta)
        categories = self._extract_texts(article_meta.findall("./article-categories//subject"))
        keywords = self._extract_texts(article_meta.findall("./kwd-group//kwd"))
        journal_title = self._find_text(article.find("./front/journal-meta"), "./journal-title-group/journal-title")

        return Paper(
            paper_id=pmcid,
            title=title,
            authors=authors,
            abstract=abstract,
            doi=doi,
            published_date=published_date,
            updated_date=published_date,
            pdf_url="",
            url=f"https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/",
            source="pmc",
            categories=categories,
            keywords=keywords,
            extra={
                "pmid": pmid,
                "journal_title": journal_title,
                "article_type": article.get("article-type", ""),
            },
        )

    def _extract_authors(self, article_meta: ET.Element) -> List[str]:
        authors: List[str] = []
        for contrib in article_meta.findall("./contrib-group/contrib[@contrib-type='author']"):
            collab = self._find_text(contrib, "./collab")
            if collab:
                authors.append(collab)
                continue

            surname = self._find_text(contrib, "./name/surname")
            given_names = self._find_text(contrib, "./name/given-names")
            full_name = " ".join(part for part in [given_names, surname] if part)
            if full_name:
                authors.append(full_name)
        return authors

    def _extract_abstract(self, article_meta: ET.Element) -> str:
        abstracts = [
            self._element_text(abstract)
            for abstract in article_meta.findall("./abstract")
        ]
        return "\n\n".join(text for text in abstracts if text)

    def _extract_date(self, article_meta: ET.Element) -> Optional[datetime]:
        candidates = article_meta.findall("./pub-date")
        priority = ["pmc-release", "epub", "ppub", "collection", ""]

        for pub_type in priority:
            for candidate in candidates:
                if (candidate.get("pub-type") or "") != pub_type:
                    continue
                parsed = self._parse_date_parts(candidate)
                if parsed is not None:
                    return parsed

        for candidate in candidates:
            parsed = self._parse_date_parts(candidate)
            if parsed is not None:
                return parsed

        return None

    def _parse_date_parts(self, node: ET.Element) -> Optional[datetime]:
        year = self._parse_int(self._find_text(node, "./year"))
        if year is None:
            return None

        month = self._parse_month(self._find_text(node, "./month")) or 1
        day = self._parse_int(self._find_text(node, "./day")) or 1

        try:
            return datetime(year, month, day)
        except ValueError:
            return None

    def _find_article_id(self, article_meta: ET.Element, pub_id_type: str) -> str:
        for node in article_meta.findall("./article-id"):
            if node.get("pub-id-type") == pub_id_type and node.text:
                return node.text.strip()
        return ""

    def _find_pmcid(self, article_meta: ET.Element) -> str:
        for pub_id_type in ("pmcid", "pmc"):
            pmcid = self._canonical_pmcid(
                self._find_article_id(article_meta, pub_id_type)
            )
            if pmcid:
                return pmcid
        return ""

    def _limitation_message(
        self,
        *,
        tool: str,
        capability: str,
        paper_id: str,
        message: str,
    ) -> str:
        payload = {
            "capability": capability,
            "docs": self.LIMITATION_DOCS,
            "message": message,
            "paper_id": paper_id,
            "reason": "not_implemented",
            "source": "pmc",
            "supported": False,
            "tool": tool,
            "type": "limitation",
        }
        return f"LIMITATION: {json.dumps(payload, sort_keys=True)}"

    @staticmethod
    def _canonical_pmcid(raw_id: str) -> str:
        value = raw_id.strip()
        if not value:
            return ""

        upper_value = value.upper()
        if upper_value.startswith("PMC"):
            suffix = upper_value[3:]
        else:
            suffix = value

        digits = "".join(character for character in suffix if character.isdigit())
        if not digits:
            return ""
        return f"PMC{digits}"

    @staticmethod
    def _find_text(node: Optional[ET.Element], path: str) -> str:
        if node is None:
            return ""

        target = node.find(path)
        if target is None:
            return ""
        return PMCSearcher._element_text(target)

    @staticmethod
    def _element_text(node: Optional[ET.Element]) -> str:
        if node is None:
            return ""
        return " ".join(part.strip() for part in node.itertext() if part and part.strip())

    @classmethod
    def _extract_texts(cls, nodes: Iterable[ET.Element]) -> List[str]:
        seen = set()
        values: List[str] = []
        for node in nodes:
            text = cls._element_text(node)
            if text and text not in seen:
                seen.add(text)
                values.append(text)
        return values

    @staticmethod
    def _parse_int(value: str) -> Optional[int]:
        digits = "".join(character for character in value if character.isdigit())
        if not digits:
            return None
        return int(digits)

    @classmethod
    def _parse_month(cls, value: str) -> Optional[int]:
        if not value:
            return None

        numeric = cls._parse_int(value)
        if numeric is not None and 1 <= numeric <= 12:
            return numeric

        return cls.MONTH_NUMBERS.get(value.strip().lower())
