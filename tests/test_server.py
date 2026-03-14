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
            "search_pmc",
            "get_crossref_paper_by_doi",
            "download_crossref",
            "download_pmc",
            "read_crossref_paper",
            "read_pmc_paper",
        }
        self.assertEqual(tool_names, expected_names)

    def test_search_crossref_schema_matches_public_contract(self):
        tools = asyncio.run(server.mcp.list_tools())
        tool_by_name = {tool.name: tool for tool in tools}

        schema = tool_by_name["search_crossref"].inputSchema
        properties = schema["properties"]

        self.assertEqual(schema["required"], ["query"])
        self.assertIn("query", properties)
        self.assertIn("max_results", properties)
        self.assertIn("filter", properties)
        self.assertIn("sort", properties)
        self.assertIn("order", properties)
        self.assertNotIn("kwargs", properties)

    def test_nonsemantic_search_tool_schemas_remain_query_driven(self):
        tools = asyncio.run(server.mcp.list_tools())
        tool_by_name = {tool.name: tool for tool in tools}

        query_driven_search_tools = {
            "search_arxiv": set(),
            "search_pubmed": set(),
            "search_pmc": set(),
            "search_biorxiv": set(),
            "search_medrxiv": set(),
            "search_google_scholar": set(),
            "search_iacr": {"fetch_details"},
            "search_crossref": {"filter", "sort", "order"},
        }

        for tool_name, extra_properties in query_driven_search_tools.items():
            with self.subTest(tool=tool_name):
                schema = tool_by_name[tool_name].inputSchema
                properties = schema["properties"]

                self.assertEqual(schema["required"], ["query"])
                self.assertIn("query", properties)
                self.assertIn("max_results", properties)
                self.assertNotIn("category", properties)

                for property_name in extra_properties:
                    self.assertIn(property_name, properties)

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
