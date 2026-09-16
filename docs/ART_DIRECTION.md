# Art Direction / Visual Quality Bar

This document is the visual design contract for ProjectionMapping. The project is technically ambitious, but technical novelty does not excuse mediocre imagery.

## Core lesson

A small user-supplied ModernGL shader playground produced a more appealing result than several earlier repository scene templates despite using much simpler code. That reference used a centered/aspect-correct domain, radial distance, repeated coordinates, cosine palettes, narrow luminous contours and coherent time evolution. It looked vivid because the image had a clear visual thesis.

The implication is important: **do not confuse shader complexity with artistic quality**. A 20-line equation with good color, hierarchy and motion can beat a large procedural system with weak composition.

## Promotion test for every visual

Before promoting a shader/particle preset into the normal TUI, ask:

- Does it have a strong silhouette / macro composition at projector distance?
- Is there a clear primary motion rather than every pixel moving independently?
- Are bright regions genuinely emissive and saturated, or covered by grey bloom/fog?
- Does black stay black enough to create contrast?
- Are high-frequency details subordinate to the main form?
- Does the motion loop/read continuously with no branch-cut seam or static deadness?
- Does it still look intentional after 60 seconds rather than only in a screenshot?
- Is the color system coherent rather than random rainbow noise?
- Does it look better on recorded/projected footage than the simpler baseline?

If not, keep it in research/legacy or rewrite it.

## Preferred visual language

### Color
- White-hot cores only where energy is highest.
- Saturated emissive shells: cyan/blue/magenta, acid green/teal, solar orange/crimson, ultraviolet.
- Dark negative space.
- Palette motion should be smooth and meaningful.
- Avoid low-saturation grey overlays unless a scene explicitly calls for smoke/fog.

### Light
Think in layers:
1. hard/white core;
2. saturated inner emission;
3. softer colored halo;
4. sparse far glow;
5. thresholded bloom from highlights only.

Do not bloom the entire image.

### Motion
Use hierarchy:
- large continuous field/depth movement;
- medium structural deformation;
- local detail motion;
- sparse event accents.

Music/gesture events should not turn every degree of freedom into random jitter.

### Geometry
Strong candidates:
- polar/radial systems;
- rose curves and angular harmonics;
- hypotrochoid/epitrochoid families;
- logarithmic spirals;
- phyllotaxis/golden-angle fields;
- Bessel/radial-wave structures;
- SDF sigils/glyphs/rings;
- coherent vector fields / curl-like advection;
- ribbons and velocity-oriented particles;
- projected architectural forms with real depth motion.

## Polar Math Lab

The first five equation families are deliberately different in composition:

### Rose Lattice
`r(theta) ~ r0 + A cos(k theta + phase)` with multiple odd/even harmonic layers. Should read floral, mechanical and symmetric, not like a static mandala wallpaper.

### Hypotrochoid Engine
Parametric rolling-circle curves. Multiple rotating curve families should create a cyber-mechanical ritual machine. Use actual distance-to-curve glow rather than generic rings.

### Log Spiral Interference
Couple `log(r)` with positive/negative angular modes. The perceptual goal is depth/portal motion without visible `atan` branch seams.

### Phyllotaxis Reactor
Golden-angle point placement with a coherent rotating/breathing field. Must stay legible at projector scale: dense mathematical structure, not undifferentiated dots.

### Bessel Wave Chamber
Radial standing-wave contours with angular modulation. Scientific/installation feel; clean oscillatory structure rather than fake random noise.

## Song Studio visual mapping

The Song Studio is a conductor:
- bass -> broad radius / scale / depth / force;
- mids -> flow / tangent velocity / deformation;
- highs -> sparse fine detail;
- beat phase -> stable periodic motion;
- strike -> local accent / flash / burst;
- drop -> macro state change;
- phrase/section -> choreography or scene changes.

Particles, Polar Math, SDF spells and generated assets should share this grammar.

## Particle material contract

Particle cores should be readable as light sources, not translucent grey sprites.

Current target material:
- compact white-hot core;
- strongly saturated shell;
- soft same-hue halo;
- optional velocity spark streak/cross detail;
- additive composition;
- chromatic feedback that decays to black;
- thresholded bloom;
- hue-preserving display mapping.

If the output looks like there is a shade/film over it, investigate feedback floor, bloom threshold and tone mapping before increasing saturation knobs.

## Cathedral / architecture rule

A scene called Cathedral must feel spatial and alive. Static repeated arches are insufficient.

Required ingredients for a promoted cathedral-like preset:
- moving depth/vault rhythm;
- perspective/vanishing structure;
- time-varying caustic or stained-light component;
- slow breathing/parallax motion;
- layered symmetry;
- a focal oculus/altar/core;
- no generic grid wallpaper.

## Generated assets

Generated 2D/3D assets should inherit the same art language. Prefer strong silhouettes and emissive material masks. Keep generation provenance so an asset can be regenerated/tuned rather than manually patched into a dead end.

Built-in procedural assets are test fixtures and design sketches, not the final content ceiling.

## Failure policy

Do not protect weak visuals because they cost engineering time. Record the lesson in a feature track, then replace them. The visual system should evolve like a curated instrument, not accumulate every experiment forever.
