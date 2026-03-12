import asyncio
from pathlib import Path
import unittest

from paper_search_mcp import server


class TestPaperSearchServer(unittest.TestCase):
    def test_server_name(self):
        self.assertEqual(server.mcp.name, "paper_search_server")

    def test_tool_registration_snapshot(self):
        tools = asyncio.run(server.mcp.list_tools())
        tool_names = {tool.name for tool in tools}
        expected_names = {
            "search_arxiv",
            "search_pubmed",
            "search_biorxiv",
            "search_medrxiv",
            "search_google_scholar",
            "search_iacr",
            "download_arxiv",
            "download_pubmed",
            "download_biorxiv",
            "download_medrxiv",
            "download_iacr",
            "read_arxiv_paper",
            "read_pubmed_paper",
            "read_biorxiv_paper",
            "read_medrxiv_paper",
            "read_iacr_paper",
            "search_semantic",
            "download_semantic",
            "read_semantic_paper",
            "search_crossref",
            "get_crossref_paper_by_doi",
            "download_crossref",
            "read_crossref_paper",
        }
        self.assertEqual(tool_names, expected_names)

    def test_canonical_save_path_ignores_user_input(self):
        self.assertEqual(server._canonical_save_path("../escape"), "docs/downloads")
        self.assertEqual(Path(server._canonical_save_path("anywhere")), Path("docs/downloads"))
        self.assertEqual(
            server._canonical_save_path("downloads/my_run"),
            "docs/downloads",
        )
        self.assertEqual(
            server._canonical_save_path("docs/downloads/my_run"),
            "docs/downloads",
        )


if __name__ == "__main__":
    unittest.main()
