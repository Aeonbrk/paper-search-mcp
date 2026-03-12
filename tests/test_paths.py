import tempfile
from pathlib import Path
import unittest

from paper_search_mcp._paths import resolve_download_target, safe_download_root


class TestSafePaths(unittest.TestCase):
    def test_safe_download_root_uses_docs_downloads(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = safe_download_root(temp_dir)
            self.assertEqual(root, Path(temp_dir).resolve() / "docs" / "downloads")
            self.assertTrue(root.is_dir())

    def test_resolve_download_target_rejects_parent_escape(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(ValueError):
                resolve_download_target(
                    filename="paper.pdf",
                    save_path="../escape",
                    base_dir=temp_dir,
                )

    def test_resolve_download_target_rejects_absolute_or_drive_paths(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(ValueError):
                resolve_download_target(
                    filename="paper.pdf",
                    save_path="/tmp/escape",
                    base_dir=temp_dir,
                )
            with self.assertRaises(ValueError):
                resolve_download_target(
                    filename="paper.pdf",
                    save_path="C:/escape",
                    base_dir=temp_dir,
                )

    def test_resolve_download_target_sanitizes_filename(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = resolve_download_target(
                filename="../evil.pdf",
                save_path="nested",
                base_dir=temp_dir,
            )
            self.assertEqual(
                target.path.parent,
                Path(temp_dir).resolve() / "docs" / "downloads" / "nested",
            )
            self.assertEqual(target.path.suffix, ".pdf")
            self.assertIn("evil", target.path.stem)

    def test_resolve_download_target_keeps_slash_based_id_information(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = resolve_download_target(
                filename="hep-th/9901001.pdf",
                base_dir=temp_dir,
            )

            self.assertEqual(target.path.suffix, ".pdf")
            self.assertIn("hep-th_9901001", target.path.stem)

    def test_resolve_download_target_avoids_collisions_for_slash_based_ids(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            slash_target = resolve_download_target(
                filename="iacr_2009/101.pdf",
                base_dir=temp_dir,
            )
            basename_target = resolve_download_target(
                filename="101.pdf",
                base_dir=temp_dir,
            )

            self.assertNotEqual(slash_target.path.name, basename_target.path.name)

    def test_resolve_download_target_avoids_collisions_for_normalized_names(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            slash_target = resolve_download_target(
                filename="a/b.pdf",
                base_dir=temp_dir,
            )
            underscore_target = resolve_download_target(
                filename="a_b.pdf",
                base_dir=temp_dir,
            )

            self.assertNotEqual(slash_target.path.name, underscore_target.path.name)

    def test_resolve_download_target_normalizes_downloads_prefixed_subdir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = resolve_download_target(
                filename="paper.pdf",
                save_path="downloads/my_run",
                base_dir=temp_dir,
            )

            self.assertEqual(
                target.path.parent,
                Path(temp_dir).resolve() / "docs" / "downloads" / "my_run",
            )

    def test_resolve_download_target_normalizes_docs_downloads_prefixed_subdir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = resolve_download_target(
                filename="paper.pdf",
                save_path="docs/downloads/my_run",
                base_dir=temp_dir,
            )

            self.assertEqual(
                target.path.parent,
                Path(temp_dir).resolve() / "docs" / "downloads" / "my_run",
            )


if __name__ == "__main__":
    unittest.main()
