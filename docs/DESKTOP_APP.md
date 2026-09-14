# Desktop app / one-click launcher

ProjectionMapping can be packaged as a desktop bundle so the control deck does not require typing commands every time.

The desktop build uses **PyInstaller** and keeps the existing renderer-process isolation model. The frozen app relaunches itself in an internal `--pm-child` mode for experiments, so fullscreen visuals still run as separate child processes and `Esc` can return to the persistent control deck.

## What gets bundled

The standard desktop bundle includes:

- the Textual control deck;
- OpenCV / classical projection features;
- the low-latency audio-reactive feature;
- `configs/features.toml`;
- experiment scripts;
- shaders and desktop assets.

Large CUDA/StreamDiffusion stacks are intentionally not guaranteed in the generic release bundle. They remain hardware/environment-sensitive. A machine-specific build can include them later, or the ML renderer can move to a dedicated sidecar environment.

## Build locally

Recommended Python: 3.12.

```text
python -m pip install -e '.[ui,vision,audio,dev,desktop]'
python packaging/build_desktop.py
```

The result is created under:

```text
dist/ProjectionMapping/
```

### Windows

Double-click:

```text
dist\ProjectionMapping\ProjectionMapping.exe
```

It is a console application because the current control deck is terminal-native. Pin the executable or create a normal Windows shortcut if desired.

### Linux

The bundle executable is:

```text
dist/ProjectionMapping/ProjectionMapping
```

To install it into the desktop application menu with the project icon:

```text
python packaging/install_linux_desktop.py
```

This installs the bundle under:

```text
~/.local/opt/ProjectionMapping/
```

and creates:

```text
~/.local/share/applications/ProjectionMapping.desktop
```

After that, launch **ProjectionMapping** from the application menu like any other desktop program. The launcher uses `Terminal=true` because the current UI is a Textual terminal application.

### macOS

The CI currently produces a native executable bundle analogous to Linux. The Textual UI still requires a terminal surface. A polished `.app` wrapper that opens the control deck in Terminal/iTerm is a follow-up packaging refinement; the core frozen executable itself is supported.

## Automated builds

`.github/workflows/desktop-build.yml` builds artifacts on Windows, Linux, and macOS when desktop-relevant files change, on version tags, or when started manually.

Artifacts are named:

```text
ProjectionMapping-windows
ProjectionMapping-linux
ProjectionMapping-macos
```

The Windows artifact is a ZIP; Linux/macOS artifacts are `.tar.gz` archives.

## Why `--onedir` instead of one huge executable?

ProjectionMapping contains native dependencies (OpenCV, audio backends, later CUDA libraries) and many runtime assets. `--onedir` gives:

- faster startup;
- easier debugging of native libraries;
- simpler bundling of experiments/configs/shaders;
- easier future CUDA/native-sidecar integration;
- fewer antivirus / temporary-extraction surprises than `--onefile`.

The user experience is still one-click: the only executable you launch is `ProjectionMapping` / `ProjectionMapping.exe`.

## Frozen child execution

Normal development commands in `configs/features.toml` look like:

```toml
command = ["python", "experiments/10_audio_reactive.py"]
```

In a normal checkout, the registry replaces `python` with the current interpreter.

In a frozen build there is no independent interpreter. The registry instead turns it into approximately:

```text
ProjectionMapping --pm-child experiments/10_audio_reactive.py ...
```

The child process executes the bundled script via `runpy`. This preserves the architecture:

```text
ProjectionMapping control deck
    |
    +-- ProjectionMapping --pm-child <visual>
            |
            +-- fullscreen projector window
```

So renderer crashes do not have to kill the control deck.

## Logs

Desktop builds write run logs to:

```text
~/.projection_mapping/
```

rather than beside the executable. This keeps packaged application folders read-only and clean.

## Current limitation

The generic desktop artifact is intended for the portable core. CUDA/TensorRT/StreamDiffusion are large and tied to GPU driver/runtime versions. For the RTX workstation, the eventual preferred architecture is likely:

```text
ProjectionMapping desktop control app
    |
    +-- portable local renderers
    |
    +-- dedicated CUDA/StreamDiffusion worker environment
            |
            +-- IPC/shared-texture output
```

That avoids making the desktop launcher hundreds of megabytes larger or fragile across driver updates just to support one ML backend.
