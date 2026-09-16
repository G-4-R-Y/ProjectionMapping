# Track — Performer FX / Open Realtime VFX Engine

## North star / finished state

Build a fully-open, TouchDesigner-grade performer and mixed-reality VFX engine: real whole-body/hand anchors, generic motion points, persistent IDs, semantic spell grammar, tens of thousands of GPU particles, fluid trails/ribbons, SDF glyphs/portals, generated 2D/3D asset ingestion, room-aware collisions, music choreography, and optional neural skinning. The deterministic renderer owns motion continuity and exact placement; neural models add slower semantic/material transformations only when they improve the result.

TouchDesigner is an aesthetic/performance reference and an optional external consumer, **not a required runtime dependency**.

## Milestone ladder

### PF0 — shared semantic bus — implemented, validation ongoing
- `TrackingState`: normalized anchors, motion points, gestures, room events, performer confidence and source.
- `MusicalSignals`: common music state from Song Studio.
- `PerformanceState`: immutable tracking + music + operator controls snapshot.
- Renderer-agnostic OSC schema/publisher is optional interoperability, not core architecture.

### PF1 — real hand / pose tracking — first implementation
- Preferred fully-open path: RTMLib `Wholebody` / RTMW-style COCO-WholeBody landmarks.
- Body anchors, wrists/ankles, palm centres, selected fingertips, chest and pelvis.
- Confidence-aware temporal smoothing and normalized velocity.
- Optional MediaPipe Tasks backend kept behind the same `TrackingState` contract.
- Never synthesize semantic hands from silhouette extrema again.

Still required: hardware latency/FPS/occlusion testing; GPU inference backend tuning; multi-person identity; robust handedness through crossing/occlusion; prediction over measured capture-to-display latency.

### PF2 — GPU particle engine — first implementation
- OpenGL 3.3 / ModernGL standalone pipeline.
- Particle state stored in ping-pong float textures; fragment simulation updates the whole field on GPU.
- Instanced point-sprite style rendering through `gl_VertexID` + `gl_PointCoord`.
- Additive luminous particle cores/halos.
- Procedural vector field, drag, emitter velocity inheritance and lifetime respawn.
- GPU feedback textures with coherent advection, bloom taps, filmic compression and vignette.
- 8/16/32/65k operating points exposed; 32k is the initial default.

Transitional debt: final image is still read back for the common OpenCV fullscreen sink. Replace with a GL-native display/shared-texture path before calling this production-grade.

### PF3 — spell grammar — first implementation
- `charge_orb`: palms near each other and relatively calm.
- `charge_release`: charged palms separate.
- `slash_trail`: high palm velocity with refractory spacing.
- `shield_dome`: hands spread and stable.
- `portal_open`: approximately circular palm trajectory with radius-stability evidence.
- `ascension_aura`: both wrists above the head.
- Missing/low-confidence semantic anchors disable the associated spell instead of guessing.

Next: palm-facing-camera shield confidence, thrust/beam detection from palm normal + forward velocity, two-hand portal plane, spin/jump/crouch events, learned sequence classifier only if it beats transparent rules on recorded sessions.

### PF4 — generated asset ingestion — first implementation
- Versioned/licensed TOML VFX pack manifest.
- Asset kinds: sprite, atlas, GLTF/GLB, material, shader, audio, metadata.
- Semantic bindings: palms/chest/head/pelvis/feet/room hit/world/screen.
- Generation metadata is preserved instead of discarded; prompts/seeds/provenance can travel with assets.
- Path traversal is rejected and licenses are mandatory.
- Optional `trimesh` loader normalizes GLB/glTF meshes to NumPy primitives for future GPU upload.
- Example `assets/packs/neon_core/manifest.toml` defines procedural spell slots plus a generated summon slot.

Next: sprite/atlas GPU texture loader, PBR glTF material ingestion, animation clips/skins, asset-cache hashes, Genforge export adapter, validation thumbnails, hot reload.

### PF5 — interoperability bridge — implemented as optional generic OSC
- `/pm/tracking/<anchor>` sends position/velocity/confidence.
- `/pm/event/<event>` sends spell state.
- `/pm/music/<signal>` sends Song Studio controls.
- `/pm/room/<event>` and `/pm/control/<name>` are reserved for spatial/operator state.
- Any OSC-capable tool can consume it; TouchDesigner is only one option.

Future Windows transport may expose GPU textures through Spout, but the open renderer remains first-class.

### PF6 — mixed-reality performance — scene-graph foundation implemented
- Deterministic MR entity IDs, transforms, attachment, lifetime and generated asset references.
- Event-to-entity routing exists for portals and spell-impact slots.
- Entity attachment can follow semantic performer anchors.

Next: GPU sprite/mesh renderer, skeletal animation, world/camera projection matrices, calibrated room planes, depth occlusion, wall/floor collision, hit volumes, creature/gameplay state and camera recording/export. This is the path toward generated-character arena / Smash-like mixed-reality experiments.

### PF7 — neural skin layer — control-map foundation implemented
- `performer_control_map` encodes semantic anchors, motion vectors, gesture energy and room events into an interpretable RGB control image.
- Intended use: sparse StreamDiffusion/video-model semantic material updates while deterministic particles/glyphs remain exact and high-rate.

Next: mask-aware neural compositing, asset/reference conditioning, stable style/seed banks, prior-frame flow warp as conditioning, low-denoise performer material skin, evaluate TemporalNet/StreamV2V/causal models against deterministic temporal baseline.

## Current runnable artifacts

- `Performer FX / Whole-Body GPU`: RTMPose semantic anchors -> spell grammar -> 32k-particle GPU renderer.
- `Song Studio / GPU Particle Stage`: music phase/events -> GPU particle choreography.
- Existing `Cyber Mage SFX / Point Tracker`: generic LK point field remains useful for clothing, props and non-semantic motion.
- `Audio Visual Instrument / GPU`: continuous shader-world branch remains complementary to particle choreography.

## Art direction rules

1. No debug circles/lines as promoted final visuals.
2. Motion must have persistence, hierarchy and material response: core particles, secondary trails/fields, sparse macro events, post stack.
3. High-frequency detail cannot drive global jitter.
4. Semantic events are sparse; continuous position/velocity own most motion.
5. Use restrained palettes with white-hot energy cores and dark negative space.
6. Generated assets are content; tracking/physics/rendering own continuity.
7. AI cannot decide where a hand, room surface or portal physically is.
8. Every visual should be judged from projector footage, not a development monitor screenshot.

## Open problems

- GPU particle shaders are code-complete but not hardware-validated on the RTX 4050/4080 yet.
- RTMPose whole-body mapping and operating point need validation against the installed RTMLib revision.
- Particle emitter uniforms and standalone GL context path need real NVIDIA Linux testing.
- No direct GL fullscreen swapchain/shared texture yet; readback remains a latency/copy tax.
- No proper multi-scale bloom pyramid, motion-vector buffer, depth buffer, mesh renderer or ribbon geometry yet.
- No calibrated camera/world/room coordinate transform for entities.
- No generated-asset hot reload or Genforge adapter yet.
- No multi-performer IDs.

## Next implementation queue

1. Hardware bring-up: GL context probe, 8k -> 16k -> 32k -> 65k particle benchmark, p50/p95 render/readback time.
2. Validate RTMPose whole-body landmark ordering/confidence and measure CPU ONNX FPS; try CUDA/TensorRT/OpenVINO backends where appropriate.
3. Add GPU ribbon/trail geometry and velocity-oriented stretched sprites.
4. Add SDF glyph/sigil/portal renderer with derivative antialiasing and distortion/refraction buffer.
5. Add true bloom pyramid + HDR intermediate textures + ACES-like projector-safe tone map.
6. Add sprite atlas / animated VFX-card renderer driven by VFX packs.
7. Add GLB/glTF mesh upload, basic PBR/emissive materials and skeletal animation path.
8. Calibrated camera/projector/world transforms + room-plane hit tests and occlusion.
9. Fuse `MusicalSignals` directly into performer particle/spell material state and choreography.
10. Add neural skin composition only after deterministic VFX is visually strong in recorded footage.

## Metrics

Motion-to-effect latency; tracker FPS/latency/confidence; anchor jitter in pixels and normalized units; hand reacquisition time; gesture precision/false triggers; active particle count; particle simulation/render/readback milliseconds p50/p95/p99; dropped frames; CPU/GPU utilization; entity/asset load latency; projector visual contrast; subjective footage quality; temporal continuity during occlusion and fast dance motion.

## Preset / operating-point vault

- **Cyber Core:** 32k particles, cyber palette, feedback ~0.94, bloom ~1.2, moderate turbulence, palms/chest/feet emitters.
- **Solar Combat:** solar palette, shorter feedback, stronger slash/release bursts.
- **Bio Summoner:** bio palette, longer trails, slower field, portal emphasis.
- **Prismatic Arena:** prismatic palette, mixed generated assets, stronger macro events but restrained idle state.

## Promotion rule

A PF feature enters the default performance path only after it works on real camera/projector footage, has latency/frame-time telemetry, survives several minutes without resource leaks, and is visibly better than the simpler baseline it replaces.
