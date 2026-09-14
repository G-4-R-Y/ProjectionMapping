from __future__ import annotations

import numpy as np


class SpoutSender:
    """Best-effort adapter for SPOUT2ForPython.

    Backend APIs vary by package revision, so import is lazy and errors are explicit.
    For zero-copy production transport, prefer a native D3D/OpenGL shared-texture path.
    """
    def __init__(self, name: str = "ProjectionMapping"):
        try:
            import SpoutGL  # type: ignore
        except ImportError as exc:
            raise RuntimeError("Spout backend not installed. Install a compatible Spout2 Python binding on Windows.") from exc
        self.backend = SpoutGL
        self.name = name
        self.sender = SpoutGL.SpoutSender()
        if hasattr(self.sender, "setSenderName"):
            self.sender.setSenderName(name)

    def __call__(self, frame: np.ndarray):
        if hasattr(self.sender, "sendImage"):
            h, w = frame.shape[:2]
            self.sender.sendImage(frame, w, h, self.backend.GL_RGB, False)
            return True
        raise RuntimeError("installed Spout binding exposes an unsupported sender API")
