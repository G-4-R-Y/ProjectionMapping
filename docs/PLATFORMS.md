# Platform support

ProjectionMapping is designed so the **core control UI, fullscreen projector output, calibration, camera capture, classical vision, and Room Skin path** can run on Windows, Linux, and macOS. GPU/transport features are capability-dependent rather than pretending every backend exists everywhere.

## Capability matrix

| Capability | Windows | Linux | macOS |
| --- | --- | --- | --- |
| Console UI / registry | ✅ | ✅ | ✅ |
| OpenCV fullscreen projector output | ✅ | ✅ | ✅ |
| Camera capture / structured light | ✅ | ✅ | ✅ |
| Gray-code / phase calibration | ✅ | ✅ | ✅ |
| Room Skin classical pipeline | ✅ | ✅ | ✅ |
| NVIDIA CUDA / RTX StreamDiffusion | ✅ | ✅ | ❌ |
| TensorRT | ✅ | ✅ | ❌ |
| Spout shared textures | ✅ | ❌ | ❌ |
| TouchDesigner | ✅ | platform/version dependent | ✅ |
| Syphon | ❌ | ❌ | planned / native macOS option |
| NDI/network transport | planned | planned | planned |

The console reads `platforms = [...]` from `configs/features.toml`. Unsupported features remain visible for discoverability but cannot be launched accidentally.

## Portable install

Use Python 3.10+ from the repository root. The commands below intentionally use `python -m ...` so they work in virtualenvs/conda and do not depend on platform-specific script shims.

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[ui,vision,dev]"
python -m projection_mapping.tui
```

If `python` does not select the desired version, the Windows launcher is also valid:

```powershell
py -3.10 -m venv .venv
```

### Windows cmd.exe

```bat
python -m venv .venv
.venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -e ".[ui,vision,dev]"
python -m projection_mapping.tui
```

### Linux / macOS shell

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[ui,vision,dev]'
python -m projection_mapping.tui
```

After installation the shorter entry points should also work on every OS:

```text
projection-ui
projection-map
```

The documentation prefers `python -m ...` when reliability across shells matters.

## StreamDiffusion / CUDA

The current realtime neural path targets **NVIDIA CUDA**, so it is supported on Windows and Linux. Install PyTorch using the command appropriate for the local driver/CUDA environment, then install StreamDiffusion as described in `docs/RTX4080.md`.

Do not assume one pinned CUDA wheel is right for every machine. Record the driver, CUDA runtime, PyTorch version, GPU, and acceleration backend with benchmark results.

macOS can still run the classical/procedural portions of the project. A future Metal/MPS-compatible generative backend should be implemented as a separate generator rather than forcing CUDA-specific code into the portable core.

## Transport strategy by OS

### Windows
Preferred same-machine path: **Spout** -> TouchDesigner/MadMapper. Fullscreen OpenCV remains the bring-up fallback.

### Linux
Use direct fullscreen output today. NDI/network transport and native OpenGL/Vulkan shared-texture options are roadmap items. StreamDiffusion/CUDA can run locally even when the final transport is not Spout.

### macOS
Use direct fullscreen output today. **Syphon** is the natural native shared-texture direction for a future macOS backend. Do not expose Spout controls as if they were portable.

## Display placement caveat

Several current OpenCV experiments still use display-index assumptions when positioning fullscreen windows. Automatic monitor enumeration and geometry-aware placement remain roadmap items. Until that lands, verify projector placement with the Alignment Grid before calibration or a long capture.

## Adding a feature

If a feature is portable, omit `platforms`:

```toml
[[feature]]
id = "portable_visual"
command = ["python", "experiments/portable_visual.py"]
```

If it depends on a platform-specific backend:

```toml
[[feature]]
id = "spout_probe"
command = ["python", "experiments/spout_probe.py"]
platforms = ["windows"]
```

Accepted names are `windows`, `linux`, and `macos`.

## Rule for documentation

Whenever a new command is documented:

1. prefer `python -m pip` over bare `pip`;
2. prefer `python -m module` where a module entry point exists;
3. show shell-specific activation only when activation is actually necessary;
4. label CUDA, Spout, Syphon, NDI, camera-driver, and projector-driver assumptions explicitly;
5. never present a Windows-only backend as a project-wide requirement.
