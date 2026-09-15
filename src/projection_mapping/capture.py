from __future__ import annotations

import sys


class Camera:
    def __init__(self, device: int = 0, width: int | None = None, height: int | None = None):
        import cv2

        self.cv2 = cv2
        self.device = int(device)

        # CAP_DSHOW exists as a constant on non-Windows OpenCV builds too, so checking
        # `hasattr(cv2, "CAP_DSHOW")` is not sufficient. Using DirectShow on Linux can
        # make an otherwise valid /dev/video device fail to open.
        if sys.platform.startswith("win"):
            backends = [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY]
        elif sys.platform.startswith("linux"):
            backends = [cv2.CAP_V4L2, cv2.CAP_ANY]
        else:
            backends = [cv2.CAP_AVFOUNDATION, cv2.CAP_ANY] if sys.platform == "darwin" else [cv2.CAP_ANY]

        self.cap = None
        tried: list[str] = []
        for backend in backends:
            cap = cv2.VideoCapture(self.device, backend)
            tried.append(str(backend))
            if cap.isOpened():
                self.cap = cap
                break
            cap.release()

        if self.cap is None:
            raise RuntimeError(
                f"could not open camera {self.device}; tried OpenCV backends {', '.join(tried)}. "
                "On Linux check `ls -l /dev/video*` and whether another app owns the camera."
            )

        if width:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        if height:
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        backend_name = "unknown"
        try:
            backend_name = self.cap.getBackendName()
        except Exception:
            pass
        print(f"[camera] device={self.device} backend={backend_name}", flush=True)

    def read(self):
        ok, frame = self.cap.read()
        if not ok:
            raise RuntimeError(f"camera {self.device} read failed")
        return frame

    def close(self):
        if self.cap is not None:
            self.cap.release()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
