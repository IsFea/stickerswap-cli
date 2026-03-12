from __future__ import annotations

import unittest
from pathlib import Path

from stickerswap.checks import forbidden_file_findings, secret_findings


class CheckTests(unittest.TestCase):
    def test_secret_pattern_detects_telegram_like_token(self) -> None:
        project_root = Path("tests_tmp_secrets")
        project_root.mkdir(exist_ok=True)
        (project_root / ".git").mkdir(exist_ok=True)
        tracked = project_root / "sample.txt"
        tracked.write_text("TELEGRAM_BOT_TOKEN=" + "123456789:" + "AAAA_fake_token_value" + "\n", encoding="utf-8")
        try:
            # Fallback behavior of git ls-files without repo contents is outside the unit scope,
            # so emulate the check through direct file content by temporarily staging via git add.
            import subprocess

            subprocess.run(["git", "init"], cwd=project_root, check=False, capture_output=True)
            subprocess.run(["git", "add", "sample.txt"], cwd=project_root, check=False, capture_output=True)
            findings = secret_findings(project_root)
            self.assertIn("sample.txt", findings)
        finally:
            if tracked.exists():
                tracked.unlink()
            git_dir = project_root / ".git"
            for path in sorted(git_dir.rglob("*"), reverse=True):
                if path.is_file():
                    path.unlink()
                elif path.is_dir():
                    path.rmdir()
            if git_dir.exists():
                git_dir.rmdir()
            project_root.rmdir()

    def test_forbidden_file_findings_blocks_workspaces_and_images(self) -> None:
        project_root = Path("tests_tmp_forbidden")
        project_root.mkdir(exist_ok=True)
        import subprocess

        subprocess.run(["git", "init"], cwd=project_root, check=False, capture_output=True)
        (project_root / "workspace_demo").mkdir(exist_ok=True)
        (project_root / "workspace_demo" / "artifact.txt").write_text("x", encoding="utf-8")
        (project_root / "face.jpg").write_text("x", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=project_root, check=False, capture_output=True)
        findings = forbidden_file_findings(project_root)
        self.assertTrue(any("face.jpg" in item for item in findings))
        self.assertTrue(any("workspace_demo" in item for item in findings))
        (project_root / "face.jpg").unlink()
        (project_root / "workspace_demo" / "artifact.txt").unlink()
        (project_root / "workspace_demo").rmdir()
        git_dir = project_root / ".git"
        for path in sorted(git_dir.rglob("*"), reverse=True):
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                path.rmdir()
        if git_dir.exists():
            git_dir.rmdir()
        project_root.rmdir()


if __name__ == "__main__":
    unittest.main()
