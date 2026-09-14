from __future__ import annotations


class Camera:
    def __init__(self, device: int = 0, width: int | None = None, height: int | None = None):
        import cv2
        self.cv2 = cv2
        self.cap = cv2.VideoCapture(device, cv2.CAP_DSHOW if hasattr(cv2, "CAP_DSHOW") else 0)
        if width:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        if height:
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        if not self.cap.isOpened():
            raise RuntimeError(f"could not open camera {device}")

    def read(self):
        ok, frame = self.cap.read()
        if not ok:
            raise RuntimeError("camera read failed")
        return frame

    def close(self):
        self.cap.release()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
