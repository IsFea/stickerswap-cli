from __future__ import annotations

import platform
import re
from dataclasses import dataclass
from pathlib import Path

MODEL_FALLBACK_URL = "https://huggingface.co/aproxtimedev/swap-face-models/resolve/main/inswapper_128.onnx"


@dataclass(slots=True)
class RuntimeInfo:
    system: str
    machine: str
    is_apple_silicon: bool
    workspace: Path
    temp_dir: Path
    mpl_config_dir: Path
    model_dir: Path
    model_path: Path


def detect_runtime(workspace: Path) -> RuntimeInfo:
    system = platform.system()
    machine = platform.machine().lower()
    temp_dir = workspace / "temp"
    model_dir = workspace / "models"
    return RuntimeInfo(
        system=system,
        machine=machine,
        is_apple_silicon=(system == "Darwin" and machine == "arm64"),
        workspace=workspace,
        temp_dir=temp_dir,
        mpl_config_dir=temp_dir / "mpl",
        model_dir=model_dir,
        model_path=model_dir / "inswapper_128.onnx",
    )


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return slug or "stickerswap"


def default_workspace(source_pack: str, project_root: Path) -> Path:
    return project_root / "workspaces" / slugify(source_pack)


def with_bot_suffix(name: str, bot_username: str) -> str:
    suffix = f"_by_{bot_username.lower()}"
    cleaned = slugify(name)
    if cleaned.endswith(suffix):
        return cleaned
    return f"{cleaned}{suffix}"

