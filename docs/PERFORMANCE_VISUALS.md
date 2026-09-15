# Performance Visuals

This document covers the projector-ready performance modes added after hardware bring-up.

## Audio Reactive Studio

Launch from the TUI as **Audio Reactive Studio**. Linux `system` capture prefers the native Pulse/PipeWire monitor path, so the visual reacts to the actual speaker mix rather than the microphone.

### Visual presets

- `spectral_bloom` — organic color clouds and coherent onset blooms.
- `ribbon_cathedral` — architectural ribbons/arches driven mostly by mids and bass.
- `pulse_tunnel` — depth tunnel; kick/beat evidence pushes the tunnel, strong onsets strike.
- `caustic_field` — liquid light with gated high-frequency glints.
- `constellation` — sparse star field; highs are deliberately gated to avoid constant noise.
- `mechanical_sync` — geometric/gear language for rhythm-heavy material.

Palettes: `neon_aurora`, `solar_flare`, `bioluminescent`, `intelli`, `mono_accent`, `prismatic`.

Reactivity modes: `smooth`, `balanced`, `punchy`, `chaotic`.

The visual does **not** directly map every FFT fluctuation to pixels. `MusicalEventMapper` creates slow continuous controls plus sparse events. Strong onset and beat events require energy evidence and obey a refractory interval; treble detail is gated. `madness` increases range/event tails without simply making noise more sensitive.

Useful starting points:

```bash
python experiments/10_audio_reactive.py --source system --preset spectral_bloom --palette neon_aurora --reactivity balanced
python experiments/10_audio_reactive.py --source system --preset pulse_tunnel --palette solar_flare --reactivity punchy --madness 0.65
python experiments/10_audio_reactive.py --source system --preset constellation --palette bioluminescent --reactivity smooth --event-threshold 0.70
```

## Human Reactor

**Human Reactor** is intended for dance/performance capture as much as projection. It uses foreground segmentation + optical flow and therefore has no pose-model dependency.

Styles: `plasma`, `outline`, `ghost`, `ember`, `xray`.

Palettes: `neon`, `jade`, `ember`, `ice`, `violet`, `mono`.

Controls include edge glow, motion energy, body fill/aura, motion sparks, temporal echo count/strength, feedback persistence, optional original-camera blend, mirroring, and optional rendered-video recording.

For a clean dance-video render, keep `camera_mix=0`; for a stylized portrait beneath the effect, try `0.15..0.35`. Temporal echoes are sampled silhouettes, not duplicated camera frames, so the result remains graphic rather than looking like ordinary frame blending.

Example:

```bash
python experiments/12_human_reactor.py --style ghost --palette violet --mirror --echoes 7 --echo-strength 1.0 --feedback 0.93
```

Record the rendered projector feed:

```bash
python experiments/12_human_reactor.py --style plasma --palette neon --mirror --record captures/reactor_take01.mp4
```

## Neural Mirror: 6 GB safe path

The TUI exposes **Neural Mirror / 6GB Safe**. The `safe` profile uses 512x288 inference and a bounded default submission rate while still rendering/upscaling to projector resolution.

Acceleration defaults to `auto`:

1. use xFormers when it is actually importable;
2. otherwise use StreamDiffusion's native/PyTorch attention path;
3. if an optional accelerator is installed but fails during pipeline construction, clean CUDA state and retry with native attention.

Startup emits explicit stages into the live log and TUI status line:

```text
PREFLIGHT
IMPORT STREAMDIFFUSION
MODEL LOAD / DOWNLOAD IF NEEDED
PREPARE
WARMUP
READY
RUNNING
```

The `auto` profile selects `safe` below 8 GiB total VRAM and `balanced` on larger devices. `custom` respects explicit inference width/height.

F11 toggles fullscreen on direct display output. ESC exits cleanly and returns to the control deck.

## Performance principle

For all performance modes: prefer stable 60 Hz deterministic rendering around sparse semantic events. Neural inference remains asynchronous/latest-frame-wins and should never create a stale frame queue. Visual intensity should come from composition, feedback, spatial structure and event design—not from making every noisy feature modulate every pixel.
