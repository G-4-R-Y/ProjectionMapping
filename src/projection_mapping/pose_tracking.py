from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import threading
import time
import urllib.request

import numpy as np

from .performance_bus import AnchorState, TrackingState, Vec3


# Versioned model URLs: explicit revisions are preferable to moving `latest` aliases.
_MEDIAPIPE_MODELS = {
    "hand": "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task",
    "pose": "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/1/pose_landmarker_full.task",
}


@dataclass
class _FilteredAnchor:
    position: np.ndarray
    timestamp: float


class _AnchorFilter:
    """Confidence-aware exponential smoothing with velocity estimation."""

    def __init__(self, smoothing: float = 0.62) -> None:
        self.smoothing = float(np.clip(smoothing, 0.0, 0.98))
        self._states: dict[str, _FilteredAnchor] = {}

    def update(
        self,
        name: str,
        position: tuple[float, float, float],
        timestamp: float,
        confidence: float,
        *,
        normal: Vec3 | None = None,
        handedness: str | None = None,
        source: str,
    ) -> AnchorState:
        raw = np.asarray(position, dtype=np.float32)
        old = self._states.get(name)
        if old is None:
            filtered = raw
            velocity = np.zeros(3, dtype=np.float32)
        else:
            dt = max(timestamp - old.timestamp, 1e-4)
            # Higher confidence allows slightly faster response; weak points are steadier.
            keep = np.clip(self.smoothing + (1.0 - confidence) * 0.18, 0.0, 0.985)
            filtered = old.position * keep + raw * (1.0 - keep)
            velocity = (filtered - old.position) / dt
        self._states[name] = _FilteredAnchor(filtered, timestamp)
        return AnchorState(
            name=name,
            position=Vec3(float(filtered[0]), float(filtered[1]), float(filtered[2])),
            velocity=Vec3(float(velocity[0]), float(velocity[1]), float(velocity[2])),
            confidence=float(np.clip(confidence, 0.0, 1.0)),
            normal=normal,
            handedness=handedness,
            source=source,
        )


class RTMPoseWholeBodyTracker:
    """Open-source whole-body tracker backed by RTMLib/RTMW.

    COCO-WholeBody provides 133 keypoints: body, feet, face and 21 points for each hand.
    This is the preferred fully-open semantic tracker. It is intentionally isolated behind
    the same TrackingState schema as MediaPipe so renderers never depend on model APIs.
    """

    # COCO body indices.
    _BODY = {
        "head": 0,
        "left_shoulder": 5,
        "right_shoulder": 6,
        "left_elbow": 7,
        "right_elbow": 8,
        "left_wrist": 9,
        "right_wrist": 10,
        "left_hip": 11,
        "right_hip": 12,
        "left_knee": 13,
        "right_knee": 14,
        "left_ankle": 15,
        "right_ankle": 16,
    }
    _LEFT_HAND = 91
    _RIGHT_HAND = 112

    def __init__(
        self,
        *,
        mode: str = "lightweight",
        backend: str = "onnxruntime",
        device: str = "cpu",
        confidence: float = 0.35,
        smoothing: float = 0.58,
    ) -> None:
        try:
            from rtmlib import Wholebody
        except ImportError as exc:
            raise RuntimeError(
                "RTMPose performer tracking is not installed. Run "
                "`python -m pip install -e '.[performer]'`."
            ) from exc
        self.model = Wholebody(mode=mode, backend=backend, device=device, to_openpose=False)
        self.confidence = float(confidence)
        self.filter = _AnchorFilter(smoothing=smoothing)

    @staticmethod
    def _score(scores: np.ndarray, index: int) -> float:
        try:
            return float(scores[index])
        except Exception:
            return 0.0

    def _anchor(
        self,
        anchors: list[AnchorState],
        keypoints: np.ndarray,
        scores: np.ndarray,
        index: int,
        name: str,
        timestamp: float,
    ) -> None:
        score = self._score(scores, index)
        if score < self.confidence or index >= len(keypoints):
            return
        x, y = keypoints[index][:2]
        anchors.append(
            self.filter.update(
                name,
                (float(x), float(y), 0.0),
                timestamp,
                score,
                source="rtmpose-wholebody",
            )
        )

    def update(self, bgr: np.ndarray, timestamp: float | None = None) -> TrackingState:
        timestamp = float(time.perf_counter() if timestamp is None else timestamp)
        height, width = bgr.shape[:2]
        keypoints, scores = self.model(bgr)
        kp = np.asarray(keypoints, dtype=np.float32)
        sc = np.asarray(scores, dtype=np.float32)
        if kp.ndim == 3:
            kp = kp[0] if len(kp) else np.empty((0, 2), np.float32)
        if sc.ndim == 2:
            sc = sc[0] if len(sc) else np.empty((0,), np.float32)
        if kp.size == 0:
            return TrackingState(timestamp, (width, height), source="rtmpose-wholebody")

        # RTMLib returns pixel coordinates. Normalize once at the semantic boundary.
        kp = kp.copy()
        kp[:, 0] /= max(float(width), 1.0)
        kp[:, 1] /= max(float(height), 1.0)
        anchors: list[AnchorState] = []
        for name, index in self._BODY.items():
            self._anchor(anchors, kp, sc, index, name, timestamp)

        # Palm centres are robust averages over wrist + MCP joints; fingertips are exposed
        # separately for particle emitters and gesture grammar.
        for side, base in (("left", self._LEFT_HAND), ("right", self._RIGHT_HAND)):
            palm_indices = [base + i for i in (0, 5, 9, 13, 17)]
            valid = [i for i in palm_indices if i < len(kp) and self._score(sc, i) >= self.confidence]
            if valid:
                p = np.mean(kp[valid, :2], axis=0)
                score = float(np.mean(sc[valid]))
                anchors.append(
                    self.filter.update(
                        f"{side}_palm",
                        (float(p[0]), float(p[1]), 0.0),
                        timestamp,
                        score,
                        handedness=side,
                        source="rtmpose-wholebody",
                    )
                )
            for finger, offset in (("thumb_tip", 4), ("index_tip", 8), ("middle_tip", 12)):
                self._anchor(anchors, kp, sc, base + offset, f"{side}_{finger}", timestamp)

        def midpoint(name: str, a: str, b: str) -> None:
            aa = next((x for x in anchors if x.name == a), None)
            bb = next((x for x in anchors if x.name == b), None)
            if aa and bb:
                p = Vec3(
                    (aa.position.x + bb.position.x) * 0.5,
                    (aa.position.y + bb.position.y) * 0.5,
                    (aa.position.z + bb.position.z) * 0.5,
                )
                c = min(aa.confidence, bb.confidence)
                anchors.append(
                    self.filter.update(name, (p.x, p.y, p.z), timestamp, c, source="rtmpose-wholebody")
                )

        midpoint("chest", "left_shoulder", "right_shoulder")
        midpoint("pelvis", "left_hip", "right_hip")
        confidence = float(np.mean([a.confidence for a in anchors])) if anchors else 0.0
        return TrackingState(
            timestamp=timestamp,
            frame_size=(width, height),
            anchors=tuple(anchors),
            performer_confidence=confidence,
            source="rtmpose-wholebody",
        )

    def close(self) -> None:
        self.model = None


class MediaPipeTaskTracker:
    """Optional MediaPipe Tasks hand+pose tracker using latest-frame-wins callbacks.

    MediaPipe is kept as a compatibility backend, not a core dependency. The open RTMPose
    path above is preferred when an entirely open stack is desired.
    """

    def __init__(
        self,
        *,
        cache_dir: str | Path | None = None,
        auto_download: bool = True,
        confidence: float = 0.45,
        smoothing: float = 0.58,
    ) -> None:
        try:
            import mediapipe as mp
        except ImportError as exc:
            raise RuntimeError(
                "MediaPipe tracking is not installed. Run `python -m pip install -e '.[mediapipe]'`."
            ) from exc
        self.mp = mp
        self.confidence = float(confidence)
        self.filter = _AnchorFilter(smoothing=smoothing)
        self.cache_dir = Path(cache_dir or Path.home() / ".cache" / "projection_mapping" / "mediapipe")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        hand_path = self._model_path("hand", auto_download)
        pose_path = self._model_path("pose", auto_download)
        self._lock = threading.Lock()
        self._hands = None
        self._pose = None
        self._hands_ts = -1
        self._pose_ts = -1

        vision = mp.tasks.vision
        base = mp.tasks.BaseOptions
        running = vision.RunningMode.LIVE_STREAM
        self.hand_task = vision.HandLandmarker.create_from_options(
            vision.HandLandmarkerOptions(
                base_options=base(model_asset_path=str(hand_path)),
                running_mode=running,
                num_hands=2,
                min_hand_detection_confidence=self.confidence,
                min_hand_presence_confidence=self.confidence,
                min_tracking_confidence=self.confidence,
                result_callback=self._on_hands,
            )
        )
        self.pose_task = vision.PoseLandmarker.create_from_options(
            vision.PoseLandmarkerOptions(
                base_options=base(model_asset_path=str(pose_path)),
                running_mode=running,
                num_poses=1,
                min_pose_detection_confidence=self.confidence,
                min_pose_presence_confidence=self.confidence,
                min_tracking_confidence=self.confidence,
                output_segmentation_masks=False,
                result_callback=self._on_pose,
            )
        )

    def _model_path(self, kind: str, auto_download: bool) -> Path:
        name = "hand_landmarker.task" if kind == "hand" else "pose_landmarker_full.task"
        path = self.cache_dir / name
        if path.exists():
            return path
        if not auto_download:
            raise FileNotFoundError(f"MediaPipe model missing: {path}")
        tmp = path.with_suffix(path.suffix + ".part")
        print(f"[performer] downloading MediaPipe {kind} model -> {path}", flush=True)
        urllib.request.urlretrieve(_MEDIAPIPE_MODELS[kind], tmp)
        tmp.replace(path)
        return path

    def _on_hands(self, result, _image, timestamp_ms: int) -> None:
        with self._lock:
            if timestamp_ms >= self._hands_ts:
                self._hands = result
                self._hands_ts = timestamp_ms

    def _on_pose(self, result, _image, timestamp_ms: int) -> None:
        with self._lock:
            if timestamp_ms >= self._pose_ts:
                self._pose = result
                self._pose_ts = timestamp_ms

    def submit(self, bgr: np.ndarray, timestamp: float | None = None) -> TrackingState:
        timestamp = float(time.perf_counter() if timestamp is None else timestamp)
        ts_ms = int(timestamp * 1000.0)
        rgb = np.ascontiguousarray(bgr[..., ::-1])
        image = self.mp.Image(image_format=self.mp.ImageFormat.SRGB, data=rgb)
        self.hand_task.detect_async(image, ts_ms)
        self.pose_task.detect_async(image, ts_ms)
        return self.latest(timestamp, (bgr.shape[1], bgr.shape[0]))

    @staticmethod
    def _category_name(item) -> str:
        name = getattr(item, "category_name", None) or getattr(item, "display_name", None)
        return str(name or "unknown").lower()

    def latest(self, timestamp: float, frame_size: tuple[int, int]) -> TrackingState:
        with self._lock:
            hands = self._hands
            pose = self._pose
        anchors: list[AnchorState] = []

        if pose is not None and getattr(pose, "pose_landmarks", None):
            lm = pose.pose_landmarks[0]
            mapping = {
                "head": 0,
                "left_shoulder": 11,
                "right_shoulder": 12,
                "left_elbow": 13,
                "right_elbow": 14,
                "left_wrist": 15,
                "right_wrist": 16,
                "left_hip": 23,
                "right_hip": 24,
                "left_knee": 25,
                "right_knee": 26,
                "left_ankle": 27,
                "right_ankle": 28,
            }
            for name, idx in mapping.items():
                p = lm[idx]
                confidence = float(getattr(p, "visibility", 1.0) or 0.0)
                if confidence < self.confidence:
                    continue
                anchors.append(
                    self.filter.update(
                        name,
                        (float(p.x), float(p.y), float(p.z or 0.0)),
                        timestamp,
                        confidence,
                        source="mediapipe-tasks",
                    )
                )

        if hands is not None and getattr(hands, "hand_landmarks", None):
            handedness = getattr(hands, "handedness", [])
            for i, lm in enumerate(hands.hand_landmarks):
                side = "unknown"
                score = 1.0
                if i < len(handedness) and handedness[i]:
                    cat = handedness[i][0]
                    side = self._category_name(cat)
                    score = float(getattr(cat, "score", 1.0) or 0.0)
                palm_ids = (0, 5, 9, 13, 17)
                p = np.mean([[lm[j].x, lm[j].y, lm[j].z or 0.0] for j in palm_ids], axis=0)
                a = np.asarray([lm[5].x - lm[0].x, lm[5].y - lm[0].y, (lm[5].z or 0.0) - (lm[0].z or 0.0)])
                b = np.asarray([lm[17].x - lm[0].x, lm[17].y - lm[0].y, (lm[17].z or 0.0) - (lm[0].z or 0.0)])
                n = np.cross(a, b)
                norm = float(np.linalg.norm(n))
                normal = Vec3(*(n / norm).tolist()) if norm > 1e-6 else None
                anchors.append(
                    self.filter.update(
                        f"{side}_palm",
                        (float(p[0]), float(p[1]), float(p[2])),
                        timestamp,
                        score,
                        normal=normal,
                        handedness=side,
                        source="mediapipe-tasks",
                    )
                )
                for name, idx in (("thumb_tip", 4), ("index_tip", 8), ("middle_tip", 12)):
                    q = lm[idx]
                    anchors.append(
                        self.filter.update(
                            f"{side}_{name}",
                            (float(q.x), float(q.y), float(q.z or 0.0)),
                            timestamp,
                            score,
                            handedness=side,
                            source="mediapipe-tasks",
                        )
                    )

        def midpoint(name: str, left: str, right: str) -> None:
            a = next((x for x in anchors if x.name == left), None)
            b = next((x for x in anchors if x.name == right), None)
            if a and b:
                anchors.append(
                    self.filter.update(
                        name,
                        ((a.position.x + b.position.x) * 0.5, (a.position.y + b.position.y) * 0.5, (a.position.z + b.position.z) * 0.5),
                        timestamp,
                        min(a.confidence, b.confidence),
                        source="mediapipe-tasks",
                    )
                )

        midpoint("chest", "left_shoulder", "right_shoulder")
        midpoint("pelvis", "left_hip", "right_hip")
        confidence = float(np.mean([a.confidence for a in anchors])) if anchors else 0.0
        return TrackingState(
            timestamp=timestamp,
            frame_size=frame_size,
            anchors=tuple(anchors),
            performer_confidence=confidence,
            source="mediapipe-tasks",
        )

    def close(self) -> None:
        for task in (self.hand_task, self.pose_task):
            try:
                task.close()
            except Exception:
                pass


__all__ = ["RTMPoseWholeBodyTracker", "MediaPipeTaskTracker"]
