from __future__ import annotations

import compileall
import re
import subprocess
import unittest
from pathlib import Path

SECRET_PATTERNS = [
    re.compile(r"\b\d{8,12}:[A-Za-z0-9_-]{20,}\b"),
]

FORBIDDEN_PATH_PARTS = [
    ".env.local",
    "workspace/",
    "workspace_",
    "workspaces/",
    ".onnx",
]


def _candidate_files(project_root: Path) -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )
    files: list[Path] = []
    for line in result.stdout.splitlines():
        if line.strip():
            files.append(project_root / line.strip())
    return files


def candidate_file_paths(project_root: Path) -> list[str]:
    return [str(path.relative_to(project_root)) for path in _candidate_files(project_root)]


def secret_findings(project_root: Path) -> list[str]:
    findings: list[str] = []
    for path in _candidate_files(project_root):
        if not path.is_file():
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pattern in SECRET_PATTERNS:
            if pattern.search(content):
                findings.append(str(path.relative_to(project_root)))
                break
    return findings


def forbidden_file_findings(project_root: Path) -> list[str]:
    findings: list[str] = []
    for path in candidate_file_paths(project_root):
        lowered = path.lower()
        if any(token in lowered for token in FORBIDDEN_PATH_PARTS):
            findings.append(path)
        if lowered.endswith((".jpg", ".jpeg", ".png", ".webp")):
            findings.append(path)
    return sorted(set(findings))


def run_local_checks(project_root: Path) -> list[str]:
    errors: list[str] = []
    if not compileall.compile_dir(project_root / "src", quiet=1):
        errors.append("compileall failed for src")
    if not compileall.compile_dir(project_root / "tests", quiet=1):
        errors.append("compileall failed for tests")
    suite = unittest.defaultTestLoader.discover(str(project_root / "tests"))
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    if not result.wasSuccessful():
        errors.append("unit tests failed")
    forbidden = forbidden_file_findings(project_root)
    if forbidden:
        errors.append(f"forbidden candidate files found: {', '.join(forbidden)}")
    secrets = secret_findings(project_root)
    if secrets:
        errors.append(f"secret-like values found in candidate files: {', '.join(secrets)}")
    return errors
