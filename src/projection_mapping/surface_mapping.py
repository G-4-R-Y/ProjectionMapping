from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

Point = tuple[float, float]
_UNIT_QUAD: tuple[Point, Point, Point, Point] = (
    (0.0, 0.0),
    (1.0, 0.0),
    (1.0, 1.0),
    (0.0, 1.0),
)


def _cv2():
    import cv2

    return cv2


def _points(value: Any, label: str) -> tuple[Point, Point, Point, Point]:
    array = np.asarray(value, dtype=np.float64)
    if array.shape != (4, 2) or not np.isfinite(array).all():
        raise ValueError(f"{label} must contain four finite x/y points")
    return tuple((float(x), float(y)) for x, y in array)  # type: ignore[return-value]


@dataclass
class MappedSurface:
    """One source-space quadrilateral corner-pinned into projector coordinates.

    Both point sets are normalized, so a profile survives content and projector
    resolution changes. Corner order is top-left, top-right, bottom-right,
    bottom-left.
    """

    name: str = "surface_1"
    projector_corners: tuple[Point, Point, Point, Point] = _UNIT_QUAD
    source_corners: tuple[Point, Point, Point, Point] = _UNIT_QUAD
    opacity: float = 1.0
    feather: float = 0.008
    enabled: bool = True

    def __post_init__(self) -> None:
        self.projector_corners = _points(self.projector_corners, "projector_corners")
        self.source_corners = _points(self.source_corners, "source_corners")
        self.opacity = float(np.clip(self.opacity, 0.0, 1.0))
        self.feather = float(np.clip(self.feather, 0.0, 0.25))
        if not self.name.strip():
            raise ValueError("surface name must not be empty")
        if abs(self.projector_area()) < 1e-6:
            raise ValueError(f"surface {self.name!r} has a degenerate projector quadrilateral")

    def projector_area(self) -> float:
        points = np.asarray(self.projector_corners, dtype=np.float64)
        x, y = points[:, 0], points[:, 1]
        return float(0.5 * (np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1))))

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "MappedSurface":
        return cls(
            name=str(payload.get("name", "surface")),
            projector_corners=_points(payload.get("projector_corners", _UNIT_QUAD), "projector_corners"),
            source_corners=_points(payload.get("source_corners", _UNIT_QUAD), "source_corners"),
            opacity=float(payload.get("opacity", 1.0)),
            feather=float(payload.get("feather", 0.008)),
            enabled=bool(payload.get("enabled", True)),
        )


@dataclass
class SurfaceMapProfile:
    name: str = "room"
    projector_width: int = 1920
    projector_height: int = 1080
    surfaces: list[MappedSurface] = field(default_factory=lambda: [MappedSurface()])
    version: int = 1

    def __post_init__(self) -> None:
        self.projector_width = int(self.projector_width)
        self.projector_height = int(self.projector_height)
        if self.projector_width < 1 or self.projector_height < 1:
            raise ValueError("projector dimensions must be positive")
        if self.version != 1:
            raise ValueError(f"unsupported surface-map version: {self.version}")
        if not self.surfaces:
            raise ValueError("surface-map profile must contain at least one surface")

    def save(self, path: str | Path) -> Path:
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(asdict(self), indent=2) + "\n", encoding="utf-8")
        return destination

    @classmethod
    def load(cls, path: str | Path) -> "SurfaceMapProfile":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("surface-map profile must be a JSON object")
        surfaces = payload.get("surfaces", [])
        if not isinstance(surfaces, list):
            raise ValueError("surface-map surfaces must be a list")
        return cls(
            name=str(payload.get("name", "room")),
            projector_width=int(payload.get("projector_width", 1920)),
            projector_height=int(payload.get("projector_height", 1080)),
            surfaces=[MappedSurface.from_dict(item) for item in surfaces],
            version=int(payload.get("version", 1)),
        )

    @classmethod
    def load_or_default(
        cls,
        path: str | Path,
        projector_width: int,
        projector_height: int,
    ) -> "SurfaceMapProfile":
        profile_path = Path(path)
        if profile_path.exists():
            profile = cls.load(profile_path)
            profile.projector_width = int(projector_width)
            profile.projector_height = int(projector_height)
            return profile
        return cls(projector_width=projector_width, projector_height=projector_height)


def _pixel_points(points: tuple[Point, ...], width: int, height: int) -> np.ndarray:
    scale = np.asarray([max(width - 1, 1), max(height - 1, 1)], dtype=np.float32)
    return np.asarray(points, dtype=np.float32) * scale


def surface_alpha(
    surface: MappedSurface,
    width: int,
    height: int,
) -> np.ndarray:
    """Return the surface's polygon/edge-feather alpha in projector space."""
    cv2 = _cv2()
    mask = np.zeros((height, width), dtype=np.uint8)
    corners = np.rint(_pixel_points(surface.projector_corners, width, height)).astype(np.int32)
    cv2.fillConvexPoly(mask, corners, 255, lineType=cv2.LINE_AA)
    alpha = mask.astype(np.float32) / 255.0
    feather_px = surface.feather * min(width, height)
    if feather_px > 0.5:
        # Padding supplies a known exterior even when a surface reaches every output edge.
        binary = np.pad((mask > 0).astype(np.uint8), 1)
        distance = cv2.distanceTransform(binary, cv2.DIST_L2, 3)[1:-1, 1:-1]
        alpha *= np.clip(distance / feather_px, 0.0, 1.0)
    return alpha * surface.opacity


def render_surface_map(
    content: np.ndarray,
    profile: SurfaceMapProfile,
    *,
    width: int | None = None,
    height: int | None = None,
) -> np.ndarray:
    """One-shot convenience wrapper around :class:`SurfaceMapRenderer`."""
    return SurfaceMapRenderer(profile, width=width, height=height).render(content)


class SurfaceMapRenderer:
    """Cached CPU reference compositor for a mutable surface-map profile.

    Homographies, masks and feather distance fields are rebuilt only when profile
    geometry changes. Each surface is warped into its clipped projector-space
    bounding box instead of allocating a full-frame intermediate.
    """

    def __init__(
        self,
        profile: SurfaceMapProfile,
        *,
        width: int | None = None,
        height: int | None = None,
    ) -> None:
        self.profile = profile
        self.width = int(width or profile.projector_width)
        self.height = int(height or profile.projector_height)
        if self.width < 1 or self.height < 1:
            raise ValueError("output dimensions must be positive")
        self._signature: tuple[Any, ...] | None = None
        self._compiled: list[tuple[MappedSurface, np.ndarray, tuple[int, int, int, int], np.ndarray]] = []

    def _profile_signature(self) -> tuple[Any, ...]:
        return (
            self.width,
            self.height,
            *(
                (
                    surface.name,
                    surface.projector_corners,
                    surface.source_corners,
                    surface.opacity,
                    surface.feather,
                    surface.enabled,
                )
                for surface in self.profile.surfaces
            ),
        )

    def _compile(self, source_width: int, source_height: int) -> None:
        cv2 = _cv2()
        compiled = []
        for surface in self.profile.surfaces:
            if not surface.enabled or surface.opacity <= 0.0:
                continue
            src = _pixel_points(surface.source_corners, source_width, source_height)
            dst = _pixel_points(surface.projector_corners, self.width, self.height)
            left = max(int(np.floor(dst[:, 0].min())), 0)
            top = max(int(np.floor(dst[:, 1].min())), 0)
            right = min(int(np.ceil(dst[:, 0].max())) + 1, self.width)
            bottom = min(int(np.ceil(dst[:, 1].max())) + 1, self.height)
            if right <= left or bottom <= top:
                continue
            local_dst = dst - np.asarray([left, top], dtype=np.float32)
            transform = cv2.getPerspectiveTransform(src, local_dst)
            alpha = surface_alpha(surface, self.width, self.height)[top:bottom, left:right]
            compiled.append((surface, transform, (left, top, right, bottom), alpha[..., None]))
        self._compiled = compiled

    def render(self, content: np.ndarray) -> np.ndarray:
        cv2 = _cv2()
        frame = np.asarray(content)
        if frame.ndim not in (2, 3):
            raise ValueError("content must be a grayscale or color image")
        channels = 1 if frame.ndim == 2 else frame.shape[2]
        source_height, source_width = frame.shape[:2]
        signature = self._profile_signature() + (source_width, source_height)
        if signature != self._signature:
            self._compile(source_width, source_height)
            self._signature = signature

        accumulator = np.zeros((self.height, self.width, channels), dtype=np.float32)
        for _surface, transform, (left, top, right, bottom), alpha in self._compiled:
            warped = cv2.warpPerspective(
                frame,
                transform,
                (right - left, bottom - top),
                flags=cv2.INTER_LINEAR,
                borderMode=cv2.BORDER_CONSTANT,
                borderValue=0,
            )
            if warped.ndim == 2:
                warped = warped[..., None]
            destination = accumulator[top:bottom, left:right]
            destination[:] = warped.astype(np.float32) * alpha + destination * (1.0 - alpha)

        output = np.clip(accumulator, 0, 255).astype(frame.dtype)
        return output[..., 0] if frame.ndim == 2 else output


class SurfaceMapProcessor:
    """Callable mapping processor suitable for the shared runtime pipeline."""

    def __init__(self, profile: SurfaceMapProfile):
        self.profile = profile
        self.renderer = SurfaceMapRenderer(profile)

    def __call__(self, frame: np.ndarray) -> np.ndarray:
        return self.renderer.render(frame)


__all__ = [
    "MappedSurface",
    "SurfaceMapProcessor",
    "SurfaceMapProfile",
    "SurfaceMapRenderer",
    "render_surface_map",
    "surface_alpha",
]
