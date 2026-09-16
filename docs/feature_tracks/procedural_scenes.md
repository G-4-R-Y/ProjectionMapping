# Track — Procedural / Shader Scene Lab

## North star
A library of projector-native, model-free scenes that are visually strong enough to stand alone and can also act as stable high-rate layers beneath neural keyframes. The target is contemporary shader-art quality: continuous domains, coherent motion, vivid emissive color, proper antialiasing/bloom/tonemapping, and no obvious mathematical seams or debug-looking geometry.

The artistic standard is documented in [`../ART_DIRECTION.md`](../ART_DIRECTION.md). A simple but beautiful equation is better than a complicated generic demo. Rough technical experiments are allowed; promising ones must earn an art/incubation pass before promotion.

## Design corrections retained

### 2026-09-15 — CPU scene pack
The first CPU NumPy scene pack was useful for plumbing but visually below target. Hardware viewing exposed a portal seam caused by multiplying `atan2` by a non-integer angular frequency across the -pi/pi branch cut. CPU scenes are now explicitly legacy/fallback.

### 2026-09-16 — visual-quality reset
The user supplied an older casual ModernGL shader study that was significantly more aesthetic/vivid than several repository templates despite being much simpler. This is now a permanent lesson: **do not equate technical complexity with beauty**. Preserve black negative space, luminous contours, coherent radial structure and strong palette travel.

The first `neon_cathedral` was also judged nearly static and ugly. It was rewritten as a moving radial vault with depth ribs, perspective bands, travelling caustics, breathing geometry and an animated oculus.

### 2026-09-16 — Liquid Chrome benchmark / structured-chaos pass
Projector/screen feedback singled out `liquid_chrome` as the first Shader Scene Lab scene that felt genuinely strong; treat it as the current in-repo aesthetic benchmark, not as a sacred implementation. The same test rejected several other scenes as too tame and asked for substantially more structured chaos.

A screenshot also showed that the original `event_horizon` still had a hard horizontal discontinuity. Root cause was the raw `atan(y,x)` coordinate being fed into a non-periodic FBM domain. `event_horizon` has now been rebuilt so angular structure is represented through unit-circle complex harmonics `(cos(n theta), sin(n theta))`; its angular field no longer depends on raw `atan`. The visual smoke probe now measures the two-row jump across the old negative-X branch-cut location as a regression sensor.

The scene library was expanded with four deliberately unstable/chaotic studies: `wormhole_choir`, `plasma_singularity`, `vortex_crown`, and `collapse_flower`. All Shader Scene Lab scenes now expose a `chaos` control that changes domain warping/harmonic interference rather than merely raising brightness.

## Current state

### Legacy CPU fallback
- Portal Architecture — branch-cut seam fixed.
- Bioluminescent Infestation.
- Liquid Cathedral.
- Mechanical Possession.
- Ancient Ruin / Living Moss.
- Ceiling Starfield.

### Shader Scene Lab
- `event_horizon` — atan-free angular field, periodic harmonics, warped accretion/corona/filaments.
- `aurora_void` — multi-stage domain-warped luminous curtains, shredding and sparse lightning/stars.
- `liquid_chrome` — warped ridge/caustic material; **current user-validated aesthetic benchmark**.
- `neon_cathedral` — v2 moving radial vault / perspective / stained-light caustics.
- `wormhole_choir` — multiple log-radius harmonic voices / portal interference.
- `plasma_singularity` — nested domain warps and high-contrast plasma web/shell fields.
- `vortex_crown` — five moving attractors with local radial harmonic crowns.
- `collapse_flower` — nested harmonic petals/fracture field collapsing into a hot core.

### Polar Math Lab — preferred mathematical-art branch
Five dedicated analytic radial families:
- `rose_lattice` — layered rose curves, cross-harmonics and fractured radial detail.
- `hypotrochoid_engine` — rolling-circle / gear-like distance-to-curve geometry with structured perturbation.
- `log_spiral_interference` — three opposing logarithmic spiral wavefields + radial bands.
- `phyllotaxis_reactor` — 96-point golden-angle field with coherent perturbed reactor structure.
- `bessel_wave_chamber` — radial standing-wave / Bessel-like contours with cross-harmonic modulation.

All five now expose a `chaos` parameter. The chaos layer is analytic/cross-harmonic plus Cartesian warping so it can become less perfect and more alive without erasing the underlying equation family into generic noise. Palette terms that previously depended directly on raw angle were replaced where practical with periodic harmonic components to reduce branch-cut color artifacts.

Palettes: spectral, cyber, solar, bio, ultraviolet. The renderer uses saturated emissive contour energy, white-hot local cores, a clean black-floor gate and hue-preserving exponential display mapping rather than a foggy grey post layer.

## Quality ladder
- **Prototype:** CPU procedural images. **Legacy/fallback.**
- **Usable:** GPU fragment scenes with continuous domains and stable fullscreen output.
- **Polished:** visually curated Polar Math / structured-chaos / architecture scenes, per-scene controls, vivid color, clean black floor, smooth transitions, real multiscale bloom and saved presets. **Current implementation is moving here; projector art validation remains the gate.**
- **Advanced:** ping-pong feedback, reaction diffusion, GPU particles, SDF/raymarched architecture, depth/parallax, audio/performer modulation, direct GPU output.
- **Ridiculous:** calibrated surface-aware shader worlds that react to performers/audio and accept sparse neural material/keyframe injections while remaining display-rate and temporally exact.

## Continuity rules
- Polar/angular fields must use periodic integer harmonics, wrapped angular distance, or branch-cut-safe unit-circle representations.
- Feeding raw `atan()` directly into non-periodic noise/domain coordinates is forbidden in promoted radial scenes unless the seam is explicitly intended and masked.
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
- `chaos` should alter structure/topology/flow. A brightness knob relabeled “chaos” does not count.

## Validation
- `experiments/21_visual_probe.py` creates a real OpenGL context and renders every promoted Shader Scene Lab scene, all five Polar Math modes and particle materials in CI.
- It also reports `event_horizon seam_mean/seam_p95` across the old branch-cut location; this is a correctness regression metric, **not** an aesthetic score.
- Mesa/llvmpipe passing does not replace RTX 4050/projector validation.

## Next queue
1. Hardware-test all eight Shader Scene Lab modes and five Polar Math modes on the projector; aggressively art-pass/rewrite weak variants rather than deleting technically promising ones too early.
2. Re-test Event Horizon specifically at the exact camera/screen framing that exposed the horizontal seam; preserve screenshot evidence if any discontinuity remains.
3. Compare every mathematical mode against the user's uploaded radial shader seed on color vividness, contour clarity, motion elegance, negative space and “designed instrument” feel.
4. Add per-mode controls beyond chaos: symmetry/order, density, radial scale, hue velocity, contour width, camera drift, bloom.
5. Add smooth morphing between equation families / singularity studies without a hard reset where mathematically sensible.
6. Add real HDR multiscale bloom/downsample chain and optional temporal accumulation.
7. Add ping-pong feedback / flow-advection mathematical fields.
8. Add high-quality SDF primitives shared with Performer FX: glyphs, runes, HUD arcs, portals and architectural motifs.
9. Route `MusicalSignals` and performer state into selected structural uniforms; Song Studio already drives backdrop chaos/intensity and should remain the integration reference.
10. Add calibrated projector-coordinate masks so walls/ceiling/doors can receive distinct fields.
11. Remove CPU readback with GL-native display/shared texture.

## Metrics
GPU scene frame time, readback time, projector FPS/p95, temporal continuity, branch-cut seam mean/p95, aliasing, black-level/contrast, highlight saturation, scene transition smoothness, parameter reproducibility and subjective projector/recording quality.

## Preset vault
Populate/promote only after hardware viewing. Initial candidates:
- Liquid Chrome / chaos 1.0–1.4 — current benchmark candidate.
- Wormhole Choir / chaos 1.1–1.6.
- Plasma Singularity / chaos 1.0–1.5.
- Vortex Crown / chaos 1.0–1.5.
- Collapse Flower / chaos 0.9–1.4.
- Rose Lattice / Spectral / chaos 1.0–1.4.
- Hypotrochoid Engine / Cyber / chaos 0.8–1.3.
- Log Spiral Interference / Ultraviolet / chaos 1.0–1.5.
- Phyllotaxis Reactor / Bio / chaos 0.8–1.3.
- Bessel Wave Chamber / Solar or Spectral / chaos 0.8–1.3.

A preset is not promoted until it is worth filming.
