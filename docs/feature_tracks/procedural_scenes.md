# Track — Procedural / Shader Scene Lab

## North star
A library of projector-native, model-free scenes that are visually strong enough to stand alone and can also act as stable high-rate layers beneath neural keyframes. The target is contemporary shader-art quality: continuous domains, coherent motion, rich material response, proper antialiasing/bloom/tonemapping, and no obvious mathematical seams or debug-looking geometry.

## Design correction — 2026-09-15
The first CPU NumPy scene pack was useful for plumbing but was visually below target. Hardware viewing exposed an especially obvious portal seam: `atan2` was multiplied by a non-integer angular frequency, so the -pi/pi branch cut became visible. The seam is fixed by using integer angular harmonics, but CPU scenes are now explicitly the **legacy/fallback** path rather than the artistic north star.

## Current state
### Legacy CPU fallback
- Portal Architecture — branch-cut seam fixed.
- Bioluminescent Infestation.
- Liquid Cathedral.
- Mechanical Possession.
- Ancient Ruin / Living Moss.
- Ceiling Starfield.

### ModernGL shader path
New **Shader Scene Lab / ModernGL** renders full-frame GLSL fragment scenes offscreen and hands the final frame to the existing projector sink:
- `event_horizon` — seamless polar harmonics, turbulent accretion/filaments and lens field.
- `aurora_void` — domain-warped luminous curtains and sparse stars.
- `liquid_chrome` — warped fBm/ridge material with chromatic specular response.
- `neon_cathedral` — symmetric architectural field with arches, columns, fog and floor perspective.

Current shader path includes filmic compression, vignette and projector-friendly dark backgrounds. ModernGL tries EGL first on Linux and falls back to the platform default standalone context.

## Quality ladder
- **Prototype:** CPU procedural images. **Legacy/fallback.**
- **Usable:** GPU fragment-shader scenes with continuous domains and stable fullscreen output. **Current implementation; hardware validation pending.**
- **Polished:** per-scene art controls, curated palettes, smooth transitions, proper multi-scale bloom, antialiasing, color management and saved presets.
- **Advanced:** ping-pong feedback, reaction diffusion, GPU particles, SDF/raymarched architecture, depth/parallax, audio/performer modulation, direct GPU output.
- **Ridiculous:** calibrated surface-aware shader worlds that react to performers/audio and accept sparse neural material/keyframe injections while remaining display-rate and temporally exact.

## Continuity rules
- Polar/angular fields must use periodic integer harmonics or branch-cut-safe `(sin(a), cos(a))` representations.
- Time animation should advect/deform a stable field, not randomly regenerate texture every frame.
- Random-looking structure should derive from deterministic spatial hashes/noise, not per-frame random seeds.
- Feedback scenes must use controlled decay/advection and bounded energy.
- Scene transitions must interpolate state/palettes/fields rather than hard-cut incompatible coordinate systems unless a hard cut is intentional.

## Next queue
1. Hardware-test the four ModernGL scenes and aggressively delete/rewrite anything that still reads as generic shader-demo art.
2. Add per-scene controls rather than only speed/intensity: palette, density, depth, turbulence, glow, structure scale, camera drift.
3. Add multi-pass bloom/downsample pyramid and optional temporal accumulation.
4. Add ping-pong feedback / flow advection scenes.
5. Add high-quality SDF primitives shared with Cyber Mage: glyphs, runes, HUD arcs, portals, architectural motifs.
6. Add GPU particle/vector fields and reaction-diffusion materials.
7. Add smooth scene morph/transition controller and preset banks.
8. Route audio musical state and persistent tracked-point fields into selected shader uniforms.
9. Add projector-coordinate surface masks so wall/ceiling/door can receive different shader worlds.
10. Allow Neural Mirror/Room Skin to inject sparse semantic textures/keyframes into procedural motion.
11. Remove CPU readback by moving display/transport to a GL/shared-texture path where platform allows.

## Metrics
GPU scene frame time, readback time, projector FPS/p95 frame time, temporal continuity, visible seams, aliasing, black-level/contrast readability, scene transition smoothness, parameter reproducibility, and subjective footage/projector quality.
