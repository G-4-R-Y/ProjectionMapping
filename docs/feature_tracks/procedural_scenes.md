# Track — Procedural / Shader Scene Lab

## North star
A library of projector-native, model-free scenes that are visually strong enough to stand alone and can also act as stable high-rate layers beneath neural keyframes. The target is contemporary shader-art quality: continuous domains, coherent motion, vivid emissive color, proper antialiasing/bloom/tonemapping, and no obvious mathematical seams or debug-looking geometry.

The artistic standard is documented in [`../ART_DIRECTION.md`](../ART_DIRECTION.md). A simple but beautiful equation is better than a complicated generic demo.

## Design corrections retained

### 2026-09-15 — CPU scene pack
The first CPU NumPy scene pack was useful for plumbing but visually below target. Hardware viewing exposed a portal seam caused by multiplying `atan2` by a non-integer angular frequency across the -pi/pi branch cut. CPU scenes are now explicitly legacy/fallback.

### 2026-09-16 — visual-quality reset
The user supplied an older casual ModernGL shader study that was significantly more aesthetic/vivid than several repository templates despite being much simpler. This is now a permanent lesson: **do not equate technical complexity with beauty**. Preserve black negative space, luminous contours, coherent radial structure and strong palette travel.

The first `neon_cathedral` was also judged nearly static and ugly. It was rewritten as a moving radial vault with depth ribs, perspective bands, travelling caustics, breathing geometry and an animated oculus.

## Current state

### Legacy CPU fallback
- Portal Architecture — branch-cut seam fixed.
- Bioluminescent Infestation.
- Liquid Cathedral.
- Mechanical Possession.
- Ancient Ruin / Living Moss.
- Ceiling Starfield.

### Shader Scene Lab
- `event_horizon` — polar harmonics / accretion filaments.
- `aurora_void` — luminous curtains and sparse stars.
- `liquid_chrome` — warped ridge/caustic material.
- `neon_cathedral` — v2 moving radial vault / perspective / stained-light caustics.

### Polar Math Lab — new preferred mathematical-art branch
Five dedicated analytic radial families:
- `rose_lattice` — layered rose curves and angular harmonics.
- `hypotrochoid_engine` — rolling-circle / gear-like distance-to-curve geometry.
- `log_spiral_interference` — opposing logarithmic spiral wavefields and radial shock bands.
- `phyllotaxis_reactor` — golden-angle point field with coherent rotating reactor structure.
- `bessel_wave_chamber` — radial standing-wave / Bessel-like contours with angular modulation.

Palettes: spectral, cyber, solar, bio, ultraviolet. The renderer uses saturated emissive contour energy, white-hot local cores and a hue-preserving exponential display transform rather than a foggy grey post layer.

## Quality ladder
- **Prototype:** CPU procedural images. **Legacy/fallback.**
- **Usable:** GPU fragment scenes with continuous domains and stable fullscreen output.
- **Polished:** visually curated Polar Math / architecture scenes, per-scene controls, vivid color, clean black floor, smooth transitions, real multiscale bloom and saved presets. **Current implementation is moving here; hardware/art validation pending.**
- **Advanced:** ping-pong feedback, reaction diffusion, GPU particles, SDF/raymarched architecture, depth/parallax, audio/performer modulation, direct GPU output.
- **Ridiculous:** calibrated surface-aware shader worlds that react to performers/audio and accept sparse neural material/keyframe injections while remaining display-rate and temporally exact.

## Continuity rules
- Polar/angular fields must use periodic integer harmonics or branch-cut-safe `(sin(a), cos(a))` representations.
- Time animation should advect/deform a stable field, not randomly regenerate texture every frame.
- Random-looking structure derives from deterministic spatial hashes/noise, not per-frame seeds.
- Feedback uses controlled decay/advection and bounded energy.
- Scene transitions interpolate state/palettes/fields unless a hard cut is artistically intentional.

## Art promotion rules
- No weak scene survives merely because it already exists.
- Black must remain black enough for projection contrast.
- Bloom comes from highlights, not every pixel.
- Macro composition must read from across the room.
- High-frequency detail supports the main structure rather than becoming noise.
- A scene should remain compelling for at least a minute of continuous motion.

## Next queue
1. Hardware-test all five Polar Math modes and Cathedral v2 on the projector; aggressively rewrite/delete weak variants.
2. Compare against the user's uploaded radial shader seed, specifically color vividness, contour clarity, motion elegance and negative space.
3. Add per-mode controls: symmetry/order, density, radial scale, hue velocity, contour width, camera drift, bloom.
4. Add smooth morphing between equation families without a hard reset where mathematically sensible.
5. Add real multiscale HDR bloom/downsample chain and optional temporal accumulation.
6. Add ping-pong feedback / flow-advection mathematical fields.
7. Add high-quality SDF primitives shared with Performer FX: glyphs, runes, HUD arcs, portals and architectural motifs.
8. Route `MusicalSignals` and performer state into selected uniforms without turning the scene into jitter.
9. Add calibrated projector-coordinate masks so walls/ceiling/doors can receive distinct fields.
10. Remove CPU readback with GL-native display/shared texture.

## Metrics
GPU scene frame time, readback time, projector FPS/p95, temporal continuity, visible seams, aliasing, black-level/contrast, highlight saturation, scene transition smoothness, parameter reproducibility and subjective projector/recording quality.

## Preset vault
Populate only after hardware viewing. Initial candidates:
- Rose Lattice / Spectral
- Hypotrochoid Engine / Cyber
- Log Spiral Interference / Ultraviolet
- Phyllotaxis Reactor / Bio
- Bessel Wave Chamber / Solar or Spectral

A preset is not promoted until it is worth filming.
