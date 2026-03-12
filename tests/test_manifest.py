from __future__ import annotations

import unittest
from pathlib import Path

from stickerswap.manifest import StickerManifest, StickerRecord


class ManifestTests(unittest.TestCase):
    def test_manifest_roundtrip(self) -> None:
        tmp_path = Path("tests_tmp_manifest")
        tmp_path.mkdir(exist_ok=True)
        manifest_path = tmp_path / "stickers.json"
        manifest = StickerManifest(
            source_pack="video_gachi",
            generated_at="2026-03-11T12:00:00+00:00",
            stickers=[
                StickerRecord(
                    source_pack="video_gachi",
                    sticker_id="abc",
                    file_id="file_1",
                    file_unique_id="uniq_1",
                    file_name="uniq_1.webm",
                    emoji=["🙂"],
                    status="downloaded",
                )
            ],
        )
        manifest.save(manifest_path)
        loaded = StickerManifest.load(manifest_path)
        self.assertEqual(loaded.source_pack, "video_gachi")
        self.assertEqual(loaded.stickers[0].file_name, "uniq_1.webm")
        self.assertEqual(loaded.stickers[0].emoji, ["🙂"])
        manifest_path.unlink()
        tmp_path.rmdir()


if __name__ == "__main__":
    unittest.main()

