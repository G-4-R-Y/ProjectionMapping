# Track — Calibration / Projection Mapping

## North star
A projector/camera system that can be set up repeatably, knows where every valid projector pixel lands in camera/room coordinates, supports moving targets later, and can scale to multiple projectors.

## Current state
- Grid/checker/ramp test patterns.
- Gray-code + phase-shift generation/decoding primitives.
- Homography estimation and warping.
- Structured-light capture bundle tooling.
- Camera abstraction and fullscreen projector path.

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

## Next queue
1. Real structured-light capture on fixed projector/camera pair.
2. Dense map confidence + hole filling + visual QA.
3. Lens calibration/undistortion and exposure/gain/WB locks.
4. Projector capability/display enumeration and latency-flash test.
5. Persist calibration metadata with every capture/run.
6. Measure end-to-end motion-to-photon latency.
7. Add planar moving-target tracker + predictive homography.
8. Add pose/body target registration for Cyber Mage projection-on-body experiments.
9. Multi-projector alignment/edge-blend after single-projector metrics are solid.

## Metrics
Reprojection error, dense-map confidence/coverage, moving-target registration error vs speed, motion-to-photon latency p50/p95, calibration time and repeatability.
