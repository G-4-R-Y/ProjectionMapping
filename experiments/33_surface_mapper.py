"""Interactive multi-surface corner-pin editor and projection-mapping player.

Drag the four handles to align content with a physical surface. Profiles are
autosaved as resolution-independent JSON and can be reused by other runtimes.

Keys: TAB next surface, N add, X delete, R reset, G guides, S save,
      [ / ] feather, F11 fullscreen, ESC exit.
"""
from __future__ import annotations

import argparse
from functools import lru_cache
import math
import time
from pathlib import Path

import cv2
import numpy as np

from projection_mapping.color_palettes import sample_palette
from projection_mapping.runtime import FullscreenSink
from projection_mapping.surface_mapping import MappedSurface, SurfaceMapProfile, SurfaceMapRenderer


@lru_cache(maxsize=8)
def _calibration_plate(width: int, height: int) -> np.ndarray:
    y, x = np.indices((height, width), dtype=np.float32)
    u = x / max(width - 1, 1)
    v = y / max(height - 1, 1)
    cells = ((np.floor(u * 12) + np.floor(v * 7)) % 2)[..., None]
    # Palette samples are RGB; OpenCV display frames are BGR.
    cold = np.asarray(sample_palette("aurora_ice", 0.45)[::-1], dtype=np.float32)
    hot = np.asarray(sample_palette("ember_gold", 0.62)[::-1], dtype=np.float32)
    image = (cold * (0.10 + cells * 0.16) + hot * (0.08 + (1.0 - cells) * 0.10)) * 255
    image = np.broadcast_to(image, (height, width, 3)).copy()

    spacing_x = max(width // 12, 12)
    spacing_y = max(height // 7, 12)
    image[:, ::spacing_x] = (235, 245, 255)
    image[::spacing_y, :] = (235, 245, 255)
    image[:, max(width // 2 - 1, 0) : width // 2 + 2] = (50, 255, 170)
    image[max(height // 2 - 1, 0) : height // 2 + 2, :] = (255, 110, 55)

    cv2.putText(image, "TL", (16, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
    cv2.putText(image, "TR", (width - 70, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
    cv2.putText(image, "BR", (width - 70, height - 18), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
    cv2.putText(image, "BL", (16, height - 18), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
    return np.clip(image, 0, 255).astype(np.uint8)


def calibration_content(width: int, height: int, t: float) -> np.ndarray:
    """Animated UV/grid plate that makes orientation and distortion obvious."""
    image = _calibration_plate(width, height).copy()
    cx = int((0.5 + 0.34 * math.cos(t * 0.53)) * width)
    cy = int((0.5 + 0.28 * math.sin(t * 0.71)) * height)
    cv2.circle(image, (cx, cy), max(min(width, height) // 28, 4), (255, 255, 255), -1, cv2.LINE_AA)
    return image


class ContentSource:
    def __init__(self, source: str, width: int, height: int):
        self.source = source
        self.width = width
        self.height = height
        self.capture: cv2.VideoCapture | None = None
        self.still: np.ndarray | None = None
        if source != "builtin:calibration":
            still = cv2.imread(source, cv2.IMREAD_COLOR)
            if still is not None:
                self.still = still
            else:
                self.capture = cv2.VideoCapture(source)
                if not self.capture.isOpened():
                    raise ValueError(f"could not open image/video source: {source}")

    def frame(self, t: float) -> np.ndarray:
        if self.source == "builtin:calibration":
            return calibration_content(self.width, self.height, t)
        if self.still is not None:
            return cv2.resize(self.still, (self.width, self.height), interpolation=cv2.INTER_AREA)
        assert self.capture is not None
        ok, frame = self.capture.read()
        if not ok:
            self.capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ok, frame = self.capture.read()
        if not ok:
            raise RuntimeError(f"video source stopped producing frames: {self.source}")
        return cv2.resize(frame, (self.width, self.height), interpolation=cv2.INTER_AREA)

    def close(self) -> None:
        if self.capture is not None:
            self.capture.release()


class SurfaceEditor:
    def __init__(self, profile: SurfaceMapProfile, profile_path: Path, guides: bool = True):
        self.profile = profile
        self.profile_path = profile_path
        self.selected_surface = 0
        self.selected_corner: int | None = None
        self.guides = guides
        self.dirty = False

    @property
    def surface(self) -> MappedSurface:
        return self.profile.surfaces[self.selected_surface]

    def _save(self) -> None:
        self.profile.save(self.profile_path)
        self.dirty = False
        print(f"[surface-map] saved {self.profile_path.resolve()}", flush=True)

    def mouse(self, event: int, x: int, y: int, _flags: int, _param: object) -> None:
        width, height = self.profile.projector_width, self.profile.projector_height
        point = np.asarray([x / max(width - 1, 1), y / max(height - 1, 1)])
        corners = np.asarray(self.surface.projector_corners)
        if event == cv2.EVENT_LBUTTONDOWN:
            distances = np.linalg.norm((corners - point) * np.asarray([width, height]), axis=1)
            corner = int(np.argmin(distances))
            if distances[corner] <= max(min(width, height) * 0.045, 24):
                self.selected_corner = corner
        elif event == cv2.EVENT_MOUSEMOVE and self.selected_corner is not None:
            corners[self.selected_corner] = np.clip(point, 0.0, 1.0)
            self.surface.projector_corners = tuple(map(tuple, corners))  # type: ignore[assignment]
            self.dirty = True
        elif event == cv2.EVENT_LBUTTONUP:
            self.selected_corner = None
            if self.dirty and abs(self.surface.projector_area()) >= 1e-6:
                self._save()

    def key(self, key: int) -> None:
        low = key & 0xFF
        if low == 9:  # TAB
            self.selected_surface = (self.selected_surface + 1) % len(self.profile.surfaces)
        elif low in (ord("g"), ord("G")):
            self.guides = not self.guides
        elif low in (ord("s"), ord("S")):
            self._save()
        elif low in (ord("n"), ord("N")):
            number = len(self.profile.surfaces) + 1
            inset = min(0.06 * (number - 1), 0.24)
            self.profile.surfaces.append(
                MappedSurface(
                    name=f"surface_{number}",
                    projector_corners=(
                        (inset, inset),
                        (1.0 - inset, inset),
                        (1.0 - inset, 1.0 - inset),
                        (inset, 1.0 - inset),
                    ),
                )
            )
            self.selected_surface = len(self.profile.surfaces) - 1
            self._save()
        elif low in (ord("x"), ord("X")) and len(self.profile.surfaces) > 1:
            del self.profile.surfaces[self.selected_surface]
            self.selected_surface %= len(self.profile.surfaces)
            self._save()
        elif low in (ord("r"), ord("R")):
            self.surface.projector_corners = (
                (0.0, 0.0),
                (1.0, 0.0),
                (1.0, 1.0),
                (0.0, 1.0),
            )
            self._save()
        elif low == ord("["):
            self.surface.feather = max(0.0, self.surface.feather - 0.002)
            self._save()
        elif low == ord("]"):
            self.surface.feather = min(0.25, self.surface.feather + 0.002)
            self._save()

    def overlay(self, frame: np.ndarray) -> np.ndarray:
        if not self.guides:
            return frame
        output = frame.copy()
        width, height = self.profile.projector_width, self.profile.projector_height
        for index, surface in enumerate(self.profile.surfaces):
            corners = np.rint(np.asarray(surface.projector_corners) * [width - 1, height - 1]).astype(np.int32)
            active = index == self.selected_surface
            color = (60, 255, 190) if active else (160, 110, 255)
            cv2.polylines(output, [corners], True, color, 2 if active else 1, cv2.LINE_AA)
            for corner_index, corner in enumerate(corners):
                cv2.circle(output, tuple(corner), 10 if active else 6, color, -1, cv2.LINE_AA)
                if active:
                    cv2.putText(
                        output,
                        str(corner_index + 1),
                        tuple(corner + [12, -8]),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.55,
                        color,
                        1,
                        cv2.LINE_AA,
                    )
        label = (
            f"{self.surface.name}  feather={self.surface.feather:.3f}  "
            "TAB surface | N add | X delete | R reset | [ ] feather | G guides | S save"
        )
        cv2.rectangle(output, (0, 0), (width, 42), (0, 0, 0), -1)
        cv2.putText(output, label, (14, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.56, (235, 245, 255), 1, cv2.LINE_AA)
        return output


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Interactive multi-surface projection mapper")
    parser.add_argument("--profile", default="calibration_data/surface_map.json")
    parser.add_argument("--source", default="builtin:calibration")
    parser.add_argument("--display", type=int, default=1)
    parser.add_argument("--content-width", type=int, default=960)
    parser.add_argument("--content-height", type=int, default=540)
    parser.add_argument("--render-width", type=int, default=960)
    parser.add_argument("--render-height", type=int, default=540)
    parser.add_argument("--projector-width", type=int, default=1920)
    parser.add_argument("--projector-height", type=int, default=1080)
    parser.add_argument("--clean-output", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    profile_path = Path(args.profile)
    profile = SurfaceMapProfile.load_or_default(
        profile_path,
        projector_width=args.projector_width,
        projector_height=args.projector_height,
    )
    editor = SurfaceEditor(profile, profile_path, guides=not args.clean_output)
    source = ContentSource(args.source, args.content_width, args.content_height)
    renderer = SurfaceMapRenderer(profile, width=args.render_width, height=args.render_height)
    sink = FullscreenSink(window="ProjectionMapping-SurfaceMapper", display=args.display, fullscreen=True)
    cv2.setMouseCallback(sink.window, editor.mouse)
    print(
        f"[surface-map] profile={profile_path} surfaces={len(profile.surfaces)} "
        f"output={profile.projector_width}x{profile.projector_height}",
        flush=True,
    )
    started = time.perf_counter()
    try:
        while True:
            content = source.frame(time.perf_counter() - started)
            mapped = renderer.render(content)
            if mapped.shape[:2] != (profile.projector_height, profile.projector_width):
                mapped = cv2.resize(
                    mapped,
                    (profile.projector_width, profile.projector_height),
                    interpolation=cv2.INTER_LINEAR,
                )
            if sink(editor.overlay(mapped)) is False:
                break
            if sink.last_key >= 0:
                editor.key(sink.last_key)
    finally:
        if editor.dirty:
            editor._save()
        source.close()
        sink.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
