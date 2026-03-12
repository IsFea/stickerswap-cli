from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

STATUS_ORDER = {
    "pending": 0,
    "downloaded": 1,
    "analyzed": 2,
    "ready": 3,
    "review": 4,
    "skip": 5,
    "swapped": 6,
    "encoded": 7,
    "validated": 8,
    "published": 9,
}


@dataclass(slots=True)
class StickerRecord:
    source_pack: str
    sticker_id: str
    file_id: str
    file_unique_id: str
    file_name: str
    emoji: list[str]
    has_face: bool | None = None
    face_count: int = 0
    dominant_face_ratio: float = 0.0
    safety: str = "unknown"
    status: str = "pending"
    notes: list[str] = field(default_factory=list)
    raw_path: str | None = None
    analysis_preview_path: str | None = None
    analysis_overlay_path: str | None = None
    swapped_video_path: str | None = None
    encoded_path: str | None = None
    validation: dict[str, object] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "StickerRecord":
        return cls(**data)

    def advance(self, target_status: str) -> None:
        current = STATUS_ORDER.get(self.status, -1)
        target = STATUS_ORDER.get(target_status, -1)
        if target >= current:
            self.status = target_status


@dataclass(slots=True)
class StickerManifest:
    source_pack: str
    generated_at: str
    version: int = 1
    stickers: list[StickerRecord] = field(default_factory=list)

    @classmethod
    def load(cls, path: Path) -> "StickerManifest":
        payload = json.loads(path.read_text(encoding="utf-8"))
        stickers = [StickerRecord.from_dict(item) for item in payload.get("stickers", [])]
        return cls(
            source_pack=payload["source_pack"],
            generated_at=payload["generated_at"],
            version=payload.get("version", 1),
            stickers=stickers,
        )

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = asdict(self)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def by_status(self, *statuses: str) -> list[StickerRecord]:
        allowed = set(statuses)
        return [record for record in self.stickers if record.status in allowed]

