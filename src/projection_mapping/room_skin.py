from __future__ import annotations

import numpy as np


def edge_map(image_rgb: np.ndarray, low: int = 80, high: int = 160) -> np.ndarray:
    import cv2
    gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(gray, low, high)
    return edges.astype(np.float32) / 255.0


def edge_lock_mask(reference_rgb: np.ndarray, generated_rgb: np.ndarray, dilate: int = 3) -> np.ndarray:
    """Return a mask indicating where reference geometry should dominate.

    The mask is intentionally simple: union of strong reference/generated edges,
    dilated slightly so high-frequency physical boundaries stay visually anchored.
    """
    import cv2
    ref = edge_map(reference_rgb)
    gen = edge_map(generated_rgb)
    mask = np.maximum(ref, gen)
    if dilate > 0:
        kernel = np.ones((dilate, dilate), np.uint8)
        mask = cv2.dilate((mask * 255).astype(np.uint8), kernel, iterations=1).astype(np.float32) / 255.0
    return mask


def preserve_edges(reference_rgb: np.ndarray, generated_rgb: np.ndarray, strength: float = 0.85) -> np.ndarray:
    import cv2
    if generated_rgb.shape[:2] != reference_rgb.shape[:2]:
        generated_rgb = cv2.resize(generated_rgb, (reference_rgb.shape[1], reference_rgb.shape[0]))
    mask = edge_lock_mask(reference_rgb, generated_rgb)[..., None]
    alpha = np.clip(mask * strength, 0.0, 1.0)
    return np.clip(generated_rgb * (1.0 - alpha) + reference_rgb * alpha, 0, 255).astype(np.uint8)


def advect_with_flow(frame_rgb: np.ndarray, flow: np.ndarray) -> np.ndarray:
    """Warp an RGB frame forward using a dense flow field.

    Useful for shader/diffusion keyframes: generated appearance can be advected at
    camera rate while a slower semantic model produces the next keyframe.
    """
    import cv2
    h, w = frame_rgb.shape[:2]
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    map_x = x - flow[..., 0].astype(np.float32)
    map_y = y - flow[..., 1].astype(np.float32)
    return cv2.remap(frame_rgb, map_x, map_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def temporal_mix(previous_rgb: np.ndarray, current_rgb: np.ndarray, alpha: float = 0.2) -> np.ndarray:
    import cv2
    if current_rgb.shape[:2] != previous_rgb.shape[:2]:
        current_rgb = cv2.resize(current_rgb, (previous_rgb.shape[1], previous_rgb.shape[0]))
    return np.clip(previous_rgb * (1.0 - alpha) + current_rgb * alpha, 0, 255).astype(np.uint8)
