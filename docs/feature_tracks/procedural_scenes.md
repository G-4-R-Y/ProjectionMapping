# Track — Procedural Scene Lab

## North star
A library of projector-native, zero-model-latency scenes that are visually strong enough to stand alone and also serve as stable high-rate layers beneath neural keyframes: architecture, portals, materials, stars, caustics, machinery, vegetation and feedback systems.

## Current state
- Portal Architecture
- Bioluminescent Infestation
- Liquid Cathedral
- Mechanical Possession
- Ancient Ruin / Living Moss
- Ceiling Starfield
- configurable speed/intensity, projector dimensions, F11 fullscreen

## Quality ladder
- **Prototype:** CPU procedural images.
- **Usable:** curated scene family with stable projector output. **Current.**
- **Polished:** scene-specific fine controls, curated palettes, transitions, preset banks and higher-quality antialiasing/composition.
- **Advanced:** GLSL/GPU implementations, feedback buffers, reaction diffusion, particles, signed-distance geometry, depth/parallax and audio/performer modulation.
- **Ridiculous:** calibrated surface-aware procedural worlds that interact with performers/audio and accept sparse neural material/keyframe injections while remaining high-rate and temporally exact.

## Next queue
1. Port expensive scenes to GLSL/GPU path.
2. Add scene-specific palettes and parameter surfaces rather than only speed/intensity.
3. Add smooth scene morph/transition layer.
4. Add persistent feedback/reaction-diffusion/particle scenes.
5. Add SDF architecture/rune/HUD primitives shared with Cyber Mage.
6. Route audio musical state and performer anchors into selected procedural parameters.
7. Add projector-coordinate/surface masks so a scene can target wall/ceiling/door independently.
8. Allow Neural Mirror/Room Skin to inject sparse semantic textures or keyframes into procedural motion.

## Metrics
Display FPS at projector resolution, CPU/GPU utilization, frame-time variance, visual aliasing, transition smoothness, subjective projector contrast/readability, parameter reproducibility.
