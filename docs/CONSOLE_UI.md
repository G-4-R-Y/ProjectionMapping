# ProjectionMapping Control Deck

The browser control deck is the primary operator surface for the installation. It runs on localhost
without a frontend service or framework dependency. The intended loop is intentionally simple:

```text
browser control deck
  -> choose feature
  -> edit parameters
  -> launch fullscreen on projector
  -> experience / inspect result
  -> ESC
  -> back to the same browser form and values
  -> mutate config
  -> launch again
```

The goal is to make experimentation feel like playing an instrument instead of repeatedly editing command lines.

## Install

The UI runs on Windows, Linux, and macOS. Use the same Python environment for the UI and its child features so the registry can always launch the active interpreter.

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[ui,vision,dev]"
```

### Windows cmd.exe

```bat
python -m venv .venv
.venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -e ".[ui,vision,dev]"
```

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[ui,vision,dev]'
```

For StreamDiffusion/CUDA features, install the ML stack separately as documented in `README.md`, `docs/RTX4080.md`, and `docs/PLATFORMS.md`.

## Start the control deck

Portable module form:

```text
python -m projection_mapping.web_ui
```

Installed entry point:

```text
projection-ui
```

The command opens `http://127.0.0.1:8765/` in the default browser. Selecting a feature renders its
registry-defined configuration form. **Launch fullscreen** starts it as a child process while the
control server remains alive. Controls, search and log scrolling stay native-browser responsive.

The Textual fallback remains available as `projection-tui` or
`python -m projection_mapping.tui`.

### Controls

- **Mouse / keyboard** — search, select and edit native browser controls
- **Esc in projector window** — the visual exits using its normal fullscreen escape handling; the console is still running behind it
- **Stop visual** — terminate the complete active child process tree
- **Follow** — keep the incremental run log pinned to its newest output

Only one visual/experiment is owned by the console at a time. Launching another feature stops the previous child first. This is intentional: projector ownership should be deterministic.

## Platform-aware feature registry

The UI is data-driven by:

`configs/features.toml`

Every `[[feature]]` becomes a selectable experience. Every `[[feature.param]]` becomes an automatically rendered control. This means both operator surfaces can grow without turning UI code into a giant feature switch statement.

Features may optionally declare OS support:

```toml
[[feature]]
id = "spout_probe"
name = "Spout Probe"
category = "Diagnostics"
command = ["python", "experiments/spout_probe.py"]
platforms = ["windows"]
```

Accepted platform names are `windows`, `linux`, and `macos`. If `platforms` is omitted, the feature is treated as portable. Unsupported entries remain visible in the console but are labeled and blocked from launch so platform limitations are explicit rather than discovered via crashes.

The special command token `python` is replaced with `sys.executable`, the exact interpreter running the console. This avoids differences among `python`, `python3`, the Windows `py` launcher, virtualenv shims, and conda environments.

Example portable visual:

```toml
[[feature]]
id = "liquid_cathedral"
name = "Liquid Cathedral"
category = "Visual Madness"
description = "Architecture dissolves into flowing illuminated stone."
command = ["python", "experiments/12_liquid_cathedral.py"]
fullscreen = true

[[feature.param]]
key = "display"
flag = "--display"
label = "Projector display"
type = "int"
default = 1
min = 0
max = 8

[[feature.param]]
key = "madness"
flag = "--madness"
label = "Madness"
type = "float"
default = 0.72
min = 0.0
max = 1.0

[[feature.param]]
key = "material"
flag = "--material"
label = "Material"
type = "choice"
default = "bioluminescent_stone"
choices = ["bioluminescent_stone", "chrome", "moss", "flesh", "circuit"]
```

No shell is used. The registry is converted to an argv list and launched directly through Python's subprocess API.

## Supported parameter types

- `text` — free text input
- `int` — integer input with optional `min` / `max`
- `float` — floating-point input with optional `min` / `max`
- `bool` — checkbox; the command-line flag is included only when enabled
- `choice` — dropdown constrained to `choices`

Every feature parameter has:

- `key`: internal stable identifier
- `flag`: command-line flag passed to the experiment
- `label`: human-facing label
- `type`: one of the types above
- `default`: initial value
- optional validation metadata (`min`, `max`, `choices`, `help`)

## Process model

`FeatureLauncher` owns the currently running visual process. It launches from the repository root,
records stdout/stderr to `~/.projection_mapping/<timestamp>-<feature>.log`, and exposes status to the
browser API and Textual fallback. Log reads are incremental/bounded so long sessions do not make the
operator surface progressively slower.

This separation is important. The UI is not the renderer. A bad model load, camera error, or GLSL crash should kill the current visual process without killing the operator console.

The process model is currently:

```text
projection-ui / projection-tui
    |
    +-- operator UI (always alive)
    |
    +-- active child: experiments/XX_*.py
            |
            +-- projector fullscreen / platform transport / compositor
```

On Windows the launcher uses a new process group. On Linux/macOS it starts a new session. On POSIX,
normal parent exit also sweeps surviving helpers in that session; explicit Stop does the same. The
launcher itself remains shell-free and uses the exact active Python interpreter for registry commands.

Later the child boundary can become a stronger service boundary (local socket/IPC, separate ML worker, hot-reloadable render graph) without replacing the console UX.

## Fullscreen behavior

Most current projector experiments use OpenCV windows and already interpret key code 27 (`Esc`) as exit. When that projector window has focus, pressing `Esc` closes the visual subprocess. The control deck then detects the child's exit and updates its status to idle.

The browser **Stop visual** action or the Textual fallback's `Esc` binding terminates the active child tree.

This gives us the intended loop:

```text
LAUNCH -> projector owns attention -> ESC -> control deck -> mutate -> LAUNCH
```

## Platform behavior

### Windows

Core fullscreen/calibration features are supported. NVIDIA CUDA/TensorRT features are supported on compatible GPUs. Spout is the preferred same-machine shared-texture transport.

### Linux

Core fullscreen/calibration features and NVIDIA CUDA/TensorRT generative features are supported. Spout entries are blocked. Direct fullscreen is the current portable output path while Linux transport options remain under development.

### macOS

Core fullscreen/calibration/Room Skin features are supported. CUDA/TensorRT and Spout entries are blocked. Syphon is the intended future native shared-texture backend.

See `docs/PLATFORMS.md` for the full matrix.

## Categories currently exposed

### Visual Madness
Long-running visual experiences meant to occupy the projector: Room Skin, Neural Mirror / StreamDiffusion on supported CUDA systems, and the lightweight neural-mirror baseline.

### Projector Setup
Deterministic patterns for placement, focus, overscan, display selection, and basic projector verification.

### Calibration
Structured-light capture and radiometric dataset acquisition. These are experiments rather than entertainment modes, but keeping them in the same operator surface reduces setup friction.

### Diagnostics
Platform-specific transport diagnostics and GPU/generative benchmarks.

## Adding infinite features without chaos

New features should follow five rules:

1. **One executable experiment, one registry entry.** Keep rendering logic out of the TUI.
2. **Expose artistic controls explicitly.** A visual should have parameters such as `madness`, `flow`, `edge_lock`, `semantic_strength`, `feedback`, `palette`, `material`, `audio_gain`, etc. instead of burying magic numbers in code.
3. **Keep hardware controls separate from art controls.** Display index, camera index, resolution and transport belong to setup; material/style/intensity belong to the experience.
4. **Document the visual contract.** Each feature should say what inputs it needs, whether it is safe without calibration, which milestone it belongs to, and what `Esc` does.
5. **Declare platform limits.** If a feature requires Spout, CUDA, Syphon, a proprietary SDK, or OS-specific hardware, encode that explicitly instead of relying on tribal knowledge.

## Direction for the next UI iterations

The current UI intentionally starts as a reliable launcher/configurator. The roadmap for the operator surface includes:

- persistent per-feature presets
- favorite scenes and named configurations
- global projector/camera profile inherited by every feature
- global **MADNESS** macro that fans out into effect-specific parameters
- live parameter updates without restarting a visual (OSC/local IPC)
- side-by-side preview thumbnail in the console
- MIDI/gamepad/phone control bindings
- audio input selection and level meters
- calibration profile picker
- semantic-room object list (wall, plant, bookshelf, person, door...) with per-object effect assignment
- playlists / scene sequencing / timed transitions
- random mutation / generative preset explorer
- benchmark and health overlay
- emergency blackout / all-output stop

The operator experience should eventually feel closer to a synth + lighting desk + spatial AI instrument than to a collection of Python scripts.
