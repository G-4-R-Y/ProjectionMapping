# Audio Reactive Pulse Field

`experiments/10_audio_reactive.py` is the first M7 audiovisual instrument mode. It is intentionally designed around **latency first** rather than elaborate offline beat analysis.

## Architecture

```text
native OS audio backend
  -> SoundCard/CFFI capture thread
  -> tiny latest-only audio block
  -> NumPy spectral features
  -> attack/release envelopes
  -> latest AudioFeatures snapshot
  -> display-rate procedural renderer
  -> fullscreen projector
```

There is no growing queue. The renderer always uses the newest available feature vector. Audio capture never waits for the visual renderer, and the visual renderer never waits for a historical stack of audio frames.

The current feature vector contains:

- RMS / overall energy
- bass energy (35-180 Hz)
- mid energy (180-2000 Hz)
- treble energy (2-10 kHz)
- spectral centroid
- positive spectral flux
- onset envelope

The visual maps these to radial pulse speed, interference frequency, hue motion, brightness, and impact flashes. This is deliberately more immediate than a slow tempo tracker.

## Install

```text
python -m pip install -e '.[ui,vision,audio,dev]'
```

The optional `audio` extra installs `SoundCard`, which talks to native audio backends through CFFI.

## List devices

```text
python experiments/10_audio_reactive.py --list-devices
```

The output labels physical inputs and detected loopback/monitor inputs.

## Microphone / line input

```text
python experiments/10_audio_reactive.py --source mic --display 1
```

Select a specific input by name or ID substring:

```text
python experiments/10_audio_reactive.py --source mic --device "USB" --display 1
```

## System / device audio

### Windows

SoundCard exposes WASAPI loopback devices as virtual microphones. Start with:

```text
python experiments/10_audio_reactive.py --source system --display 1
```

For experiments with lower latency, try `--exclusive-mode`. SoundCard documents this as experimental on WASAPI, so compare it rather than assuming it is always better.

### Linux

With PulseAudio/PipeWire, output monitor sources can be exposed as capture devices. Inspect them with `--list-devices`, then either use automatic `--source system` selection or pass a monitor device substring via `--device`.

PipeWire supports explicit latency controls and sink-monitor capture. If the desktop audio stack adds too much latency, the next optimization is a native PipeWire sidecar using a small quantum rather than increasing complexity inside the renderer.

### macOS

Microphone/line input works through CoreAudio. SoundCard itself does not provide native macOS output loopback. For the first wall test, route system audio into a virtual input such as BlackHole and select that input by name. A native ScreenCaptureKit audio backend is a future M7 optimization; ScreenCaptureKit can capture system audio directly on modern macOS.

## Latency tuning

Defaults are deliberately aggressive:

- sample rate: 48 kHz
- capture block size: 256 samples (~5.3 ms at 48 kHz)
- attack: 6 ms
- release: 85 ms
- fixed analysis work per native block
- renderer: latest features only
- visual computation at 640x360, then GPU/display-friendly resize to projector resolution

Try 128 samples if the backend is stable:

```text
python experiments/10_audio_reactive.py --source mic --blocksize 128 --attack-ms 4 --display 1
```

Try 64 only after 128 is stable. Tiny buffers reduce theoretical latency but make underruns/dropouts more likely. The correct operating point is the smallest stable buffer on the actual machine/audio device.

Every two seconds the experiment prints `feature_age=...ms`. This is the approximate age of the latest analyzed audio feature vector at render time and is the first number to watch during tuning.

## Console UI

The feature is registered as **Visual Madness -> Audio Reactive Pulse Field**. Main controls:

- audio source: microphone or system
- device name / ID substring
- projector display / resolution
- audio block size
- attack / release
- sensitivity
- global `madness`
- experimental Windows exclusive mode

Launch fullscreen from the control deck and press `Esc` to return exactly like the other visual modes.

## Why not Rust/C++ yet?

The critical capture path already sits on native OS audio APIs through SoundCard/CFFI, while NumPy's FFT executes in optimized native code. Python only orchestrates block delivery and feature snapshots. For this feature set, that is usually not the dominant latency source; OS audio buffering is.

If profiling shows Python scheduling is actually measurable on the wall test, M7 can replace only the capture/analyzer with a native sidecar:

- Windows: WASAPI event-driven loopback/input
- Linux: native PipeWire stream with explicit quantum/latency
- macOS: ScreenCaptureKit for system audio + CoreAudio for microphone
- IPC: shared memory or local UDP/OSC carrying ~7 floats per audio block

That preserves the control deck and renderer while letting the lowest-level backend become as aggressive as needed.

## Next M7 steps

1. measure real mic/system feature age on the wall-test laptop;
2. add beat-phase / tempo inference outside the hard realtime callback;
3. add audio -> shader/particle/feedback buses;
4. add live OSC/MIDI routing;
5. route the same features into Room Skin, Neural Mirror prompt/style weights, and semantic-room objects;
6. consider native audio sidecars only when profiling justifies them.
