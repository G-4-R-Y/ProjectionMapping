# Track — Performer FX / Open Realtime VFX Engine

## North star / finished state

Build a fully-open, TouchDesigner-grade performer and mixed-reality VFX engine: real whole-body/hand anchors, generic motion points, persistent IDs, semantic spell grammar, tens of thousands of GPU particles, fluid trails/ribbons, SDF glyphs/portals, generated 2D/3D asset ingestion, room-aware collisions, music choreography, and optional neural skinning. The deterministic renderer owns motion continuity and exact placement; neural models add slower semantic/material transformations only when they improve the result.

TouchDesigner is an aesthetic/performance reference and an optional external consumer, **not a required runtime dependency**.

Read `MEMORY.md` and `docs/ART_DIRECTION.md` before changing the visual stack.

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

### PF2 — GPU particle engine — first implementation + visual-material rewrite
- OpenGL 3.3 / ModernGL standalone pipeline.
- Particle state stored in ping-pong float textures; fragment simulation updates the whole field on GPU.
- GPU point-sprite rendering through `gl_VertexID` + `gl_PointCoord`.
- Procedural vector field, drag, emitter velocity inheritance and lifetime respawn.
- GPU feedback textures with coherent advection.
- 8/16/32/65k operating points exposed; 32k desktop target and 16k conservative RTX-4050 bring-up point.
- After projector feedback that the first version looked covered by a grey shade, the material was rewritten to use compact white-hot cores, saturated colored shells, same-hue halos, velocity sparkle, chromatic feedback decay, thresholded bloom and a clean black floor.
- Display mapping now uses a hue-preserving exponential transform rather than the old wash-prone per-channel Reinhard pass.

Transitional debt: final image is still read back for the common OpenCV fullscreen sink. Replace with a GL-native display/shared-texture path before calling this production-grade.

### PF3 — spell grammar — first implementation
- `charge_orb`: palms near each other and relatively calm.
- `charge_release`: charged palms separate.
- `slash_trail`: high palm velocity with refractory spacing.
- `shield_dome`: hands spread and stable.
- `portal_open`: approximately circular palm trajectory with radius-stability evidence.
- `ascension_aura`: both wrists above the head.
- Missing/low-confidence semantic anchors disable the associated spell instead of guessing.
- SDF spell renderer provides analytic GPU charge/portal/shield/ascension/impact geometry rather than promoted OpenCV debug circles.

Next: palm-facing-camera shield confidence, thrust/beam detection from palm normal + forward velocity, two-hand portal plane, spin/jump/crouch events, learned sequence classifier only if it beats transparent rules on recorded sessions.

### PF4 — generated asset ingestion — first implementation
- Versioned/licensed TOML VFX pack manifest.
- Asset kinds: sprite, atlas, GLTF/GLB, material, shader, audio, metadata.
- Semantic bindings: palms/chest/head/pelvis/feet/room hit/world/screen.
- Generation metadata is preserved; prompts/seeds/provenance can travel with assets.
- Path traversal is rejected and licenses are mandatory.
- `trimesh` loader normalizes external GLB/glTF/OBJ/etc meshes to renderer-agnostic NumPy primitives.
- Built-in procedural smoke-test assets now include:
  - `builtin:cyber_orb`
  - `builtin:energy_ring`
  - `builtin:crystal`
  - `builtin:relic`
  - `builtin:drone`
  - `builtin:sigil_totem`
  - `builtin:summon_proxy`
- The TUI defaults to `builtin:cyber_orb` so Mixed Reality cannot launch with an empty mandatory asset argument.
- Example `assets/packs/neon_core/manifest.toml` defines procedural spell slots plus a generated summon slot.

Next: sprite/atlas GPU texture loader, PBR glTF material ingestion, animation clips/skins, asset-cache hashes, Genforge export adapter, validation thumbnails and hot reload.

### PF5 — interoperability bridge — implemented as optional generic OSC
- `/pm/tracking/<anchor>` sends position/velocity/confidence.
- `/pm/event/<event>` sends spell state.
- `/pm/music/<signal>` sends Song Studio controls.
- `/pm/room/<event>` and `/pm/control/<name>` are reserved for spatial/operator state.
- Any OSC-capable tool can consume it; TouchDesigner is only one option.

Future Windows transport may expose GPU textures through Spout, but the open renderer remains first-class.

### PF6 — mixed-reality performance — first mesh-render path implemented
- Deterministic MR entity IDs, transforms, attachment, lifetime and generated asset references.
- Event-to-entity routing exists for portals and spell-impact slots.
- Entity attachment can follow semantic performer anchors.
- `GPUMeshRenderer` uploads mesh primitives to ModernGL with depth testing, normalization, screen/world placement, animated transform, cyber/emissive material and camera compositing.
- `Mixed Reality / Generated 3D Asset` can attach a built-in or external mesh to `world`, `left_palm`, `right_palm`, `chest` or `head` and optionally surround it with the shared GPU particle field.

Next: textured/PBR material path, skeletal animation, calibrated camera/world projection, depth occlusion, room-plane collision, hit volumes, creature/gameplay state and recording/export. This is the path toward generated-character arena / Smash-like mixed-reality experiments.

### PF7 — neural skin layer — control-map foundation implemented
- `performer_control_map` encodes semantic anchors, motion vectors, gesture energy and room events into an interpretable RGB control image.
- Intended use: sparse StreamDiffusion/video-model semantic material updates while deterministic particles/glyphs remain exact and high-rate.

Next: mask-aware neural compositing, asset/reference conditioning, stable style/seed banks, prior-frame flow warp as conditioning, low-denoise performer material skin, evaluate TemporalNet/StreamV2V/causal models against deterministic temporal baseline.

## Current runnable artifacts

- `Performer FX / Whole-Body GPU`: RTMPose semantic anchors -> spell grammar -> vivid GPU particle renderer + SDF spells.
- `Song Studio / GPU Particle Stage`: music phase/events -> shared GPU particle choreography.
- `Mixed Reality / Generated 3D Asset`: built-in or generated mesh -> semantic/world anchor -> GPU mesh material + optional particle aura.
- `Polar Math Lab / Vivid GLSL`: reusable analytic radial visuals that can become performer/room/spell backdrops.
- Existing `Cyber Mage SFX / Point Tracker`: generic LK point field remains useful for clothing, props and non-semantic motion.

## Hardware findings / corrections

### 2026-09-16 — Mixed Reality launch failed before renderer initialization
Observed on Linux / RTX 4050 Laptop GPU: TUI passed no `--asset` when the text field was empty, while the experiment marked `--asset` as required. `argparse` exited with return code 2 before ModernGL, RTMPose, mesh upload or camera rendering executed. This was a product/registry contract bug, **not** a graphics, VRAM or tracker failure.

Correction:
- `--asset` defaults to `builtin:cyber_orb`.
- TUI registry defaults to the same built-in asset.
- built-ins provide no-file smoke tests for mesh rendering and anchor attachment.
- external missing paths produce an actionable error listing built-in alternatives.

### 2026-09-16 — particle art feedback
The particle stage was technically promising but looked muted/"shaded" rather than livid and clear. Treat this as a material/compositing failure. The current renderer has been rewritten accordingly; hardware validation of the new material is pending.

## Art direction rules

1. No debug circles/lines as promoted final visuals.
2. Motion must have persistence, hierarchy and material response.
3. High-frequency detail cannot drive global jitter.
4. Semantic events are sparse; continuous position/velocity own most motion.
5. Use white-hot energy cores, saturated shells and dark negative space.
6. Generated assets are content; tracking/physics/rendering own continuity.
7. AI cannot decide where a hand, room surface or portal physically is.
8. Every visual is judged from projector footage, not only a development monitor.
9. Simple beautiful math beats complicated generic templates.

## Open problems

- GPU particle/SDF/mesh shaders still need full hardware/art validation on RTX 4050 and RTX 4080.
- RTMPose whole-body mapping and operating point need validation against the installed RTMLib revision.
- No direct GL fullscreen swapchain/shared texture yet; readback remains a latency/copy tax.
- Bloom is not yet a true multiscale HDR pyramid; ribbons and motion-vector distortion remain incomplete.
- Mesh renderer uses geometry/normals + procedural emissive material; no glTF PBR textures or skeletal animation yet.
- No calibrated camera/world/room transform for entities.
- No generated-asset hot reload or Genforge adapter yet.
- No multi-performer IDs.

## Next implementation queue

1. Hardware bring-up: graphics probe, all built-in MR fixtures, 8k -> 16k -> 32k -> 65k particle benchmark, p50/p95 render/readback time.
2. Projector-test vivid particle material and tune highlight size, thresholded bloom, feedback floor and saturation.
3. Validate RTMPose whole-body landmark ordering/confidence and measure CPU ONNX FPS; try CUDA/TensorRT/OpenVINO backends where appropriate.
4. Add GPU ribbon/trail geometry and velocity-oriented stretched sprites.
5. Upgrade bloom to a real HDR downsample/upsample pyramid + projector-safe tone mapping.
6. Add sprite atlas / animated VFX-card renderer driven by VFX packs.
7. Extend mesh renderer to glTF textures/PBR/emissive materials and animation/skin path.
8. Add Genforge export adapter: deterministic manifest + mesh/sprite/material metadata + preview + hot reload.
9. Calibrated camera/projector/world transforms + room-plane hit tests and occlusion.
10. Fuse `MusicalSignals` directly into performer particles, spells and generated-asset material/choreography state.
11. Add neural skin composition only after deterministic VFX is visually strong in recorded footage.

## Metrics

Motion-to-effect latency; tracker FPS/latency/confidence; anchor jitter; hand reacquisition time; gesture precision; particle simulation/render/readback p50/p95/p99; black-level/contrast; highlight saturation; mesh upload/render latency; dropped frames; CPU/GPU utilization; entity/asset load latency; subjective footage quality; temporal continuity during occlusion and fast dance motion.

## Preset / operating-point vault

- **Cyber Core:** 32k particles, cyber palette, feedback ~0.94, vivid material, moderate turbulence, palms/chest/feet emitters.
- **4050 Bring-up:** 16k particles, `builtin:cyber_orb`, right-palm anchor, cyber material, modest bloom/feedback.
- **Relic Test:** `builtin:relic` / chest or world anchor / cyber or ultraviolet-adjacent styling.
- **Drone Test:** `builtin:drone` / right palm / particle aura.
- **Summon Test:** `builtin:summon_proxy` / world/chest anchor as a transform/scene-graph placeholder for future generated creatures.
- **Solar Combat:** solar palette, shorter feedback, stronger slash/release bursts.
- **Bio Summoner:** bio palette, longer trails, slower field, portal emphasis.
- **Prismatic Arena:** prismatic palette, mixed generated assets, stronger macro events but restrained idle state.

## Promotion rule

A PF feature enters the default performance path only after it works on real camera/projector footage, has latency/frame-time telemetry, survives several minutes without resource leaks, and is visibly better than the simpler baseline it replaces.
