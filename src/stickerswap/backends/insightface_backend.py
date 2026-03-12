from __future__ import annotations

import os
from pathlib import Path

import numpy as np

from .base import FaceSwapBackend, FaceSwapError

try:
    import cv2
    import onnxruntime
    from insightface.app import FaceAnalysis
    from insightface.model_zoo import get_model
except ImportError:  # pragma: no cover
    cv2 = None
    onnxruntime = None
    FaceAnalysis = None
    get_model = None


class InsightFaceSwapBackend(FaceSwapBackend):
    def __init__(self) -> None:
        if cv2 is None or FaceAnalysis is None or get_model is None:
            raise FaceSwapError(
                "insightface backend is unavailable. Install with `pip install -e \".[face-swap]\"`."
            )
        available_providers = onnxruntime.get_available_providers() if onnxruntime is not None else ["CPUExecutionProvider"]
        providers = [provider for provider in ["CoreMLExecutionProvider", "CPUExecutionProvider"] if provider in available_providers]
        self.app = FaceAnalysis(name="buffalo_l", providers=providers)
        self.app.prepare(ctx_id=-1, det_size=(640, 640))
        local_model = os.environ.get("INSWAPPER_MODEL_PATH")
        if local_model and Path(local_model).exists():
            self.swapper = get_model(local_model, download=False, providers=providers)
        else:
            self.swapper = get_model("inswapper_128.onnx", download=True, download_zip=True, providers=providers)
        self.identity_face = None

    @staticmethod
    def _sorted_faces(faces: list) -> list:
        return sorted(
            faces,
            key=lambda item: (item.bbox[2] - item.bbox[0]) * (item.bbox[3] - item.bbox[1]),
            reverse=True,
        )

    @staticmethod
    def _enhance_for_detection(image):
        # Detection-only preprocessing for dark/profile/extreme-closeup frames.
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        l_channel = clahe.apply(l_channel)
        enhanced = cv2.merge((l_channel, a_channel, b_channel))
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
        gamma = 0.85
        lookup = np.array([((i / 255.0) ** gamma) * 255 for i in range(256)], dtype="uint8")
        return cv2.LUT(enhanced, lookup)

    def _swap_with_padding(self, image):
        height, width = image.shape[:2]
        pad_y = max(int(height * 0.2), 48)
        pad_x = max(int(width * 0.2), 48)
        padded = cv2.copyMakeBorder(image, pad_y, pad_y, pad_x, pad_x, cv2.BORDER_REPLICATE)
        padded_faces = self.app.get(padded)
        if not padded_faces:
            enhanced = self._enhance_for_detection(padded)
            padded_faces = self.app.get(enhanced)
        if not padded_faces:
            return image
        swapped = padded
        for face in self._sorted_faces(padded_faces):
            swapped = self.swapper.get(swapped, face, self.identity_face, paste_back=True)
        return swapped[pad_y : pad_y + height, pad_x : pad_x + width]

    def prepare_identity(self, identity_image: Path) -> None:
        image = cv2.imread(str(identity_image))
        faces = self.app.get(image)
        if not faces:
            raise FaceSwapError(f"No source face found in {identity_image}")
        self.identity_face = max(faces, key=lambda item: (item.bbox[2] - item.bbox[0]) * (item.bbox[3] - item.bbox[1]))

    def swap_directory(self, input_dir: Path, output_dir: Path) -> None:
        if self.identity_face is None:
            raise FaceSwapError("Identity face is not prepared")
        output_dir.mkdir(parents=True, exist_ok=True)
        for frame_path in sorted(input_dir.glob("frame_*.png")):
            image = cv2.imread(str(frame_path))
            faces = self.app.get(image)
            if not faces:
                enhanced = self._enhance_for_detection(image)
                faces = self.app.get(enhanced)
            if not faces:
                cv2.imwrite(str(output_dir / frame_path.name), self._swap_with_padding(image))
                continue
            swapped = image
            # Swap all detected faces, largest first, so ambiguous multi-face frames are still processed.
            for face in self._sorted_faces(faces):
                swapped = self.swapper.get(swapped, face, self.identity_face, paste_back=True)
            cv2.imwrite(str(output_dir / frame_path.name), swapped)
