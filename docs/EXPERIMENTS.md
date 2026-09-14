# Experiments

This file is the experiment index. The canonical milestone/progress tracker is [`ROADMAP.md`](../ROADMAP.md). Every experiment should map back to a roadmap milestone so prototype work does not drift away from project goals.

## E00 — photons -> M0
Project grid/checker/ramp. Verify native resolution, overscan, focus, refresh mode, and display placement.

## E01 — dense correspondence -> M1
Project Gray-code normal/inverse pairs, capture every frame, decode camera pixels into projector `(x,y)` coordinates, and save validity/confidence masks. Add phase-shift refinement and reprojection-error visualization.

## E02 — radiometry -> M1 / M5
Project per-channel intensity sweeps under locked camera exposure. Fit monotonic inverse LUTs. Compare target-vs-camera error before/after compensation, then extend to spatially varying response and ambient-light adaptation.

## E03 — learned inverse display -> M5
Dataset: `(target_rgb, surface_rgb, xy) -> projector_rgb`. Train the appearance model, compare against LUT baseline, measure spatial generalization, and later train a differentiable forward surrogate for closed-loop optimization.

## E04 — neural mirror -> M3
Camera -> foreground/semantic mask + depth + optical flow -> StreamDiffusion -> masked composite -> projector. Keep the static background on procedural shaders to save diffusion budget and improve temporal stability. Run inference asynchronously with latest-frame-wins semantics.

## E05 — room skin -> M4
Capture a clean reference of the room, estimate depth/segmentation, and condition generation so edges remain registered while material semantics change. Explore object/UV-like canonicalization and hybrid diffusion + shader temporal stabilization.

## E06 — semantic room -> M6
Assign effect graphs per class/instance: wall, furniture, person, plant, ceiling. Treat segmentation as a persistent dynamic scene graph rather than a single mask. Route prompt/LoRA/material controls per object.

## E07 — closed-loop perceptual control -> M5
Train/fit a differentiable surrogate of the physical projector-camera response. Optimize emitted pixels against pixel + feature losses and compare RGB, LPIPS, DINO/self-supervised, segmentation, CLIP, and diffusion-feature objectives.

## E08 — audio-latent instrument -> M7
Extract beat/onset/chroma/spectral features and map them to style interpolation, prompt embeddings, LoRA weights, seed schedules, shader parameters, and feedback gains. Add MIDI/OSC and Ableton experiments.

## E09 — dynamic projection -> M8
Track a moving planar target, measure end-to-end system latency, predict pose forward by that latency, warp output to the predicted pose, and measure registration error versus target speed.

## E10 — multi-projector canvas -> M9
Calibrate two or more projectors into a common space, solve overlap/edge blending and brightness/color balancing, and test shadow-aware projector selection.

## E11 — advanced neural spatial representations -> M10
Evaluate StreamDiffusionV2 / streaming video diffusion, single-GPU distilled/quantized variants, Gaussian-splat or NeRF-like room representations, and learned calibration/inverse-rendering methods. Promote only approaches that beat simpler baselines or unlock qualitatively new behavior.
