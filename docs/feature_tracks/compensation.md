# Track — Radiometry / Closed-loop Compensation

## North star
Make the physically observed projection match the intended appearance despite wall color, projector gamma, ambient light, blur, occlusion and surface albedo.

## Current state
- Per-channel monotonic inverse LUT baseline.
- Radiometry dataset capture tooling.
- Learned appearance-compensation MLP scaffold.
- Closed-loop optimization scaffold.

## Quality ladder
- **Prototype:** inverse gamma/LUT.
- **Usable:** measured wall/projector dataset and LUT improvement.
- **Polished:** spatially varying correction, ambient adaptation, defocus/occlusion masks.
- **Advanced:** learned forward/inverse display model with online camera refinement.
- **Ridiculous:** perceptual/semantic closed-loop optimization jointly aware of room geometry, projector limits and generative target.

## Next queue
1. Capture real grayscale/RGB/random-patch dataset.
2. Compare direct projection vs LUT vs learned inverse on held-out colors/patches.
3. Add spatially varying response map and camera exposure lock.
4. Add saturation/gamut constraints and shadow/occlusion masks.
5. Add defocus compensation baseline.
6. Train forward surrogate `C(P, surface, illumination)` and validate predictions.
7. Add online refinement and perceptual objectives (LPIPS/DINO/segmentation) only after RGB baseline.

## Metrics
Observed RGB/Lab error, perceptual error, spatial error maps, saturation rate, convergence time, temporal stability, latency overhead.
