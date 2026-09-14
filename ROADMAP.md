# ProjectionMapping Roadmap

This is the canonical roadmap for the project. Milestone numbering **M0–M6 is stable** and follows the original plan. Additional research/art goals live under extension milestones so they do not get lost or silently replace the core path.

Legend: **✅ done** · **🟡 in progress / scaffolded** · **⬜ planned** · **🧪 research / stretch**

## North star

Build a home-scale spatial generative system where the projector is a programmable light source, the camera is feedback, and realtime graphics + generative models can alter the perceived material/behavior of the room while remaining geometrically registered to the physical world.

The preferred runtime architecture is hybrid rather than diffusion-only:

`camera / audio / controls -> perception -> async generative inference -> procedural realtime graphics -> compensation / warp -> Spout / fullscreen -> projector -> camera feedback`

The display loop should remain responsive even when AI inference is slower than refresh rate; **latest-frame-wins** semantics and asynchronous inference are first-class requirements.

---

## M0 — photons ✅

**Goal:** Python generates a realtime test pattern -> fullscreen projector.

### Deliverables
- ✅ fullscreen projector output
- ✅ grid / checkerboard / color-ramp patterns
- ✅ Gray-code and phase-shift pattern generation
- ✅ selectable projector display
- ✅ basic camera preview
- ⬜ automatic display enumeration instead of fixed 1920px offsets
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
- 🟡 structured-light capture experiment
- ⬜ confidence-aware dense projector->camera correspondence map
- ⬜ camera->projector inverse map with hole filling / validity masks
- ⬜ phase-shift refinement for subpixel correspondence
- ⬜ calibration bundle serialization with camera/projector metadata
- ⬜ reprojection-error diagnostics and visual QA overlays

### Camera / photometric calibration
- ✅ camera capture abstraction
- ⬜ exposure/gain/white-balance locking helpers
- ⬜ lens distortion calibration / undistortion
- ⬜ projector intrinsic/extrinsic calibration where useful
- ⬜ synchronization / exposure timing characterization

### Attached goal: radiometry
- ✅ per-channel monotonic inverse-LUT baseline
- ⬜ automated RGB intensity-sweep acquisition
- ⬜ spatially varying radiometric model
- ⬜ ambient-light compensation
- ⬜ defocus compensation baseline
- ⬜ shadow / occlusion masks

### Exit criterion
Given a camera pixel on a valid observed surface, recover where to emit light in projector coordinates with measured confidence/error, and reproduce a requested color substantially better than the uncompensated baseline.

---

## M2 — realtime GPU transport 🟡

**Goal:** PyTorch output -> Spout -> TouchDesigner, with no encode/decode step.

### Deliverables
- ✅ Spout sender abstraction
- ✅ fullscreen fallback path
- ✅ modular source / processor / sink runtime
- ⬜ concrete, tested Spout2 Windows backend
- ⬜ PyTorch/CUDA -> shared GPU texture path
- ⬜ verify no CPU readback in production path
- ⬜ TouchDesigner receiver example/project
- ⬜ MadMapper handoff example via Spout
- ⬜ optional NDI transport for multi-machine setups
- ⬜ transport benchmark: throughput, frame latency, CPU/GPU copy counts

### Runtime goals
- ⬜ independent capture, inference, compositing, and output clocks
- ⬜ bounded queues
- ⬜ latest-frame-wins dropping policy
- ⬜ per-stage timestamps and latency telemetry
- ⬜ graceful restart if the ML worker crashes

### Exit criterion
A generated GPU frame reaches TouchDesigner/projector with stable realtime throughput and without encode/decode or unnecessary host copies.

---

## M3 — neural mirror 🟡

**Goal:** camera -> segmentation/depth/flow -> StreamDiffusion -> projector.

### Perception
- ✅ foreground mask baseline
- ✅ Farneback optical flow baseline
- ⬜ semantic segmentation backend
- ⬜ monocular depth backend
- ⬜ pose / hand tracking backend
- ⬜ optional depth-camera input

### StreamDiffusion / generative runtime
- ✅ generic StreamDiffusion integration wrapper
- ✅ neural-mirror experiment scaffold
- 🟡 concrete Daydream StreamDiffusion runtime integration
- ⬜ async inference worker with latest-frame-wins input
- ⬜ model warmup and live prompt/seed/style updates
- ⬜ benchmark SD-Turbo / LCM paths on RTX 4080
- ⬜ TensorRT engine build + runtime path
- ⬜ runtime FPS / p50 / p95 inference latency logging
- ⬜ similarity filtering for low-motion frames
- ⬜ ControlNet hooks for depth / edges / pose
- ⬜ TemporalNet / StreamV2V evaluation for temporal coherence

### Hybrid rendering
- ⬜ diffusion supplies semantic appearance/keyframes
- ⬜ GLSL / particles / feedback produce stable 60+ FPS motion
- ⬜ temporal compositing that hides slower AI update rate
- ⬜ mask-aware compositing per person / background / object

### Exit criterion
A live camera feed is semantically transformed by a realtime model, projected back into the room, while the output display remains smooth even when inference FPS is lower than projector refresh.

---

## M4 — spatially locked generation ⬜

**Goal:** preserve scene geometry while generatively changing material / appearance.

This is the **room skin** milestone.

### Deliverables
- ⬜ capture a clean room reference
- ⬜ construct geometric/depth priors for the scene
- ⬜ maintain physical edges under generative transformation
- ⬜ condition generation on depth / normal / edge / segmentation maps
- ⬜ use optical flow / feature tracking to stabilize material identity over time
- ⬜ object-space or UV-like canonicalization for static surfaces
- ⬜ texture-space generation so the bookshelf/wall/door keeps its physical shape
- ⬜ procedural warp/feedback between AI keyframes
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
- ⬜ automated `(projected pattern, camera observation)` dataset capture
- ⬜ compare LUT vs neural inverse model

### Learned physical display model
- ⬜ learn forward model `C(P, surface, illumination)`
- ⬜ learn inverse model for desired observed appearance
- ⬜ spatially varying compensation
- ⬜ differentiable surrogate for projector-camera response
- ⬜ online refinement from camera feedback

### Perceptual control
- ⬜ RGB / L1-L2 objective baseline
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

These were discussed alongside M0–M6 and are intentionally tracked here rather than left as loose ideas.

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

**Goal:** track emerging research that can materially improve the installation.

- 🧪 StreamDiffusionV2 / streaming video-diffusion evaluation
- 🧪 distilled / quantized video models for single-4080 deployment
- 🧪 Gaussian splats / NeRF-like room representation
- 🧪 4D scene representations for moving content
- 🧪 neural material / inverse-rendering representations
- 🧪 learned projector-camera calibration
- 🧪 semantic optimization directly in physical appearance space

These are not blockers for M0–M6; they should be pulled forward only when they beat simpler baselines.

---

# Cross-cutting engineering goals

## Performance / reliability
- ⬜ benchmark every stage separately: capture, perception, inference, compositing, transport, scanout
- ⬜ p50 / p95 / p99 latency logging
- ⬜ GPU memory telemetry
- ⬜ frame-drop / queue-depth telemetry
- ⬜ deterministic benchmark scenes
- ⬜ hot-reload prompts / configs without restarting display
- ⬜ crash isolation between ML worker and projection output

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
- ⬜ optional ComfyUI only as an experimental model graph, not the core runtime architecture

## Research discipline
- ⬜ pin model/repository revisions used by experiments
- ⬜ save calibration + runtime metadata with captures
- ⬜ record benchmark environment (GPU, driver, CUDA, projector mode)
- ⬜ keep classical baselines next to learned approaches
- ⬜ promote an experiment to core only after it beats or meaningfully extends a simpler baseline

---

# Current priority queue

1. **M3:** finish concrete StreamDiffusion integration for the RTX 4080.
2. **M3/M2:** implement asynchronous latest-frame-wins inference and per-stage telemetry.
3. **M2:** validate Spout transport end-to-end with TouchDesigner and remove avoidable host copies.
4. **M1:** capture a real structured-light dataset from the home projector/camera pair.
5. **M1/M5:** fit radiometric and learned compensation baselines from real captures.
6. **M4:** spatially locked room-skin prototype.
7. **M6:** semantic scene graph and per-object effect routing.
8. **M7/M8:** audio instrument and moving-target projection once the static spatial pipeline is robust.

---

# Experiment mapping

The experiments in `docs/EXPERIMENTS.md` map to milestones as follows:

- E00 -> M0
- E01 -> M1 geometry
- E02 -> M1 radiometry / M5 baseline
- E03 -> M5 learned inverse display
- E04 -> M3 neural mirror
- E05 -> M4 room skin
- E06 -> M6 semantic room
- E07 -> M5 perceptual closed-loop control
- E08 -> M7 audio-latent instrument
- E09 -> M8 dynamic projection

When adding a new experiment, link it to a milestone here so research prototypes and product progress remain synchronized.
