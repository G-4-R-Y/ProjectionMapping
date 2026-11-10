# Track — Room Skin / Spatially Locked Generation

## North star
Change the apparent material/semantics of walls, furniture, plants, doors and ceilings while preserving their physical geometry and spatial identity over time.

## Current state
- Optical-flow advection, temporal blending and physical-edge locking primitives.
- Standalone Room Skin experiment with camera path and procedural fallback.
- Structured-light and calibration infrastructure exist separately but are not yet fully fused into Room Skin.

## Quality ladder
- **Prototype:** camera-driven texture feedback.
- **Usable:** stable advection and edge lock on a static scene.
- **Polished:** calibrated projector coordinates, clean masks, surface-specific presets.
- **Advanced:** depth/normal/semantic controls, canonical surface coordinates, neural semantic keyframes.
- **Ridiculous:** persistent room materials, depth-aware occlusion, learned relighting/appearance control, multi-surface effect graph with camera-feedback correction.

## Open problems
- Room Skin still needs real fixed-room calibration data.
- Camera/projector mapping and surface masks are not yet first-class inputs to the runtime.
- No canonical/object-space material coordinate system.
- No direct diffusion keyframe injection yet.

## Next queue
1. Capture and validate real structured-light bundle for the target wall/room.
2. Generate validity masks and camera<->projector dense maps.
3. Lock camera exposure/white balance and save room reference frames.
4. Feed calibration maps into Room Skin so feedback/advection runs in projector coordinates.
5. Add wall/ceiling/furniture semantic masks and independent material presets.
6. Add depth/edge/normal conditioning and neural semantic keyframes.
7. Add room-surface temporal metrics and automatic drift reset.
8. Evaluate geometry-guided relighting/material models only after calibrated baseline.

## Metrics
Registration error, edge drift over time, temporal flicker, reset frequency, surface-mask leakage, display/inference FPS, setup/calibration time.

## 2026-11-10: opt-in manually traced projector-output matte (research branch)

- Added `surface_masks.py`: normalized polygon outlines, even–odd holes, bounded validated JSON, 0–256px **inward** feather; no lighting outside outlines. Independent small implementation inspired by [Projection Mapper's 2026-11-07 traced-zone feature](https://github.com/atul016/projection-mapper/commit/879de56ef840) (MIT).
- `experiments/09_room_skin.py` now accepts `--surface-mask` and `--surface-feather-px`; the operator registry exposes both. Mask is rasterized once, applied **after** projector-size resize, and opt-in; default pixels unchanged. [Demo arched outline](../../configs/surface_shapes/demo_arch.json) and [operator instructions](../SURFACE_MASKS.md).
- **Limited validation:** ten isolated NumPy/OpenCV geometry smoke cases passed in an unpinned test host; no complete repo suite, UI boot, camera/projector, output leakage or frame-time measurements. This is **not** M1 camera-to-projector calibration and does not solve automatic semantic segmentation, stage warp, multi-projector composition or UI tracing.
- **Next gate:** verify pinned dependencies + F11/ESC, then 60-second actual-wall A/B at 1920×1080 with feather 0/4/12. Measure coverage/leakage, look, p50/p95 CPU frame time. Only then evaluate GPU-native clipping and camera-calibrated surfaces.
