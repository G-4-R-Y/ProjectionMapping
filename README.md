# ProjectionMapping

A research playground for **projection mapping, spatial augmented reality, projector-camera calibration, learned appearance compensation, realtime generative vision, and interactive AI art**.

The projector is treated as a spatial output device, the camera as feedback, and generative models as one layer in a realtime graphics/control system.

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
 generative / procedural layer
 diffusion / shaders / feedback
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

## Implemented

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

## Suggested experiments

1. **Neural mirror** — webcam -> mask/depth/flow -> realtime diffusion -> projection.
2. **Room skin** — preserve scene geometry while changing material semantics.
3. **Closed-loop compensation** — learn what pixels must be emitted so the camera sees a target appearance.
4. **Semantic room** — segment wall/furniture/people and assign different effects per region.
5. **Audio-latent instrument** — drive latent/style/control parameters from beat/onset/spectral features.
6. **Dynamic mapping** — track moving targets and compensate latency with prediction.

See `docs/ARCHITECTURE.md` and `docs/EXPERIMENTS.md`.
