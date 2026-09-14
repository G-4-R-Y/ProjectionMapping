# Progress log

This file records concrete implementation progress against `ROADMAP.md`. Hardware-dependent items remain open until validated on the actual RTX 4080 / projector / camera setup.

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
- actual feature age on the target laptop at 256 / 128 / 64 sample blocks
- microphone vs system-loopback timing comparison
- Windows WASAPI exclusive-mode comparison
- Linux PipeWire monitor latency measurement
- macOS native system-audio backend (ScreenCaptureKit) if virtual routing is insufficient
- beat-phase / tempo tracker outside the hard realtime capture path
- route features into Room Skin / shaders / particles / diffusion controls

### M3 — neural mirror / realtime generation

Implemented:
- concrete StreamDiffusion live experiment (`experiments/04_streamdiffusion_live.py`)
- async/latest-frame runtime primitives (`src/projection_mapping/async_runtime.py`)
- concrete StreamDiffusion backend adapter (`src/projection_mapping/streamdiffusion_backend.py`)
- RTX 4080 benchmark utilities (`src/projection_mapping/benchmark.py`)
- reproducible StreamDiffusion benchmark harness (`experiments/05_benchmark_streamdiffusion.py`)

Needs hardware validation:
- xformers vs TensorRT timings on RTX 4080
- SD-Turbo vs LCM operating points
- p50/p95 inference latency at 512x512, 768x432 and 960x540
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

The preferred operator path is now through `projection-ui`; the equivalent scripts remain available for debugging/reproducibility.

1. launch `projection-ui` and verify Alignment Grid on the intended display;
2. run **Audio Reactive Pulse Field** with microphone input and tune block size / attack / sensitivity;
3. repeat Audio Reactive with system/loopback audio and compare `feature_age`;
4. run the RTX 4080 benchmark feature;
5. run Spout Diagnostics into TouchDesigner;
6. collect Structured-Light Capture from the real room;
7. collect Radiometry Dataset Capture without moving the rig;
8. run Room Skin and inspect edge locking;
9. run Neural Mirror / StreamDiffusion with tuned 4080 settings;
10. merge audio buses + async StreamDiffusion output into the room-skin temporal/advection path;
11. train/apply physical appearance compensation;
12. turn the renderer toward the visual targets in `docs/VISUAL_MADNESS.md`.
