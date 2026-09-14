# ProjectionMapping Console UI

The console UI is the operator surface for the installation. The intended loop is intentionally simple:

```text
console UI
  -> choose feature
  -> edit parameters
  -> launch fullscreen on projector
  -> experience / inspect result
  -> ESC
  -> back to console UI
  -> mutate config
  -> launch again
```

The goal is to make experimentation feel like playing an instrument instead of repeatedly editing command lines.

## Install

From the repository root:

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[ui,vision,dev]"
```

For StreamDiffusion features, install the ML stack separately as documented in `README.md` and `docs/RTX4080.md`.

## Start the console

```powershell
projection-ui
```

The UI supports keyboard and mouse. Selecting a feature opens its configuration screen. **LAUNCH FULLSCREEN** starts it as a child process while the console remains alive underneath.

### Controls

- **Mouse / Enter** — select a feature or button
- **Esc in projector window** — the visual exits using its normal fullscreen escape handling; the console is still running behind it
- **Esc while terminal has focus** — terminate the active visual
- **L** — refresh and show the tail of the last run log
- **R** — refresh current process status
- **Q** — quit the console

Only one visual/experiment is owned by the console at a time. Launching another feature stops the previous child first. This is intentional: projector ownership should be deterministic.

## Feature registry

The UI is data-driven by:

`configs/features.toml`

Every `[[feature]]` becomes a selectable experience. Every `[[feature.param]]` becomes an automatically rendered control. This means the console can grow to hundreds of visual modes without turning `tui.py` into a giant switch statement.

Example:

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

`FeatureLauncher` owns the currently running visual process. It launches from the repository root, records stdout/stderr to `.projection_mapping/<timestamp>-<feature>.log`, and exposes status back to the TUI.

This separation is important. The UI is not the renderer. A bad model load, camera error, or GLSL crash should kill the current visual process without killing the operator console.

The process model is currently:

```text
projection-ui
    |
    +-- operator UI (always alive)
    |
    +-- active child: experiments/XX_*.py
            |
            +-- projector fullscreen / Spout / TouchDesigner
```

Later the child boundary can become a stronger service boundary (local socket/IPC, separate ML worker, hot-reloadable render graph) without replacing the console UX.

## Fullscreen behavior

Most current projector experiments use OpenCV windows and already interpret key code 27 (`Esc`) as exit. When that projector window has focus, pressing `Esc` closes the visual subprocess. The TUI then detects the child's exit and updates its status to idle.

If the terminal has focus instead, the TUI's own `Esc` binding terminates the active child.

This gives us the intended loop:

```text
LAUNCH -> projector owns attention -> ESC -> control deck -> mutate -> LAUNCH
```

## Categories currently exposed

### Visual Madness
Long-running visual experiences meant to occupy the projector: Room Skin, Neural Mirror / StreamDiffusion, and the lightweight neural-mirror baseline.

### Projector Setup
Deterministic patterns for placement, focus, overscan, display selection, and basic projector verification.

### Calibration
Structured-light capture and radiometric dataset acquisition. These are experiments rather than entertainment modes, but keeping them in the same operator surface reduces setup friction.

### Diagnostics
Spout transport diagnostics and RTX 4080 StreamDiffusion benchmarks.

## Adding infinite features without chaos

New features should follow four rules:

1. **One executable experiment, one registry entry.** Keep rendering logic out of the TUI.
2. **Expose artistic controls explicitly.** A visual should have parameters such as `madness`, `flow`, `edge_lock`, `semantic_strength`, `feedback`, `palette`, `material`, `audio_gain`, etc. instead of burying magic numbers in code.
3. **Keep hardware controls separate from art controls.** Display index, camera index, resolution and transport belong to setup; material/style/intensity belong to the experience.
4. **Document the visual contract.** Each feature should say what inputs it needs, whether it is safe without calibration, which milestone it belongs to, and what `Esc` does.

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
