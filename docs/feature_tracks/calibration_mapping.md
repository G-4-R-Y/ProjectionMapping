# Track — Calibration / Projection Mapping

## North star
A projector/camera system that can be set up repeatably, knows where every valid projector pixel lands in camera/room coordinates, supports moving targets later, and can scale to multiple projectors.

## Current state
- Grid/checker/ramp test patterns.
- Gray-code + phase-shift generation/decoding primitives.
- Homography estimation and warping.
- Structured-light capture bundle tooling.
- Camera abstraction and fullscreen projector path.
- Interactive multi-surface corner-pin mapper with draggable projector-space quads.
- Resolution-independent JSON mapping profiles, per-surface UV crop/opacity, polygon masking and edge feathering.
- Reusable `SurfaceMapProcessor` for inserting saved surface geometry into other frame pipelines.

## Surface Mapper workflow
Launch **Surface Mapper / Corner Pin** from the browser control deck. The default animated calibration plate exposes orientation, stretching and seams clearly; an image or looping video path can be used instead.

- drag numbered handles to the physical surface corners;
- `Tab` selects the next surface;
- `N` adds a surface and `X` removes the selected surface;
- `[` / `]` adjusts edge feathering;
- `G` hides/shows edit guides and `S` saves explicitly;
- geometry edits autosave to the selected JSON profile;
- `F11` toggles fullscreen and `Esc` returns to the same deck configuration.

Profiles store normalized source and projector coordinates, so geometry is not tied to one render resolution. This is a manual planar registration baseline, not a substitute for dense structured-light calibration or lens correction.
The current reference compositor maps at a configurable CPU working resolution (960x540 by default) and scales the finished result to the projector framebuffer. That keeps the editor responsive while the planned GPU-native compositor is still pending; use higher working resolutions only when measured hardware headroom permits.

Software-only benchmark in the current Linux container: one full-frame surface with the animated calibration plate, 960x540 mapping workspace, and final 1920x1080 scale measured about **17.9 ms / 55.7 FPS** over 60 frames. This is an implementation benchmark, not projector/hardware validation; display presentation and real machine results remain to be measured.

## Quality ladder
- **Prototype:** manually placed fullscreen output.
- **Usable:** planar homography + structured-light capture.
- **Polished:** dense correspondences, confidence masks, lens correction, exposure lock, repeatable QA.
- **Advanced:** dynamic target tracking/prediction and automatic projector calibration.
- **Ridiculous:** multi-projector self-calibration, edge blending, occlusion-aware projector assignment and quantified low-latency moving-object registration.

## Open problems
- Real-room dense correspondence still needs validation.
- Display placement still has fixed-layout assumptions in some paths.
- Camera intrinsics/distortion and timing are not yet characterized.
- No dynamic motion-to-photon prediction loop.
- Surface profiles do not yet attach camera-space anchors, dense correspondence maps, or lens models.

## Next queue
1. Validate manual multi-surface profiles on a real fixed projector/room pair.
2. Route one promoted GPU scene through a saved surface profile without CPU readback.
3. Real structured-light capture on fixed projector/camera pair.
4. Dense map confidence + hole filling + visual QA.
5. Lens calibration/undistortion and exposure/gain/WB locks.
6. Projector capability/display enumeration and latency-flash test.
7. Persist calibration metadata with every capture/run.
8. Measure end-to-end motion-to-photon latency.
9. Add planar moving-target tracker + predictive homography.
10. Add pose/body target registration for Cyber Mage projection-on-body experiments.
11. Multi-projector alignment/edge-blend after single-projector metrics are solid.

## Metrics
Reprojection error, dense-map confidence/coverage, moving-target registration error vs speed, motion-to-photon latency p50/p95, calibration time and repeatability.
