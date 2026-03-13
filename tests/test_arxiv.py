import ast
import os
from pathlib import Path
import unittest
from unittest import mock

import paper_search_mcp.academic_platforms.arxiv as arxiv_module
from paper_search_mcp.academic_platforms.arxiv import ArxivSearcher
from tests._offline import OfflineTestCase, read_fixture_text


LIVE_TESTS_ENABLED = os.getenv("PAPER_SEARCH_LIVE_TESTS") == "1"


class TestArxivSearcher(unittest.TestCase):
    def test_search(self):
        if not LIVE_TESTS_ENABLED:
            self.skipTest("Set PAPER_SEARCH_LIVE_TESTS=1 to run live arXiv tests")

        searcher = ArxivSearcher()
        papers = searcher.search("machine learning", max_results=10)
        self.assertEqual(len(papers), 10)
        self.assertTrue(papers[0].title)

    def test_module_main_uses_pathlib_for_directory_creation(self):
        source = Path(arxiv_module.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)

        imports_path = any(
            isinstance(node, ast.ImportFrom)
            and node.module == "pathlib"
            and any(alias.name == "Path" for alias in node.names)
            for node in tree.body
        )
        self.assertTrue(imports_path)

        main_block = next(
            (
                node
                for node in tree.body
                if isinstance(node, ast.If)
                and isinstance(node.test, ast.Compare)
                and isinstance(node.test.left, ast.Name)
                and node.test.left.id == "__name__"
                and len(node.test.comparators) == 1
                and isinstance(node.test.comparators[0], ast.Constant)
                and node.test.comparators[0].value == "__main__"
            ),
            None,
        )
        self.assertIsNotNone(main_block)
        self.assertFalse(
            any(
                isinstance(node, ast.Name) and node.id == "os"
                for node in ast.walk(main_block)
            )
        )

        mkdir_calls = [
            node
            for node in ast.walk(main_block)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "mkdir"
        ]
        self.assertTrue(
            any(
                isinstance(call.func.value, ast.Call)
                and isinstance(call.func.value.func, ast.Name)
                and call.func.value.func.id == "Path"
                and any(
                    keyword.arg == "parents"
                    and isinstance(keyword.value, ast.Constant)
                    and keyword.value.value is True
                    for keyword in call.keywords
                )
                and any(
                    keyword.arg == "exist_ok"
                    and isinstance(keyword.value, ast.Constant)
                    and keyword.value.value is True
                    for keyword in call.keywords
                )
                for call in mkdir_calls
            )
        )


class TestArxivSearcherOffline(OfflineTestCase):
    def test_search_offline_fixture(self):
        searcher = ArxivSearcher()
        response = mock.Mock()
        response.content = read_fixture_text("arxiv", "search_response.xml").encode("utf-8")
        response.raise_for_status = mock.Mock()

        with mock.patch.object(searcher.session, "get", return_value=response) as mock_get:
            papers = searcher.search("quantum gravity", max_results=2)

        mock_get.assert_called_once_with(
            searcher.BASE_URL,
            params={
                "search_query": "quantum gravity",
                "max_results": 2,
                "sortBy": "submittedDate",
                "sortOrder": "descending",
            },
            timeout=searcher.timeout,
        )
        response.raise_for_status.assert_called_once_with()
        self.assertEqual(len(papers), 2)

        first = papers[0]
        self.assertEqual(first.paper_id, "2503.12345v1")
        self.assertEqual(first.title, "Offline Fixture Paper One")
        self.assertEqual(first.authors, ["Alice Example", "Bob Example"])
        self.assertEqual(first.abstract, "A deterministic offline fixture for arXiv search parsing.")
        self.assertEqual(first.url, "http://arxiv.org/abs/2503.12345v1")
        self.assertEqual(first.pdf_url, "http://arxiv.org/pdf/2503.12345v1")
        self.assertEqual(first.source, "arxiv")
        self.assertEqual(first.categories, ["cs.AI", "cs.LG"])
        self.assertEqual(first.doi, "10.1000/example-doi")

        second = papers[1]
        self.assertEqual(second.paper_id, "2503.54321v2")
        self.assertEqual(second.authors, ["Carol Example"])
        self.assertEqual(second.categories, ["math.CO"])
        self.assertEqual(second.doi, "")

        serialized = first.to_dict()
        self.assertEqual(serialized["paper_id"], "2503.12345v1")
        self.assertEqual(serialized["source"], "arxiv")
        self.assertEqual(serialized["categories"], "cs.AI; cs.LG")
        self.assertEqual(serialized["doi"], "10.1000/example-doi")


if __name__ == "__main__":
    unittest.main()
