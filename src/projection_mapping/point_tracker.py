from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass(frozen=True)
class TrackedPoint:
    id: int
    x: float
    y: float
    vx: float
    vy: float
    speed: float
    age: int
    quality: float

    def xy(self) -> tuple[int, int]:
        return int(round(self.x)), int(round(self.y))


class LKPointTracker:
    """Persistent Shi-Tomasi + pyramidal Lucas-Kanade point tracker.

    Tracks texture points rather than guessed body joints. Forward/backward validation
    rejects drifting tracks; new points are reseeded away from existing tracks. The
    caller may provide a foreground/person mask, or track the full frame.
    """

    def __init__(
        self,
        max_points: int = 96,
        quality_level: float = 0.012,
        min_distance: float = 10.0,
        reseed_interval: int = 10,
        fb_error: float = 1.6,
        lk_error: float = 32.0,
    ) -> None:
        self.max_points = max(8, int(max_points))
        self.quality_level = float(max(quality_level, 1e-5))
        self.min_distance = float(max(min_distance, 2.0))
        self.reseed_interval = max(1, int(reseed_interval))
        self.fb_error = float(max(fb_error, 0.1))
        self.lk_error = float(max(lk_error, 1.0))
        self._previous_gray: np.ndarray | None = None
        self._points = np.empty((0, 1, 2), dtype=np.float32)
        self._ids: list[int] = []
        self._ages: list[int] = []
        self._next_id = 1
        self._frame_index = 0

    def reset(self) -> None:
        self._previous_gray = None
        self._points = np.empty((0, 1, 2), dtype=np.float32)
        self._ids.clear()
        self._ages.clear()
        self._next_id = 1
        self._frame_index = 0

    @staticmethod
    def _gray(frame: np.ndarray) -> np.ndarray:
        arr = np.asarray(frame)
        if arr.ndim == 2:
            return arr.astype(np.uint8, copy=False)
        return cv2.cvtColor(arr, cv2.COLOR_BGR2GRAY)

    def _seed_mask(self, shape: tuple[int, int], mask: np.ndarray | None) -> np.ndarray:
        if mask is None:
            out = np.full(shape, 255, dtype=np.uint8)
        else:
            out = (np.asarray(mask) > 0).astype(np.uint8) * 255
            out = cv2.erode(out, np.ones((5, 5), np.uint8), iterations=1)
        for p in self._points.reshape(-1, 2):
            cv2.circle(out, (int(round(p[0])), int(round(p[1]))), int(self.min_distance), 0, -1)
        return out

    def _reseed(self, gray: np.ndarray, mask: np.ndarray | None) -> None:
        missing = self.max_points - len(self._ids)
        if missing <= 0:
            return
        seed_mask = self._seed_mask(gray.shape[:2], mask)
        fresh = cv2.goodFeaturesToTrack(
            gray,
            maxCorners=missing,
            qualityLevel=self.quality_level,
            minDistance=self.min_distance,
            mask=seed_mask,
            blockSize=5,
            useHarrisDetector=False,
        )
        if fresh is None or len(fresh) == 0:
            return
        fresh = fresh.astype(np.float32)
        if self._points.size:
            self._points = np.concatenate([self._points, fresh], axis=0)
        else:
            self._points = fresh
        for _ in range(len(fresh)):
            self._ids.append(self._next_id)
            self._ages.append(0)
            self._next_id += 1

    def update(self, frame: np.ndarray, mask: np.ndarray | None = None) -> list[TrackedPoint]:
        gray = self._gray(frame)
        self._frame_index += 1

        if self._previous_gray is None:
            self._previous_gray = gray.copy()
            self._reseed(gray, mask)
            return [
                TrackedPoint(pid, float(p[0]), float(p[1]), 0.0, 0.0, 0.0, age, 1.0)
                for pid, age, p in zip(self._ids, self._ages, self._points.reshape(-1, 2))
            ]

        tracked: list[TrackedPoint] = []
        if self._points.size:
            nxt, status, error = cv2.calcOpticalFlowPyrLK(
                self._previous_gray,
                gray,
                self._points,
                None,
                winSize=(21, 21),
                maxLevel=3,
                criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 24, 0.01),
            )
            if nxt is not None:
                back, back_status, _ = cv2.calcOpticalFlowPyrLK(
                    gray,
                    self._previous_gray,
                    nxt,
                    None,
                    winSize=(21, 21),
                    maxLevel=3,
                    criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 24, 0.01),
                )
            else:
                back = None
                back_status = None

            keep_points: list[np.ndarray] = []
            keep_ids: list[int] = []
            keep_ages: list[int] = []
            h, w = gray.shape[:2]
            for i, (old, pid, age) in enumerate(zip(self._points.reshape(-1, 2), self._ids, self._ages)):
                if nxt is None or status is None or not bool(status[i, 0]):
                    continue
                new = nxt[i, 0]
                if back is None or back_status is None or not bool(back_status[i, 0]):
                    continue
                fb = float(np.linalg.norm(old - back[i, 0]))
                err = float(error[i, 0]) if error is not None else 0.0
                x, y = float(new[0]), float(new[1])
                if fb > self.fb_error or err > self.lk_error or not (1 <= x < w - 1 and 1 <= y < h - 1):
                    continue
                if mask is not None and np.asarray(mask)[int(round(y)), int(round(x))] == 0:
                    continue
                vx, vy = x - float(old[0]), y - float(old[1])
                speed = float(np.hypot(vx, vy))
                quality = float(np.clip(1.0 - fb / self.fb_error, 0.0, 1.0))
                keep_points.append(new.reshape(1, 2))
                keep_ids.append(pid)
                keep_ages.append(age + 1)
                tracked.append(TrackedPoint(pid, x, y, vx, vy, speed, age + 1, quality))

            self._points = (
                np.asarray(keep_points, dtype=np.float32).reshape(-1, 1, 2)
                if keep_points
                else np.empty((0, 1, 2), dtype=np.float32)
            )
            self._ids = keep_ids
            self._ages = keep_ages

        need_reseed = (
            len(self._ids) < int(self.max_points * 0.70)
            or self._frame_index % self.reseed_interval == 0
        )
        if need_reseed:
            existing = set(self._ids)
            self._reseed(gray, mask)
            for pid, age, p in zip(self._ids, self._ages, self._points.reshape(-1, 2)):
                if pid not in existing:
                    tracked.append(TrackedPoint(pid, float(p[0]), float(p[1]), 0.0, 0.0, 0.0, age, 1.0))

        self._previous_gray = gray.copy()
        return tracked
