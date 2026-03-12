from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _read_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip("'\"")
    return values


def _merge_files(paths: list[Path]) -> dict[str, str]:
    values: dict[str, str] = {}
    for path in paths:
        values.update(_read_env_file(path))
    return values


def save_local_config(path: Path, values: dict[str, str | int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"{key}={value}" for key, value in sorted(values.items()) if value not in {None, ""}]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


@dataclass(slots=True)
class AppConfig:
    telegram_bot_token: str | None
    telegram_owner_user_id: int | None
    output_pack_name: str | None
    output_pack_title: str | None
    output_pack_bot_username: str | None
    pilot_limit: int
    max_sticker_size_bytes: int
    max_duration_seconds: float
    max_fps: int
    require_manual_safety_review: bool
    local_config_path: Path | None = None

    @classmethod
    def load(cls, workdir: Path, project_root: Path | None = None) -> "AppConfig":
        root = project_root or Path.cwd()
        env_values = _merge_files(
            [
                root / ".env",
                root / ".env.local",
                workdir / ".env",
                workdir / ".env.local",
            ]
        )

        def get(name: str, default: str | None = None) -> str | None:
            return os.environ.get(name, env_values.get(name, default))

        owner_user_id = get("TELEGRAM_OWNER_USER_ID")
        return cls(
            telegram_bot_token=get("TELEGRAM_BOT_TOKEN"),
            telegram_owner_user_id=int(owner_user_id) if owner_user_id else None,
            output_pack_name=get("OUTPUT_PACK_NAME"),
            output_pack_title=get("OUTPUT_PACK_TITLE"),
            output_pack_bot_username=get("OUTPUT_PACK_BOT_USERNAME"),
            pilot_limit=int(get("PILOT_LIMIT", "10") or "10"),
            max_sticker_size_bytes=int(get("MAX_STICKER_SIZE_BYTES", str(256 * 1024)) or 256 * 1024),
            max_duration_seconds=float(get("MAX_DURATION_SECONDS", "3") or "3"),
            max_fps=int(get("MAX_FPS", "30") or "30"),
            require_manual_safety_review=(get("REQUIRE_MANUAL_SAFETY_REVIEW", "false") or "false").lower()
            in {"1", "true", "yes", "on"},
            local_config_path=root / ".env.local",
        )
