# Track — Cyber Mage / Point + Semantic SFX

## North star
A high-end performer / camera-motion SFX instrument with two complementary measurement fields: generic persistent feature points for arbitrary texture/props/clothing, and real semantic whole-body/hand landmarks for body-owned emitters. Rendering must look like contemporary realtime VFX rather than debug geometry: GPU particles, coherent trails/ribbons, plasma/vector fields, SDF sigils/portals, distortion, bloom, generated assets and room-aware impacts. Deterministic realtime rendering owns continuity; neural generation remains an optional slower semantic/style layer.

## Design correction — 2026-09-15
The first Cyber Mage performer-rig prototype was rejected after hardware testing. Its supposed hand anchors were derived from the left/right extrema of the upper foreground contour, so `hands_together`, charge/release and similar gestures were not trustworthy and frequently did nothing. The OpenCV circle/line aesthetic was also below the visual-quality target.

This failure is retained deliberately: **never build semantic gesture behavior on guessed silhouette extrema and never promote debug primitives as final art direction.**

## Current state
- Generic Cyber Mage path: persistent Shi-Tomasi features + pyramidal Lucas-Kanade flow with forward/backward drift rejection.
- Point tracks keep IDs, age, velocity, speed and quality; foreground-only or full-frame seeding is available.
- CPU point-SFX fallback still provides plasma mesh / constellation / afterburner / liquid-wire experiments.
- New shared `TrackingState` / `PerformanceState` semantic bus is implemented.
- New preferred fully-open semantic path: RTMLib Wholebody/RTMW-style COCO-WholeBody landmarks behind a renderer-independent tracker interface.
- Optional MediaPipe Tasks backend lives behind the same contract.
- Semantic anchors now include body joints, palm centres, fingertips, chest/pelvis and normalized velocity instead of contour guesses.
- `SpellGrammar` implements real-anchor charge/release, slash, shield, circular portal and ascension events; low-confidence/missing anchors disable spells rather than inventing them.
- New `GPUParticleField` keeps particle simulation in ping-pong float textures and renders additive point sprites plus feedback/advection/bloom on GPU.
- `Performer FX / Whole-Body GPU` connects real semantic anchors -> spell grammar -> GPU particles.
- VFX pack / GLB-glTF ingestion and mixed-reality entity foundations now exist for generated content.
- Neural performer-control maps encode anchors/motion/gesture energy for the later style-skin path.

The new umbrella track is [`performer_fx.md`](performer_fx.md); this file remains the Cyber Mage-specific design/history vault.

## Quality ladder
- **Prototype:** mask + circles/lines. **Rejected.**
- **Usable:** persistent generic point tracking with coherent motion SFX. Implemented and previously promoted as Cyber Mage v2.
- **Polished target:** real semantic anchors + 16k–65k GPU particles + GPU ribbons/SDF glyphs + feedback/advection + curated spell/material presets. **First implementation exists; hardware/art validation pending.**
- **Advanced:** pose/hands + generic point field together, depth-aware occlusion, anchor-specific generated assets, predictive tracking, room collisions, audio choreography, HDR multi-pass post.
- **Ridiculous:** persistent points + true hands/pose + calibrated room anchors + depth/occlusion + generated animated 3D entities + GPU particle/fluid/SDF renderer + sparse temporally coherent neural material layer, suitable for dance footage and room-scale mixed reality.

## Architecture contract
`camera -> semantic whole-body landmarks + generic point field -> TrackingState -> SpellGrammar / motion descriptors -> GPU emitters + generated assets -> particles/ribbons/SDF/feedback -> optional neural skin -> projector warp/compensation`

Semantic pose/hands **augment** the generic point field rather than replacing it. Generic tracks remain useful for fabric, hair, props, environmental features and motion trails.

## SFX ownership
- position/orientation -> exact emitter/asset placement;
- velocity -> trail length/brightness/direction and slash energy;
- acceleration -> shockwaves / burst emitters;
- palm proximity -> charge field;
- circular palm trajectory -> portal event;
- stable spread hands -> shield state;
- point density / coherent flow -> non-semantic plasma/ribbon field;
- Song Studio signals -> global material/choreography state, never raw noisy per-pixel twitch;
- room events -> wall/floor/surface impacts once calibration is available.

## Shader / renderer direction
Current GPU particle implementation is the first native renderer branch, not the endpoint. Continue toward:
- velocity-oriented stretched particle sprites;
- proper GPU ribbon/trail geometry;
- SDF runes/HUD/sigils/portals with derivative antialiasing;
- distortion/refraction and motion-vector buffers;
- ping-pong feedback with optical/vector-field advection;
- HDR render targets + multi-scale bloom pyramid;
- depth-aware particle/mesh occlusion;
- PBR/emissive GLB/glTF generated assets;
- projector-aware tone mapping and calibrated surface composition;
- GL-native fullscreen/shared texture so the final frame does not return to CPU.

## Open problems
- New RTMPose semantic path needs hardware validation for landmark ordering, latency, occlusion and hand crossings.
- GPU particle pipeline needs NVIDIA Linux/Windows validation, operating-point benchmarks and shader error hardening.
- Current particle output still performs final GPU -> CPU readback for the shared OpenCV sink.
- No depth-aware occlusion or calibrated room collisions yet.
- No long-term semantic multi-person identity or generic point re-identification after occlusion.
- No GPU sprite-atlas or mesh renderer consuming VFX packs yet.
- Spell thresholds are transparent heuristics and need recorded-session tuning.

## Next queue
1. Validate `Performer FX / Whole-Body GPU` on RTX 4050: anchor count/confidence, semantic FPS and motion-to-effect latency.
2. Benchmark 8k/16k/32k/65k GPU particles and measure simulation/render/readback p50/p95.
3. Fuse RTMPose semantic anchors and LK point tracks into one `TrackingState` update.
4. Add GPU ribbon/trail geometry and velocity-oriented sprites.
5. Add SDF sigil/portal/shield renderer and distortion/refraction layer.
6. Add sprite-atlas loader and generated 2D VFX cards through VFX packs.
7. Add GLB/glTF renderer for generated summon/arena entities.
8. Add track/landmark prediction using measured camera->display latency.
9. Add depth/person segmentation and calibrated room-plane collisions.
10. Share Song Studio `MusicalSignals` with performer material/particle states.
11. Neural skin only after deterministic SFX is worth filming: point/velocity/pose/depth/energy maps + flow-warp previous style + stable low-denoise conditioning.

## Metrics
Semantic tracker latency/FPS/confidence; palm/wrist jitter; reacquisition time; gesture precision and false triggers; generic point lifetime/FB error/reseed rate; active particle count; particle simulation/render/readback frame time; display FPS/p95; motion-to-effect/motion-to-photon latency; visual popping; GPU/CPU utilization; subjective footage quality.

## Preset vault
- **Cyber Core:** semantic palms/chest/feet + ~32k cyber particles, feedback ~0.94, moderate vector field, bloom ~1.2.
- **Solar Combat:** solar particles, shorter persistence, stronger slash/release bursts.
- **Bio Summoner:** bio palette, long trails and portal-weighted events.
- **Prismatic Arena:** generated asset slots + prismatic particle accents, low idle density / high macro-event density.
- Legacy point-only presets remain useful when semantic tracking is unavailable: Plasma Dance, Sparse Constellation, Kinetic Afterburner, Liquid Wire.
