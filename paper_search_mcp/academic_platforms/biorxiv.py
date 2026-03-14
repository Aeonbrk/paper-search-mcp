from ._preprint_base import PreprintSearcherBase


class BioRxivSearcher(PreprintSearcherBase):
    """Searcher for bioRxiv papers."""

    SOURCE_NAME = "biorxiv"
    BASE_URL = "https://api.biorxiv.org/details/biorxiv"
    CONTENT_BASE_URL = "https://www.biorxiv.org/content"
