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
- GPU-native profile compositor and **GPU-Mapped Shader Scene** vertical slice: promoted shader scene -> GPU texture -> multi-surface homography/mask/feather shader -> native window framebuffer, with zero frame-loop readbacks.

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
The reference editor compositor maps at a configurable CPU working resolution (960x540 by default) and scales the finished result to the projector framebuffer. That keeps editing responsive. Clean playback of promoted Shader Scene Lab content can use the GPU-native mapped-scene path, which keeps source rendering, homography, masking, feathering and presentation in one OpenGL context.

Software-only benchmark in the current Linux container: one full-frame surface with the animated calibration plate, 960x540 mapping workspace, and final 1920x1080 scale measured about **17.9 ms / 55.7 FPS** over 60 frames. This is an implementation benchmark, not projector/hardware validation; display presentation and real machine results remain to be measured.

The synchronized zero-readback GPU probe at 960x540 measured **12.81 ms / 78.1 FPS** for one surface and **16.02 ms / 62.4 FPS** for four surfaces over 60 frames. The reported renderer was Mesa llvmpipe, so these numbers prove the shader/compositor path is bounded and readback-free but are not representative RTX or projector results.

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
2. Hardware/projector-validate the zero-readback GPU mapped-scene path and record frame-time percentiles.
3. Generalize the GPU compositor input contract beyond Shader Scene Lab to particles/math/video textures.
4. Real structured-light capture on fixed projector/camera pair.
5. Dense map confidence + hole filling + visual QA.
6. Lens calibration/undistortion and exposure/gain/WB locks.
7. Projector capability/display enumeration and latency-flash test.
8. Persist calibration metadata with every capture/run.
9. Measure end-to-end motion-to-photon latency.
10. Add planar moving-target tracker + predictive homography.
11. Add pose/body target registration for Cyber Mage projection-on-body experiments.
12. Multi-projector alignment/edge-blend after single-projector metrics are solid.

## Metrics
Reprojection error, dense-map confidence/coverage, moving-target registration error vs speed, motion-to-photon latency p50/p95, calibration time and repeatability.
