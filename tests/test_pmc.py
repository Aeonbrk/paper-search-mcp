import json
from pathlib import Path
import unittest
from unittest import mock
from xml.etree import ElementTree as ET

import paper_search_mcp.academic_platforms.pmc as pmc_module
from paper_search_mcp.academic_platforms.pmc import PMCSearcher
from paper_search_mcp.server import download_pmc, read_pmc_paper
from tests._offline import OfflineTestCase, read_fixture_text


LIMITATION_PREFIX = "LIMITATION: "
LIMITATION_DOCS = [
    "docs/project-specs/source-capability-matrix.md",
    "docs/project-specs/source-notes/pmc.md",
]


class TestPMCSearcherOffline(OfflineTestCase):
    def test_search_offline_fixture(self):
        searcher = PMCSearcher()

        search_response = mock.Mock()
        search_response.content = read_fixture_text("pmc", "esearch.xml").encode("utf-8")
        search_response.raise_for_status = mock.Mock()

        fetch_response = mock.Mock()
        fetch_response.content = read_fixture_text("pmc", "efetch.xml").encode("utf-8")
        fetch_response.raise_for_status = mock.Mock()

        with mock.patch.object(
            pmc_module,
            "request_with_retries",
            side_effect=[search_response, fetch_response],
        ) as mock_request:
            papers = searcher.search("single cell atlas", max_results=2)

        self.assertEqual(mock_request.call_count, 2)
        mock_request.assert_any_call(
            searcher.session,
            "GET",
            searcher.SEARCH_URL,
            params={
                "db": "pmc",
                "term": "single cell atlas",
                "retmax": 2,
                "retmode": "xml",
            },
            timeout=searcher.timeout,
        )
        mock_request.assert_any_call(
            searcher.session,
            "GET",
            searcher.FETCH_URL,
            params={
                "db": "pmc",
                "id": "1234567,7654321",
                "retmode": "xml",
            },
            timeout=searcher.timeout,
        )

        self.assertEqual(len(papers), 2)

        first = papers[0]
        self.assertEqual(first.paper_id, "PMC1234567")
        self.assertEqual(first.title, "Offline PMC Paper One")
        self.assertEqual(first.authors, ["Alice Example", "Bob Example"])
        self.assertEqual(first.abstract, "Deterministic fixture abstract for PMC paper one.")
        self.assertEqual(first.doi, "10.1000/pmc.one")
        self.assertEqual(first.source, "pmc")
        self.assertEqual(first.categories, ["Genomics", "Cell Biology"])
        self.assertEqual(first.keywords, ["single-cell", "atlas"])
        self.assertEqual(first.published_date.isoformat(), "2024-02-14T00:00:00")
        self.assertEqual(first.url, "https://pmc.ncbi.nlm.nih.gov/articles/PMC1234567/")
        self.assertEqual(first.extra["pmid"], "34567890")
        self.assertEqual(first.extra["journal_title"], "Offline Journal")
        self.assertEqual(first.extra["article_type"], "research-article")

        serialized = first.to_dict()
        self.assertEqual(serialized["paper_id"], "PMC1234567")
        self.assertEqual(serialized["source"], "pmc")
        self.assertEqual(serialized["categories"], "Genomics; Cell Biology")
        self.assertEqual(serialized["keywords"], "single-cell; atlas")
        self.assertIn("'pmid': '34567890'", serialized["extra"])

        second = papers[1]
        self.assertEqual(second.paper_id, "PMC7654321")
        self.assertEqual(second.authors, ["PMC Collaboration"])
        self.assertEqual(second.doi, "")
        self.assertEqual(second.published_date.isoformat(), "2021-07-01T00:00:00")

    def test_parse_article_prefers_pmcid_and_ignores_pmcid_ver(self):
        searcher = PMCSearcher()
        article = ET.fromstring(
            """
            <article article-type="research-article">
              <front>
                <journal-meta>
                  <journal-title-group>
                    <journal-title>Regression Journal</journal-title>
                  </journal-title-group>
                </journal-meta>
                <article-meta>
                  <article-id pub-id-type="pmcid-ver">PMC12976881.1</article-id>
                  <article-id pub-id-type="pmcid">PMC12976881</article-id>
                  <article-id pub-id-type="pmid">12345678</article-id>
                  <title-group>
                    <article-title>PMCID Regression Case</article-title>
                  </title-group>
                  <pub-date pub-type="epub">
                    <year>2024</year>
                  </pub-date>
                </article-meta>
              </front>
            </article>
            """
        )

        paper = searcher._parse_article(article)

        self.assertIsNotNone(paper)
        self.assertEqual(paper.paper_id, "PMC12976881")

    def test_parse_article_skips_articles_without_explicit_pmcid(self):
        searcher = PMCSearcher()
        article = ET.fromstring(
            """
            <article article-type="research-article">
              <front>
                <journal-meta>
                  <journal-title-group>
                    <journal-title>Regression Journal</journal-title>
                  </journal-title-group>
                </journal-meta>
                <article-meta>
                  <article-id pub-id-type="pmcid-ver">PMC12976881.1</article-id>
                  <article-id pub-id-type="pmid">12345678</article-id>
                  <title-group>
                    <article-title>Missing PMCID Case</article-title>
                  </title-group>
                  <pub-date pub-type="epub">
                    <year>2024</year>
                  </pub-date>
                </article-meta>
              </front>
            </article>
            """
        )

        self.assertIsNone(searcher._parse_article(article))


class TestPMCToolLimitations(OfflineTestCase):
    def test_placeholder_tools_return_limitation_json_without_download_side_effects(self):
        downloads_dir = Path("docs/downloads")
        existed_before = downloads_dir.exists()

        async def immediate_run(callable_, /, *args, **kwargs):
            return callable_(*args, **kwargs)

        with (
            mock.patch(
                "paper_search_mcp.server.resolve_download_target",
                side_effect=AssertionError("PMC placeholder tools must not create docs/downloads"),
            ) as mock_resolve,
            mock.patch("paper_search_mcp.server._run_sync", new=immediate_run),
        ):
            download_message = self._run_without_event_loop(
                download_pmc("PMC1234567", save_path="ignored")
            )
            read_message = self._run_without_event_loop(
                read_pmc_paper("PMC1234567", save_path="ignored")
            )

        mock_resolve.assert_not_called()
        self.assertEqual(downloads_dir.exists(), existed_before)

        self._assert_limitation_payload(
            message=download_message,
            tool="download_pmc",
            capability="download",
            expected_text="PMC full-text download is not supported yet in this repo.",
        )
        self._assert_limitation_payload(
            message=read_message,
            tool="read_pmc_paper",
            capability="read",
            expected_text="PMC full-text reading is not supported yet in this repo.",
        )

    def _assert_limitation_payload(
        self,
        *,
        message: str,
        tool: str,
        capability: str,
        expected_text: str,
    ) -> None:
        self.assertTrue(message.startswith(LIMITATION_PREFIX))
        payload = json.loads(message[len(LIMITATION_PREFIX):])

        self.assertEqual(payload["type"], "limitation")
        self.assertEqual(payload["source"], "pmc")
        self.assertEqual(payload["tool"], tool)
        self.assertEqual(payload["capability"], capability)
        self.assertFalse(payload["supported"])
        self.assertEqual(payload["reason"], "not_implemented")
        self.assertEqual(payload["paper_id"], "PMC1234567")
        self.assertEqual(payload["docs"], LIMITATION_DOCS)
        self.assertEqual(payload["message"], expected_text)

    def _run_without_event_loop(self, coroutine):
        try:
            coroutine.send(None)
        except StopIteration as stop:
            return stop.value

        coroutine.close()
        self.fail("Coroutine yielded unexpectedly while offline")


if __name__ == "__main__":
    unittest.main()
