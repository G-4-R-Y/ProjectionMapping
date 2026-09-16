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
- `MusicStructureTracker` now provides a transparent baseline `breakdown/build/drop/release/steady` section state plus phrase phase; it is explicitly a heuristic baseline, not claimed as semantic song understanding.
- GPU shader branch: `Audio Visual Instrument / GPU` with Aurora/Liquid/Pulse/Void/Cathedral + Journey crossfades.
- GPU particle branch: `Song Studio / GPU Particle Stage` with persistent particle state, feedback/advection and music-aware choreography.
- Particle material was rewritten after hardware feedback that it looked covered by a grey shade: current target is white-hot core + saturated shell + same-hue halo + thresholded bloom + chromatic feedback + clean black floor.
- Original choreography banks: `orbit_reactor`, `dual_comet`, `cathedral_rain`, `vortex_gate`, `constellation_bloom`.
- New choreography banks: `reactor_bloom`, `polar_gate`, `ritual_rain`, `helix_fountain`, `nebula_bloom`, `techno_lattice`.
- `journey` mode chooses banks at section/phrase boundaries without resetting the particle simulation.
- Optional music-reactive Polar Math backdrop supports all five analytic radial equation families; screen-style blending is intentionally restrained to avoid reintroducing haze.
- Particle bank parameters are driven by musical role: beat/bar phase sets coherent trajectories; loudness sets density; bass broadens/energizes fields; strikes create bursts; drops alter macro emission; highs are not the global animation clock.
- Shader palettes: Neon Aurora, Solar Flare, Bioluminescent, Intelli, Mono Accent, Prismatic. Particle materials: cyber, solar, bio, prismatic.
- Smooth/Balanced/Punchy/Chaotic musical reactivity modes and Calm<->Madness macro remain available.
- Curated shader performance banks: `journey_balanced`, `techno_pulse`, `ambient_void`, `liquid_melodic`, `cathedral_installation`, `acid_afterhours`.
- Previous NumPy/OpenCV studio remains available as a CPU legacy fallback rather than the art-quality target.

## Quality ladder
- **Prototype:** audio reaches visual.
- **Usable:** stable loopback + band-separated motion.
- **Polished:** rolling spectral analysis, sparse adaptive events, tempo phase, persistent particle choreography, vivid emissive materials, section-aware Journey and curated launchable banks. **Implemented; projector/art validation ongoing.**
- **Advanced:** chroma/key, stronger phrase boundaries, reliable half/double-time handling, beat-synchronous bank/palette morphing, user snapshots, live controls and MIDI/OSC/Ableton clock.
- **Ridiculous:** song structure orchestrates performer particles, generated assets, portals and calibrated room surfaces; semantic audio embeddings change scene/material/style state; neural style/LoRA state follows sections while deterministic VFX remains exact at display rate.

## Design rules learned from hardware testing
1. Capture block size is a latency setting, **not** the FFT size. A 256-sample FFT at 48 kHz has 187.5 Hz bin spacing and is unsuitable for a 35–180 Hz bass control.
2. Continuous motion uses smoothed envelopes/phase. Large visual events are sparse and gated.
3. The display loop may read the same audio feature several times; a single audio block must never retrigger multiple musical events.
4. High-frequency content is detail, not the global animation clock.
5. Scene changes need macro musical evidence and preferably phrase boundaries; hard cuts on every onset destroy continuity.
6. Palette richness does not mean random rainbow noise: preserve dark negative space and let strong events temporarily expand the gamut.
7. Particle emission is choreography, not confetti: persistent trajectories/fields establish visual identity and sparse musical accents modulate them.
8. Song Studio publishes state; downstream VFX consume that state. Do not create separate FFT/event detectors in every feature.
9. If particle output looks shaded/muddy, fix feedback floor, bloom threshold and display transform before adding more saturation or fog.
10. A mathematical backdrop is structural light, not wallpaper: keep its mix low enough that particles still read as the foreground instrument.

## Current GPU scene language
### Shader worlds
- **Aurora:** domain-warped luminous veils; bass broadens the field, mids move the flow, highs add fine filaments.
- **Liquid:** chrome/caustic material response with broad musical breathing rather than twitchy pixels.
- **Pulse:** seamless polar/tunnel geometry using integer angular harmonics.
- **Void:** sparse star/nebula field where highs only add fine detail and drops lift the whole space.
- **Cathedral:** architecture branch; standalone Shader Scene Lab Cathedral has been rewritten after static-looking hardware feedback.
- **Journey:** crossfades between shader worlds using drop/max-dwell logic.

### Particle choreography
- **Orbit Reactor:** four phase-locked orbiting emitters.
- **Dual Comet:** opposing beat-phase trajectories.
- **Cathedral Rain:** restrained top-down columns.
- **Vortex Gate:** orbit emitters forming a rotating gate.
- **Constellation Bloom:** sparse idle field that blooms mainly on meaningful events.
- **Reactor Bloom:** nested radial emitter rings that burst outward on marked events.
- **Polar Gate:** eight alternating tangent/radial emitters forming a rotating gate.
- **Ritual Rain:** ordered vertical energy lances with sparse event accents.
- **Helix Fountain:** phase-opposed upward plasma/DNA-like fountain.
- **Nebula Bloom:** low-density breakdown/ambient cloud with rare macro flareups.
- **Techno Lattice:** symmetric beat-quantized emitter lattice for stronger dance material.

### Polar Math background families
- Rose Lattice
- Hypotrochoid Engine
- Log Spiral Interference
- Phyllotaxis Reactor
- Bessel Wave Chamber

## Open problems
- Tempo tracker is intentionally lightweight; syncopated/breakbeat material can still produce half/double-time ambiguity.
- Section tracker is a transparent dynamics heuristic; no chroma/key or learned/novelty-based robust phrase segmentation yet.
- ModernGL particle/shader paths render offscreen then read back into the shared OpenCV sink; direct GL display/shared texture is still the target.
- Particle material rewrite is not yet hardware-tuned after the latest visual changes.
- Shader/particle parameters are launch-time settings; no live hot-control/preset morphing yet.
- Curated built-in banks exist, but user-saved named banks / A-B snapshots do not yet.
- Need real recordings of event precision and Journey transitions across multiple genres before tuning defaults further.

## Next implementation queue
1. Test the vivid material rewrite on projector footage: black floor, saturation, bloom threshold, trail decay and white-core size.
2. Benchmark particle capacities 8k/16k/32k/65k and readback cost; preserve the lowest-latency visually dense operating point.
3. Test `journey` across techno/house/ambient/rock/breakbeat; log section state and bank switches against perceived musical structure.
4. Test Polar Math `backdrop=auto` at low mix and record which bank/equation combinations look intentional.
5. Add chroma/key-class vector + harmonic-change descriptor; use them for palette/asset-state decisions rather than per-frame pixel motion.
6. Add beat/bar-synchronous bank morphing and palette/material transitions without particle-state reset.
7. Add live local IPC/hot controls, user-named banks and A/B snapshots.
8. Add audio-reactive VFX-pack spawning: rare macro events can summon approved sprite/GLB assets rather than random per-beat clutter.
9. Add MIDI/OSC mappings and Ableton Link/clock experiment.
10. Move display to GL-native/shared texture and remove final readback.
11. Route `MusicalSignals` into Performer FX, Human Reactor and Room Skin as a shared state bus.
12. Evaluate CLAP/audio embeddings only after deterministic controls are measured and stable; use embeddings for semantic/style/asset-bank state.

## Metrics
Capture latency, feature age, bass-band stability, event precision, duplicate-event rate, BPM error/confidence, phrase transition precision, Journey switch rate, particle simulation/render/readback p50/p95, active particle count, display FPS/p95, black-level/contrast, highlight saturation, visual jitter under steady tones and setup friction.

## Preset vault
### Shader banks
- `journey_balanced` — broad default.
- `techno_pulse` — kick-heavy techno/house.
- `ambient_void` — sparse/ambient.
- `liquid_melodic` — melodic/electronic.
- `cathedral_installation` — architectural/installational.
- `acid_afterhours` — denser club material.

### Particle banks
- `journey` — section-aware bank conductor; new default.
- `reactor_bloom` — high-value general-purpose radial energy preset candidate.
- `polar_gate` — portal/build candidate.
- `ritual_rain` — restrained atmospheric candidate.
- `helix_fountain` — stable melodic/steady-state candidate.
- `nebula_bloom` — breakdown/ambient candidate.
- `techno_lattice` — drop/dance candidate.
- Original banks remain available as baselines.

CPU legacy: Spectral Bloom / Neon Aurora / Balanced remains the low-dependency fallback.
