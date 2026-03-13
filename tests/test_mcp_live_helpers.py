from __future__ import annotations

import unittest

from mcp.types import CallToolResult, TextContent

from tests.test_mcp_live import _json_items


class TestMcpLiveHelperAssertions(unittest.TestCase):
    def test_json_items_rejects_empty_content(self) -> None:
        with self.assertRaisesRegex(AssertionError, "Expected at least one content block"):
            _json_items(CallToolResult(content=[], isError=False))

    def test_json_items_rejects_error_payloads(self) -> None:
        with self.assertRaisesRegex(AssertionError, "Tool returned protocol error"):
            _json_items(
                CallToolResult(
                    content=[TextContent(type="text", text="boom")],
                    isError=True,
                )
            )

    def test_json_items_rejects_empty_json_arrays(self) -> None:
        with self.assertRaisesRegex(AssertionError, "Expected at least one JSON object payload"):
            _json_items(
                CallToolResult(
                    content=[TextContent(type="text", text="[]")],
                    isError=False,
                )
            )


if __name__ == "__main__":
    unittest.main()
