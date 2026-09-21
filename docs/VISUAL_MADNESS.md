# Visual Madness Playbook

The target is not "AI video on a wall." The target is a room whose apparent material, topology and behavior become unstable while physical geometry still reads clearly.

## Design law

Use diffusion/video models for **semantic mutation** and conventional realtime graphics for **motion, continuity and violence**.

`semantic keyframe -> depth/edges/segmentation -> optical-flow advection -> shaders/particles/feedback -> spatial warp -> projector`

This gives AI-level semantic richness without asking a diffusion model to generate every display frame.

## Scene families

### 1. Bioluminescent infestation
- walls develop vascular growth and fungal membranes
- plants emit impossible internal light
- shelves become root systems / coral / circuitry
- motion causes spores and filaments to detach into particles
- bass expands growth; transients trigger branching

### 2. Liquid cathedral
- preserve wall/door/shelf edges but reinterpret materials as wet carved stone, chrome, glass and volumetric light
- projected architecture appears deeper than the wall
- slow raymarched caustics between semantic keyframes
- human silhouettes disturb the reflected structure like a fluid surface

### 3. Mechanical possession
- furniture remains geometrically locked while seams open into gears, pistons and impossible machinery
- optical flow drives sparks, hydraulic motion and debris
- hands can become local attractors/repulsors

### 4. Ancient ruin / living moss
- optimize semantic appearance toward moss, wet stone, roots, dust and age rather than exact RGB reproduction
- use closed-loop compensation so the real wall contributes to the illusion rather than fighting it
- slowly shift the target material over minutes, not frames

### 5. Portal architecture
- doors/windows become spatial discontinuities
- depth-conditioned parallax inside portals
- scene behind the opening can use a different renderer/model than the wall
- use hard geometry masks so the portal boundary never drifts

### 6. Human reactor
- person silhouette is not merely stylized: body regions become effect sources
- hands emit particles / fluid / tendrils
- head/torso can carry a separate semantic material
- motion magnitude controls local feedback gain
- pose events trigger abrupt state changes

### 7. Semantic operating system
Assign each persistent scene object its own graph:

```text
wall       -> slow environment shader + semantic texture
plants     -> alien vegetation model + glow feedback
bookshelf  -> mechanical material transform
door       -> portal renderer
ceiling    -> starfield / volumetric field
person     -> neural mirror
hands      -> particle/fluid emitters
```

## Shader performance deck

The ModernGL Shader Scene Lab is now a performance instrument rather than a single-look experiment.

- liquid family: `liquid_chrome`, `liquid_membrane`, `holographic_oil`, `ferrofluid_bloom`, `data_tide`
- palette layer: cyan/magenta default, plus ultraviolet, deep ocean, sunset neon, spectral and mono
- any scene can crossfade into any other scene inside the same shader pass
- palette phase can drift continuously without changing geometry
- curated presets combine scene pair, crossfade, palette, chaos, speed, intensity and palette drift
- `Shader Performance Deck` exposes the presets as one-click looks; `Shader Scene Lab` remains the detailed manual surface

Current preset bank:
`liquid_neon`, `mercury_bloom`, `membrane_flux`, `data_tide`,
`cathedral_dream`, and `singularity_choir`.

The design rule is to treat liquid/chrome as a reusable material language, not a one-off effect.
Crossfades should preserve continuous motion so changing looks feels like the projected material is
mutating rather than switching scenes.

## Performance Director

The high-level performance layer now treats shaders and particles as one instrument:

```text
AudioFeatures
  -> MusicalSignals
  -> MusicStructure
  -> PerformanceDirector
       -> cue identity / transition
       -> shared MADNESS macro
       -> Shader Performance Deck
       -> GPU particle choreography
  -> screen/additive composition
  -> projector
```

Three sequencing modes are implemented:

- `timed` — authored cue journeys with deterministic maximum dwell;
- `musical` — breakdown/build/drop/release evidence selects cue identity;
- `hybrid` — authored journey is the backbone, phrase/section changes steer it, and strong drops
  can interrupt immediately.

The shared macro intentionally changes several visual dimensions at once. As MADNESS rises, shader
chaos/intensity/palette drift, particle emission/turbulence/bloom/vector-field force, and the
shader/particle composite amount rise together. It is a coordinated art-direction control, not a
single brightness knob.

Initial journeys: `liquid_arc`, `neon_ritual`, `cosmic_rave`.

## Temporal strategy

A slower neural renderer should create semantic keyframes. Between them:

1. advect the previous keyframe using optical flow;
2. run procedural feedback / particles / fluid at display rate;
3. blend a new neural keyframe only when available;
4. preserve high-confidence physical edges;
5. use segmentation/depth to keep effects in object space;
6. never queue old neural frames.

## Closed-loop insanity

Once projector-camera calibration and appearance compensation work, the objective does not have to be pixel reconstruction. Optimize for a perceptual target:

- LPIPS for visual appearance
- DINO/self-supervised features for structure/material similarity
- segmentation consistency to keep semantic boundaries stable
- CLIP-like semantic objectives for broad appearance concepts
- eventually diffusion features / learned priors

Then the question becomes not "what RGB should I project?" but:

> What light should I emit so this physical wall is perceived as wet alien stone?

## Performance priorities

1. motion-to-photon latency
2. temporal stability
3. geometric registration
4. semantic quality
5. raw diffusion FPS

A gorgeous 12 FPS semantic layer over a locked 60/120 FPS graphics system can look better than an unstable nominally faster model.

## First ecstatic target

**Neural Room Skin v1**

- structured-light calibrated wall
- stable clean-room reference
- optical-flow advection
- StreamDiffusion semantic keyframes
- edge/depth ControlNet once available
- procedural reaction-diffusion + particle feedback at display rate
- radiometric compensation
- Spout -> TouchDesigner -> projector
- one live macro control called `MADNESS` that simultaneously increases semantic mutation, shader feedback, particle density and prompt/LoRA interpolation

The system should remain recognizably attached to the real room while looking increasingly impossible as `MADNESS -> 1.0`.
