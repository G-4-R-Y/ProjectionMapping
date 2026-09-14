# ProjectionMapping Roadmap

This is the canonical roadmap for the project. Milestone numbering **M0–M6 is stable** and follows the original plan. Additional research/art goals live under extension milestones so they do not get lost or silently replace the core path.

Legend: **✅ done / implemented** · **🟡 implemented but needs integration or hardware validation** · **⬜ planned** · **🧪 research / stretch**

## North star

Build a home-scale spatial generative system where the projector is a programmable light source, the camera is feedback, and realtime graphics + generative models can alter the perceived material/behavior of the room while remaining geometrically registered to the physical world.

Preferred runtime architecture:

`camera / audio / controls -> perception -> async generative inference -> procedural realtime graphics -> compensation / warp -> GPU/native transport or fullscreen -> projector -> camera feedback`

The display loop must remain responsive even when AI inference is slower than refresh rate. **Latest-frame-wins**, bounded queues, process isolation, and hardware-measured latency are first-class requirements.

The operator experience is the persistent `projection-ui` control deck: configure -> launch fullscreen -> ESC -> reconfigure -> launch again. Long term, live IPC/OSC/MIDI control should allow parameters to change without restarting the renderer.

---

## M0 — photons ✅

**Goal:** Python generates a realtime test pattern -> fullscreen projector.

### Deliverables
- ✅ fullscreen projector output
- ✅ grid / checkerboard / color-ramp patterns
- ✅ Gray-code and phase-shift pattern generation
- ✅ selectable projector display
- ✅ basic camera preview
- ✅ console control deck / feature registry
- ⬜ automatic display enumeration instead of fixed pixel offsets
- ⬜ projector capability report: native resolution, refresh rate, overscan, HDR/color mode, latency notes
- ⬜ latency-flash test pattern for camera/projector timing measurements

### Exit criterion
A deterministic framebuffer can be shown fullscreen on the actual projector at known resolution/refresh with repeatable display placement.

---

## M1 — camera/projector calibration 🟡

**Goal:** Gray-code / structured-light correspondence and projector<->camera homography / dense warp.

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
- ✅ camera capture abstraction
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
Given a camera pixel on a valid observed surface, recover where to emit light in projector coordinates with measured confidence/error, and reproduce a requested color substantially better than the uncompensated baseline.

---

## M2 — realtime GPU transport 🟡

**Goal:** generated GPU output -> native/shared texture transport -> compositor/projector, with no unnecessary encode/decode step.

### Deliverables
- ✅ Spout sender abstraction
- ✅ fullscreen fallback path
- ✅ modular source / processor / sink runtime
- ✅ deterministic Spout diagnostics experiment
- ✅ platform-aware feature registry
- ✅ optional external-tool command detection in the console
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
- ✅ child renderer isolation from the persistent console
- 🟡 latency/throughput telemetry primitives and benchmark reports
- ⬜ full per-stage timestamps through capture -> scanout
- ⬜ GPU memory telemetry

### Exit criterion
A generated GPU frame reaches the compositor/projector with stable realtime throughput and without encode/decode or unnecessary host copies.

---

## M3 — neural mirror 🟡

**Goal:** camera -> segmentation/depth/flow -> realtime generative transformation -> projector.

### Perception
- ✅ foreground mask baseline
- ✅ Farneback optical flow baseline
- ⬜ semantic segmentation backend
- ⬜ monocular depth backend
- ⬜ pose / hand tracking backend
- ⬜ optional depth-camera input

### StreamDiffusion / generative runtime
- ✅ generic StreamDiffusion integration wrapper
- ✅ concrete Daydream StreamDiffusion backend adapter
- ✅ async latest-frame-wins worker
- ✅ live camera -> async StreamDiffusion experiment
- ✅ reproducible RTX benchmark harness with JSON reports
- 🟡 xformers / SD-Turbo operating point implemented but not measured on the real RTX 4080
- ⬜ TensorRT engine build + measured runtime path
- ⬜ live prompt/seed/style updates over IPC
- ⬜ similarity filtering for low-motion frames
- ⬜ ControlNet hooks for depth / edges / pose
- ⬜ TemporalNet / StreamV2V evaluation for temporal coherence

### Hybrid rendering
- ✅ room-skin temporal/advection primitives establish the hybrid direction
- ⬜ diffusion supplies semantic keyframes directly into room-skin
- ⬜ GLSL / particles / feedback produce stable 60+ FPS motion between AI keyframes
- ⬜ mask-aware compositing per person / background / object

### Exit criterion
A live camera feed is semantically transformed by a realtime model, projected back into the room, while the output display remains smooth even when inference FPS is lower than projector refresh.

---

## M4 — spatially locked generation 🟡

**Goal:** preserve scene geometry while generatively changing material / appearance. This is the **room skin** milestone.

### Deliverables
- ✅ physical-edge locking primitives
- ✅ optical-flow advection between semantic keyframes
- ✅ temporal blending
- ✅ standalone room-skin prototype with procedural fallback
- ⬜ capture a clean room reference + calibrated projector coordinates
- ⬜ construct geometric/depth priors for the scene
- ⬜ condition generation on depth / normal / edge / segmentation maps
- ⬜ object-space or UV-like canonicalization for static surfaces
- ⬜ texture-space generation so bookshelf/wall/door keep their physical shape
- ⬜ procedural shaders/particles/feedback between AI keyframes
- ⬜ quantitative registration metric: generated feature edge vs physical edge

### Visual targets
- wall -> underwater caustics / architecture / organic material
- bookshelf -> stone / machinery / bioluminescent growth
- plants -> alien vegetation
- door -> portal / depth illusion
- room surfaces -> coherent material transformations instead of rectangular video

### Exit criterion
A static room surface can change apparent material/semantics while its important physical edges remain visually registered over time.

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

---

## M6 — semantic room ⬜

**Goal:** detect surfaces / objects and assign independently controllable generative behaviors.

### Scene understanding
- ⬜ wall / ceiling / floor segmentation
- ⬜ furniture / plants / people / doors / windows
- ⬜ instance tracking across frames
- ⬜ depth-aware occlusion relationships
- ⬜ persistent semantic scene graph

### Effect graph
- ⬜ independent shader / diffusion graph per object or region
- ⬜ priorities and occlusion rules
- ⬜ composable masks
- ⬜ persistent object identities
- ⬜ per-object prompt / LoRA / material controls
- ⬜ live controls via OSC / MIDI / gamepad / phone

### Example behavior map
- wall -> slow procedural environment
- plants -> generative glowing vegetation
- person -> neural mirror / silhouette effects
- bookshelf -> mechanical/material transformation
- ceiling -> stars / volumetric field
- hands -> particle/fluid emitters

### Exit criterion
Multiple physical objects/surfaces in one room can simultaneously run different spatially registered effects with stable identity and controllable behavior.

---

# Extension milestones

## M7 — audio-latent instrument ⬜

**Goal:** make the system a performable audiovisual instrument, not an FFT-to-brightness visualizer.

- ⬜ beat / onset / chroma / spectral features
- ⬜ audio embeddings
- ⬜ map audio to prompt embeddings / latent directions
- ⬜ LoRA weight interpolation
- ⬜ seed / style interpolation
- ⬜ shader / particle / feedback modulation
- ⬜ MIDI / OSC control surface
- ⬜ Ableton integration experiment

Exit criterion: musical structure produces coherent, repeatable changes in semantic appearance and realtime motion.

---

## M8 — dynamic projection mapping ⬜

**Goal:** keep projection registered on moving objects.

- ⬜ full motion-to-photon latency measurement
- ⬜ planar target tracking baseline
- ⬜ pose prediction over measured latency
- ⬜ realtime homography update
- ⬜ moving hand/body target experiments
- ⬜ registration error vs target speed benchmark
- 🧪 high-speed camera/projector path if consumer hardware becomes the bottleneck

Exit criterion: projection remains acceptably registered on a moving target with quantified latency/error.

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

**Goal:** track emerging research that can materially improve the installation without destabilizing the practical M0–M6 path.

- 🧪 StreamDiffusionV2 / streaming video-diffusion evaluation
- 🧪 distilled / quantized video models for single-4080 deployment
- 🧪 Gaussian splats / NeRF-like room representation
- 🧪 4D scene representations for moving content
- 🧪 neural material / inverse-rendering representations
- 🧪 learned projector-camera calibration
- 🧪 semantic optimization directly in physical appearance space
- 🧪 structure-preserving streaming video editing / relighting
- 🧪 sparse neural keyframes + high-rate deterministic warping/interpolation

These are not blockers for M0–M6; pull them forward only when they beat simpler baselines on our hardware or unlock a qualitatively new visual capability.

---

# Cross-cutting engineering goals

## Performance / reliability
- ✅ renderer process isolation behind the persistent console UI
- ✅ bounded latest-frame-wins worker
- ✅ benchmark report utilities
- ✅ cross-platform CI matrix: Windows/Linux/macOS × Python 3.10/3.12
- ⬜ benchmark every physical stage separately: capture, perception, inference, compositing, transport, scanout
- ⬜ p50 / p95 / p99 end-to-end latency logging
- ⬜ GPU memory telemetry
- ⬜ deterministic benchmark scenes
- ⬜ hot-reload prompts / configs without restarting display

## Evaluation
- ⬜ geometric registration error
- ⬜ radiometric error before/after compensation
- ⬜ temporal flicker / consistency metrics
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
- ⬜ optional ComfyUI only as an experimental model graph, not the core runtime architecture

## Research discipline
- ✅ monthly research-watch policy documented
- ✅ external command availability can be represented in the feature registry
- ⬜ pin model/repository revisions used by promoted experiments
- ⬜ save calibration + runtime metadata with captures
- ⬜ record benchmark environment (GPU, driver, CUDA, projector mode)
- ⬜ keep classical baselines next to learned approaches
- ⬜ promote an experiment to core only after it beats or meaningfully extends a simpler baseline

---

# Research sweep — 2026-09-14

Detailed notes live in [`docs/research/2026-09-14.md`](docs/research/2026-09-14.md).

### High-priority research candidates

- **LiveEdit** — <https://github.com/cp-cp/LiveEdit> — Apache-2.0, code/checkpoints released June 2026, long-stream update August 2026. Strong M3/M4 candidate because it performs causal streaming edits while preserving unchanged regions. Linux/NVIDIA-first; evaluate separately before integrating into the Python 3.12 control environment.
- **LiveLight** — <https://github.com/mayuelala/LiveLight> — MIT, code/weights released July 2026. Interactive 3D point-light relighting with geometry-guided streaming consistency is directly relevant to M4 room-skin and future M5 perceptual-light control. CUDA/Python-3.10 research environment; benchmark before promotion.
- **LongLive 2.0** — <https://github.com/airobotcode/longlive> — Apache-2.0. Useful source of KV-cache, async decode, quantization, and long-stream scheduling ideas for M10; current performance work targets much larger GPUs than the RTX 4080, so do not make it a runtime dependency.
- **rusty-syphon-spout** — <https://github.com/geepot/rusty-syphon-spout> — MIT. Interesting M2 reference for a native Windows Spout / macOS Syphon abstraction with platform CI and runtime roundtrip tests. Consider a small native sidecar later rather than embedding Rust into the core Python package immediately.

### Standalone compositor / mapping tools to evaluate

- **TiXL** — <https://github.com/tixl3d/tixl> — MIT, actively updated August 2026, mature Windows/DirectX realtime motion-graphics graph with OSC/Spout. Strong TouchDesigner-alternative experiment for Windows, especially M7 procedural/audio work.
- **OpenVJ** — <https://github.com/kniessner/openvj> — MIT browser/WebGL projection mapper with GLSL, MIDI, p5.js and audio-reactive generation. Cross-platform and easy to inspect, but still beta/small; evaluate as a lightweight mapping frontend rather than a dependency.
- **Ghost Arcade** — <https://github.com/riskcapital/ghost-arcade> — AGPL-3.0, WebGPU, multi-output mapping, ISF, point clouds/splats and Spout. Technically compelling, but keep as a standalone external application because of license coupling and overlapping scope.
- **Vorce** — <https://github.com/Vorce-Studios/Vorce> — GPL-3.0 Rust/WGPU/Bevy mapping/VJ tool. Interesting architecture and audio/3D ideas, but currently early-stage; watch rather than integrate.

### Deferred / rejected this sweep

- **Bucatini** — <https://github.com/naporin0624/bucatini> — excellent NDI -> Syphon/Spout bridge concept, macOS hardware-tested and Windows CI-compile-tested, but no clear top-level project license was found during this sweep. Do not auto-integrate until licensing is explicit.
- **Krea Realtime 14B** — <https://github.com/krea-ai/realtime-video> — impressive streaming architecture, but CC BY-NC-SA licensing and 40GB+ VRAM recommendation make it unsuitable for the practical RTX-4080 path. Research reference only.
- **RDVFI** — <https://github.com/Mayongrui/RDVFI> — the sparse diffusion motion + deterministic high-resolution warping idea is highly aligned with our hybrid renderer, but the repository currently exposes a project page rather than released implementation code. Watch for code release.

---

# Current priority queue

1. **M3:** run the StreamDiffusion benchmark harness on the actual RTX 4080 and record xformers/TensorRT operating points.
2. **M2:** validate Spout end-to-end with TouchDesigner and measure copy/latency behavior.
3. **M1:** capture a real structured-light bundle from the fixed projector/camera pair.
4. **M1/M5:** capture real radiometry data; fit and compare LUT and learned inverse baselines.
5. **M4:** feed async StreamDiffusion keyframes into the room-skin optical-flow/edge-lock path using calibrated projector coordinates.
6. **M3/M4 research:** test LiveEdit/LiveLight in isolated environments only after the baseline path works.
7. **M6:** semantic scene graph and per-object effect routing.
8. **M7/M8:** audio instrument and moving-target projection once the static spatial pipeline is robust.

---

# Experiment mapping

- E00 -> M0 photons
- E01 -> M1 dense correspondence
- E02 -> M1 radiometry / M5 baseline
- E03 -> M5 learned inverse display
- E04 -> M3 neural mirror
- E05 -> M4 room skin
- E06 -> M6 semantic room
- E07 -> M5 perceptual closed-loop control
- E08 -> M7 audio-latent instrument
- E09 -> M8 dynamic projection

When adding a new experiment, link it to a milestone here so research prototypes and product progress remain synchronized.
