# Track — Audio / Audiovisual Instrument

## North star
A performable visual instrument that responds to musical structure, not raw FFT noise: stable system-audio capture, sparse meaningful events, continuous harmonic motion, tempo/phase-aware animation, coherent shader worlds, persistent GPU particle choreography, seamless transitions, saved performance states, and eventually MIDI/OSC/Ableton + neural latent/style modulation. The same `MusicalSignals` bus must drive Song Studio, Performer FX, Human Reactor and Room Skin rather than duplicating audio logic.

## Current state
- Linux system-audio monitor capture works through native Pulse/PipeWire (`parec`) with SoundCard fallback.
- Low-latency capture blocks remain independent from spectral resolution.
- `RollingMusicFeatureExtractor` uses a default 2048-sample rolling FFT while capture can stay at 128/256 samples.
- Band energy is derived from spectral power fractions, avoiding inactive-band self-normalization and the old 256-sample bass-resolution failure.
- Spectral novelty + RMS-rise onset evidence, adaptive loudness reference, bass/mid/treble/centroid controls.
- `MusicalEventMapper` enforces one event decision per captured audio block, robust median/MAD adaptive thresholds, refractory spacing, macro energy tracking, drop accents and a lightweight beat-period/phase estimator.
- GPU shader branch: `Audio Visual Instrument / GPU` with Aurora/Liquid/Pulse/Void/Cathedral + Journey crossfades.
- GPU particle branch: `Song Studio / GPU Particle Stage` with persistent particle state, feedback/advection, additive glow and music-aware choreography.
- Particle choreography banks: `orbit_reactor`, `dual_comet`, `cathedral_rain`, `vortex_gate`, `constellation_bloom`.
- Particle bank parameters are driven by musical role: beat/bar phase sets coherent trajectories; loudness sets density; bass broadens/energizes fields; strikes create bursts; drops alter macro emission; highs are not the global animation clock.
- Shader palettes: Neon Aurora, Solar Flare, Bioluminescent, Intelli, Mono Accent, Prismatic. Particle materials: cyber, solar, bio, prismatic.
- Smooth/Balanced/Punchy/Chaotic musical reactivity modes and Calm<->Madness macro remain available.
- Curated shader performance banks: `journey_balanced`, `techno_pulse`, `ambient_void`, `liquid_melodic`, `cathedral_installation`, `acid_afterhours`.
- Previous NumPy/OpenCV studio remains available as a CPU legacy fallback rather than the art-quality target.
- F11 fullscreen, ESC return-to-console and runtime telemetry include feature age, event counts, BPM confidence and beat phase.

## Quality ladder
- **Prototype:** audio reaches visual.
- **Usable:** stable loopback + band-separated motion.
- **Polished:** rolling spectral analysis, sparse adaptive events, tempo phase, coherent GPU shader composition, persistent particle choreography, dark-space discipline and curated launchable banks. **Implemented; projector/art validation ongoing.**
- **Advanced:** chroma/key, section boundaries, phrase/bar hierarchy, reliable half/double-time handling, beat-synchronous bank morphing, user snapshots, live controls and MIDI/OSC/Ableton clock.
- **Ridiculous:** song structure orchestrates performer particles, generated assets, portals and calibrated room surfaces; semantic audio embeddings change scene/material/style state; neural style/LoRA state follows sections while deterministic VFX remains exact at display rate.

## Design rules learned from hardware testing
1. Capture block size is a latency setting, **not** the FFT size. A 256-sample FFT at 48 kHz has 187.5 Hz bin spacing and is unsuitable for a 35-180 Hz bass control.
2. Continuous motion should use smoothed envelopes/phase. Large visual events should be sparse and gated.
3. The display loop may read the same audio feature several times; a single audio block must never retrigger multiple musical events.
4. High-frequency content is detail, not the global animation clock.
5. Scene changes need crossfades and macro musical evidence; hard cuts on every onset destroy continuity.
6. Palette richness does not mean random rainbow noise: preserve dark negative space and let strong events temporarily expand the gamut.
7. Particle emission is choreography, not confetti: persistent trajectories/fields establish visual identity and sparse musical accents modulate them.
8. Song Studio publishes state; downstream VFX consume that state. Do not create separate FFT/event detectors in every feature.

## Current GPU scene language
### Shader worlds
- **Aurora:** domain-warped luminous veils; bass broadens the field, mids move the flow, highs add fine filaments.
- **Liquid:** chrome/caustic material response with broad musical breathing rather than twitchy pixels.
- **Pulse:** seamless polar/tunnel geometry using integer angular harmonics so the atan branch cut cannot create the old portal seam.
- **Void:** sparse star/nebula field where highs only add fine detail and drops lift the whole space.
- **Cathedral:** repeated architectural lines/arches with beat-phase breathing and transient highlights.
- **Journey:** crossfades between the above; a strong detected drop can request a transition, otherwise a maximum dwell time prevents visual stagnation.

### Particle choreography
- **Orbit Reactor:** four phase-locked orbiting emitters; bass changes radius, mids change tangential speed, drops increase density.
- **Dual Comet:** opposing beat-phase trajectories with directional emission and stronger transient acceleration.
- **Cathedral Rain:** restrained top-down columns with beat-phase modulation and long persistence.
- **Vortex Gate:** six orbit emitters form a rotating gate; drops increase tangential energy and density.
- **Constellation Bloom:** intentionally sparse idle field that blooms mainly on meaningful strikes/drops.

## Open problems
- Tempo tracker is intentionally lightweight; syncopated/breakbeat material can still produce half/double-time ambiguity.
- No chroma/key or robust section-boundary/phrase model yet.
- ModernGL particle/shader paths currently render offscreen then read back into the shared OpenCV fullscreen sink; direct GL display/shared texture is still the target.
- Particle engine is implemented but not yet hardware-benchmarked on the RTX 4050/4080.
- Shader/particle parameters are launch-time settings; no live hot-control/preset morphing yet.
- Curated built-in banks exist, but user-saved named banks / A-B snapshots do not yet.
- Drop detector is a macro-dynamics heuristic, not learned song-structure analysis.
- Need real recordings of event precision against several genres before tuning defaults further.

## Next implementation queue
1. Hardware-tune `analysis_size=2048` vs `4096` and 128/256 capture blocks; measure feature age and bass stability.
2. Benchmark Song Studio particle capacities 8k/16k/32k/65k and readback cost; preserve the lowest-latency visually dense operating point.
3. Record event logs against techno, house, ambient, rock and dense/breakbeat material; tune adaptive MAD selectivity and BPM confidence.
4. Add chroma/key-class vector + harmonic-change descriptor and a phrase/section state machine (`intro`, `breakdown`, `build`, `drop`, `release`).
5. Add beat/bar-synchronous particle bank morphing and palette/material transitions without particle-state reset.
6. Add live local IPC/hot controls, user-named banks and A/B snapshots.
7. Add audio-reactive VFX-pack spawning: rare macro events can summon approved sprite/GLB assets rather than random per-beat clutter.
8. Add MIDI/OSC mappings and Ableton Link/clock experiment.
9. Move shader/particle display to a GL-native window/shared texture path and remove final readback.
10. Route `MusicalSignals` into Performer FX, Human Reactor and Room Skin as a shared state bus.
11. Evaluate CLAP/audio embeddings only after deterministic musical controls are measured and stable; use embeddings for semantic/style/asset-bank state, not frame-rate modulation.

## Metrics
Capture latency, feature age, bass-band stability at small capture blocks, event precision against kick/snare markers, duplicate-event rate, BPM error/confidence, phrase transition precision, particle simulation/render/readback p50/p95, active particle count, event rate/minute, scene-transition frequency, display FPS/p95 frame time, visual jitter under steady tones and setup friction.

## Preset vault
### Shader banks
- `journey_balanced` — Journey / Neon Aurora / Balanced / madness 0.42; broad default.
- `techno_pulse` — Pulse / Solar Flare / Punchy; kick-heavy techno/house.
- `ambient_void` — Void / Bioluminescent / Smooth; sparse/ambient.
- `liquid_melodic` — Liquid / Prismatic / Balanced; continuous melodic/electronic material.
- `cathedral_installation` — Cathedral / Intelli / Balanced; architectural/installational.
- `acid_afterhours` — Journey / Prismatic / Punchy / higher madness; denser club material.

### Particle banks
- `orbit_reactor` — broad default / melodic electronic.
- `dual_comet` — kinetic techno / break accents.
- `cathedral_rain` — restrained architectural ambient.
- `vortex_gate` — drops/builds and portal-like musical moments.
- `constellation_bloom` — sparse tracks where accents should feel expensive rather than constant.

CPU legacy: Spectral Bloom / Neon Aurora / Balanced remains the low-dependency fallback.
