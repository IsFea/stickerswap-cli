from __future__ import annotations

import unittest
from pathlib import Path

from stickerswap.runtime import default_workspace, slugify, with_bot_suffix


class RuntimeTests(unittest.TestCase):
    def test_slugify_normalizes_text(self) -> None:
        self.assertEqual(slugify("Vladisleyv Pack By IsFea"), "vladisleyv_pack_by_isfea")

    def test_with_bot_suffix_appends_bot_suffix(self) -> None:
        self.assertEqual(
            with_bot_suffix("My Pack", "Faces_isfea_bot"),
            "my_pack_by_faces_isfea_bot",
        )

    def test_default_workspace_uses_slug(self) -> None:
        workspace = default_workspace("fucking_english", Path("/tmp/project"))
        self.assertEqual(str(workspace), "/tmp/project/workspaces/fucking_english")


if __name__ == "__main__":
    unittest.main()

