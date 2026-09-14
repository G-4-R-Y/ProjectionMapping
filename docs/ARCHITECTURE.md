# Architecture

## Principle

Keep **physical calibration**, **vision/ML**, **artistic rendering**, **display transport**, and the **operator/control plane** separable. A model crash should not take down calibration; switching from diffusion to shaders should not require rewriting the projector output path; changing the operator UI should not require touching the renderer.

## Control plane vs render plane

The project now has an explicit operator/control plane:

```text
projection-ui
    |
    +-- configs/features.toml
    |       \-- feature metadata + typed parameters
    |
    +-- FeatureLauncher
            \-- one active experiment/visual subprocess
```

The UI is not a renderer. It selects and configures a feature, starts it, monitors it, captures logs, and stops it. The visual process owns fullscreen projector output or Spout. This keeps the control deck alive when a visual exits or crashes.

The intended interaction is:

```text
select -> configure -> launch fullscreen -> ESC -> return -> mutate -> relaunch
```

Current feature processes are command-line experiments. Later, selected long-running renderers can expose local IPC/OSC so parameters update live without restarts while preserving the same operator UX.

## Render/data plane

### Capture
Camera frames, timestamps, optional exposure/gain locking.

### Calibration
- planar homography for immediate experiments
- Gray-code / phase-shift structured light for dense projector-camera mapping
- reusable calibration bundles with resolution and camera/projector metadata

### Perception
- foreground masks
- optical flow
- optional depth / semantic segmentation / pose

### Generation
- shaders and procedural feedback for temporally stable high-rate motion
- diffusion/video generation for semantic transformation
- hybrid path: AI produces appearance/keyframes, graphics produce 60+ FPS dynamics

### Compensation
- geometric warp
- radiometric LUT baseline
- learned inverse-display network
- later: defocus and shadow compensation

### Transport
- direct fullscreen output for bring-up
- Spout for same-machine Windows GPU sharing
- NDI for networked/multi-machine setups

## Feature contract

Every operator-visible experience should have:

1. a standalone executable/experiment;
2. a registry entry in `configs/features.toml`;
3. explicit typed parameters rather than hidden magic constants;
4. deterministic exit behavior (`Esc` for fullscreen visuals);
5. a clear hardware/calibration dependency statement;
6. milestone/experiment documentation.

The registry supports text, integer, float, boolean, and choice parameters. Commands are built as argv arrays and launched without a shell.

## Process isolation

Only one operator-owned visual is active at a time. `FeatureLauncher` launches it from the repository root and redirects stdout/stderr to `.projection_mapping/<timestamp>-<feature>.log`.

This gives us a useful failure boundary:

```text
operator console stays alive
        |
        +-- child visual succeeds -> ESC -> console
        +-- child visual errors    -> log + exit -> console
        +-- child hangs            -> console ESC/STOP -> terminate -> console
```

As the system grows, ML inference can become its own worker/service and the projector renderer another process. The console should remain the orchestration surface rather than absorbing those responsibilities.

## Closed loop

Let P be projector pixels, C(P) the camera-observed physical result, and T the target. Optimize

`P* = argmin_P d(C(P), T) + lambda R(P)`

where `d` can combine pixel loss and learned features. For stable surfaces, learn an inverse model first; for dynamic scenes, combine online feedback with a prior model.

## Latency budget

Track capture, perception, generation, compositing, transport, projector scanout, and camera exposure separately. Dynamic mapping quality is dominated by end-to-end motion-to-photon latency, not just neural inference time.

The operator layer should never enter that critical render loop. UI responsiveness and visual-frame timing are intentionally decoupled.
