from __future__ import annotations

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import torch


def build_appearance_mlp(hidden: int = 128):
    """Small inverse-display model.

    Input features per sample are [target_rgb, surface_rgb, x, y] -> projector_rgb.
    Coordinates should be normalized to [-1, 1].
    """
    import torch.nn as nn
    return nn.Sequential(
        nn.Linear(8, hidden), nn.SiLU(),
        nn.Linear(hidden, hidden), nn.SiLU(),
        nn.Linear(hidden, hidden), nn.SiLU(),
        nn.Linear(hidden, 3), nn.Sigmoid(),
    )


def perceptual_closed_loop_loss(observed, target, feature_fn=None, pixel_weight: float = 1.0, feature_weight: float = 0.2):
    import torch.nn.functional as F
    loss = pixel_weight * F.l1_loss(observed, target)
    if feature_fn is not None and feature_weight:
        loss = loss + feature_weight * F.l1_loss(feature_fn(observed), feature_fn(target))
    return loss
