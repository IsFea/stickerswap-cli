from __future__ import annotations

import unittest

from stickerswap.manifest import StickerManifest, StickerRecord
from stickerswap.pipeline import summarize_manifest


class PipelineSummaryTests(unittest.TestCase):
    def test_summarize_manifest_counts_statuses(self) -> None:
        manifest = StickerManifest(
            source_pack="video_gachi",
            generated_at="2026-03-11T12:00:00+00:00",
            stickers=[
                StickerRecord(
                    source_pack="video_gachi",
                    sticker_id="1",
                    file_id="f1",
                    file_unique_id="u1",
                    file_name="u1.webm",
                    emoji=["🙂"],
                    status="validated",
                ),
                StickerRecord(
                    source_pack="video_gachi",
                    sticker_id="2",
                    file_id="f2",
                    file_unique_id="u2",
                    file_name="u2.webm",
                    emoji=["🔥"],
                    status="review",
                ),
            ],
        )
        summary = summarize_manifest(manifest)
        self.assertIn("validated=1", summary)
        self.assertIn("review=1", summary)


if __name__ == "__main__":
    unittest.main()
