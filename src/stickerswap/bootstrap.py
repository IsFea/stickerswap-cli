from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Callable

import requests

from .media import MediaError
from .runtime import MODEL_FALLBACK_URL, RuntimeInfo

Reporter = Callable[[str], None]


def _run(command: list[str]) -> None:
    result = subprocess.run(command, check=False, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(command)}")


def ffmpeg_install_command() -> list[str] | None:
    if shutil.which("brew"):
        return ["brew", "install", "ffmpeg"]
    if shutil.which("apt-get"):
        return ["sudo", "apt-get", "install", "-y", "ffmpeg"]
    if shutil.which("dnf"):
        return ["sudo", "dnf", "install", "-y", "ffmpeg"]
    if shutil.which("yum"):
        return ["sudo", "yum", "install", "-y", "ffmpeg"]
    return None


def ensure_system_dependencies(auto_install: bool, assume_yes: bool, reporter: Reporter | None = None) -> None:
    if shutil.which("ffmpeg") and shutil.which("ffprobe"):
        return
    command = ffmpeg_install_command()
    if reporter is not None:
        reporter("ffmpeg/ffprobe not found")
    if auto_install and command is not None:
        if assume_yes or input(f"Install ffmpeg automatically using `{' '.join(command)}`? [Y/n]: ").strip().lower() in {"", "y", "yes"}:
            _run(command)
            return
    if command is not None:
        raise MediaError(f"ffmpeg/ffprobe not found. Install with `{' '.join(command)}`.")
    raise MediaError("ffmpeg/ffprobe not found and no supported package manager was detected.")


def ensure_runtime_dirs(runtime: RuntimeInfo) -> None:
    runtime.workspace.mkdir(parents=True, exist_ok=True)
    runtime.temp_dir.mkdir(parents=True, exist_ok=True)
    runtime.mpl_config_dir.mkdir(parents=True, exist_ok=True)
    runtime.model_dir.mkdir(parents=True, exist_ok=True)


def ensure_model(runtime: RuntimeInfo, reporter: Reporter | None = None) -> Path:
    ensure_runtime_dirs(runtime)
    if runtime.model_path.exists():
        return runtime.model_path
    if reporter is not None:
        reporter(f"Downloading face-swap model to {runtime.model_path}")
    response = requests.get(MODEL_FALLBACK_URL, stream=True, timeout=120)
    response.raise_for_status()
    total = int(response.headers.get("content-length", "0"))
    downloaded = 0
    with runtime.model_path.open("wb") as handle:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if not chunk:
                continue
            handle.write(chunk)
            downloaded += len(chunk)
            if reporter is not None and total:
                reporter(f"Model download: {downloaded // (1024 * 1024)} / {total // (1024 * 1024)} MB")
    return runtime.model_path


def export_runtime_env(runtime: RuntimeInfo, model_path: Path) -> None:
    os.environ["TMPDIR"] = str(runtime.temp_dir) + "/"
    os.environ["MPLCONFIGDIR"] = str(runtime.mpl_config_dir)
    os.environ["INSWAPPER_MODEL_PATH"] = str(model_path)

