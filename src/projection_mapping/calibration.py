from __future__ import annotations

from dataclasses import dataclass
import numpy as np


def _cv2():
    import cv2
    return cv2


@dataclass
class HomographyCalibration:
    matrix: np.ndarray
    reprojection_error: float

    @classmethod
    def fit(cls, src_xy: np.ndarray, dst_xy: np.ndarray, ransac_threshold: float = 3.0) -> "HomographyCalibration":
        cv2 = _cv2()
        src = np.asarray(src_xy, np.float32)
        dst = np.asarray(dst_xy, np.float32)
        H, mask = cv2.findHomography(src, dst, cv2.RANSAC, ransac_threshold)
        if H is None:
            raise ValueError("homography estimation failed")
        pred = cv2.perspectiveTransform(src[None, ...], H)[0]
        err = np.linalg.norm(pred - dst, axis=1)
        if mask is not None:
            err = err[mask.ravel().astype(bool)]
        return cls(H, float(err.mean()) if len(err) else float("nan"))

    def warp(self, image: np.ndarray, width: int, height: int) -> np.ndarray:
        return _cv2().warpPerspective(image, self.matrix, (width, height))


def gray_to_binary(gray: np.ndarray) -> np.ndarray:
    gray = np.asarray(gray, dtype=np.uint32)
    out = gray.copy()
    shift = 1
    while shift < 32:
        out ^= out >> shift
        shift <<= 1
    return out


def decode_gray_pairs(normal: list[np.ndarray], inverse: list[np.ndarray], threshold: float = 12.0) -> tuple[np.ndarray, np.ndarray]:
    """Decode captured normal/inverse Gray-code frames.

    Inputs are ordered MSB->LSB grayscale images. Returns integer coordinate image and confidence mask.
    """
    if len(normal) != len(inverse) or not normal:
        raise ValueError("normal and inverse sequences must be non-empty and equal length")
    shape = normal[0].shape
    gray = np.zeros(shape, dtype=np.uint32)
    valid = np.ones(shape, dtype=bool)
    for a, b in zip(normal, inverse):
        a = np.asarray(a, dtype=np.float32)
        b = np.asarray(b, dtype=np.float32)
        valid &= np.abs(a - b) >= threshold
        gray = (gray << 1) | (a > b).astype(np.uint32)
    return gray_to_binary(gray), valid


def decode_projector_coordinates(
    x_normal: list[np.ndarray], x_inverse: list[np.ndarray],
    y_normal: list[np.ndarray], y_inverse: list[np.ndarray],
    projector_width: int, projector_height: int, threshold: float = 12.0,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    x, vx = decode_gray_pairs(x_normal, x_inverse, threshold)
    y, vy = decode_gray_pairs(y_normal, y_inverse, threshold)
    valid = vx & vy & (x < projector_width) & (y < projector_height)
    return x, y, valid
