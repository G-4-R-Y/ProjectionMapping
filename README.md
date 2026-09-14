# ProjectionMapping

A research playground for **projection mapping, spatial augmented reality, projector-camera calibration, learned appearance compensation, realtime generative vision, and interactive AI art**.

The projector is treated as a spatial output device, the camera as feedback, and generative models as one layer in a realtime graphics/control system.

> **Project tracking:** [`ROADMAP.md`](ROADMAP.md) is the canonical roadmap and progress tracker. It preserves the core M0–M6 plan and tracks all extension goals (audio-latent control, dynamic mapping, multi-projector work, advanced neural spatial methods, performance/evaluation, etc.).

## Target setup

- Windows 11 + NVIDIA RTX 4080
- Python 3.10+
- USB webcam / capture camera
- Home projector connected as a second display
- Optional TouchDesigner / MadMapper
- Optional StreamDiffusion / TensorRT
- Optional Spout2 GPU texture sharing

## Architecture

```text
camera / audio / controls
        |
        v
 perception + calibration
 depth / masks / optical flow
        |
        v
 async generative inference
 diffusion / video models
        |
        v
 realtime procedural graphics
 shaders / particles / feedback
        |
        v
 compensation + spatial warp
        |
        v
 fullscreen / Spout -> TouchDesigner -> MadMapper -> projector
        |
        v
 physical room -> camera feedback
```

The intended runtime is hybrid: the projector/display loop stays responsive at display refresh while expensive generative inference runs asynchronously with **latest-frame-wins** semantics.

## Current milestone status

- **M0 — photons:** ✅ core path implemented
- **M1 — camera/projector calibration:** 🟡 structured-light and radiometric foundations implemented; real hardware capture/validation pending
- **M2 — realtime GPU transport:** 🟡 Spout/runtime scaffolding implemented; zero-copy Windows/TouchDesigner validation pending
- **M3 — neural mirror:** 🟡 perception + integration scaffolding present; concrete RTX 4080 StreamDiffusion async runtime is current priority
- **M4 — spatially locked generation:** ⬜ planned
- **M5 — closed-loop compensation:** 🟡 inverse/optimization scaffolding implemented; real projector-camera dataset pending
- **M6 — semantic room:** ⬜ planned

See [`ROADMAP.md`](ROADMAP.md) for detailed deliverables, exit criteria, extension milestones M7–M10, and the current priority queue.

## Implemented foundations

- fullscreen projector test-pattern player
- grids, checkerboards, color ramps, Gray-code and phase-shift structured-light patterns
- camera capture helpers
- homography estimation and image warping
- Gray-code decoding for dense projector coordinates
- per-channel radiometric LUT estimation
- PyTorch appearance-compensation MLP
- Farneback optical flow and foreground masks
- optional StreamDiffusion adapter with lazy imports
- modular realtime runtime loop
- OpenCV fullscreen sink
- Spout adapter interface / optional SPOUT2ForPython backend
- reaction-diffusion GLSL shader starter
- perceptual closed-loop objective scaffolding
- tests for patterns, Gray-code, geometry, LUTs, and runtime plumbing

## Quick start

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev,vision]"

# Show a projector alignment grid on display 1
projection-map patterns --kind grid --display 1

# Play a Gray-code calibration sequence
projection-map patterns --kind graycode --display 1 --hold-ms 250

# Preview camera
projection-map camera --device 0
```

## Optional realtime diffusion

Keep StreamDiffusion outside the core dependency set because its CUDA/TensorRT pins move quickly:

```powershell
pip install "git+https://github.com/daydreamlive/StreamDiffusion.git@main#egg=streamdiffusion[tensorrt,controlnet,ipadapter]"
python -m streamdiffusion.tools.install-tensorrt
```

On one Windows machine, use **Spout** for local GPU texture sharing into TouchDesigner. Use NDI when inference and display are on different machines.

## Docs

- [`ROADMAP.md`](ROADMAP.md) — canonical milestones, progress, priorities, and extension goals
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — system design principles and layers
- [`docs/EXPERIMENTS.md`](docs/EXPERIMENTS.md) — experiment index mapped back to roadmap milestones
- [`docs/RTX4080.md`](docs/RTX4080.md) — hardware-specific starting points and tuning notes
