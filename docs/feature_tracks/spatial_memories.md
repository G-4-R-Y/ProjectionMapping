# Track — Spatial Memories / Reconstructed Worlds / Human Point Clouds

## Visual north star
Make a physical wall feel like a passage through a remembered place: recognizable
geometry from scans, dark negative space, extremely fine white luminous points,
intentional forward camera motion, per-point spatial deformation, and music-led
transitions. Reference: ethereal point-cloud walk through trees; avoid broad
low-threshold bloom and a washed-out grey overlay.

## 2026-11-05 vertical slice: implemented on feature branch
- Self-contained WebGL2 stage: procedurally generated forest corridor, camera
  travel illusion, configurable vortex/dissolve geometry, optional palette variants.
- Browser-only file/clipboard import: ASCII/binary-LE PLY, XYZ/PTS, PNG/JPEG/WebP.
  Raster images become 2.5D reliefs, **not real point-cloud reconstruction**.
- Spectral Reactor: rolling FFT-height memory grid; synthetic demo until user
  consents to local WebAudio microphone capture.
- Human Cloud: camera-local edge/motion point experiment. **No semantic tracking,
  stable person IDs, skeletal joints, 3D depth or body point cloud yet.**
- Local static read-only server, explicit size/point caps, WebGL2 shader, no
  outbound APIs, manual Windows onedir packaging script, local tests.
- Native attractor: black-floor parameter now defaults to 0.10, suppressing weak
  additive haze before tone mapping. Plausible fix, not proof of screenshot cause.

## Quality status
PROTOTYPE. Python/Node smoke checks pass locally; automated Chromium visual
capture was blocked by environment policy. GPU shaders, browser camera/FFT, full
native suite, projector and Windows executable remain unvalidated.

## Next: measurable improvements in priority order
1. 60-second captured projection A/B (dark floor, color, seam, frame time) across
   Linux RTX 4050 and Windows RTX 4080. Iterate forest silhouettes and camera
   movement before marking a default.
2. RTMPose/whole-body plus persistent IDs and semantic particle anchors from the
   existing tracker, sent over an authenticated localhost-only state bridge;
   optional depth or segmentation. No invented 3D geometry from a single photo.
3. Import real scans with transforms, streamable chunk/LOD formats, normal/color
   metadata and provenance. Evaluate PLY-to-octree and LAS/LAZ via a license review.
4. Synchronize Spatial Memories to shared MusicalSignals phrase/drop state,
   rather than simple raw FFT deformation. Build authorable camera spline and transitions.
5. Move from CPU GL readback to native GPU display/projector compositor, with
   calibrated surface warp/mask as the final pass and explicit monitor geometry.
6. Evaluate Rust/wgpu decoder/core vs Python/OpenGL **only** after profiling
   p50/p95 frame time, parse cost, GPU upload, VRAM and transport copies.
7. Public static gallery over HTTPS with safe example datasets and no uploaded
   private scans; separately authenticate any local operator/control endpoints.

## Metrics
Scene startup, p50/p95/p99 FPS, VRAM, point count, upload time, black pixel fraction,
saturation, calibrated projector latency, track jitter, resource cleanup and provenance.

## Constraints
No GitHub Actions; no third-party media without a clear license; assets reproducible;
browser demo cannot silently gain remote execution; WebGL2 preview is not projector-tested.
