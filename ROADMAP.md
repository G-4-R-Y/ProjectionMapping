# ProjectionMapping Roadmap

This is the canonical milestone roadmap. Milestone numbering **M0–M6 is stable**. Extension milestones preserve performance-art and research directions without displacing the core spatial pipeline.

Legend: **✅ done / implemented** · **🟡 implemented but needs integration or hardware validation** · **⬜ planned** · **🧪 research / stretch**

Fine-grained research/progress is tracked permanently in [`docs/feature_tracks/`](docs/feature_tracks/README.md). Every meaningful feature change must update its track so successful presets, failed approaches, measurements, open problems and the path toward the advanced version do not disappear.

## North star

Build a home-scale spatial hallucination instrument where projector, camera, audio, performers and realtime graphics form one low-latency system. Deterministic tracking/geometry/shaders own continuity and spatial registration; neural models provide lower-rate semantic/material/style transformations where they actually add value.

Preferred architecture:

`camera / audio / controls -> perception + persistent identities/points -> deterministic realtime FX/shaders -> async neural semantic/style updates -> compensation / warp -> GPU/native transport or fullscreen -> projector -> camera feedback`

Core runtime rules:
- latest-frame-wins for neural inference; never queue stale visual state
- persistent IDs/points/geometry own temporal continuity
- process isolation and clean GPU teardown
- conservative VRAM policy
- F11 fullscreen toggle / ESC returns to control deck
- hardware-measured latency and frame-time telemetry
- visual quality is evaluated on the projector/recorded footage, not only in code

A central design rule applies across Human Reactor, Cyber Mage, Neural Mirror and Room Skin: **deterministic spatial ownership first; generative stylization second**.

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

Next:
- ⬜ direct PyTorch/CUDA -> shared texture path
- ⬜ real Spout/TouchDesigner validation on Windows
- ⬜ MadMapper handoff
- ⬜ Syphon macOS / optional NDI
- ⬜ transport copy-count + latency benchmark
- ⬜ direct ModernGL/shared-texture output so shader scenes do not read back to CPU

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
- ⬜ stable seed/style bank + gradual prompt interpolation
- ⬜ similarity filtering / adaptive submit rate
- ⬜ mask-aware person/background/energy compositing
- ⬜ feed prior/warped style into neural conditioning where backend permits
- ⬜ persistent latent/state experiments
- ⬜ pose/depth/edge/point-energy controls
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

Visual/shader direction:
- ✅ legacy CPU portal branch-cut seam fixed
- ✅ shader scenes: Event Horizon, Aurora Void, Liquid Chrome, Neon Cathedral
- ⬜ per-scene art controls + preset vault
- ⬜ multi-pass bloom / GPU feedback / reaction diffusion / particles
- ⬜ SDF/raymarched architectural primitives
- ⬜ calibrated surface masks and projector-coordinate scene routing

Spatial/neural direction:
- ⬜ clean room reference + calibrated projector coordinates
- ⬜ depth/normal/edge/segmentation priors
- ⬜ object-/surface-space canonicalization
- ⬜ neural semantic keyframes injected into deterministic shader/feedback motion
- ⬜ quantitative edge-registration metric

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

Effect routing:
- ⬜ independent shader/neural graph per region/object
- ⬜ priorities + occlusion rules + composable masks
- ⬜ per-object material/prompt/style controls
- ⬜ OSC/MIDI/gamepad/phone controls
- ⬜ cross-node interactions: tracked motion -> wall effect; feet -> floor field; audio -> ceiling state

Track: [`docs/feature_tracks/semantic_room.md`](docs/feature_tracks/semantic_room.md)

---

# Extension milestones

## M7 — audiovisual instrument 🟡

**Goal:** musical structure controls visual state, not noisy FFT-to-pixel modulation.

Implemented:
- ✅ reliable Linux system-audio monitor capture
- ✅ RMS/bass/mid/treble/centroid/flux/onset
- ✅ multiple visual presets + curated palettes
- ✅ smooth/balanced/punchy/chaotic modes
- ✅ event-driven gating + Calm<->Madness

Next:
- ⬜ adaptive peak/refractory detector
- ⬜ tempo/beat phase/confidence
- ⬜ chroma/key/section/drop descriptors
- ⬜ live scene transitions + preset A/B/morph banks
- ⬜ MIDI/OSC/Ableton clock
- ⬜ audio embeddings -> prompt/latent/LoRA/style state
- ⬜ audio modulation of Shader Scene Lab and point-SFX fields

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
- ⬜ use persistent point tracks as a dynamic-mapping measurement signal

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

Promote only when the research path beats a simpler baseline on our actual hardware or unlocks a qualitatively new effect.

---

## M11 — performer / motion SFX instrument 🟡

**Goal:** visually polished realtime SFX for dance/performance and projection, driven by persistent motion/points first and real semantic landmarks second.

### Rejected prototype — retained as a lesson
- ⚠️ the first Cyber Mage used upper-silhouette left/right extrema as fake “hands”
- ⚠️ hands-together / charge/release therefore failed on hardware
- ⚠️ OpenCV circles/lines read as debug graphics rather than finished SFX
- ✅ failure and reason permanently recorded in Cyber Mage feature track

### Active Cyber Mage SFX v2
- ✅ persistent Shi-Tomasi feature points
- ✅ pyramidal Lucas-Kanade propagation
- ✅ forward/backward drift rejection
- ✅ persistent IDs, age, velocity, speed, quality
- ✅ foreground-only or full-frame tracking
- ✅ track trails, proximity plasma mesh, velocity sparks, acceleration shockwaves
- ✅ optional silhouette aura without pretending edges are joints
- ✅ modes: plasma mesh / constellation / afterburner / liquid wire
- ✅ ModernGL post FX: chromatic split, bloom taps, lens warp, filmic compression, procedural atmosphere

### Next graphics jump
- ⬜ GPU-native point sprites and trail geometry
- ⬜ GPU proximity/field rendering
- ⬜ ping-pong feedback/advection
- ⬜ multi-scale bloom
- ⬜ SDF sprites/runes/HUD/portals with derivative antialiasing
- ⬜ clustered optical-flow ribbons/vortices
- ⬜ GPU particles / fluid-like emitters

### Semantic tracking later
- ⬜ real pose + hand landmarks as additional high-confidence emitters
- ⬜ confidence-aware loss/reacquisition
- ⬜ Kalman/predictive motion compensation
- ⬜ multi-performer IDs
- ⬜ depth-aware occlusion
- ⬜ room collisions / calibrated surface hits

### Human Reactor convergence
- ✅ dance-video silhouette/echo renderer exists
- ⬜ share persistent point field with Human Reactor
- ⬜ recording profiles/mattes/metadata
- ⬜ real pose-driven body-part emitters only after landmarks are reliable

### Neural layer
- ⬜ point/velocity/pose/depth/energy control maps
- ⬜ flow-warp previous neural style
- ⬜ stable style/seed bank + low-denoise live style skin
- ⬜ mask-aware composition preserving deterministic exact SFX

Track: [`docs/feature_tracks/cyber_mage.md`](docs/feature_tracks/cyber_mage.md) and [`docs/feature_tracks/human_reactor.md`](docs/feature_tracks/human_reactor.md)

---

# Cross-cutting engineering goals

Performance/reliability:
- ✅ process isolation
- ✅ latest-frame-wins async inference
- ✅ VRAM guard / cleanup
- ✅ cross-platform CI
- ⬜ p50/p95/p99 capture/perception/render/inference/transport/scanout timings
- ⬜ continuous GPU/CPU memory and frame-time telemetry
- ⬜ live parameter hot-reload
- ⬜ named preset/performance-state snapshots

Evaluation:
- ⬜ geometric registration error
- ⬜ radiometric error
- ⬜ temporal flicker/flow-warp residual
- ⬜ tracked-point lifetime/FB error/reseed rate
- ⬜ motion-to-effect and motion-to-photon latency
- ⬜ shader/GPU/readback frame cost
- ⬜ subjective projector/recording visual-quality captures

Product/UX:
- ✅ Textual control deck + modular feature fragments
- ✅ persistent logs / copy/open / stage status
- ⬜ robust monitor enumeration
- ⬜ live parameter IPC + preset browser
- ⬜ Linux AppImage/DEB, Windows Setup.exe, polished macOS app

Research discipline:
- ✅ per-category feature tracks
- ✅ failed visual/technical directions are recorded rather than silently erased
- ✅ implemented vs hardware-validated claims separated
- ⬜ pin promoted model/repository revisions
- ⬜ save runtime/calibration/benchmark metadata with captures
- ⬜ keep classical baselines beside learned paths

---

# No-forgetting ledger

### Audio / performance
- multiple audio visuals/palettes
- event-driven gating and configurable thresholds
- smooth/balanced/punchy/chaotic modes
- Calm<->Madness
- tempo/beat phase/chroma/sections/drops
- transitions/presets/MIDI/OSC/Ableton
- eventual audio -> neural/style state

### Human Reactor / dance video
- style/palette/edge/motion/aura/sparks/trails/echo/camera-underlay controls
- rendered-video recording
- portrait/landscape/high-quality profiles, matte/metadata outputs
- persistent points, later real pose landmarks, multi-person IDs and depth layers
- Human Reactor + audio + point SFX + neural style composition

### Cyber Mage / SFX
- **point tracking and motion SFX are now first-class**, not only semantic gestures
- persistent IDs/velocity/acceleration + trails/mesh/sparks/shockwaves
- ModernGL/GLSL path, GPU particles, feedback, SDF graphics, distortion and real bloom
- real hand/body tracking only when actual landmarks exist
- runes/sigils/portals remain desired, but must be shader-quality and landmark/room anchored—not debug circles
- deterministic high-rate mode remains useful without AI
- neural style skin remains additive

### Neural/video continuity
- previous-frame/latent/state reuse
- optical-flow warp of previous stylized output **implemented as first baseline**
- stable seed/style/prompt interpolation + low denoise
- pose/depth/segmentation/edge/point-energy conditioning
- temporal/video models evaluated against deterministic baseline
- never claim hard generative consistency guarantee

### Procedural / shader scenes
- portal architecture, infestation, cathedral, machinery, moss ruin, starfield retained as ideas
- CPU scenes are fallback, not quality target
- branch-cut/periodicity continuity bugs must be treated as correctness issues
- ModernGL Shader Scene Lab is preferred path
- Event Horizon / Aurora Void / Liquid Chrome / Neon Cathedral baseline
- future feedback, particles, reaction diffusion, SDF/raymarching and transitions

### Spatial / physical path
- wall test / structured light / dense calibration
- radiometry and learned compensation
- Room Skin / semantic room
- dynamic moving-target projection
- multi-projector display

### Runtime/product
- F11/ESC behavior
- dependency preflight/logging/process-tree cleanup/VRAM safety
- 6 GB Neural Mirror safe profile + stronger desktop modes
- stage/load/download/warmup/run visibility
- live controls/presets without relaunch
- native installers / cross-platform operation

---

# Current priority queue

1. **M11:** hardware-test Cyber Mage SFX v2 point tracking and tune drift/reseed/track count.
2. **M4/M11:** validate ModernGL Shader Scene Lab + Cyber Mage post shader on Linux/NVIDIA; rewrite weak art immediately.
3. **M11:** move point/trail/particle rendering fully to GPU + feedback/bloom chain.
4. **M3:** benchmark Neural Mirror 6 GB safe profile and temporal warp on RTX 4050.
5. **M7:** beat phase / live presets / scene transitions; route music state into shaders/SFX.
6. **M11:** add real pose/hand landmarks only as trustworthy semantic emitters alongside generic points.
7. **M1:** capture real structured-light bundle.
8. **M1/M5:** capture radiometry data and compare classical/learned compensation.
9. **M4:** calibrated Room Skin + neural keyframes + display-rate shaders.
10. **M2:** validate Spout/TouchDesigner on Windows and remove GPU->CPU readback where possible.
11. **M6:** persistent semantic scene graph and interactions.
12. **M8/M9:** dynamic mapping / multi-projector after static calibration and latency metrics are solid.

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
- E10 -> M7 audio-reactive instrument
- E11 -> M4/M6 legacy CPU procedural scenes
- E12 -> M11 Human Reactor
- E13 -> M11 Cyber Mage SFX / persistent point tracking
- E14 -> M4/M11 ModernGL Shader Scene Lab

When adding an experiment, link it to a milestone **and update the corresponding feature track** so research prototypes, failures, good presets, measurements and product progress stay synchronized.
