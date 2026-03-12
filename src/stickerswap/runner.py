from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from .bootstrap import ensure_model, ensure_runtime_dirs, ensure_system_dependencies, export_runtime_env
from .checks import candidate_file_paths, forbidden_file_findings, run_local_checks, secret_findings
from .config import AppConfig, save_local_config
from .pipeline import encode_pack, fetch_pack, publish_pack, summarize_manifest, swap_faces, validate_pack
from .runtime import RuntimeInfo, default_workspace, detect_runtime, slugify, with_bot_suffix
from .telegram import TelegramBotAPI


@dataclass(slots=True)
class RunOptions:
    source_pack: str | None
    face_image: Path | None
    workdir: Path | None
    output_pack_name: str | None
    output_pack_title: str | None
    resume: bool
    assume_yes: bool
    auto_install: bool
    save_local: bool


def _prompt(label: str, default: str | None = None, secret: bool = False) -> str:
    suffix = f" [{default}]" if default else ""
    value = input(f"{label}{suffix}: ").strip()
    if value:
        return value
    if default is not None:
        return default
    raise RuntimeError(f"{label} is required")


def _report(stage: str, message: str) -> None:
    print(f"[{stage}] {message}")


def _progress(stage: str, current: int, total: int, item: str) -> None:
    print(f"[{stage}] {current}/{total} {item}")


def _prepare_runtime(project_root: Path, workspace: Path, auto_install: bool, assume_yes: bool) -> RuntimeInfo:
    runtime = detect_runtime(workspace)
    ensure_runtime_dirs(runtime)
    ensure_system_dependencies(auto_install=auto_install, assume_yes=assume_yes, reporter=lambda msg: _report("bootstrap", msg))
    model_path = ensure_model(runtime, reporter=lambda msg: _report("bootstrap", msg))
    export_runtime_env(runtime, model_path)
    return runtime


def _load_config(project_root: Path, workspace: Path) -> AppConfig:
    return AppConfig.load(workspace, project_root=project_root)


def _ensure_output_naming(client: TelegramBotAPI, output_pack_name: str | None, output_pack_title: str | None) -> tuple[str, str]:
    bot_username = client.get_me()["username"]
    safe_title = output_pack_title or "StickerSwap Pack"
    safe_name = with_bot_suffix(output_pack_name or safe_title, bot_username)
    return safe_name, safe_title


def run_guided(project_root: Path, options: RunOptions) -> None:
    preliminary_workspace = options.workdir or default_workspace(options.source_pack or "stickerswap", project_root)
    config = _load_config(project_root, preliminary_workspace)
    source_pack = options.source_pack or _prompt("Source sticker pack short name")
    face_image = options.face_image or Path(_prompt("Face image path"))
    workspace = options.workdir or default_workspace(source_pack, project_root)
    runtime = _prepare_runtime(project_root, workspace, auto_install=options.auto_install, assume_yes=options.assume_yes)
    config = _load_config(project_root, workspace)
    token = config.telegram_bot_token or _prompt("Telegram bot token")
    owner_user_id = config.telegram_owner_user_id or int(_prompt("Telegram owner user id"))
    os.environ["TELEGRAM_BOT_TOKEN"] = token
    os.environ["TELEGRAM_OWNER_USER_ID"] = str(owner_user_id)
    client = TelegramBotAPI(token)
    output_pack_name, output_pack_title = _ensure_output_naming(
        client,
        options.output_pack_name or config.output_pack_name,
        options.output_pack_title or config.output_pack_title,
    )
    os.environ["OUTPUT_PACK_NAME"] = output_pack_name
    os.environ["OUTPUT_PACK_TITLE"] = output_pack_title
    os.environ["OUTPUT_PACK_BOT_USERNAME"] = client.get_me()["username"]
    if options.save_local:
        save_local_config(
            project_root / ".env.local",
            {
                "TELEGRAM_BOT_TOKEN": token,
                "TELEGRAM_OWNER_USER_ID": owner_user_id,
                "OUTPUT_PACK_NAME": output_pack_name,
                "OUTPUT_PACK_TITLE": output_pack_title,
                "OUTPUT_PACK_BOT_USERNAME": client.get_me()["username"],
            },
        )
        _report("config", f"Saved local defaults to {project_root / '.env.local'}")
    _report("runtime", f"Workspace: {runtime.workspace}")
    _report("runtime", f"Mode: {'Apple Silicon optimized' if runtime.is_apple_silicon else 'CPU'}")
    manifest = fetch_pack(workspace, source_pack, resume=options.resume, reporter=_progress)
    _report("fetch", summarize_manifest(manifest))
    manifest = swap_faces(workspace, face_image, resume=options.resume, reporter=_progress)
    _report("swap", summarize_manifest(manifest))
    manifest = encode_pack(workspace, resume=options.resume, reporter=_progress)
    _report("encode", summarize_manifest(manifest))
    manifest = validate_pack(workspace, reporter=_progress)
    _report("validate", summarize_manifest(manifest))
    manifest = publish_pack(workspace, resume=options.resume, reporter=_progress)
    _report("publish", summarize_manifest(manifest))
    print(f"Pack URL: https://t.me/addstickers/{output_pack_name}")


def run_check(project_root: Path) -> None:
    print("[check] Running local checks")
    errors = run_local_checks(project_root)
    print(f"[check] Candidate files: {len(candidate_file_paths(project_root))}")
    if forbidden_file_findings(project_root):
        print(f"[check] Forbidden files: {', '.join(forbidden_file_findings(project_root))}")
    if secret_findings(project_root):
        print(f"[check] Secret findings: {', '.join(secret_findings(project_root))}")
    if errors:
        raise RuntimeError("Local checks failed:\n- " + "\n- ".join(errors))
    print("[check] All local checks passed")


def run_live_test(project_root: Path, source_pack: str, face_image: Path, assume_yes: bool) -> None:
    workspace = default_workspace(f"live_test_{source_pack}", project_root)
    runtime = _prepare_runtime(project_root, workspace, auto_install=True, assume_yes=assume_yes)
    config = _load_config(project_root, workspace)
    if not config.telegram_bot_token or not config.telegram_owner_user_id:
        raise RuntimeError("Live test requires TELEGRAM_BOT_TOKEN and TELEGRAM_OWNER_USER_ID in local config or env")
    os.environ["TELEGRAM_BOT_TOKEN"] = config.telegram_bot_token
    os.environ["TELEGRAM_OWNER_USER_ID"] = str(config.telegram_owner_user_id)
    client = TelegramBotAPI(config.telegram_bot_token)
    debug_name = with_bot_suffix(f"stickerswap_live_test_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}", client.get_me()["username"])
    debug_title = "StickerSwap Live Test"
    os.environ["OUTPUT_PACK_NAME"] = debug_name
    os.environ["OUTPUT_PACK_TITLE"] = debug_title
    os.environ["OUTPUT_PACK_BOT_USERNAME"] = client.get_me()["username"]
    manifest = fetch_pack(workspace, source_pack, resume=False, limit=1, reporter=_progress)
    print(f"[live-test] {summarize_manifest(manifest)}")
    manifest = swap_faces(workspace, face_image, resume=False, reporter=_progress)
    print(f"[live-test] {summarize_manifest(manifest)}")
    manifest = encode_pack(workspace, resume=False, reporter=_progress)
    print(f"[live-test] {summarize_manifest(manifest)}")
    manifest = validate_pack(workspace, reporter=_progress)
    print(f"[live-test] {summarize_manifest(manifest)}")
    manifest = publish_pack(workspace, resume=False, reporter=_progress)
    print(f"[live-test] {summarize_manifest(manifest)}")
    print(f"[live-test] Debug pack URL: https://t.me/addstickers/{debug_name}")
