from __future__ import annotations

import asyncio
import contextlib
import importlib.util
import io
import json
import re
import sys
from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
BENCHMARK_SCRIPT = REPO_ROOT / "scripts" / "benchmarks" / "tool_latency_smoke.py"
THRESHOLD_DOC = REPO_ROOT / "docs" / "project-specs" / "performance-stability-targets.md"


def _load_benchmark_module():
    spec = importlib.util.spec_from_file_location(
        "tests._tool_latency_smoke",
        BENCHMARK_SCRIPT,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load benchmark script: {BENCHMARK_SCRIPT}")

    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault(spec.name, module)
    spec.loader.exec_module(module)
    return module


def _load_thresholds() -> dict[str, int]:
    thresholds: dict[str, int] = {}

    for key, value in re.findall(r"^([a-z0-9_.]+)=([0-9]+)$", THRESHOLD_DOC.read_text(), re.MULTILINE):
        thresholds[key] = int(value)

    if not thresholds:
        raise AssertionError("No latency threshold keys were found in the target spec")

    return thresholds


class TestPerformanceSmoke(unittest.TestCase):
    def test_dry_run_benchmark_stays_within_documented_thresholds(self):
        module = _load_benchmark_module()
        thresholds = _load_thresholds()
        parser = module._build_parser()
        args = parser.parse_args(["--dry-run", "--iterations", "3", "--warmup", "1", "--json"])

        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            exit_code = asyncio.run(module._amain(args))

        self.assertEqual(exit_code, 0)

        report = json.loads(buffer.getvalue())
        self.assertEqual(report["mode"], "dry-run")

        seen_tools = set()
        for result in report["results"]:
            tool_name = result["tool_name"]
            seen_tools.add(tool_name)
            p50_key = f"{tool_name}.dry_run.p50_ms_max"
            failures_key = f"{tool_name}.dry_run.failures_max"

            self.assertIn(p50_key, thresholds)
            self.assertIn(failures_key, thresholds)
            self.assertLessEqual(result["p50_ms"], thresholds[p50_key], tool_name)
            self.assertLessEqual(result["failures"], thresholds[failures_key], tool_name)

        self.assertEqual(
            seen_tools,
            {"search_arxiv", "download_arxiv", "read_arxiv_paper"},
        )


if __name__ == "__main__":
    unittest.main()
