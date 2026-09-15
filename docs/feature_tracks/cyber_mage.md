# Track — Cyber Mage / Point SFX

## North star
A high-end performer / camera-motion SFX instrument built on persistent tracked points, velocity, acceleration and eventually real pose/hand landmarks. Effects must look like contemporary VFX rather than debug geometry: fluid luminous trails, plasma meshes, particles, shockwaves, distortion, volumetric-looking atmosphere and high-quality shader composition. Deterministic realtime rendering owns continuity; neural generation remains an optional slower semantic/style layer.

## Design correction — 2026-09-15
The first Cyber Mage performer-rig prototype was rejected after hardware testing. Its supposed hand anchors were derived from the left/right extrema of the upper foreground contour, so `hands_together`, charge/release and similar gestures were not trustworthy and frequently did nothing. The OpenCV circle/line aesthetic was also below the visual-quality target.

This failure is retained deliberately: **never build semantic gesture behavior on guessed silhouette extrema and never promote debug primitives as final art direction.**

## Current state
- Active Cyber Mage path is now persistent Shi-Tomasi corner detection + pyramidal Lucas-Kanade tracking.
- Forward/backward optical-flow validation rejects drifting tracks.
- Tracks have persistent IDs, age, velocity, speed and quality.
- Optional foreground mask scopes feature seeding to the performer; full-frame point tracking is also available.
- Point-driven SFX modes: `plasma_mesh`, `constellation`, `afterburner`, `liquid_wire`.
- Persistent track trails, proximity mesh, velocity sparks, acceleration-triggered shockwaves, silhouette aura and feedback buffer.
- Palettes: `cyber`, `ion`, `acid`, `ember`, `ice`.
- Optional ModernGL post-process path with chromatic separation, multi-tap bloom, lens warp, filmic compression, vignette and procedural atmosphere (`nebula`, `grid`, `liquid`).
- The old mask/gesture rig code remains in the repository as research history/fallback, but it is no longer the active TUI Cyber Mage implementation.

## Quality ladder
- **Prototype:** mask + circles/lines. **Rejected.**
- **Usable:** persistent point tracking with coherent trails/mesh/sparks/shockwaves and graceful track reseeding. **Current implementation; hardware validation pending.**
- **Polished:** GPU-native particle trails, signed-distance-field sprites, motion-vector distortion, velocity-color mapping, curated shot presets, stable foreground segmentation and no CPU readback in graphics path.
- **Advanced:** real pose/hands plus generic point field, depth-aware occlusion, anchor-specific emitters, predictive tracking, room collisions, audio modulation, GPU compute/transform-feedback particles.
- **Ridiculous:** persistent tracked points + true hands/pose + calibrated room anchors + depth/occlusion + GPU particle/fluid/SDF renderer + sparse temporally coherent neural style/material layer, suitable for dance footage and room-scale projection.

## Architecture contract
`camera -> foreground/full-frame feature mask -> persistent point tracker -> motion descriptors -> SFX event field -> GPU shader/particle renderer -> optional neural semantic skin -> projector warp/compensation`

Later pose/hands must **augment** the point field, not replace it. Generic tracked points are useful for fabric, hair, props, environmental features and motion trails even when semantic landmarks are available.

## Tracking strategy
1. Shi-Tomasi detects strong local features.
2. Pyramidal LK propagates positions frame-to-frame.
3. Forward/backward consistency rejects bad tracks.
4. Tracks preserve IDs and history.
5. Lost tracks decay visually rather than popping instantly.
6. Reseeding occurs away from existing tracks.
7. Future: add descriptor/re-identification for longer-term IDs and Kalman prediction over measured display latency.

## SFX strategy
Motion should control effects continuously, not depend on brittle gestures:
- velocity -> trail length/brightness, directional sparks, chromatic energy;
- acceleration -> shockwaves / burst emitters;
- local point density -> plasma mesh / cloth-like field;
- coherent flow clusters -> larger ribbons / vortices;
- proximity graph -> energy connections;
- segmentation edge -> optional aura, never semantic joint inference;
- future real hand/pose landmarks -> specialized emitters/portals layered on top.

## Shader direction
The ModernGL path is the beginning, not the endpoint. Continue toward:
- GPU-native additive particles instead of drawing them with OpenCV;
- SDF circles/sprites/runes with derivative antialiasing;
- ping-pong feedback textures with flow advection;
- velocity/distortion buffers;
- bloom/downsample pyramid rather than single-pass taps;
- signed-distance raymarched / volumetric-looking fields where useful;
- ACES/filmic tonemapping and projector-aware contrast;
- direct GL texture output / Spout on Windows to remove final readback.

## Open problems
- Current point tracker follows texture, not true anatomy; plain clothing can have few trackable features.
- Foreground MOG2 can temporarily absorb slow performers into background.
- ModernGL currently renders offscreen then reads back to CPU because the shared display sink is OpenCV; this is transitional.
- Point SFX renderer still creates base tracks/mesh/sparks on CPU before the shader post pass.
- No long-term track re-identification after occlusion.
- No depth-aware occlusion, collision or room interaction yet.
- No real pose/hand landmarks yet; when added they must be confidence-aware and hardware-tested before gesture triggers are promoted.

## Next queue
1. Hardware-test LK track count, drift and FPS under dance motion; tune max-points / FB threshold / feature reseeding.
2. Move point sprites, trails, proximity links and sparks into ModernGL vertex/fragment pipeline with additive blending.
3. Add GPU ping-pong feedback/advection and a proper multi-scale bloom chain.
4. Add clustered-flow ribbon/vortex emitters so effects follow groups of points rather than independent spark noise.
5. Add optional MediaPipe/other pose + hand landmarks as high-confidence semantic emitters alongside generic tracks.
6. Add track/landmark prediction using measured camera->display latency.
7. Add depth/person segmentation for foreground/background occlusion.
8. Add room-plane collision: tracked motion can hit calibrated wall/floor/door coordinates and spawn effects there.
9. Fuse audio events with SFX intensity/palette/scene state without tying every FFT fluctuation to every point.
10. Neural skin only after deterministic SFX is polished: use point/velocity/pose/depth maps and flow-warped previous style as controls.

## Metrics
Tracked-point lifetime, forward/backward error, retained-track ratio, track count, velocity stability, reseed rate, SFX frame time, shader frame time, readback cost, display FPS/p95 frame time, motion-to-effect latency, visual popping on track loss, foreground-mask stability, GPU/CPU utilization and subjective footage quality.

## Preset vault
- **Plasma Dance:** `plasma_mesh`, cyber, ~96 points, radius 95, feedback 0.91, nebula shader.
- **Sparse Constellation:** `constellation`, ion, ~64 points, radius 130, feedback 0.94, black/nebula shader.
- **Kinetic Afterburner:** `afterburner`, ember/acid, ~110 points, shorter feedback, stronger bloom.
- **Liquid Wire:** `liquid_wire`, ice/cyber, long trails, liquid shader background.
