from .base import FaceSwapBackend, FaceSwapError

__all__ = ["FaceSwapBackend", "FaceSwapError", "InsightFaceSwapBackend"]


def __getattr__(name: str):
    if name == "InsightFaceSwapBackend":
        from .insightface_backend import InsightFaceSwapBackend

        return InsightFaceSwapBackend
    raise AttributeError(name)
