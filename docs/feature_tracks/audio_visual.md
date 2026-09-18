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
- `MusicStructureTracker` provides a transparent baseline `breakdown/build/drop/release/steady` section state plus phrase phase; it is explicitly a heuristic baseline, not claimed as semantic song understanding.
- GPU shader branch: `Audio Visual Instrument / GPU` with Aurora/Liquid/Pulse/Void/Cathedral + Journey crossfades.
- GPU particle branch: `Song Studio / GPU Particle Stage` with persistent particle state, feedback/advection and music-aware choreography.
- Particle material was rewritten after hardware feedback that it looked covered by a grey shade: current target is white-hot core + saturated shell + same-hue halo + thresholded bloom + chromatic feedback + clean black floor.
- Original choreography banks: `orbit_reactor`, `dual_comet`, `cathedral_rain`, `vortex_gate`, `constellation_bloom`.
- Additional choreography banks: `reactor_bloom`, `polar_gate`, `ritual_rain`, `helix_fountain`, `nebula_bloom`, `techno_lattice`.
- New structured-chaos choreography studies: `lissajous_storm`, `singularity_crown`, `prism_shards`.
- New **cosmic vector-field particle worlds**: `cosmic_roam`, `binary_star`, `event_horizon_drift`,
  `accretion_storm`, and `supernova_nebula`. GPU particles can now inhabit authored flow
  families (`flow / nebula / binary_star / event_horizon / cosmic_roam`) instead of every bank
  sharing one generic curl field. Bass controls gravitational collapse, mids/highs shape
  curl/nebula motion, and sparse drops can drive singularity/supernova events.
- `journey` mode chooses banks at section/phrase boundaries without resetting the particle simulation.
- Journey bank changes now smoothstep-morph emitter position/velocity/energy and continuous field
  parameters; `backdrop=auto` crossfades the old/new mathematical worlds over the same transition.
  The existing persistent GPU particle state is not reset. Projector/art validation is pending.
- Song Studio backdrop conductor supports **both** all five Polar Math families and all Shader Scene Lab scenes through `scene:<id>`; `backdrop=auto` chooses a structural backdrop per choreography bank.
- Shader/Polar backdrop chaos is driven by macro section energy, mids and sparse drops, while backdrop mix stays deliberately restrained so particle light remains the foreground hierarchy.
- `techno_lattice -> liquid_chrome` is deliberately included because Liquid Chrome is the current strongest user-validated Shader Scene Lab aesthetic; other auto pairings are research candidates rather than promoted presets.
- Polar Math backdrops expose structured chaos as analytic cross-harmonic/domain deformation rather than generic noise; Song Studio can modulate the same control without resetting the mathematical field.
- Particle bank parameters are driven by musical role: beat/bar phase sets coherent trajectories; loudness sets density; bass broadens/energizes fields; strikes create bursts; drops alter macro emission; highs are not the global animation clock.
- Shader palettes: Neon Aurora, Solar Flare, Bioluminescent, Intelli, Mono Accent, Prismatic. Particle palettes: cyber, solar, bio, prismatic.
- Particle sprite materials: plasma, comet, spark, mote, shock-ring.
- Smooth/Balanced/Punchy/Chaotic musical reactivity modes and Calm<->Madness macro remain available.
- Curated shader performance banks: `journey_balanced`, `techno_pulse`, `ambient_void`, `liquid_melodic`, `cathedral_installation`, `acid_afterhours`.
- Previous NumPy/OpenCV studio remains available as a CPU legacy fallback rather than the art-quality target.

## Quality ladder
- **Prototype:** audio reaches visual.
- **Usable:** stable loopback + band-separated motion.
- **Polished:** rolling spectral analysis, sparse adaptive events, tempo phase, persistent particle choreography, vivid emissive materials, section-aware Journey and curated launchable banks. **Implemented; projector/art validation ongoing.**
- **Advanced:** chroma/key, stronger phrase boundaries, reliable half/double-time handling, beat-synchronous bank/palette/material/backdrop morphing, user snapshots, live controls and MIDI/OSC/Ableton clock.
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
10. A mathematical/shader backdrop is structural light, not wallpaper: keep its mix low enough that particles still read as the foreground instrument.
11. “Chaos” should modulate topology/warp/interference/density, not just overall intensity. Musical drops may temporarily raise chaos; ordinary beats should not randomize the whole scene.
12. Keep `backdrop=none` as a clean A/B baseline. A fancy backdrop that makes the particle instrument less legible is a regression.
13. Chaotic choreography should be deterministic and phase-coherent. Lissajous/harmonic motion can look wild while remaining temporally exact; random per-frame emitter placement is not acceptable.

## Current GPU scene language
### Shader worlds / chaotic backdrops
- **Liquid Chrome:** current strongest in-repo Shader Scene Lab aesthetic; warped chrome/caustic ridge material and a useful benchmark for saturation/motion quality.
- **Event Horizon:** rebuilt around unit-circle harmonics instead of a raw-angle FBM coordinate after a projector screenshot exposed a horizontal branch-cut seam.
- **Aurora Void:** multi-stage warped luminous curtains / sparse lightning.
- **Neon Cathedral v2:** moving architecture branch with radial vaults, perspective floor, caustics and oculus.
- **Wormhole Choir:** log-radius multi-harmonic portal voices.
- **Plasma Singularity:** nested domain-warp plasma web/shell field.
- **Vortex Crown:** multiple moving attractors and local harmonic crowns.
- **Collapse Flower:** layered radial petals/fractures collapsing toward a hot center.

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
- **Lissajous Storm:** eight phase-offset 3:2 Lissajous emitters with analytic velocity derivatives; visually chaotic but exactly periodic/phase coherent.
- **Singularity Crown:** asymmetric eight-emitter crown with alternating implosion/explosion velocities and shock-ring drop accents.
- **Prism Shards:** sparse rotating radial shard emitters that keep black space and explode outward on strong accents.

### Polar Math background families
- Rose Lattice — cross-harmonic floral/mechanical contour field.
- Hypotrochoid Engine — rolling-circle ritual machine.
- Log Spiral Interference — three-way spiral interference/portal field.
- Phyllotaxis Reactor — perturbed 96-point golden-angle reactor.
- Bessel Wave Chamber — cross-harmonic radial standing-wave chamber.

### `backdrop=auto` research mapping
- Orbit Reactor -> Bessel Wave Chamber
- Dual Comet -> Wormhole Choir
- Cathedral Rain -> Neon Cathedral
- Vortex Gate -> Event Horizon
- Constellation Bloom -> Phyllotaxis Reactor
- Reactor Bloom -> Plasma Singularity
- Polar Gate -> Vortex Crown
- Ritual Rain -> Rose Lattice
- Helix Fountain -> Collapse Flower
- Nebula Bloom -> Aurora Void
- Techno Lattice -> Liquid Chrome
- Lissajous Storm -> Liquid Chrome
- Singularity Crown -> Vortex Crown
- Prism Shards -> Log Spiral Interference

These mappings are **implemented experiments**, not all promoted artistic presets yet.

## Reusable visual asset packs
Current reusable manifests now include:
- `particle_arsenal` — plasma/comet/spark/mote/shock-ring materials.
- `ritual_geometry` — all five Polar Math shader assets.
- `singularity_suite` — Event Horizon + Wormhole Choir + Plasma Singularity + Vortex Crown + Collapse Flower.
- `holographic_overlays` — Liquid Chrome/Aurora/Cathedral plus incubation slots for future hex/scanline overlays.
- existing `spell_arsenal`, `neon_core`, and `mr_summons` remain available for performer/MR convergence.

The next step is not to spawn these on every beat. Asset spawning should happen on sparse macro events/sections with persistent entity lifetimes.

## Open problems
- Tempo tracker is intentionally lightweight; syncopated/breakbeat material can still produce half/double-time ambiguity.
- Section tracker is a transparent dynamics heuristic; no chroma/key or learned/novelty-based robust phrase segmentation yet.
- ModernGL particle/shader paths render offscreen then read back into the shared OpenCV sink; direct GL display/shared texture is still the target.
- Particle material rewrite still needs hardware tuning after the latest visual changes.
- Cosmic vector fields are implemented and GL-smoke-covered but still need RTX/projector art tuning:
  tune gravity, advection and density so they read as astronomical motion rather than particle soup.
- Shader/particle parameters are launch-time settings; no live hot-control/preset morphing yet.
- Curated built-in banks exist, but user-saved named banks / A-B snapshots do not yet.
- Transition duration and auto-pairing still need projector tuning; palette/material are global particle
  shader state and currently switch at the morph midpoint rather than being dual-rendered.
- The three new chaos choreography banks are manual research banks first; only promote them into automatic Journey routing after projector tests.
- Need real recordings of event precision and Journey transitions across multiple genres before tuning defaults further.

## Next implementation queue
1. Projector-test the vivid particle rewrite with `backdrop=none`: black floor, saturation, bloom threshold, trail decay and white-core size.
2. Projector-test `lissajous_storm`, `singularity_crown`, and `prism_shards` individually; compare readability/continuity against existing banks rather than rewarding density alone.
3. Projector-test each chaotic backdrop independently; compare against Liquid Chrome as the current internal quality benchmark.
4. Test `journey + backdrop=auto` across techno/house/ambient/rock/breakbeat at low mix; record which pairings are additive and which become visual soup.
5. 🟡 Projector-tune the implemented phrase/drop-synchronous backdrop crossfade and choreography
   morph; evaluate transition duration and the midpoint palette/material switch.
6. Benchmark particle capacities 8k/16k/32k/65k and GL readback cost; preserve the lowest-latency visually dense operating point.
7. Add chroma/key-class vector + harmonic-change descriptor; use them for palette/asset-state decisions rather than per-frame pixel motion.
8. Add live local IPC/hot controls, user-named banks and A/B snapshots.
9. Add audio-reactive VFX-pack / generated-asset spawning: rare macro events can summon approved sprite/GLB entities with persistent lifetimes.
10. Add MIDI/OSC mappings and Ableton Link/clock experiment.
11. Move display to GL-native/shared texture and remove final readback.
12. Route `MusicalSignals` into Performer FX, Human Reactor and Room Skin as a shared state bus.
13. Evaluate CLAP/audio embeddings only after deterministic controls are measured and stable; use embeddings for semantic/style/asset-bank state.

## Metrics
Capture latency, feature age, bass-band stability, event precision, duplicate-event rate, BPM error/confidence, phrase transition precision, Journey switch rate, backdrop switch rate, particle simulation/render/readback p50/p95, active particle count, display FPS/p95, black-level/contrast, highlight saturation, visual jitter under steady tones and setup friction.

## Preset vault
### Shader banks
- `journey_balanced` — broad default.
- `techno_pulse` — kick-heavy techno/house.
- `ambient_void` — sparse/ambient.
- `liquid_melodic` — melodic/electronic.
- `cathedral_installation` — architectural/installational.
- `acid_afterhours` — denser club material.

### Particle banks
- `journey` — section-aware bank conductor; current default.
- `reactor_bloom` — high-value general-purpose radial energy candidate.
- `polar_gate` — portal/build candidate.
- `ritual_rain` — restrained atmospheric candidate.
- `helix_fountain` — stable melodic/steady-state candidate.
- `nebula_bloom` — breakdown/ambient candidate.
- `techno_lattice` — drop/dance candidate.
- `lissajous_storm` — structured-chaos / flowing comet candidate; projector verdict pending.
- `singularity_crown` — implosion/explosion macro candidate; projector verdict pending.
- `prism_shards` — sparse high-contrast accent candidate; projector verdict pending.
- Original banks remain available as baselines.

### Backdrop candidates
- `scene:liquid_chrome` at low mix — current strongest shader benchmark.
- `scene:wormhole_choir`, `scene:plasma_singularity`, `scene:vortex_crown`, `scene:collapse_flower` — new chaos candidates; projector verdict pending.
- Polar Math chaos 0.8–1.4 — equation-specific art pass range; projector verdict pending.

CPU legacy: Spectral Bloom / Neon Aurora / Balanced remains the low-dependency fallback.
