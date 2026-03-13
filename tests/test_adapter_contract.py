import importlib
import inspect
import socket
import unittest

from tests._offline import NetworkAccessDenied, OfflineTestCase, read_fixture_text


ADAPTER_SPECS = [
    ("arxiv", "paper_search_mcp.academic_platforms.arxiv", "ArxivSearcher"),
    ("pubmed", "paper_search_mcp.academic_platforms.pubmed", "PubMedSearcher"),
    ("pmc", "paper_search_mcp.academic_platforms.pmc", "PMCSearcher"),
    ("crossref", "paper_search_mcp.academic_platforms.crossref", "CrossRefSearcher"),
    ("semantic", "paper_search_mcp.academic_platforms.semantic", "SemanticSearcher"),
    ("iacr", "paper_search_mcp.academic_platforms.iacr", "IACRSearcher"),
]


class TestOfflineHelpers(OfflineTestCase):
    def test_deny_network_blocks_socket_connect(self):
        with self.assertRaises(NetworkAccessDenied):
            socket.create_connection(("127.0.0.1", 9), timeout=0.1)

        with self.assertRaises(NetworkAccessDenied):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(("127.0.0.1", 9))

    def test_fixture_loader_works_with_network_denied(self):
        content = read_fixture_text("README.md")
        self.assertIn("tests/fixtures/", content)


class TestAdapterContract(OfflineTestCase):
    def test_adapter_classes_exist_and_construct_offline(self):
        for source_id, module_path, class_name in ADAPTER_SPECS:
            with self.subTest(source=source_id):
                module = importlib.import_module(module_path)
                adapter_cls = getattr(module, class_name)

                init_sig = inspect.signature(adapter_cls.__init__)
                required = [
                    p
                    for name, p in init_sig.parameters.items()
                    if name != "self" and p.default is inspect.Parameter.empty
                ]
                self.assertEqual(
                    required,
                    [],
                    f"{class_name} should construct with no required args",
                )

                adapter = adapter_cls()
                self.assertTrue(callable(getattr(adapter, "search", None)))
                self.assertTrue(callable(getattr(adapter, "download_pdf", None)))
                self.assertTrue(callable(getattr(adapter, "read_paper", None)))

    def test_adapter_method_signatures(self):
        for source_id, module_path, class_name in ADAPTER_SPECS:
            with self.subTest(source=source_id):
                module = importlib.import_module(module_path)
                adapter_cls = getattr(module, class_name)

                search_sig = inspect.signature(adapter_cls.search)
                self.assertIn("query", search_sig.parameters)
                self.assertIn("max_results", search_sig.parameters)
                self.assertEqual(search_sig.parameters["max_results"].default, 10)

                download_sig = inspect.signature(adapter_cls.download_pdf)
                self.assertIn("paper_id", download_sig.parameters)
                self.assertIn("save_path", download_sig.parameters)
                self.assertIs(download_sig.parameters["save_path"].default, inspect.Parameter.empty)

                read_sig = inspect.signature(adapter_cls.read_paper)
                self.assertIn("paper_id", read_sig.parameters)
                self.assertIn("save_path", read_sig.parameters)
                self.assertEqual(read_sig.parameters["save_path"].default, "./downloads")


if __name__ == "__main__":
    unittest.main()
