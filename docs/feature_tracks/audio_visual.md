# Track — Audio / Audiovisual Instrument

## North star
A performable visual instrument that responds to musical structure, not raw FFT noise: stable system-audio capture, sparse meaningful events, continuous harmonic motion, tempo/phase-aware animation, coherent GPU shader scenes, seamless transitions, saved performance states, and eventually MIDI/OSC/Ableton + neural latent/style modulation.

## Current state
- Linux system-audio monitor capture works through native Pulse/PipeWire (`parec`) with SoundCard fallback.
- Low-latency capture blocks remain independent from spectral resolution.
- `RollingMusicFeatureExtractor` uses a default 2048-sample rolling FFT while capture can stay at 128/256 samples.
- Band energy is derived from spectral power fractions, avoiding inactive-band self-normalization and the old 256-sample bass-resolution failure.
- Spectral novelty + RMS-rise onset evidence, adaptive loudness reference, bass/mid/treble/centroid controls.
- `MusicalEventMapper` now enforces one event decision per captured audio block, robust median/MAD adaptive thresholds, refractory spacing, macro energy tracking, drop accents and a lightweight beat-period/phase estimator.
- GPU-first `Audio Visual Instrument / GPU` uses ModernGL shader scenes and seamless scene crossfades.
- Shader scenes: `aurora`, `liquid`, `pulse`, `void`, `cathedral`, plus `journey` mode that advances on strong macro drops or a maximum scene duration.
- Palettes: Neon Aurora, Solar Flare, Bioluminescent, Intelli, Mono Accent, Prismatic.
- Smooth/Balanced/Punchy/Chaotic musical reactivity modes and Calm<->Madness macro remain available.
- Curated performance banks are implemented: `journey_balanced`, `techno_pulse`, `ambient_void`, `liquid_melodic`, `cathedral_installation`, `acid_afterhours`; `custom` exposes the fine controls.
- Previous NumPy/OpenCV studio remains available as a CPU legacy fallback rather than the art-quality target.
- F11 fullscreen, ESC return-to-console and runtime telemetry include feature age, event counts, BPM confidence and beat phase.

## Quality ladder
- **Prototype:** audio reaches visual.
- **Usable:** stable loopback + band-separated motion.
- **Polished:** rolling spectral analysis, sparse adaptive events, tempo phase, GPU shader composition, dark-space discipline, seamless scene continuity and curated launchable banks. **Current implementation; hardware/art validation ongoing.**
- **Advanced:** chroma/key, section boundaries, reliable half/double-time tempo handling, user-saved/morphable banks, live scene/palette mutation and MIDI/OSC/Ableton clock.
- **Ridiculous:** audio embeddings -> semantic scene state, latent/LoRA/style interpolation, performer + room effects sharing one musical state machine, calibrated room surfaces responding by musical role rather than as one rectangular canvas.

## Design rules learned from hardware testing
1. Capture block size is a latency setting, **not** the FFT size. A 256-sample FFT at 48 kHz has 187.5 Hz bin spacing and is unsuitable for a 35-180 Hz bass control.
2. Continuous motion should use smoothed envelopes/phase. Large visual events should be sparse and gated.
3. The display loop may read the same audio feature several times; a single audio block must never retrigger multiple musical events.
4. High-frequency content is detail, not the global animation clock.
5. Scene changes need crossfades and macro musical evidence; hard cuts on every onset destroy continuity.
6. Palette richness does not mean random rainbow noise: preserve dark negative space and let strong events temporarily expand the gamut.

## Current GPU scene language
- **Aurora:** domain-warped luminous veils; bass broadens the field, mids move the flow, highs add fine filaments.
- **Liquid:** chrome/caustic material response with broad musical breathing rather than twitchy pixels.
- **Pulse:** seamless polar/tunnel geometry using integer angular harmonics so the atan branch cut cannot create the old portal seam.
- **Void:** sparse star/nebula field where highs only add fine detail and drops lift the whole space.
- **Cathedral:** repeated architectural lines/arches with beat-phase breathing and transient highlights.
- **Journey:** crossfades between the above; a strong detected drop can request a transition, otherwise a maximum dwell time prevents visual stagnation.

## Open problems
- Tempo tracker is intentionally lightweight; syncopated/breakbeat material can still produce half/double-time ambiguity.
- No chroma/key or robust section-boundary model yet.
- ModernGL currently renders offscreen then reads back into the shared OpenCV fullscreen sink; direct GL display/shared texture is still the target.
- Shader parameters are launch-time settings; no live hot-control/preset morphing yet.
- Curated built-in banks exist, but user-saved named banks / A-B snapshots do not yet.
- Drop detector is a macro-dynamics heuristic, not learned song-structure analysis.
- Need real recordings of event precision against several genres before tuning defaults further.

## Next implementation queue
1. Hardware-tune `analysis_size=2048` vs `4096` and 128/256 capture blocks; measure feature age and bass stability.
2. Record event logs against techno, house, ambient, rock and dense/breakbeat material; tune adaptive MAD selectivity and BPM confidence.
3. Add chroma/key-class vector and harmonic-change descriptor from the rolling spectrum.
4. Add section-boundary evidence from multi-second novelty/energy/color trajectories; distinguish breakdown/build/drop rather than one generic `drop` scalar.
5. Add live local IPC for scene/palette/reactivity controls without relaunch.
6. Add user-saved named banks, A/B snapshots and timed/beat-synchronous parameter morphs on top of the built-in curated banks.
7. Add MIDI/OSC mappings and Ableton Link/clock experiment.
8. Move shader display to a GL-native window/shared texture path and remove readback.
9. Route the same `MusicalSignals` bus into Cyber Mage point SFX, Human Reactor and Room Skin so music changes scene state rather than duplicating FFT logic in every feature.
10. Evaluate CLAP/audio embeddings only after deterministic musical controls are measured and stable; use embeddings for semantic/style state, not frame-rate modulation.

## Metrics
Capture latency, feature age, bass-band stability at small capture blocks, event precision subjectively against kick/snare markers, duplicate-event rate, BPM error/confidence on steady material, event rate/minute, scene-transition frequency, display FPS/p95 frame time, shader/readback time, visual jitter under steady tones, setup friction.

## Preset vault
- `journey_balanced` — Journey / Neon Aurora / Balanced / madness 0.42; broad default.
- `techno_pulse` — Pulse / Solar Flare / Punchy; kick-heavy techno/house.
- `ambient_void` — Void / Bioluminescent / Smooth; sparse/ambient.
- `liquid_melodic` — Liquid / Prismatic / Balanced; continuous melodic/electronic material.
- `cathedral_installation` — Cathedral / Intelli / Balanced; architectural/installational.
- `acid_afterhours` — Journey / Prismatic / Punchy / higher madness; denser club material.
- CPU legacy: Spectral Bloom / Neon Aurora / Balanced remains the low-dependency fallback.
