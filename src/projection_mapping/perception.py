from __future__ import annotations

import numpy as np


def _cv2():
    import cv2
    return cv2


def optical_flow(prev_bgr: np.ndarray, curr_bgr: np.ndarray) -> np.ndarray:
    cv2 = _cv2()
    a = cv2.cvtColor(prev_bgr, cv2.COLOR_BGR2GRAY)
    b = cv2.cvtColor(curr_bgr, cv2.COLOR_BGR2GRAY)
    return cv2.calcOpticalFlowFarneback(a, b, None, 0.5, 3, 21, 3, 5, 1.2, 0)


class BackgroundMask:
    def __init__(self, history: int = 500, threshold: float = 16.0):
        self.model = _cv2().createBackgroundSubtractorMOG2(history=history, varThreshold=threshold, detectShadows=False)

    def __call__(self, frame_bgr: np.ndarray) -> np.ndarray:
        return self.model.apply(frame_bgr)
