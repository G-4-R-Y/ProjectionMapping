# Progress log

This file records concrete implementation progress against `ROADMAP.md`. Hardware-dependent items remain open until validated on the actual target hardware.

## 2026-09-15

### Research/feature-track discipline

Implemented:
- canonical fine-grained research ledger under `docs/feature_tracks/`
- dedicated tracks for Audio/Audiovisual, Human Reactor, Cyber Mage, Neural Mirror, Room Skin, Calibration/Mapping, Compensation, Runtime/Transport/UI, and Semantic Room
- each track records north star, current state, quality ladder, open problems, next queue, metrics and preset/operating-point knowledge
- `ROADMAP.md` now links the tracks and contains a no-forgetting ledger of recent visual/research requests
- experiment mapping extended through E13

### M11 — performer instrument / Cyber Mage

Implemented:
- `src/projection_mapping/performer_rig.py`: persistent classical performer rig with semantic anchors for head, chest/core, hands and feet
- initial gesture state: arms spread, hands together, hands raised, motion burst
- `src/projection_mapping/cyber_mage_fx.py`: deterministic body-owned sigils, plasma arcs, trails, aura, charge orb and ground glyph
- `experiments/13_cyber_mage.py`: camera -> segmentation/flow -> performer rig -> spell renderer -> projector
- TUI registry entry with palette, intensity, complexity, trail length, feedback, rig smoothing, camera underlay and mirror controls
- synthetic performer-rig unit tests

Next:
- optional pose/hand landmark backend behind the same `PerformerRig` interface
- confidence-aware loss/reacquisition and predictive smoothing
- composable Sigil/Arc/Trail/Emitter/Aura/Portal/GroundGlyph modules
- GLSL/SDF rune atlas and GPU particles
- gesture state machine with charge/hold/release, cast, shield, swipe, spin, jump and crouch
- audio/gesture fusion and room-targeted spells
- flow-warped low-denoise neural style skin without surrendering deterministic spatial ownership

### Neural Mirror / temporal consistency

Implemented since previous log:
- optional xFormers fallback to native PyTorch attention
- safe 6 GB laptop profile at lower inference resolution / bounded submission rate
- explicit startup stages for preflight, model load/download, prepare, warmup, ready and running
- benchmark path uses same guarded backend/fallback

Next:
- measure safe-profile latency/VRAM on RTX 4050 Laptop
- previous-neural-frame optical-flow warp baseline
- stable seed/style bank and gradual prompt interpolation
- mask-aware person/background/energy compositing
- pose/depth/edge controls
- TemporalNet/StreamV2V evaluation only after the simpler temporal baseline is measured

### M7 — Audio Reactive Studio

Implemented since previous log:
- Linux native Pulse/PipeWire monitor capture (`pactl`/`parec`) for reliable system audio
- curated multi-scene Audio Reactive Studio
- multiple palettes and smooth/balanced/punchy/chaotic reactivity modes
- musical-event gating instead of indiscriminate FFT modulation
- Calm<->Madness macro and configurable event thresholds

Next:
- stronger adaptive peak picking and minimum-event spacing
- tempo/beat phase, chroma/key and section/drop descriptors
- live scene/palette transitions and preset banks
- MIDI/OSC/Ableton integration

### Human Reactor

Implemented since previous log:
- multiple styles/palettes
- independent edge/motion/aura/spark/feedback controls
- temporal silhouette echoes
- mirror and camera-underlay controls
- rendered-video recording path

Next:
- share performer anchors with Cyber Mage
- joint/body-axis emitters and skeleton arcs
- portrait/landscape/high-quality recording profiles and mask/matte outputs
- multi-performer IDs and depth-aware layering

---

## 2026-09-14

### Operator console / control plane

Implemented:
- clickable + keyboard Textual console (`projection-ui`)
- registry-driven feature catalog (`configs/features.toml`)
- typed per-feature controls: text, int, float, bool, choice
- safe argv generation without a shell (`src/projection_mapping/feature_registry.py`)
- one-active-feature child-process lifecycle (`src/projection_mapping/launcher.py`)
- fullscreen launch -> `Esc` -> console interaction model
- terminal-focus `Esc` can terminate the active child
- stdout/stderr capture under `.projection_mapping/`
- UI status polling and last-run log view
- feature-registry unit tests
- operator/extension documentation (`docs/CONSOLE_UI.md`)
- architecture updated to explicitly separate control plane from render/data plane

Current feature categories exposed:
- Visual Madness
- Projector Setup
- Calibration
- Diagnostics

Current UI-visible features include Audio Reactive Pulse Field, Room Skin, live StreamDiffusion / Neural Mirror, baseline neural mirror, alignment grid, structured-light capture, radiometry capture, Spout diagnostics, and the RTX 4080 benchmark.

Next operator-surface work:
- persistent named presets per feature
- inherited global projector/camera profiles
- global MADNESS macro
- live parameter updates through local IPC / OSC without restarting renderer
- preview thumbnails
- MIDI / gamepad / phone bindings
- audio input controls/meters
- calibration profile picker
- semantic-room object/effect routing UI
- playlists / timed transitions / generative preset mutation
- emergency blackout control

### M7 — audio-latent instrument

Implemented:
- low-latency native-audio capture path via SoundCard/CFFI (`src/projection_mapping/audio_reactive.py`)
- microphone / line-input mode
- system/loopback mode where the platform exposes output-monitor inputs
- latest-only audio feature stream: no accumulating audio-analysis queue
- RMS, bass, mid, treble, spectral centroid, spectral flux and onset features
- configurable attack/release/sensitivity and audio block size
- first fullscreen music-reactive procedural visual (`experiments/10_audio_reactive.py`)
- control-deck entry with source/device/latency/art controls
- audio feature extractor unit tests
- cross-platform latency/setup guide (`docs/AUDIO_REACTIVE.md`)

Needs wall/audio hardware validation:
- actual feature age on target laptop at 256 / 128 / 64 sample blocks
- microphone vs system-loopback timing comparison
- Windows WASAPI exclusive-mode comparison
- Linux PipeWire monitor latency measurement
- macOS native system-audio backend if virtual routing is insufficient
- beat-phase / tempo tracker outside hard realtime capture path
- route features into Room Skin / shaders / particles / diffusion controls

### M3 — neural mirror / realtime generation

Implemented:
- concrete StreamDiffusion live experiment (`experiments/04_streamdiffusion_live.py`)
- async/latest-frame runtime primitives (`src/projection_mapping/async_runtime.py`)
- concrete StreamDiffusion backend adapter (`src/projection_mapping/streamdiffusion_backend.py`)
- RTX benchmark utilities (`src/projection_mapping/benchmark.py`)
- reproducible StreamDiffusion benchmark harness (`experiments/05_benchmark_streamdiffusion.py`)

Needs hardware validation:
- xformers vs TensorRT timings on RTX 4080
- SD-Turbo vs LCM operating points
- p50/p95 inference latency at multiple resolutions
- prompt/style hot updates under load
- ControlNet/TemporalNet/StreamV2V temporal-quality comparison

### M2 — realtime GPU transport

Implemented:
- Spout abstraction
- animated Spout diagnostic stream (`experiments/06_spout_diagnostics.py`)
- explicit no-growing-queue architecture

Needs hardware validation:
- actual Spout binding/API on Windows
- TouchDesigner receive path
- copy-count / CPU-readback inspection
- transport latency

### M1 — projector-camera calibration

Implemented:
- richer reusable calibration-bundle format (`src/projection_mapping/calibration_bundle.py`)
- capture of black/white references + Gray-code + phase-shift frames (`experiments/07_capture_calibration_bundle.py`)
- capture metadata and timestamps

Needs hardware data:
- real room capture
- dense decode + confidence map
- inverse camera-to-projector map
- reprojection-error QA
- locked exposure / white balance

### M5 — closed-loop appearance compensation

Implemented:
- automated radiometry dataset capture (`experiments/08_capture_radiometry_dataset.py`)
- grayscale sweeps
- independent RGB sweeps
- deterministic random RGB patch fields
- existing LUT + learned-MLP compensation scaffolds

Needs hardware data:
- capture real projector/surface response
- fit LUT baseline
- train/evaluate learned inverse model
- held-out error comparison
- later perceptual losses and online refinement

### M4 — spatially locked generation / room skin

Implemented:
- physical-edge locking primitives (`src/projection_mapping/room_skin.py`)
- optical-flow advection between semantic keyframes
- temporal blending
- first standalone room-skin experiment (`experiments/09_room_skin.py`)
- visual-direction playbook (`docs/VISUAL_MADNESS.md`)

Next integration:
- replace procedural candidate frames with async StreamDiffusion keyframes
- use calibrated projector coordinates rather than raw camera geometry
- add depth/edge conditioning
- feed reaction-diffusion / particles / feedback between neural updates
- apply learned radiometric compensation before output

## Current bring-up order

The preferred operator path is through `projection-ui`; equivalent scripts remain available for debugging/reproducibility.

1. launch `projection-ui` and verify Alignment Grid on intended display;
2. validate Audio Reactive Studio with system audio and inspect feature/event telemetry;
3. test Human Reactor and Cyber Mage camera/performer paths;
4. run Neural Mirror / 6GB Safe and record stage/inference/VRAM telemetry;
5. collect Structured-Light Capture from the real room;
6. collect Radiometry Dataset Capture without moving the rig;
7. run Room Skin and inspect edge locking;
8. validate Spout into TouchDesigner on Windows;
9. merge performer/audio buses + async neural keyframes into stable deterministic rendering;
10. train/apply physical appearance compensation;
11. move toward the semantic-room and dynamic-mapping targets in `ROADMAP.md`.
