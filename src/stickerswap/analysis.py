from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .media import extract_preview_frame

try:
    import cv2
except ImportError:  # pragma: no cover
    cv2 = None


@dataclass(slots=True)
class FaceAnalysisResult:
    face_count: int
    dominant_face_ratio: float
    status: str
    safety: str
    notes: list[str]
    preview_path: Path | None = None
    overlay_path: Path | None = None


class StickerAnalyzer:
    def __init__(self, require_manual_safety_review: bool = False) -> None:
        self.require_manual_safety_review = require_manual_safety_review
        self.classifier = None
        if cv2 is not None:
            cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            self.classifier = cv2.CascadeClassifier(cascade_path)

    def analyze_video(self, video_path: Path, preview_path: Path, overlay_path: Path) -> FaceAnalysisResult:
        extract_preview_frame(video_path, preview_path)
        if cv2 is None or self.classifier is None:
            return FaceAnalysisResult(
                face_count=0,
                dominant_face_ratio=0.0,
                status="review",
                safety="unknown",
                notes=["opencv not installed; manual review required"],
                preview_path=preview_path,
            )

        image = cv2.imread(str(preview_path))
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = self.classifier.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(48, 48))
        image_area = image.shape[0] * image.shape[1]
        dominant_ratio = 0.0
        for (x, y, w, h) in faces:
            dominant_ratio = max(dominant_ratio, (w * h) / image_area)
            cv2.rectangle(image, (x, y), (x + w, y + h), (36, 255, 12), 2)
        overlay_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(overlay_path), image)

        face_count = len(faces)
        notes: list[str] = []
        safety = "pass"
        status = "skip"
        if face_count == 1 and dominant_ratio >= 0.045:
            status = "ready"
            notes.append("single dominant face detected")
        elif face_count == 0:
            notes.append("no face detected in preview frame")
            status = "skip"
        else:
            notes.append("multiple or ambiguous faces detected")
            status = "review"

        if dominant_ratio >= 0.35:
            safety = "review"
            status = "review"
            notes.append("frame flagged by conservative skin/zoom heuristic")

        if self.require_manual_safety_review:
            safety = "review"
            status = "review"
            notes.append("manual safety review is enabled")

        return FaceAnalysisResult(
            face_count=face_count,
            dominant_face_ratio=dominant_ratio,
            status=status,
            safety=safety,
            notes=notes,
            preview_path=preview_path,
            overlay_path=overlay_path,
        )

