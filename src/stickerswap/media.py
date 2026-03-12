from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


class MediaError(RuntimeError):
    pass


def ensure_ffmpeg() -> None:
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        raise MediaError("ffmpeg/ffprobe not found. Install with `brew install ffmpeg`.")


def _run(command: list[str]) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        raise MediaError(result.stderr.strip() or f"Command failed: {' '.join(command)}")
    return result


@dataclass(slots=True)
class VideoProbe:
    width: int
    height: int
    duration: float
    fps: float
    codec_name: str
    has_audio: bool


def probe_video(path: Path) -> VideoProbe:
    ensure_ffmpeg()
    result = _run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_streams",
            "-show_format",
            "-of",
            "json",
            str(path),
        ]
    )
    payload = json.loads(result.stdout)
    video_stream = next((stream for stream in payload["streams"] if stream["codec_type"] == "video"), None)
    if video_stream is None:
        raise MediaError(f"No video stream found in {path}")
    audio_stream = next((stream for stream in payload["streams"] if stream["codec_type"] == "audio"), None)
    frame_rate = video_stream.get("r_frame_rate", "0/1")
    numerator, denominator = frame_rate.split("/")
    fps = (float(numerator) / float(denominator)) if float(denominator) else 0.0
    duration = float(video_stream.get("duration") or payload.get("format", {}).get("duration") or 0.0)
    return VideoProbe(
        width=int(video_stream["width"]),
        height=int(video_stream["height"]),
        duration=duration,
        fps=fps,
        codec_name=video_stream.get("codec_name", ""),
        has_audio=audio_stream is not None,
    )


def extract_preview_frame(video_path: Path, output_path: Path, time_offset: float = 0.5) -> None:
    ensure_ffmpeg()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    _run(["ffmpeg", "-y", "-ss", str(time_offset), "-i", str(video_path), "-frames:v", "1", str(output_path)])


def extract_frames(video_path: Path, output_dir: Path, fps_cap: int = 30) -> float:
    ensure_ffmpeg()
    output_dir.mkdir(parents=True, exist_ok=True)
    probe = probe_video(video_path)
    fps = min(int(round(probe.fps)) or 15, fps_cap)
    _run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(video_path),
            "-vf",
            f"fps={fps}",
            str(output_dir / "frame_%04d.png"),
        ]
    )
    return float(fps)


def encode_webm(input_path: Path, output_path: Path, max_fps: int, max_duration: float, max_bytes: int) -> None:
    ensure_ffmpeg()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    crf_candidates = [30, 32, 34, 36, 38, 40, 42, 46]
    last_error: str | None = None
    for crf in crf_candidates:
        try:
            _run(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    str(input_path),
                    "-an",
                    "-c:v",
                    "libvpx-vp9",
                    "-pix_fmt",
                    "yuva420p",
                    "-b:v",
                    "0",
                    "-crf",
                    str(crf),
                    "-r",
                    str(max_fps),
                    "-vf",
                    "scale='if(gt(iw,ih),512,-2)':'if(gt(iw,ih),-2,512)':flags=lanczos,"
                    f"fps={max_fps},trim=duration={max_duration}",
                    "-deadline",
                    "good",
                    "-row-mt",
                    "1",
                    "-tile-columns",
                    "2",
                    "-auto-alt-ref",
                    "0",
                    str(output_path),
                ]
            )
        except MediaError as exc:
            last_error = str(exc)
            continue
        if output_path.stat().st_size <= max_bytes:
            return
    if output_path.exists():
        return
    raise MediaError(last_error or "Failed to encode WEBM within size constraints")


def assemble_frames_to_mp4(frames_dir: Path, fps: float, output_path: Path) -> None:
    ensure_ffmpeg()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    _run(
        [
            "ffmpeg",
            "-y",
            "-framerate",
            str(fps),
            "-i",
            str(frames_dir / "frame_%04d.png"),
            "-vf",
            "pad=ceil(iw/2)*2:ceil(ih/2)*2",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            str(output_path),
        ]
    )
