# Track — Audio / Audiovisual Instrument

## North star
A performable visual instrument that responds to musical structure, not raw FFT noise: stable system-audio capture, sparse meaningful events, continuous harmonic motion, curated palettes/scenes, saved presets, transitions, and eventually MIDI/OSC/Ableton + neural latent/style modulation.

## Current state
- Linux system-audio monitor capture works through native Pulse/PipeWire (`parec`) with SoundCard fallback.
- FFT features: RMS, bass, mid, treble, centroid, spectral flux, onset envelope.
- Audio Reactive Studio: multiple scenes/palettes/reactivity modes, event gating, calm<->madness macro.
- F11 fullscreen and persistent run logs.

## Quality ladder
- **Prototype:** audio reaches visual.
- **Usable:** stable loopback + band-separated motion.
- **Polished:** curated palettes, scene presets, sparse beat/strike events, no nervous jitter. **Current target.**
- **Advanced:** tempo/beat phase, chroma/key, sections/drops, automatic gain/noise calibration, preset morphing.
- **Ridiculous:** audio embeddings -> semantic scene state, latent/LoRA/style interpolation, performer + room effects sharing one musical state machine.

## Open problems
- False-positive transients and excessive high-frequency noise on dense tracks.
- No reliable tempo/beat phase or song-section model yet.
- Presets are launch-time parameters; no live scene morphing/hot control.
- No preset persistence / A-B snapshots.

## Next queue
1. Add robust peak-picking with adaptive local threshold + minimum inter-event spacing.
2. Add tempo/beat-phase estimator and confidence; use phase for periodic motion and sparse events for accents.
3. Add scene transitions and palette morphs without relaunch.
4. Add preset save/load and named performance banks.
5. Add MIDI/OSC mappings and Ableton clock experiment.
6. Evaluate audio embeddings / CLAP-like semantic descriptors only after deterministic musical control is solid.

## Metrics
Capture latency, feature age, event precision subjectively against kick/snare markers, event rate/minute, display FPS, dropped audio blocks, visual jitter under steady tones, setup friction.

## Preset vault
- Spectral Bloom + Neon Aurora + Balanced — broad/default.
- Pulse Tunnel + Solar Flare + Punchy — kick-heavy techno.
- Constellation + Bioluminescent + Smooth — ambient/sparse.
- Ribbon Cathedral + Intelli + Balanced — architectural.
- Mechanical Sync + Prismatic + Punchy — aggressive rhythmic.
