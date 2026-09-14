# Experiments

## E00 — photons
Project grid/checker/ramp. Verify native resolution, overscan, focus, refresh mode, and display placement.

## E01 — dense correspondence
Project Gray-code normal/inverse pairs, capture every frame, decode camera pixels into projector `(x,y)` coordinates, and save validity/confidence masks.

## E02 — radiometry
Project per-channel intensity sweeps under locked camera exposure. Fit monotonic inverse LUTs. Compare target-vs-camera error before/after compensation.

## E03 — learned inverse display
Dataset: `(target_rgb, surface_rgb, xy) -> projector_rgb`. Train `build_appearance_mlp`. Compare against LUT baseline and measure spatial generalization.

## E04 — neural mirror
Camera -> foreground/semantic mask + optical flow -> StreamDiffusion -> masked composite -> projector. Keep the static background on procedural shaders to save diffusion budget and improve temporal stability.

## E05 — room skin
Capture a clean reference of the room, estimate depth/segmentation, and condition generation so edges remain registered while material semantics change.

## E06 — semantic room
Assign effect graphs per class/instance: wall, furniture, person, plant, ceiling. Treat segmentation as a dynamic scene graph rather than a single mask.

## E07 — closed-loop perceptual control
Train/fit a differentiable surrogate of the physical projector-camera response. Optimize emitted pixels against pixel + feature losses and compare LPIPS/DINO-style features to RGB-only control.

## E08 — audio-latent instrument
Extract beat/onset/chroma/spectral features and map them to style interpolation, prompt embeddings, LoRA weights, seed schedules, shader parameters, and feedback gains.

## E09 — dynamic projection
Track a moving planar target, predict pose forward by measured system latency, warp output to the predicted pose, and measure registration error versus target speed.
