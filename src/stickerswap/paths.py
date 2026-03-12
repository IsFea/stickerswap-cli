from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class WorkspacePaths:
    root: Path
    raw: Path
    analysis: Path
    manifest: Path
    frames: Path
    swapped: Path
    encoded: Path
    temp: Path


def ensure_workspace(workdir: Path) -> WorkspacePaths:
    paths = WorkspacePaths(
        root=workdir,
        raw=workdir / "raw",
        analysis=workdir / "analysis",
        manifest=workdir / "manifest" / "stickers.json",
        frames=workdir / "frames",
        swapped=workdir / "swapped",
        encoded=workdir / "encoded",
        temp=workdir / "temp",
    )
    for path in [paths.root, paths.raw, paths.analysis, paths.frames, paths.swapped, paths.encoded, paths.temp]:
        path.mkdir(parents=True, exist_ok=True)
    return paths

