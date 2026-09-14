# ProjectionMapping

A research playground for **projection mapping, spatial augmented reality, projector-camera calibration, learned appearance compensation, realtime generative vision, and interactive AI art**.

The projector is treated as a spatial output device, the camera as feedback, and generative models as one layer in a realtime graphics/control system.

> **Project tracking:** [`ROADMAP.md`](ROADMAP.md) is the canonical roadmap and progress tracker. It preserves the core M0–M6 plan and tracks all extension goals (audio-latent control, dynamic mapping, multi-projector work, advanced neural spatial methods, performance/evaluation, etc.).

## Supported platforms

The portable core targets **Windows, Linux, and macOS**. Capability-specific backends remain explicit:

- Windows: portable core + NVIDIA CUDA/TensorRT + Spout
- Linux: portable core + NVIDIA CUDA/TensorRT; direct fullscreen today, additional transport backends planned
- macOS: portable core + fullscreen/calibration/Room Skin; CUDA/TensorRT unavailable, Syphon is the planned native shared-texture direction

See [`docs/PLATFORMS.md`](docs/PLATFORMS.md) for the compatibility matrix and shell-specific setup instructions. The console marks unsupported features instead of attempting to launch them.

## Target setup

- Python 3.10+
- USB webcam / capture camera
- Home projector connected as another display
- Optional NVIDIA RTX-class GPU for CUDA generative paths
- Optional TouchDesigner / MadMapper
- Optional StreamDiffusion / TensorRT on Windows/Linux NVIDIA systems
- Optional Spout2 GPU texture sharing on Windows

## Operator workflow

The preferred way to use the project is the interactive console.

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[ui,vision,dev]"
python -m projection_mapping.tui
```

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[ui,vision,dev]'
python -m projection_mapping.tui
```

After installation, the shorter entry point also works:

```text
projection-ui
```

The loop is:

```text
console UI
  -> choose an effect / experiment
  -> change its parameters
  -> LAUNCH FULLSCREEN
  -> projector shows it
  -> ESC
  -> back to the console
  -> mutate settings / switch mapping / launch again
```

The console stays alive while each visual runs as a child process. If the projector window has focus, `Esc` exits that visual normally. If the terminal has focus, `Esc` terminates the active visual from the control deck. Run logs are captured under `.projection_mapping/`.

The UI is **registry-driven** by [`configs/features.toml`](configs/features.toml): new effects declare their command, supported OSs, and typed parameters there, and the console renders their controls automatically. Registry commands use a portable `python` token that is replaced with the exact active interpreter, avoiding virtualenv/conda/path mismatches across OSs.

See [`docs/CONSOLE_UI.md`](docs/CONSOLE_UI.md) for the full operator and extension guide.

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
 fullscreen / platform transport -> compositor -> projector
        |
        v
 physical room -> camera feedback
```

The intended runtime is hybrid: the projector/display loop stays responsive at display refresh while expensive generative inference runs asynchronously with **latest-frame-wins** semantics.

## Current milestone status

- **M0 — photons:** ✅ core path implemented
- **M1 — camera/projector calibration:** 🟡 structured-light and radiometric foundations implemented; real hardware capture/validation pending
- **M2 — realtime GPU transport:** 🟡 Spout/runtime scaffolding implemented; Windows zero-copy validation pending; Linux/macOS transport backends remain roadmap items
- **M3 — neural mirror:** 🟡 perception + concrete async StreamDiffusion path implemented; RTX 4080 hardware benchmark pending
- **M4 — spatially locked generation:** 🟡 first Room Skin prototype implemented; calibrated/AI-driven version pending
- **M5 — closed-loop compensation:** 🟡 inverse/optimization scaffolding and dataset capture implemented; real projector-camera dataset pending
- **M6 — semantic room:** ⬜ planned

See [`ROADMAP.md`](ROADMAP.md) for detailed deliverables, exit criteria, extension milestones M7–M10, and the current priority queue.

## Implemented foundations

- fullscreen projector test-pattern player
- clickable/keyboard Textual operator console (`projection-ui`)
- typed, extensible, platform-aware feature registry (`configs/features.toml`)
- cross-platform child-process lifecycle management with ESC-to-return workflow
- per-run log capture under `.projection_mapping/`
- grids, checkerboards, color ramps, Gray-code and phase-shift structured-light patterns
- camera capture helpers
- homography estimation and image warping
- Gray-code decoding for dense projector coordinates
- calibration bundle capture
- radiometry dataset acquisition
- per-channel radiometric LUT estimation
- PyTorch appearance-compensation MLP
- Farneback optical flow and foreground masks
- concrete asynchronous StreamDiffusion integration path
- latest-frame-wins worker and runtime telemetry
- StreamDiffusion benchmark harness
- first spatially locked Room Skin prototype
- modular realtime runtime loop
- OpenCV fullscreen sink
- Spout adapter interface + diagnostics on Windows
- reaction-diffusion GLSL shader starter
- perceptual closed-loop objective scaffolding
- tests for patterns, Gray-code, geometry, LUTs, runtime plumbing, async runtime, and feature registry

## CLI quick start

The lower-level CLI remains useful for scripting and debugging. These commands are portable after installation:

```text
# Show a projector alignment grid on display 1
python -m projection_mapping.cli patterns --kind grid --display 1

# Play a Gray-code calibration sequence
python -m projection_mapping.cli patterns --kind graycode --display 1 --hold-ms 250

# Preview camera
python -m projection_mapping.cli camera --device 0
```

## Optional realtime diffusion

Keep StreamDiffusion outside the core dependency set because its CUDA/TensorRT pins move quickly. On supported Windows/Linux NVIDIA systems:

```text
python -m pip install "git+https://github.com/daydreamlive/StreamDiffusion.git@main#egg=streamdiffusion[tensorrt,controlnet,ipadapter]"
python -m streamdiffusion.tools.install-tensorrt
```

On Windows, Spout is the preferred same-machine GPU-sharing path into TouchDesigner/MadMapper. Linux currently uses direct fullscreen for the portable path while additional transport options are explored. macOS keeps the portable renderer/calibration path and will gain a native Syphon backend separately.

## Ongoing research watch

A monthly research sweep tracks new projection-mapping, spatial-AR, realtime-generative, projector-camera, neural-rendering, and interactive-media projects. Mature, compatible open-source work may be prototyped automatically; risky/unclear/large integrations are added to the roadmap as research candidates instead.

See [`docs/RESEARCH_WATCH.md`](docs/RESEARCH_WATCH.md) for the curation and auto-integration policy.

## Docs

- [`ROADMAP.md`](ROADMAP.md) — canonical milestones, progress, priorities, and extension goals
- [`docs/CONSOLE_UI.md`](docs/CONSOLE_UI.md) — operator console, ESC/fullscreen lifecycle, feature registry, and extension format
- [`docs/PLATFORMS.md`](docs/PLATFORMS.md) — Windows/Linux/macOS support matrix and setup commands
- [`docs/RESEARCH_WATCH.md`](docs/RESEARCH_WATCH.md) — monthly research-sweep and auto-integration policy
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — system design principles and layers
- [`docs/EXPERIMENTS.md`](docs/EXPERIMENTS.md) — experiment index mapped back to roadmap milestones
- [`docs/HARDWARE_BRINGUP.md`](docs/HARDWARE_BRINGUP.md) — physical setup and bring-up order
- [`docs/RTX4080.md`](docs/RTX4080.md) — hardware-specific starting points and tuning notes
- [`docs/VISUAL_MADNESS.md`](docs/VISUAL_MADNESS.md) — artistic direction and high-intensity visual concepts
- [`docs/PROGRESS.md`](docs/PROGRESS.md) — implemented vs hardware-validated status
