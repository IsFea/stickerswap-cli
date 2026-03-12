from __future__ import annotations

import os
import unittest
from pathlib import Path

from stickerswap.config import AppConfig, save_local_config


class ConfigTests(unittest.TestCase):
    def test_local_config_is_loaded_from_project_root(self) -> None:
        project_root = Path("tests_tmp_config")
        workdir = project_root / "workspaces" / "demo"
        workdir.mkdir(parents=True, exist_ok=True)
        save_local_config(
            project_root / ".env.local",
            {
                "TELEGRAM_BOT_TOKEN": "123456789:fake_token_value",
                "TELEGRAM_OWNER_USER_ID": 42,
                "OUTPUT_PACK_TITLE": "Demo Pack",
            },
        )
        config = AppConfig.load(workdir, project_root=project_root)
        self.assertEqual(config.telegram_bot_token, "123456789:fake_token_value")
        self.assertEqual(config.telegram_owner_user_id, 42)
        self.assertEqual(config.output_pack_title, "Demo Pack")
        (project_root / ".env.local").unlink()
        workdir.rmdir()
        (project_root / "workspaces").rmdir()
        project_root.rmdir()

    def test_environment_overrides_local_file(self) -> None:
        project_root = Path("tests_tmp_config_env")
        workdir = project_root / "workspace"
        workdir.mkdir(parents=True, exist_ok=True)
        save_local_config(project_root / ".env.local", {"OUTPUT_PACK_TITLE": "Old"})
        previous = os.environ.get("OUTPUT_PACK_TITLE")
        os.environ["OUTPUT_PACK_TITLE"] = "New"
        try:
            config = AppConfig.load(workdir, project_root=project_root)
            self.assertEqual(config.output_pack_title, "New")
        finally:
            if previous is None:
                os.environ.pop("OUTPUT_PACK_TITLE", None)
            else:
                os.environ["OUTPUT_PACK_TITLE"] = previous
        (project_root / ".env.local").unlink()
        workdir.rmdir()
        project_root.rmdir()


if __name__ == "__main__":
    unittest.main()

