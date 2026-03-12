from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Callable

from .analysis import StickerAnalyzer
from .config import AppConfig
from .manifest import StickerManifest, StickerRecord
from .media import MediaError, assemble_frames_to_mp4, encode_webm, extract_frames, probe_video
from .paths import WorkspacePaths, ensure_workspace
from .telegram import TelegramBotAPI

ProgressReporter = Callable[[str, int, int, str], None]


def _report(reporter: ProgressReporter | None, stage: str, current: int, total: int, item: str) -> None:
    if reporter is not None:
        reporter(stage, current, total, item)


def load_or_create_manifest(paths: WorkspacePaths, source_pack: str) -> StickerManifest:
    if paths.manifest.exists():
        return StickerManifest.load(paths.manifest)
    manifest = StickerManifest(source_pack=source_pack, generated_at=datetime.now(UTC).isoformat())
    manifest.save(paths.manifest)
    return manifest


def fetch_pack(
    workdir: Path,
    source_pack: str,
    resume: bool = False,
    limit: int | None = None,
    reporter: ProgressReporter | None = None,
) -> StickerManifest:
    paths = ensure_workspace(workdir)
    config = AppConfig.load(workdir)
    if not config.telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is required for fetch-pack")
    client = TelegramBotAPI(config.telegram_bot_token)
    sticker_set = client.get_sticker_set(source_pack)
    existing_manifest = StickerManifest.load(paths.manifest) if resume and paths.manifest.exists() else None
    existing_records = {record.file_unique_id: record for record in existing_manifest.stickers} if existing_manifest else {}
    manifest = StickerManifest(source_pack=source_pack, generated_at=datetime.now(UTC).isoformat())
    downloaded = 0
    video_stickers = [sticker for sticker in sticker_set["stickers"] if sticker.get("is_video", False)]
    if limit is not None:
        video_stickers = video_stickers[:limit]
    for index, sticker in enumerate(video_stickers, start=1):
        if not sticker.get("is_video", False):
            continue
        _report(reporter, "fetch", index, len(video_stickers), sticker["file_unique_id"])
        file_info = client.get_file(sticker["file_id"])
        file_name = f"{sticker['file_unique_id']}.webm"
        raw_path = paths.raw / file_name
        if not (resume and raw_path.exists()):
            client.download_file(file_info["file_path"], raw_path)
        existing = existing_records.get(sticker["file_unique_id"])
        if existing:
            existing.file_id = sticker["file_id"]
            existing.file_name = file_name
            existing.raw_path = str(raw_path)
            existing.emoji = [sticker.get("emoji", "🙂")]
            existing.source_pack = source_pack
            if existing.status == "pending":
                existing.status = "downloaded"
            manifest.stickers.append(existing)
            continue
        manifest.stickers.append(
            StickerRecord(
                source_pack=source_pack,
                sticker_id=str(sticker["file_unique_id"]),
                file_id=sticker["file_id"],
                file_unique_id=sticker["file_unique_id"],
                file_name=file_name,
                emoji=[sticker.get("emoji", "🙂")],
                status="downloaded",
                raw_path=str(raw_path),
            )
        )
        downloaded += 1
    manifest.save(paths.manifest)
    return manifest


def analyze_pack(workdir: Path, limit: int | None = None, resume: bool = False) -> StickerManifest:
    paths = ensure_workspace(workdir)
    config = AppConfig.load(workdir)
    manifest = StickerManifest.load(paths.manifest)
    analyzer = StickerAnalyzer(require_manual_safety_review=config.require_manual_safety_review)
    ready_count = 0
    for record in manifest.stickers:
        if resume and record.status in {"ready", "review", "skip", "analyzed", "swapped", "encoded", "validated", "published"}:
            continue
        if limit is not None and ready_count >= limit:
            break
        raw_path = Path(record.raw_path or paths.raw / record.file_name)
        preview_path = paths.analysis / f"{record.file_unique_id}_preview.png"
        overlay_path = paths.analysis / f"{record.file_unique_id}_overlay.png"
        result = analyzer.analyze_video(raw_path, preview_path, overlay_path)
        record.has_face = result.face_count > 0
        record.face_count = result.face_count
        record.dominant_face_ratio = result.dominant_face_ratio
        record.analysis_preview_path = str(result.preview_path) if result.preview_path else None
        record.analysis_overlay_path = str(result.overlay_path) if result.overlay_path else None
        record.safety = result.safety
        record.notes = sorted(set(record.notes + result.notes))
        record.status = result.status
        if result.status == "ready":
            ready_count += 1
    manifest.save(paths.manifest)
    return manifest


def swap_faces(
    workdir: Path,
    face_image: Path,
    resume: bool = False,
    reporter: ProgressReporter | None = None,
) -> StickerManifest:
    paths = ensure_workspace(workdir)
    manifest = StickerManifest.load(paths.manifest)
    from .backends import InsightFaceSwapBackend

    backend = InsightFaceSwapBackend()
    backend.prepare_identity(face_image)
    processable = [
        record
        for record in manifest.stickers
        if record.status in {"ready", "review", "skip", "downloaded"}
        or (record.status == "swapped" and record.swapped_video_path and not Path(record.swapped_video_path).exists())
    ]
    for index, record in enumerate(processable, start=1):
        output_video = paths.swapped / record.file_name.replace(".webm", ".mp4")
        _report(reporter, "swap", index, len(processable), record.file_name)
        if resume and output_video.exists():
            record.swapped_video_path = str(output_video)
            record.advance("swapped")
            continue
        frame_input_dir = paths.frames / record.file_unique_id / "input"
        frame_output_dir = paths.frames / record.file_unique_id / "output"
        fps = extract_frames(Path(record.raw_path or paths.raw / record.file_name), frame_input_dir)
        backend.swap_directory(frame_input_dir, frame_output_dir)
        assemble_frames_to_mp4(frame_output_dir, fps=fps, output_path=output_video)
        record.swapped_video_path = str(output_video)
        record.advance("swapped")
    manifest.save(paths.manifest)
    return manifest


def encode_pack(workdir: Path, resume: bool = False, reporter: ProgressReporter | None = None) -> StickerManifest:
    paths = ensure_workspace(workdir)
    config = AppConfig.load(workdir)
    manifest = StickerManifest.load(paths.manifest)
    processable = [record for record in manifest.stickers if record.status == "swapped"]
    for index, record in enumerate(processable, start=1):
        _report(reporter, "encode", index, len(processable), record.file_name)
        encoded_path = paths.encoded / record.file_name
        if resume and encoded_path.exists():
            record.encoded_path = str(encoded_path)
            record.advance("encoded")
            continue
        input_path = Path(record.swapped_video_path or record.raw_path or "")
        encode_webm(
            input_path=input_path,
            output_path=encoded_path,
            max_fps=config.max_fps,
            max_duration=config.max_duration_seconds,
            max_bytes=config.max_sticker_size_bytes,
        )
        record.encoded_path = str(encoded_path)
        record.advance("encoded")
    manifest.save(paths.manifest)
    return manifest


def validate_pack(workdir: Path, reporter: ProgressReporter | None = None) -> StickerManifest:
    paths = ensure_workspace(workdir)
    config = AppConfig.load(workdir)
    manifest = StickerManifest.load(paths.manifest)
    processable = [record for record in manifest.stickers if record.status in {"encoded", "validated"}]
    for index, record in enumerate(processable, start=1):
        _report(reporter, "validate", index, len(processable), record.file_name)
        if not record.encoded_path:
            continue
        probe = probe_video(Path(record.encoded_path))
        file_size = Path(record.encoded_path).stat().st_size
        validation = {
            "width": probe.width,
            "height": probe.height,
            "duration": probe.duration,
            "fps": probe.fps,
            "codec_name": probe.codec_name,
            "has_audio": probe.has_audio,
            "file_size": file_size,
            "emoji_count": len(record.emoji),
        }
        errors: list[str] = []
        if probe.codec_name != "vp9":
            errors.append("codec must be vp9")
        if probe.has_audio:
            errors.append("audio stream must be absent")
        if max(probe.width, probe.height) != 512:
            errors.append("one side must equal 512 px")
        if probe.duration > config.max_duration_seconds + 0.01:
            errors.append("duration exceeds limit")
        if probe.fps > config.max_fps + 0.01:
            errors.append("fps exceeds limit")
        if file_size > config.max_sticker_size_bytes:
            errors.append("file size exceeds limit")
        if not record.emoji:
            errors.append("emoji mapping is missing")
        validation["errors"] = errors
        record.validation = validation
        record.status = "validated" if not errors else "review"
        if errors:
            record.notes = sorted(set(record.notes + errors))
    manifest.save(paths.manifest)
    return manifest


def publish_pack(workdir: Path, resume: bool = False, reporter: ProgressReporter | None = None) -> StickerManifest:
    paths = ensure_workspace(workdir)
    config = AppConfig.load(workdir)
    manifest = StickerManifest.load(paths.manifest)
    if not config.telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is required for publish-pack")
    if not config.telegram_owner_user_id:
        raise RuntimeError("TELEGRAM_OWNER_USER_ID is required for publish-pack")
    if not config.output_pack_name or not config.output_pack_title:
        raise RuntimeError("OUTPUT_PACK_NAME and OUTPUT_PACK_TITLE are required for publish-pack")
    client = TelegramBotAPI(config.telegram_bot_token)
    bot_user = client.get_me()
    bot_username = (config.output_pack_bot_username or bot_user["username"]).lower()
    if not config.output_pack_name.lower().endswith(f"_by_{bot_username}"):
        raise RuntimeError(f"OUTPUT_PACK_NAME must end with _by_{bot_username}")

    publishable = [record for record in manifest.stickers if record.status in {"validated", "published"} and record.encoded_path]
    publishable.sort(key=lambda record: (record.status != "published", record.file_name))
    if not publishable:
        raise RuntimeError("No validated stickers found")

    first = publishable[0]
    set_already_created = any(record.status == "published" for record in publishable)
    if not (resume and set_already_created):
        _report(reporter, "publish", 1, len(publishable), first.file_name)
        client.create_new_sticker_set(
            user_id=config.telegram_owner_user_id,
            name=config.output_pack_name,
            title=config.output_pack_title,
            sticker_path=Path(first.encoded_path),
            emoji_list=first.emoji or ["🙂"],
        )
        first.advance("published")

    for index, record in enumerate(publishable[1:], start=2):
        _report(reporter, "publish", index, len(publishable), record.file_name)
        if resume and record.status == "published":
            continue
        client.add_sticker_to_set(
            user_id=config.telegram_owner_user_id,
            name=config.output_pack_name,
            sticker_path=Path(record.encoded_path),
            emoji_list=record.emoji or ["🙂"],
        )
        record.advance("published")
    manifest.save(paths.manifest)
    return manifest


def summarize_manifest(manifest: StickerManifest) -> str:
    counts: dict[str, int] = {}
    for record in manifest.stickers:
        counts[record.status] = counts.get(record.status, 0) + 1
    summary = ", ".join(f"{status}={count}" for status, count in sorted(counts.items()))
    return f"{manifest.source_pack}: {len(manifest.stickers)} stickers ({summary})"
