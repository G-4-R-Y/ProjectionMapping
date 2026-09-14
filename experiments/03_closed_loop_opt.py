"""Toy differentiable closed-loop optimizer.

The real system replaces `surrogate(projector_rgb)` with a learned model of the
camera-observed physical projector/surface response.
"""
from __future__ import annotations
import torch
from projection_mapping.compensation import perceptual_closed_loop_loss


def optimize_emission(target: torch.Tensor, surrogate, steps=100, lr=0.05):
    logits = torch.zeros_like(target, requires_grad=True)
    opt = torch.optim.Adam([logits], lr=lr)
    for _ in range(steps):
        emitted = logits.sigmoid()
        observed = surrogate(emitted)
        loss = perceptual_closed_loop_loss(observed, target)
        opt.zero_grad(); loss.backward(); opt.step()
    return logits.sigmoid().detach()


if __name__ == '__main__':
    target = torch.rand(1, 3, 64, 64)
    # Example colored-wall transfer function.
    wall = torch.tensor([0.75, 0.9, 0.65]).view(1, 3, 1, 1)
    result = optimize_emission(target, lambda x: torch.clamp(x * wall, 0, 1))
    print('mean target error:', (result * wall - target).abs().mean().item())
