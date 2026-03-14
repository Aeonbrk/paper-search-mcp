from ._preprint_base import PreprintSearcherBase


class MedRxivSearcher(PreprintSearcherBase):
    """Searcher for medRxiv papers."""

    SOURCE_NAME = "medrxiv"
    BASE_URL = "https://api.biorxiv.org/details/medrxiv"
    CONTENT_BASE_URL = "https://www.medrxiv.org/content"
