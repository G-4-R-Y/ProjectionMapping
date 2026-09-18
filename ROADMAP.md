# ProjectionMapping Roadmap

This is the canonical milestone roadmap. Milestone numbering **M0–M6 is stable**. Extension milestones preserve performance-art and research directions without displacing the core spatial pipeline.

Legend: **✅ done / implemented** · **🟡 implemented but needs integration or hardware validation** · **⬜ planned** · **🧪 research / stretch**

Before substantial work, read:
- [`MEMORY.md`](MEMORY.md) — durable project/agent handoff memory, hardware findings, rejected approaches, and non-negotiable engineering rules.
- [`docs/ART_DIRECTION.md`](docs/ART_DIRECTION.md) — visual-quality contract and promotion bar.
- [`docs/feature_tracks/`](docs/feature_tracks/README.md) — fine-grained research/progress ledgers.

Every meaningful feature change must update its track so successful presets, failed approaches, measurements, open problems and the path toward the advanced version do not disappear.

## North star

Build a home-scale spatial hallucination / mixed-reality performance instrument where projector, camera, audio, performers, generated 2D/3D assets and realtime graphics form one low-latency system. Deterministic tracking/geometry/particles/shaders own continuity and spatial registration; neural models provide lower-rate semantic/material/style transformations where they actually add value.

Preferred architecture:

`camera / audio / controls -> shared semantic bus -> persistent points + real landmarks -> deterministic GPU particles/shaders/assets -> async neural semantic/style updates -> compensation / warp -> GPU/native transport or fullscreen -> projector -> camera feedback`

Core runtime rules:
- latest-frame-wins for neural inference; never queue stale visual state
- persistent IDs/points/geometry own temporal continuity
- `TrackingState` / `PerformanceState` / `MusicalSignals` are shared contracts rather than feature-specific islands
- generated assets are content; tracking/physics/rendering own motion continuity
- process isolation and clean GPU teardown
- conservative VRAM policy
- F11 fullscreen toggle / ESC returns to control deck
- hardware-measured latency and frame-time telemetry
- visual quality is evaluated on projector/recorded footage, not only in code
- prototype freely; art-pass promising experiments before promotion
- weak promoted visuals are rewritten or retired; technical complexity does not excuse mediocre art direction

A central design rule applies across Performer FX, Human Reactor, Cyber Mage, Neural Mirror and Room Skin: **deterministic spatial ownership first; generative stylization second**.

TouchDesigner is an aesthetic/performance reference and optional interoperability target, **not a required dependency**. The primary runtime should remain fully open-source and extensible.

---

## M0 — photons ✅

**Goal:** deterministic pixels -> intended projector, reliably.

Implemented:
- ✅ fullscreen projector output
- ✅ F11 toggle / ESC visual exit in shared sink
- ✅ grid/checkerboard/color-ramp + Gray-code/phase-shift patterns
- ✅ selectable display
- ✅ basic camera preview
- ✅ Textual control deck / modular feature registry

Next:
- ⬜ real monitor enumeration instead of fixed pixel-offset assumptions
- ⬜ projector capability report: native resolution/refresh/overscan/HDR/color mode
- ⬜ camera/projector timing flash test

Exit: repeatable known framebuffer on known projector/display mode.

---

## M1 — camera/projector calibration 🟡

**Goal:** accurate projector<->camera geometry and photometric characterization.

Geometry:
- ✅ Gray-code generation/decoding primitives
- ✅ homography estimation + warp
- ✅ structured-light capture tooling
- ✅ calibration-bundle serialization + metadata
- 🟡 black/white + Gray-code + phase-shift capture path; real-room validation pending
- ⬜ confidence-aware dense correspondence
- ⬜ inverse camera->projector map with holes/validity masks
- ⬜ phase refinement / reprojection QA

Camera/photometric:
- ✅ cross-platform camera abstraction with Linux V4L2 path
- ⬜ exposure/gain/WB lock
- ⬜ lens distortion calibration
- ⬜ timing characterization

Radiometry attachment:
- ✅ monotonic inverse-LUT baseline
- ✅ grayscale/RGB sweep capture
- ✅ deterministic random-patch dataset capture
- ⬜ real projector/wall dataset
- ⬜ spatially varying model, ambient adaptation, defocus, shadows/occlusion

Track: [`docs/feature_tracks/calibration_mapping.md`](docs/feature_tracks/calibration_mapping.md)

---

## M2 — realtime GPU transport 🟡

**Goal:** GPU output -> compositor/projector without unnecessary encode/decode/readback.

Implemented:
- ✅ Spout abstraction + diagnostics
- ✅ fullscreen fallback
- ✅ modular runtime / one active child process
- ✅ feature dependency detection
- ✅ full run logs, GPU snapshots, process-tree cleanup
- ✅ conservative CUDA VRAM guard
- ✅ explicit ModernGL/glcontext graphics extra and desktop packaging path
- ✅ centralized standalone OpenGL context probe with EGL-first Linux diagnostics

Next:
- ⬜ direct OpenGL swapchain / fullscreen path so particle/shader scenes do not read back to CPU
- ⬜ direct PyTorch/CUDA -> shared texture path
- ⬜ real Spout validation on Windows; TouchDesigner may be used only as one test consumer
- ⬜ MadMapper handoff
- ⬜ Syphon macOS / optional NDI
- ⬜ transport copy-count + latency benchmark
- ⬜ native GPU interop between renderer, neural output and projector compositor

Track: [`docs/feature_tracks/runtime_transport_ui.md`](docs/feature_tracks/runtime_transport_ui.md)

---

## M3 — Neural Mirror / realtime generative video 🟡

**Goal:** live semantic transformation with bounded latency and measurable temporal stability.

Perception/runtime:
- ✅ foreground mask baseline
- ✅ Farneback optical flow baseline
- ✅ async latest-frame-wins worker
- ✅ Daydream StreamDiffusion backend
- ✅ live camera -> StreamDiffusion path
- ✅ benchmark harness
- ✅ native-attention fallback when xFormers is absent/fails
- ✅ 6 GB safe profile
- ✅ startup/load/warmup/run stage telemetry

Temporal consistency ladder:
- ✅ display-side previous-neural-frame optical-flow warp
- ✅ fresh neural keyframe blended against motion-predicted frame
- ✅ warp residual + neural-keyframe residual telemetry
- ✅ performer semantic/motion/gesture control-map primitive available through shared state
- ⬜ stable seed/style bank + gradual prompt interpolation
- ⬜ similarity filtering / adaptive submit rate
- ⬜ mask-aware person/background/energy compositing
- ⬜ feed prior/warped style into neural conditioning where backend permits
- ⬜ persistent latent/state experiments
- ⬜ pose/depth/edge/point-energy controls connected into the live backend
- 🧪 TemporalNet / StreamV2V / causal streaming-edit evaluation
- 🧪 newer video models only when they beat the deterministic flow/state baseline on temporal quality, latency and VRAM

Hardware work:
- ⬜ measure 512x288 safe profile on RTX 4050 Laptop
- ⬜ measure xFormers/TensorRT operating points on RTX 4080

Track: [`docs/feature_tracks/neural_mirror.md`](docs/feature_tracks/neural_mirror.md)

---

## M4 — Room Skin / spatially locked generation 🟡

**Goal:** change perceived room materials/semantics while preserving physical geometry.

Implemented:
- ✅ physical-edge locking primitives
- ✅ optical-flow advection
- ✅ temporal blending
- ✅ standalone Room Skin prototype
- ✅ model-free procedural scene experiments
- ✅ ModernGL Shader Scene Lab baseline
- ✅ **Polar Math Lab** with five vivid analytic radial families: Rose Lattice, Hypotrochoid Engine, Log Spiral Interference, Phyllotaxis Reactor, Bessel Wave Chamber
- ✅ Polar Math structured-chaos control: analytic cross-harmonic/domain deformation while preserving each equation family's identity
- ✅ Neon Cathedral rewritten as a moving radial vault with perspective bands, caustics and breathing/oculus motion after the original static-looking version failed the art bar
- ✅ new structured-chaos shader studies: Wormhole Choir, Plasma Singularity, Vortex Crown, Collapse Flower
- ✅ reusable shader asset manifests: `ritual_geometry`, `singularity_suite`, `holographic_overlays`

Visual/shader direction:
- ✅ legacy CPU portal branch-cut seam fixed
- ✅ Shader Scene Lab scenes: Event Horizon, Aurora Void, Liquid Chrome, Neon Cathedral v2, Wormhole Choir, Plasma Singularity, Vortex Crown, Collapse Flower
- ✅ Event Horizon raw-angle FBM branch cut removed: promoted angular field now uses unit-circle complex harmonics instead of raw `atan()` coordinates
- ✅ `experiments/21_visual_probe.py` includes an Event Horizon seam-regression metric across the previously visible negative-X discontinuity
- ✅ Liquid Chrome is the current user-validated in-repo aesthetic benchmark; use it as a quality floor to beat, not a ceiling
- ✅ saturated emissive / clean-black visual direction documented in `docs/ART_DIRECTION.md`
- ⬜ projector-test the four new chaos studies and all five revised Polar Math modes; keep/incubate/rewrite based on beauty, motion, color and projection readability
- ⬜ per-scene art controls + preset vault
- ⬜ shared GPU particle/feedback engine as a spatial surface layer
- ⬜ multi-pass HDR bloom / reaction diffusion / fluid-like fields
- ⬜ SDF/raymarched architectural primitives
- ⬜ calibrated surface masks and projector-coordinate scene routing

Spatial/neural direction:
- ⬜ clean room reference + calibrated projector coordinates
- ⬜ depth/normal/edge/segmentation priors
- ⬜ object-/surface-space canonicalization
- ⬜ neural semantic keyframes injected into deterministic shader/feedback motion
- ⬜ quantitative edge-registration metric
- ⬜ performer/particle room impacts routed through calibrated surface anchors

Track: [`docs/feature_tracks/room_skin.md`](docs/feature_tracks/room_skin.md) and [`docs/feature_tracks/procedural_scenes.md`](docs/feature_tracks/procedural_scenes.md)

---

## M5 — closed-loop compensation 🟡

**Goal:** camera observes the projected result and learns/optimizes the actual emitted image.

Implemented:
- ✅ inverse radiometric LUT utilities
- ✅ learned appearance-compensation MLP scaffold
- ✅ closed-loop optimization scaffold
- ✅ automated projector/camera radiometry dataset capture

Next:
- ⬜ real dataset + LUT vs learned inverse evaluation
- ⬜ forward model `C(P, surface, illumination)`
- ⬜ spatially varying inverse model
- ⬜ online refinement
- ⬜ LPIPS / DINO / segmentation / semantic objectives
- ⬜ albedo/ambient/gamma/defocus/shadow/gamut handling

Track: [`docs/feature_tracks/compensation.md`](docs/feature_tracks/compensation.md)

---

## M6 — semantic room ⬜

**Goal:** persistent objects/surfaces/people with independently controlled behaviors and interactions.

Scene graph:
- ⬜ wall/ceiling/floor/furniture/plants/doors/windows/people
- ⬜ instance IDs across frames
- ⬜ depth/occlusion relationships
- ⬜ persistent object/effect graph
- ✅ performer-side deterministic MR entity scene-graph primitive exists as a foundation

Effect routing:
- ⬜ independent shader/neural graph per region/object
- ⬜ priorities + occlusion rules + composable masks
- ⬜ per-object material/prompt/style controls
- ⬜ OSC/MIDI/gamepad/phone controls
- ⬜ cross-node interactions: tracked motion -> wall effect; feet -> floor field; audio -> ceiling state
- ⬜ generated GLB/sprite entities attach to calibrated room/world anchors

Track: [`docs/feature_tracks/semantic_room.md`](docs/feature_tracks/semantic_room.md)

---

# Extension milestones

## M7 — audiovisual instrument 🟡

**Goal:** musical structure orchestrates coherent shader worlds, particles, performer effects and room state rather than noisy FFT-to-pixel modulation.

Implemented:
- ✅ reliable Linux system-audio monitor capture
- ✅ low-latency capture independent from rolling 2048-sample spectral analysis
- ✅ RMS/bass/mid/treble/centroid/flux/onset controls
- ✅ adaptive median/MAD event gating + refractory periods + one-trigger-per-audio-block semantics
- ✅ tempo / beat phase / bar phase / confidence estimator
- ✅ macro energy + drop accents
- ✅ smooth/balanced/punchy/chaotic modes + Calm<->Madness
- ✅ GPU shader instrument with seamless Journey transitions
- ✅ curated shader performance banks
- ✅ GPU particle stage with persistent feedback/advection
- ✅ authored GPU vector-field families: flow, nebula advection, binary-star gravity, event-horizon collapse and wandering multi-well cosmic flow
- ✅ cosmic Song Studio banks: Cosmic Roam, Binary Star, Event Horizon Drift, Accretion Storm and Supernova Nebula
- ✅ particle materials overhauled toward white-hot cores, saturated emissive shells, chromatic feedback, thresholded bloom and a clean black floor after hardware feedback identified a muddy/"shaded" look
- ✅ original choreography banks: Orbit Reactor, Dual Comet, Cathedral Rain, Vortex Gate, Constellation Bloom
- ✅ additional choreography banks: Reactor Bloom, Polar Gate, Ritual Rain, Helix Fountain, Nebula Bloom, Techno Lattice
- ✅ heuristic section/phrase state (`breakdown/build/drop/release/steady`) and **Journey** controller can switch choreography without resetting particle state
- ✅ optional Polar Math backdrop driven by the same `MusicalSignals`, with restrained screen-style emissive blending rather than grey haze
- ✅ Song Studio backdrop conductor can also run every structured-chaos Shader Scene Lab scene via `scene:<id>`
- ✅ `backdrop=auto` maps choreography banks to complementary Polar/Shader worlds while keeping particle state continuous
- ✅ backdrop chaos responds to section energy/mids/sparse drops rather than twitching on every FFT bin
- ✅ same `MusicalSignals` schema can be embedded in `PerformanceState`

Next:
- ⬜ hardware/art-tune particle material after the vividness overhaul; compare black floor, bloom and palette response on several tracks/projector footage
- ⬜ projector-test `journey + backdrop=auto` at low mix and curate/remove pairings that become visual soup
- 🟡 crossfade/morph backdrop identity and choreography at accepted Journey phrase/drop boundaries;
  implemented without particle-state reset, projector/art tuning pending
- ⬜ chroma/key/harmonic-change descriptors
- ⬜ improve section classifier from heuristic dynamics into robust phrase/section evidence while preserving transparent baseline
- ⬜ beat/bar-synchronous palette/particle/preset morphing without state reset
- ⬜ live scene controls + user A/B/morph banks
- ⬜ audio-reactive VFX-pack / generated-asset spawning on rare macro events
- ⬜ MIDI/OSC/Ableton Link/clock
- ⬜ route `MusicalSignals` into Performer FX, Human Reactor and Room Skin
- ⬜ audio embeddings -> semantic asset/style/latent/LoRA state, never frame-rate noise

Track: [`docs/feature_tracks/audio_visual.md`](docs/feature_tracks/audio_visual.md)

---

## M8 — dynamic projection mapping ⬜

**Goal:** keep physical projection registered on moving targets.

- ⬜ full motion-to-photon measurement
- ⬜ planar target tracking
- ⬜ predicted target positions over measured latency
- ⬜ realtime homography update
- ⬜ moving body/object tests
- ⬜ registration error vs speed
- ⬜ use persistent point + semantic landmark tracks as dynamic-mapping measurements

---

## M9 — multi-projector / spatial display ⬜

- ⬜ automatic multi-projector calibration
- ⬜ geometric alignment / edge blend
- ⬜ color/brightness balance
- ⬜ shadow-aware projector assignment
- ⬜ distributed rendering where useful

---

## M10 — advanced neural / spatial research 🧪

- 🧪 StreamDiffusionV2 / streaming video diffusion
- 🧪 TemporalNet / StreamV2V / causal streaming edits
- 🧪 distilled/quantized video models for single-4080 operation
- 🧪 previous-latent/state reuse + cross-frame attention
- 🧪 Gaussian splats / NeRF-like room representation
- 🧪 4D moving-scene representations
- 🧪 inverse rendering / neural material models
- 🧪 learned projector-camera calibration
- 🧪 sparse neural keyframes + high-rate deterministic warping/interpolation
- 🧪 asset/reference-conditioned live style skin for generated performers/creatures

Promote only when the research path beats a simpler baseline on our actual hardware or unlocks a qualitatively new effect.

---

## M11 — Performer FX / open mixed-reality VFX engine 🟡

**Goal:** a fully-open TouchDesigner-grade realtime VFX engine for performers, generated assets and room-scale mixed reality. Generic motion points and real semantic landmarks feed persistent GPU particles, spell grammar, shaders and entities. Optional external tools consume the state; they do not define the architecture.

Track: [`docs/feature_tracks/performer_fx.md`](docs/feature_tracks/performer_fx.md), with Cyber Mage history/details in [`docs/feature_tracks/cyber_mage.md`](docs/feature_tracks/cyber_mage.md) and dance-video composition in [`docs/feature_tracks/human_reactor.md`](docs/feature_tracks/human_reactor.md).

### Rejected prototype — retained as a lesson
- ⚠️ first Cyber Mage used upper-silhouette extrema as fake “hands”
- ⚠️ charge/release therefore failed on hardware
- ⚠️ OpenCV circles/lines read as debug graphics rather than finished SFX
- ✅ failure/reason retained permanently in feature tracks

### PF0 — shared semantic bus ✅
- ✅ `TrackingState`: normalized anchors, motion points, gestures, room events, confidence/source
- ✅ `PerformanceState`: tracking + `MusicalSignals` + operator controls
- ✅ optional generic OSC state publisher; TouchDesigner/Max/Unity/etc. may consume the same schema
- ⬜ shared-memory / native local IPC for very high-rate state when OSC becomes insufficient

### PF1 — real hand / pose tracking 🟡
- ✅ preferred open tracker abstraction built around RTMLib Wholebody/RTMW-style whole-body landmarks
- ✅ body joints, palm centres, fingertips, chest/pelvis, normalized velocities
- ✅ confidence-aware temporal smoothing
- ✅ optional MediaPipe Tasks compatibility backend behind the same contract
- ⬜ hardware-validate landmark mapping/FPS/latency on RTX 4050/4080 systems
- ⬜ GPU/TensorRT/OpenVINO operating points
- ⬜ confidence-aware reacquisition / crossing / multi-performer IDs
- ⬜ prediction over measured camera-to-display latency

### PF2 — GPU particle engine 🟡
- ✅ particle state stored in ping-pong float textures
- ✅ GPU fragment simulation with vector field, drag, lifetime and emitter-velocity inheritance
- ✅ additive point-sprite rendering using GPU particle state
- ✅ persistent feedback/advection
- ✅ vivid material pass: white-hot core / saturated shell / colored halo / velocity sparkle
- ✅ thresholded highlight bloom + hue-preserving exponential display transform + low-energy black-floor gate
- ✅ 8k/16k/32k/65k TUI operating points; 32k default
- ⬜ hardware benchmark simulation/render/readback p50/p95/p99
- ⬜ velocity-oriented sprites + true ribbon/trail geometry
- ⬜ HDR intermediate textures + proper multiscale bloom pyramid
- ⬜ distortion/refraction + depth/motion buffers
- ⬜ direct GL fullscreen/shared texture, removing final CPU readback

### PF3 — spell grammar 🟡
- ✅ charge orb / separation release from real palm anchors
- ✅ high-velocity slash events
- ✅ stable spread-hand shield state
- ✅ approximately circular palm path -> portal event
- ✅ wrists-above-head ascension state
- ✅ low-confidence/missing anchors disable spells instead of guessing
- ⬜ palm-normal shield confidence + thrust/beam
- ⬜ two-hand portal plane, spin/jump/crouch and floor-impact grammar
- ⬜ tune on recorded sessions; learned sequence classifier only if it beats transparent rules

### PF4 — generated asset ingestion 🟡
- ✅ versioned/licensed TOML VFX-pack schema
- ✅ sprite / atlas / GLTF / GLB / material / shader / audio / metadata asset types
- ✅ semantic binding slots for performer/world/room anchors
- ✅ generation provenance/custom metadata preserved
- ✅ secure relative-path validation + mandatory declared license
- ✅ optional trimesh GLB/glTF -> NumPy primitive ingestion
- ✅ GPU geometry/normals/emissive mesh renderer exists for generated external meshes
- ✅ built-in smoke-test assets: cyber orb, energy ring, crystal, relic, drone, sigil totem, summon proxy
- ✅ reusable visual packs now include `particle_arsenal`, `ritual_geometry`, `singularity_suite`, `holographic_overlays`, `spell_arsenal`, `mr_summons`, `neon_core`
- ✅ `neon_core` example pack with procedural spell assets + generated summon slot
- ⬜ Genforge export adapter
- ⬜ sprite-atlas GPU loader / animated VFX cards
- ⬜ PBR glTF materials/textures, skins/animations
- ⬜ hot reload + content hashes + validation thumbnails

### PF5 — optional interoperability bridge ✅/⬜
- ✅ renderer-agnostic OSC address schema and publisher
- ✅ tracking/music/event/room/control channels
- ⬜ Windows GPU texture sharing / Spout consumer validation
- ⬜ optional sample TouchDesigner graph only if useful; never make TD required
- ⬜ other consumers: Godot/Unity/Processing/Max/Pure Data as modular adapters

### PF6 — mixed-reality performance 🟡
- ✅ deterministic MR entity IDs/transforms/attachments/lifetimes + asset references
- ✅ gesture-event -> portal/impact entity routing foundation
- ✅ entities can follow semantic performer anchors
- ✅ first mixed-reality mesh stage can attach built-in/external meshes to world/head/chest/palms and optionally add a GPU particle aura
- ⬜ generated character/creature summon system with animation/state
- ⬜ camera/world/projector transform chain
- ⬜ calibrated wall/floor collisions and room-aware spell impacts
- ⬜ depth occlusion, hit volumes, lightweight gameplay state
- ⬜ arena / Smash-like mixed-reality prototype using generated 3D assets
- ⬜ recording/export of camera + mattes + semantic state + rendered result

### PF7 — neural skin layer 🟡
- ✅ deterministic performer control-map primitive for semantic anchors/motion/gesture/room energy
- ✅ existing Neural Mirror optical-flow previous-style baseline
- ⬜ mask-aware performer/material composition preserving exact particle/SDF effects
- ⬜ generated asset/reference conditioning
- ⬜ stable style/seed/prompt bank + low-denoise performer skin
- ⬜ prior-frame/flow-warp control + persistent latent/state experiments
- 🧪 TemporalNet/StreamV2V/causal video models only if they beat deterministic temporal baseline

### Human Reactor convergence
- ✅ dance-video silhouette/echo renderer exists
- ⬜ consume shared `TrackingState` / real semantic anchors
- ⬜ combine silhouette, point field, GPU particles, generated assets and Song Studio state
- ⬜ recording profiles / clean matte / semantic metadata outputs

---

# Cross-cutting engineering goals

Performance/reliability:
- ✅ process isolation
- ✅ latest-frame-wins async inference
- ✅ VRAM guard / cleanup
- ✅ cross-platform CI
- ✅ graphics dependency/context diagnostics improved; desktop graphics extra now packaged
- ✅ Linux Mesa/EGL visual-smoke CI compiles/renders promoted Shader Scene/Polar/particle materials and runs seam regression
- ⬜ p50/p95/p99 capture/perception/particle/render/inference/transport/scanout timings
- ⬜ continuous GPU/CPU memory and frame-time telemetry
- ⬜ live parameter hot-reload
- ⬜ named preset/performance-state snapshots

Evaluation:
- ⬜ geometric registration error
- ⬜ radiometric error
- ⬜ temporal flicker/flow-warp residual
- ⬜ tracked-point lifetime/FB error/reseed rate
- ⬜ semantic anchor jitter/reacquisition/gesture precision
- ⬜ active particle count + simulation/render/readback timings
- ⬜ motion-to-effect and motion-to-photon latency
- ✅ Event Horizon branch-cut regression metric in visual probe
- ⬜ visual promotion scorecard from `docs/ART_DIRECTION.md` using projector/recorded footage

Product/UX:
- ✅ Textual control deck + modular feature fragments
- ✅ launching/ESC preserves the active feature configuration screen and session values instead of dumping the operator back to defaults
- ✅ persistent logs / copy/open / stage status
- ✅ Song Studio GPU particle stage entry
- ✅ Performer FX whole-body GPU entry
- ✅ Polar Math Lab entry with structured-chaos control
- ✅ Mixed Reality generated-asset stage entry with built-in fallback assets
- ⬜ robust monitor enumeration
- ⬜ live parameter IPC + preset/asset browser
- ⬜ VFX-pack browser + generated asset hot reload
- ⬜ Linux AppImage/DEB, Windows Setup.exe, polished macOS app

Research discipline:
- ✅ per-category feature tracks
- ✅ failed visual/technical directions are recorded rather than silently erased
- ✅ implemented vs hardware-validated claims separated
- ✅ Performer FX PF0–PF7 umbrella has its own permanent track
- ✅ root `MEMORY.md` exists as durable handoff context for future agents/models
- ✅ `docs/ART_DIRECTION.md` preserves the artistic bar and lessons from successful/failed visuals
- ⬜ pin promoted model/repository revisions
- ⬜ save runtime/calibration/benchmark/asset-generation metadata with captures
- ⬜ keep classical baselines beside learned paths

---

# No-forgetting ledger

### Song Studio / audio performance
- rolling spectral analysis independent from capture latency
- adaptive event gating / beat phase / bar phase / drop state
- shader-world banks + persistent GPU particle choreography banks
- cosmic vector-field families and gravity-well choreography; bass/mids/highs/drop modulate physical-looking field behavior rather than only emission rate
- vivid particle materials: white-hot core, saturated shell, clean black floor, thresholded bloom
- section-aware Journey without particle-state resets
- optional Polar Math and structured-chaos Shader Scene emissive backgrounds driven by the same music state
- `backdrop=auto` is an experiment layer; preserve `backdrop=none` as a clean A/B baseline
- backdrop chaos should respond to macro musical state, not jitter every pixel every beat
- smooth/balanced/punchy/chaotic + Calm<->Madness
- chroma/key/harmonic change + stronger phrase/section state
- beat-synchronous palette/particle/preset/backdrop morphing
- transitions / user snapshots / DJ-VJ switching
- MIDI/OSC/Ableton Link/clock
- audio-reactive generated asset spawning only on meaningful macro events
- eventual audio -> semantic neural/style/asset-bank state

### Performer FX / Cyber Mage
- generic persistent points remain useful for fabric/hair/props/environment
- real hands/body semantics must come from actual landmark trackers
- shared `TrackingState` / `PerformanceState`
- GPU particles, ribbons, vector fields, feedback, SDF glyphs/portals, distortion, HDR bloom
- charge/release/slash/shield/portal/ascension grammar
- generated 2D sprite/atlas and 3D GLB/glTF asset packs
- built-in relic/drone/sigil-totem/summon-proxy fixtures
- Genforge pipeline adapter + provenance/license/content hashes
- mixed-reality entities, room collisions, arena/gameplay experiments
- optional OSC/Spout/TouchDesigner bridge; open renderer remains canonical
- neural style skin remains additive and slower-rate

### Human Reactor / dance video
- style/palette/edge/motion/aura/sparks/trails/echo/camera-underlay controls
- rendered-video recording
- portrait/landscape/high-quality profiles, matte/metadata outputs
- shared semantic performer state, multi-person IDs and depth layers
- Human Reactor + Song Studio + particles + generated assets + neural style composition

### Neural/video continuity
- previous-frame/latent/state reuse
- optical-flow warp of previous stylized output implemented as first baseline
- stable seed/style/prompt interpolation + low denoise
- pose/depth/segmentation/edge/point/gesture-energy conditioning
- generated asset/reference conditioning
- temporal/video models evaluated against deterministic baseline
- never claim hard generative consistency guarantee

### Procedural / shader scenes
- user-supplied casual radial shader is an **art benchmark**, not something to dismiss because it is simple
- Liquid Chrome is the current in-repo Shader Scene Lab aesthetic benchmark from hardware/user feedback
- rose/hypotrochoid/log-spiral/phyllotaxis/Bessel families are first-class visual research directions and now expose structured chaos
- structured-chaos studies: Wormhole Choir, Plasma Singularity, Vortex Crown, Collapse Flower
- Event Horizon raw-angle FBM branch cut was a correctness bug; unit-circle harmonics + seam regression are the retained fix pattern
- portal architecture, infestation, cathedral, machinery, moss ruin, starfield retained as ideas
- CPU scenes are fallback, not quality target
- branch-cut/periodicity continuity bugs are correctness issues
- shader worlds + particle fields should share common renderer/post infrastructure
- reusable shader assets live in VFX packs rather than only experiment code
- future reaction diffusion, SDF/raymarching, fluid/vector fields, proper HDR bloom and transitions
- static/generic promoted scenes are rewritten rather than preserved for sunk-cost reasons; promising ugly research sketches can remain in incubation

### Spatial / physical path
- wall test / structured light / dense calibration
- radiometry and learned compensation
- Room Skin / semantic room
- performer/world/projector coordinate chain
- wall/floor/ceiling collisions and asset placement
- dynamic moving-target projection
- multi-projector display

### Runtime/product
- F11/ESC behavior
- dependency preflight/logging/process-tree cleanup/VRAM safety
- ModernGL + glcontext packaging/context diagnostics
- 6 GB Neural Mirror safe profile + stronger desktop modes
- stage/load/download/warmup/run visibility
- live controls/presets/assets without relaunch
- native installers / cross-platform operation

---

# Current priority queue

1. **M4:** pull the new scene code and re-test Event Horizon at the exact framing that showed the horizontal seam; if any hard cut remains, capture another screenshot and treat it as correctness, not taste.
2. **M4 art bring-up:** compare Liquid Chrome against Wormhole Choir, Plasma Singularity, Vortex Crown and Collapse Flower at chaos ~0.8–1.6; incubate promising scenes and art-pass weak ones.
3. **M4:** test all five revised Polar Math modes with chaos ~0.8–1.4. Keep/rewrite based on beauty, motion, color and projector readability—not implementation effort.
4. **M7/M11:** test the vivid particle material with `backdrop=none` on the RTX 4050/projector. If it still looks shaded, tune thresholded bloom/feedback floor/display transform before adding haze.
5. **M7:** validate Song Studio `journey` choreography across techno/house/ambient/dense tracks; tune section/phrase switching.
6. **M7/M4:** test `backdrop=auto` at low mix; preserve only pairings where shader math adds structure without obscuring particle light.
7. **M7:** implement bar/phrase-synchronous backdrop crossfades/morphs so auto mode never hard-cuts mathematical worlds.
8. **M11/PF2:** hardware-test graphics context + GPU particle engine; benchmark 8k/16k/32k/65k and render/readback cost.
9. **M11/PF1:** hardware-test RTMPose whole-body landmarks; validate hands, confidence, smoothing, latency and reacquisition.
10. **M11/PF3:** tune charge/release/slash/shield/portal/ascension grammar from real performer footage.
11. **M11/PF4/PF6:** Genforge VFX-pack adapter, sprite atlases, PBR/animated GLB rendering and first generated-asset summon/arena prototype.
12. **M2:** remove GL -> CPU readback with a native OpenGL display/shared-texture path.
13. **M3:** benchmark Neural Mirror 6 GB safe profile and temporal warp on RTX 4050; connect performer control maps later.
14. **M7/M11:** route one `MusicalSignals` bus into Performer FX / Human Reactor / Room Skin.
15. **M1:** capture real structured-light bundle.
16. **M1/M5:** capture radiometry data and compare classical/learned compensation.
17. **M4/M6/PF6:** calibrated Room Skin + room-plane collisions + generated entities.
18. **M8/M9:** dynamic mapping / multi-projector after static calibration and latency metrics are solid.

---

# Experiment mapping

- E00 -> M0 photons
- E01 -> M1 dense correspondence
- E02 -> M1 radiometry / M5 baseline
- E03 -> M5 learned inverse display
- E04 -> M3 Neural Mirror / StreamDiffusion
- E05 -> M3 benchmark
- E06 -> M2 transport diagnostics
- E07 -> M1 calibration bundle
- E08 -> M1/M5 radiometry capture
- E09 -> M4 Room Skin
- E10 -> M7 legacy CPU audio-reactive studio
- E11 -> M4/M6 legacy CPU procedural scenes
- E12 -> M11 Human Reactor
- E13 -> M11 generic-point Cyber Mage SFX
- E14 -> M4/M11 ModernGL Shader Scene Lab
- E15 -> M7 GPU shader Audio Visual Instrument
- E16 -> M7/M11 GPU Song Studio particle choreography / section-aware journey / Polar+structured-chaos backdrop conductor
- E17 -> M11 PF1/PF2/PF3 whole-body GPU Performer FX
- E18 -> M2 graphics runtime / OpenGL context probe
- E19 -> M11 PF4/PF6 mixed-reality generated/built-in 3D asset stage
- E20 -> M4/M7 Polar Math Lab / vivid analytic radial shader research
- E21 -> cross-cutting real-GL visual smoke / shader compile / Event Horizon seam regression

When adding an experiment, link it to a milestone **and update the corresponding feature track** so research prototypes, failures, good presets, measurements and product progress stay synchronized.
