from __future__ import annotations

from pathlib import Path


class FaceSwapError(RuntimeError):
    pass


class FaceSwapBackend:
    def prepare_identity(self, identity_image: Path) -> None:
        raise NotImplementedError

    def swap_directory(self, input_dir: Path, output_dir: Path) -> None:
        raise NotImplementedError

