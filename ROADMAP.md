# ProjectionMapping Roadmap

This is the canonical milestone roadmap. Milestone numbering **M0–M6 is stable** and follows the original plan. Extension milestones preserve performance-art and research directions without displacing the core spatial pipeline.

Legend: **✅ done / implemented** · **🟡 implemented but needs integration or hardware validation** · **⬜ planned** · **🧪 research / stretch**

Fine-grained research/progress is tracked permanently in [`docs/feature_tracks/`](docs/feature_tracks/README.md). Every material feature change should update its feature track so successful presets, open problems, measurements and the path toward the advanced version are not lost.

## North star

Build a home-scale spatial hallucination instrument where the projector is a programmable light source, the camera is feedback, performers/audio are control signals, and realtime graphics + generative models alter the perceived material and behavior of people/room surfaces while remaining geometrically registered to the physical world.

Preferred runtime architecture:

`camera / audio / controls -> perception + persistent identities -> deterministic realtime FX -> async generative semantic/style updates -> compensation / warp -> GPU/native transport or fullscreen -> projector -> camera feedback`

The display loop must remain responsive even when AI inference is slower than refresh rate. **Latest-frame-wins**, bounded queues, process isolation, persistent semantic anchors, clean GPU teardown and hardware-measured latency are first-class requirements.

The operator experience is the persistent `projection-ui` control deck: configure -> launch fullscreen -> F11 toggle -> ESC -> reconfigure -> launch again. Long term, live IPC/OSC/MIDI/phone control should mutate parameters/presets without restarting renderers.

A central design rule now applies across Human Reactor, Cyber Mage, Neural Mirror and Room Skin: **deterministic spatial ownership first; generative stylization second**. Tracking/geometry/persistent IDs own consistency; neural generation supplies semantic material/style and lower-rate keyframes.

---

## M0 — photons ✅

**Goal:** Python generates a realtime test pattern -> fullscreen projector.

### Deliverables
- ✅ fullscreen projector output
- ✅ F11 fullscreen toggle / ESC visual exit in shared sink
- ✅ grid / checkerboard / color-ramp patterns
- ✅ Gray-code and phase-shift pattern generation
- ✅ selectable projector display
- ✅ basic camera preview
- ✅ console control deck / modular feature registry
- ⬜ automatic display enumeration instead of fixed pixel offsets
- ⬜ projector capability report: native resolution, refresh, overscan, HDR/color mode, latency notes
- ⬜ latency-flash test pattern for camera/projector timing measurements

### Exit criterion
A deterministic framebuffer can be shown fullscreen on the actual projector at known resolution/refresh with repeatable display placement.

---

## M1 — camera/projector calibration 🟡

**Goal:** structured-light correspondence and projector<->camera geometry suitable for static and later dynamic mapping.

### Geometry
- ✅ Gray-code normal/inverse sequence generation
- ✅ Gray-code decoding primitives
- ✅ planar homography estimation and image warp
- ✅ structured-light capture tooling
- ✅ calibration-bundle serialization with camera/projector metadata
- 🟡 black/white + Gray-code + phase-shift capture bundle; real-room validation pending
- ⬜ confidence-aware dense projector->camera correspondence map from real captures
- ⬜ camera->projector inverse map with hole filling / validity masks
- ⬜ phase-shift refinement for subpixel correspondence
- ⬜ reprojection-error diagnostics and visual QA overlays

### Camera / photometric calibration
- ✅ cross-platform camera capture abstraction with Linux V4L2 path
- ⬜ exposure/gain/white-balance locking helpers
- ⬜ lens distortion calibration / undistortion
- ⬜ projector intrinsic/extrinsic calibration where useful
- ⬜ synchronization / exposure timing characterization

### Attached goal: radiometry
- ✅ per-channel monotonic inverse-LUT baseline
- ✅ automated grayscale/RGB intensity-sweep dataset capture tooling
- ✅ deterministic random-patch capture tooling
- 🟡 real projector/wall dataset pending
- ⬜ spatially varying radiometric model
- ⬜ ambient-light compensation
- ⬜ defocus compensation baseline
- ⬜ shadow / occlusion masks

### Exit criterion
Given a camera pixel on a valid observed surface, recover where to emit light in projector coordinates with measured confidence/error, and reproduce requested color substantially better than the uncompensated baseline.

Track: [`docs/feature_tracks/calibration_mapping.md`](docs/feature_tracks/calibration_mapping.md)

---

## M2 — realtime GPU transport 🟡

**Goal:** generated GPU output -> native/shared texture transport -> compositor/projector without unnecessary encode/decode or copies.

### Deliverables
- ✅ Spout sender abstraction
- ✅ fullscreen fallback path
- ✅ modular source / processor / sink runtime
- ✅ deterministic Spout diagnostics experiment
- ✅ platform-aware feature registry + optional dependency/command detection
- 🟡 Spout2 Windows backend still requires real hardware/TouchDesigner validation
- ⬜ PyTorch/CUDA -> shared GPU texture path without avoidable host readback
- ⬜ TouchDesigner receiver example/project
- ⬜ MadMapper handoff example via Spout
- ⬜ Syphon output path for macOS
- ⬜ optional NDI transport for multi-machine setups
- ⬜ transport benchmark: throughput, frame latency, CPU/GPU copy counts

### Runtime goals
- ✅ bounded latest-frame-wins inference queue
- ✅ capture/display remain independent of slow inference
- ✅ child renderer isolation from persistent console
- ✅ persistent full logs + GPU snapshots + process-tree termination
- ✅ conservative CUDA VRAM guard and recoverable OOM path
- 🟡 latency/throughput telemetry primitives and benchmark reports
- ⬜ full per-stage timestamps through capture -> scanout
- ⬜ continuous GPU memory telemetry
- ⬜ live parameter IPC / preset mutation without relaunch

### Exit criterion
A generated GPU frame reaches the compositor/projector with stable realtime throughput and without encode/decode or unnecessary host copies.

Track: [`docs/feature_tracks/runtime_transport_ui.md`](docs/feature_tracks/runtime_transport_ui.md)

---

## M3 — neural mirror 🟡

**Goal:** camera -> segmentation/depth/flow/pose -> temporally coherent realtime generative transformation -> projector.

### Perception
- ✅ foreground mask baseline
- ✅ Farneback optical flow baseline
- ✅ classical persistent performer-anchor baseline shared with Cyber Mage
- ⬜ semantic segmentation backend
- ⬜ monocular depth backend
- ⬜ optional learned pose / hand tracking backend behind performer-rig interface
- ⬜ optional depth-camera input

### StreamDiffusion / generative runtime
- ✅ generic StreamDiffusion integration wrapper
- ✅ concrete Daydream StreamDiffusion backend adapter
- ✅ async latest-frame-wins worker
- ✅ live camera -> async StreamDiffusion experiment
- ✅ reproducible RTX benchmark harness with JSON reports
- ✅ optional-xformers fallback to native PyTorch attention
- ✅ 6 GB safe Neural Mirror profile (512x288, bounded submit rate)
- 🟡 SD-Turbo/native-attention path requires measured RTX 4050 operating point
- 🟡 xformers/TensorRT operating points require measured RTX 4080 validation
- ⬜ TensorRT engine build + measured runtime path
- ⬜ live prompt/seed/style updates over IPC
- ⬜ similarity filtering / adaptive submit rate for low-motion frames
- ⬜ ControlNet hooks for depth / edges / pose / deterministic energy masks

### Temporal consistency ladder
- ⬜ stable seed/style bank + gradual prompt interpolation
- ⬜ previous neural frame flow-warp + blend baseline
- ⬜ persistent latent/state experiments where upstream API allows
- ⬜ mask-aware neural compositing per person/background/object
- ⬜ quantitative temporal flicker / warped-residual metrics
- 🧪 TemporalNet / StreamV2V evaluation
- 🧪 newer streaming video-edit/video-diffusion models only when they beat the simpler flow/state baseline on latency, VRAM and stability

### Hybrid rendering
- ✅ room-skin temporal/advection primitives establish hybrid direction
- ✅ deterministic Cyber Mage/Human Reactor establish performer-owned high-rate FX direction
- ⬜ diffusion supplies semantic keyframes/style skins into room-skin/performer paths
- ⬜ GLSL / particles / feedback provide stable 60+ FPS motion between AI updates

### Exit criterion
A live feed is semantically transformed while spatial identity and temporal appearance remain acceptably stable and the display stays smooth even when neural inference FPS is lower than projector refresh.

Track: [`docs/feature_tracks/neural_mirror.md`](docs/feature_tracks/neural_mirror.md)

---

## M4 — spatially locked generation 🟡

**Goal:** preserve scene geometry while generatively changing material / appearance — the **Room Skin** milestone.

### Deliverables
- ✅ physical-edge locking primitives
- ✅ optical-flow advection between semantic keyframes
- ✅ temporal blending
- ✅ standalone room-skin prototype with procedural fallback
- ⬜ capture clean room reference + calibrated projector coordinates
- ⬜ construct geometric/depth priors for scene
- ⬜ condition generation on depth / normal / edge / segmentation maps
- ⬜ object-space or UV-like canonicalization for static surfaces
- ⬜ texture-space generation so bookshelf/wall/door keep physical shape
- ⬜ procedural shaders/particles/feedback between AI keyframes
- ⬜ quantitative registration metric: generated feature edge vs physical edge

### Visual targets
- wall -> underwater caustics / architecture / organic material
- bookshelf -> stone / machinery / bioluminescent growth
- plants -> alien vegetation
- door -> portal / depth illusion
- ceiling -> stars / volumetric field
- room surfaces -> coherent material transformations rather than rectangular video

### Exit criterion
A static room surface can change apparent material/semantics while important physical edges remain visually registered over time.

Track: [`docs/feature_tracks/room_skin.md`](docs/feature_tracks/room_skin.md)

---

## M5 — closed-loop compensation 🟡

**Goal:** camera observes projected result and learns / optimizes the actual emitted image.

### Baselines
- ✅ inverse radiometric LUT utilities
- ✅ learned appearance-compensation MLP scaffold
- ✅ closed-loop optimization experiment scaffold
- ✅ automated `(projected pattern, camera observation)` dataset capture tooling
- 🟡 real dataset + LUT-vs-neural comparison pending

### Learned physical display model
- ⬜ learn forward model `C(P, surface, illumination)`
- ⬜ learn inverse model for desired observed appearance
- ⬜ spatially varying compensation
- ⬜ differentiable surrogate for projector-camera response
- ⬜ online refinement from camera feedback

### Perceptual control
- ⬜ RGB / L1-L2 objective baseline on real captures
- ⬜ LPIPS objective
- ⬜ DINO / self-supervised feature objective
- ⬜ segmentation-consistency objective
- ⬜ CLIP / semantic objective experiments
- 🧪 diffusion-feature or generative-prior objective

### Physical effects
- ⬜ surface albedo compensation
- ⬜ ambient illumination adaptation
- ⬜ projector nonlinearity / gamma
- ⬜ defocus compensation
- ⬜ shadow / occlusion handling
- ⬜ saturation / gamut constraints and regularization

### Exit criterion
For a static surface, closed-loop compensated projection measurably reduces observed target error versus direct projection and classical LUT compensation.

Track: [`docs/feature_tracks/compensation.md`](docs/feature_tracks/compensation.md)

---

## M6 — semantic room ⬜

**Goal:** detect surfaces / objects / performers and assign independently controllable persistent behaviors.

### Scene understanding
- ⬜ wall / ceiling / floor segmentation
- ⬜ furniture / plants / people / doors / windows
- ⬜ instance tracking across frames
- ⬜ depth-aware occlusion relationships
- ⬜ persistent semantic scene graph
- ⬜ PerformerRig represented as a person/body subgraph

### Effect graph
- ⬜ independent shader / diffusion graph per object or region
- ⬜ priorities and occlusion rules
- ⬜ composable masks
- ⬜ persistent object identities
- ⬜ per-object prompt / LoRA / material controls
- ⬜ live controls via OSC / MIDI / gamepad / phone
- ⬜ cross-node interactions: hand spell -> wall portal, feet -> floor glyph, audio -> ceiling/star state

### Example behavior map
- wall -> slow procedural environment / portal target
- plants -> generative glowing vegetation
- person -> Human Reactor / Cyber Mage / Neural Mirror skin
- bookshelf -> mechanical/material transformation
- ceiling -> stars / volumetric field
- hands -> particles/fluid/sigil emitters

### Exit criterion
Multiple physical objects/surfaces in one room simultaneously run different spatially registered effects with stable identity, occlusion and controllable behavior.

Track: [`docs/feature_tracks/semantic_room.md`](docs/feature_tracks/semantic_room.md)

---

# Extension milestones

## M7 — audio-latent instrument 🟡

**Goal:** make the system a performable audiovisual instrument, not an FFT-to-brightness visualizer.

### Implemented
- ✅ native Linux system-audio monitor capture with SoundCard fallback
- ✅ low-latency RMS/bass/mid/treble/centroid/flux/onset features
- ✅ multiple audiovisual scenes and curated palettes
- ✅ smooth/balanced/punchy/chaotic reactivity modes
- ✅ event-driven gating + calm<->madness macro
- ✅ feature-age/runtime telemetry

### Next
- ⬜ stronger adaptive peak-picking / refractory event detector
- ⬜ tempo / beat phase + confidence
- ⬜ chroma/key and musical section/drop descriptors
- ⬜ live scene/palette transitions without relaunch
- ⬜ preset save/load/A-B/morph banks
- ⬜ MIDI / OSC control surface and Ableton clock integration
- ⬜ audio embeddings
- ⬜ map audio to prompt embeddings / latent directions
- ⬜ LoRA / seed / style interpolation
- ⬜ audio + performer gesture fusion

Exit criterion: musical structure produces coherent, repeatable state changes in semantic appearance and high-rate motion without noisy one-frame reactions.

Track: [`docs/feature_tracks/audio_visual.md`](docs/feature_tracks/audio_visual.md)

---

## M8 — dynamic projection mapping ⬜

**Goal:** keep projection registered on moving objects.

- ⬜ full motion-to-photon latency measurement
- ⬜ planar target tracking baseline
- ⬜ pose/body anchor prediction over measured latency
- ⬜ realtime homography update
- ⬜ moving hand/body target experiments
- ⬜ registration error vs target speed benchmark
- ⬜ use Cyber Mage performer anchors as dynamic-mapping test signals
- 🧪 high-speed camera/projector path if consumer hardware becomes bottleneck

Exit criterion: projection remains acceptably registered on moving target with quantified latency/error.

---

## M9 — multi-projector / spatial display ⬜

**Goal:** expand from one projector to a coherent spatial display.

- ⬜ projector auto-calibration
- ⬜ multi-projector geometric alignment
- ⬜ edge blending
- ⬜ brightness / color balancing
- ⬜ overlap assignment
- ⬜ shadow-aware projector selection
- ⬜ distributed rendering / NDI where useful

Exit criterion: two or more projectors behave like one calibrated canvas.

---

## M10 — advanced neural / spatial research 🧪

**Goal:** track emerging research that can materially improve the installation without destabilizing the practical path.

- 🧪 StreamDiffusionV2 / streaming video-diffusion evaluation
- 🧪 TemporalNet / StreamV2V / causal streaming-edit evaluation
- 🧪 distilled / quantized video models for single-4080 deployment
- 🧪 previous-latent/state reuse and temporal cross-frame attention approaches
- 🧪 Gaussian splats / NeRF-like room representation
- 🧪 4D scene representations for moving content
- 🧪 neural material / inverse-rendering representations
- 🧪 learned projector-camera calibration
- 🧪 semantic optimization directly in physical appearance space
- 🧪 structure-preserving streaming video editing / relighting
- 🧪 sparse neural keyframes + high-rate deterministic warping/interpolation

These are not blockers; pull them forward only when they beat simpler baselines on our hardware or unlock a qualitatively new capability.

---

## M11 — performer instrument / Cyber Mage 🟡

**Goal:** build a high-end performer-owned realtime FX system suitable for dance/performance videos and room-scale techno-magic interaction.

### Implemented baseline
- ✅ Human Reactor silhouette/motion visual with styles, palettes, echoes, recording
- ✅ persistent classical `PerformerRig` with head/chest/core/hands/feet anchors
- ✅ gesture baseline: arms spread, hands together, hands raised, motion burst
- ✅ Cyber Mage deterministic sigils/arcs/trails/aura/charge orb/ground glyph
- ✅ Cyber Mage palette/intensity/complexity/trail/feedback/rig-smoothing controls

### Performer rig next
- ⬜ optional MediaPipe/learned pose landmarks behind same rig interface
- ⬜ hand/finger landmarks and gesture features
- ⬜ confidence-aware loss/reacquisition
- ⬜ Kalman/predictive tracking based on measured display latency
- ⬜ multi-performer persistent IDs
- ⬜ depth-aware body/FX occlusion

### Effect system next
- ⬜ split Sigil/Arc/Trail/Emitter/Aura/Portal/GroundGlyph render modules
- ⬜ GLSL/SDF rune/glyph atlas with higher-quality anti-alias/glow
- ⬜ GPU particle/fluid emitters tied to semantic anchors
- ⬜ gesture state machine: charge -> hold -> release, summon, shield, cast, swipe, spin, jump, crouch
- ⬜ room-targeted spells: hand->wall portal, foot->floor glyph, head/chest halo, projected energy hitting surfaces
- ⬜ audio/gesture fusion and performance presets

### Neural performer skin
- ⬜ current camera + person mask + pose/edge/depth + deterministic energy mask as controls
- ⬜ flow-warp previous stylized output before next neural keyframe
- ⬜ stable seed/style bank + low-denoise StreamDiffusion skin
- ⬜ mask-aware compositing so exact sigils/trails remain deterministic
- 🧪 TemporalNet/StreamV2V/video-edit models on stronger GPU after flow-warp baseline

Exit criterion: performer can intentionally execute a vocabulary of tracked gestures that produce stable, legible, body-owned effects at display rate, optionally decorated by temporally coherent neural style without losing spatial ownership.

Tracks: [`docs/feature_tracks/cyber_mage.md`](docs/feature_tracks/cyber_mage.md) and [`docs/feature_tracks/human_reactor.md`](docs/feature_tracks/human_reactor.md)

---

# Cross-cutting engineering goals

## Performance / reliability
- ✅ renderer process isolation behind persistent console UI
- ✅ bounded latest-frame-wins worker
- ✅ benchmark report utilities
- ✅ cross-platform CI matrix: Windows/Linux/macOS × Python 3.10/3.12
- ✅ conservative CUDA VRAM policy + cleanup path
- ⬜ benchmark every physical stage separately: capture, perception, inference, compositing, transport, scanout
- ⬜ p50 / p95 / p99 end-to-end latency logging
- ⬜ continuous GPU memory telemetry
- ⬜ deterministic benchmark scenes
- ⬜ hot-reload prompts / configs / visual parameters without restarting display
- ⬜ named preset banks and performance-state snapshots

## Evaluation
- ⬜ geometric registration error
- ⬜ radiometric error before/after compensation
- ⬜ temporal flicker / flow-warp residual / consistency metrics
- ⬜ performer-anchor jitter + gesture precision
- ⬜ motion-to-photon latency
- ⬜ subjective visual quality snapshots / recordings
- ⬜ reproducible benchmark reports per GPU/model/projector configuration

## Tool integrations
- 🟡 TouchDesigner via Spout
- ⬜ MadMapper output/calibration workflow
- ⬜ OSC / MIDI controls
- ⬜ optional NDI network transport
- ⬜ optional Syphon transport on macOS
- 🧪 evaluate open-source mapping/compositor alternatives as standalone peers, not copied dependencies
- ⬜ optional ComfyUI only as experimental model graph, not core runtime architecture

## Product / UX / packaging
- ✅ Textual control deck + modular registry
- ✅ live log panel / copy/open / persistent run logs
- ⬜ monitor enumeration and robust projector placement
- ⬜ explicit structured runtime-stage protocol in TUI
- ⬜ live parameter IPC and preset browser
- ⬜ Linux AppImage/standalone installer + optional DEB
- ⬜ Windows Setup.exe installer
- ⬜ polished macOS `.app` / DMG

## Research discipline
- ✅ monthly research-watch policy documented
- ✅ external command/module availability represented in registry
- ✅ per-category feature-track ledger in `docs/feature_tracks/`
- ✅ feature tracks separate implemented vs hardware-validated claims
- ⬜ require track update when adding/promoting meaningful visual/research feature
- ⬜ pin model/repository revisions used by promoted experiments
- ⬜ save calibration + runtime metadata with captures
- ⬜ record benchmark environment (GPU, driver, CUDA, projector mode)
- ⬜ keep classical baselines next to learned approaches
- ⬜ promote experiment to core only after it beats or meaningfully extends simpler baseline

---

# No-forgetting ledger — accumulated visual/research requests

The following are explicitly retained from recent design sessions and should not silently disappear:

### Audio / performance
- multiple audio reaction presets and curated palette selector
- event-driven gating instead of noisy all-feature modulation
- beat/onset threshold knobs; smooth/balanced/punchy/chaotic modes; calm<->madness macro
- tempo/beat-phase/chroma/section awareness; scene transitions; presets; MIDI/OSC/Ableton
- eventually audio -> prompt/latent/LoRA/style state

### Human Reactor / dance video
- style/palette/edge/motion/aura/sparks/trails/echo/camera-underlay customization
- rendered-video recording, later vertical/landscape/high-quality profiles and matte/metadata outputs
- body-part emitters, limb trails, skeleton arcs, multi-person identities and depth-aware layering
- Human Reactor + audio + Cyber Mage + neural-style composition

### Cyber Mage
- glowing runic/magic circles, holographic sigils, cyber-HUD geometry
- hand/body tracked spellcasting, energy arcs/ribbons, particles, portals, aura, ground glyphs
- gesture vocabulary and intentional charge/hold/release spell state machine
- deterministic high-rate path without generative AI remains a first-class mode
- neural semantic/style skin with pose/depth/edges/energy masks and temporal state is additive, not required
- eventually spells interact with calibrated room surfaces

### Neural/video temporal consistency
- previous-frame/latent/state reuse
- optical-flow warp of previous stylized output
- cross-frame/temporal/video conditioning
- stable seed/prompt/style interpolation and low denoise
- pose/depth/segmentation/edge/object-ID conditioning
- temporal loss/video-model research, but never claim a hard consistency guarantee
- deterministic tracking/geometry is the reliability foundation

### Procedural / room visuals
- portal architecture, bioluminescent infestation, liquid cathedral, mechanical possession
- ancient ruin/living moss and ceiling starfield
- underwater caustics, alien vegetation, moving machinery, circuit/HUD structures, spatial portals
- procedural effects remain useful independently and as stable motion underneath neural keyframes

### Spatial / physical path
- fixed-room wall test, structured-light calibration, dense correspondence, photometric/radiometric calibration
- geometry/depth-aware Room Skin, semantic room, closed-loop compensation
- dynamic projection mapping to moving people/objects and later multi-projector spatial display

### Runtime/product quality
- F11 toggle; ESC exits only active visual back to console
- dependency/preflight detection, full logs, process-tree cleanup, VRAM safety
- 6 GB laptop-safe Neural Mirror plus stronger desktop profiles
- live stage status/download/load/warmup/run feedback
- live controls/preset banks without relaunch, native installers, cross-platform operation

---

# Research sweep — 2026-09-14

Detailed notes live in [`docs/research/2026-09-14.md`](docs/research/2026-09-14.md).

### High-priority research candidates
- **LiveEdit** — Apache-2.0; causal streaming edits while preserving unchanged regions. Strong M3/M4 candidate; isolated Linux/NVIDIA evaluation first.
- **LiveLight** — MIT; geometry-guided interactive relighting relevant to Room Skin/closed-loop light control.
- **LongLive 2.0** — Apache-2.0; KV-cache/async/quantization scheduling ideas; research reference for larger-GPU video runtime.
- **rusty-syphon-spout** — MIT; native Spout/Syphon abstraction reference.

### Standalone compositor / mapping tools to evaluate
- **TiXL** — MIT; Windows/DirectX graph with OSC/Spout.
- **OpenVJ** — MIT; browser/WebGL mapping with GLSL/MIDI/audio.
- **Ghost Arcade** — AGPL-3.0; WebGPU/multi-output/ISF/splats/Spout; external-app only because of license/scope.
- **Vorce** — GPL-3.0; Rust/WGPU/Bevy mapping/VJ architecture reference.

### Deferred / research-only from that sweep
- **Bucatini** — licensing unclear during sweep; do not integrate automatically.
- **Krea Realtime 14B** — non-commercial licensing + 40GB+ VRAM recommendation; research reference only.
- **RDVFI** — sparse neural motion + deterministic high-res warping idea is aligned; watch for released implementation.

---

# Current priority queue

1. **M11:** refine Cyber Mage performer rig: optional pose/hands, confidence/prediction, modular effects, gesture state machine.
2. **M3:** measure Neural Mirror 6 GB safe profile on RTX 4050 and record temporal/VRAM/latency metrics.
3. **M3/M11:** implement previous-output flow-warp temporal baseline before heavier video models.
4. **M7:** polish musical event detector, beat phase and live preset/scene transitions.
5. **M11:** extend Human Reactor with shared performer anchors and recording/presentation profiles.
6. **M1:** capture a real structured-light bundle from fixed projector/camera pair.
7. **M1/M5:** capture real radiometry data; compare LUT and learned inverse baselines.
8. **M4:** feed async neural semantic keyframes into calibrated Room Skin while procedural layers maintain display-rate motion.
9. **M2:** validate Spout end-to-end with TouchDesigner and measure copy/latency behavior on Windows.
10. **M6:** persistent semantic scene graph and cross-node interactions.
11. **M8/M9:** dynamic moving-target projection and multi-projector only after static mapping + latency metrics are reliable.

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
- E11 -> M4/M6 procedural spatial scenes
- E12 -> M11 Human Reactor
- E13 -> M11 Cyber Mage

When adding a new experiment, link it to a milestone **and update the corresponding feature track** so research prototypes, successful presets, measurements and product progress remain synchronized.
