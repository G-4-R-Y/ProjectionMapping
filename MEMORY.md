# ProjectionMapping — Project Memory / Agent Handoff

This file is the durable working memory for humans and auxiliary agents continuing this repository. Read it together with `ROADMAP.md` and `docs/feature_tracks/README.md` before making substantial changes.

It is intentionally opinionated: it preserves successful decisions, hardware findings, rejected approaches, visual-quality standards, and the reasoning behind the current architecture so a future agent does not rediscover old mistakes or silently regress the project.

## 1. North star

Build a fully open, extensible realtime spatial-performance / mixed-reality instrument:

`camera + audio + controls + generated assets -> shared semantic state -> deterministic high-rate GPU rendering -> optional sparse neural semantic/style updates -> projector calibration/compensation -> room -> camera feedback`

The project should eventually support:
- projector-native installations and room transformation;
- performer/body/hand tracked SFX comparable in polish to strong TouchDesigner work;
- music-driven visual choreography that responds to musical structure rather than FFT noise;
- generated 2D/3D assets from external pipelines such as Genforge;
- mixed-reality summons/entities/arena-like interactions;
- realtime neural style/material transformation when it adds something deterministic graphics cannot.

TouchDesigner is an **aesthetic and workflow reference**, not a required dependency. The canonical runtime should remain open-source.

## 2. Non-negotiable architecture rules

1. **Deterministic spatial ownership first; generative stylization second.** Tracking, geometry, IDs, masks and room calibration decide where an effect belongs. AI may decorate/transform that stable state.
2. **Latest-frame-wins neural inference.** Never build a queue of stale camera frames.
3. **Shared state, not feature islands.** `TrackingState`, `PerformanceState`, `MusicalSignals`, gestures and room events should be reusable across Performer FX, Human Reactor, Song Studio, Neural Mirror and Room Skin.
4. **Generated assets are content, not motion logic.** Renderer/tracking/physics own continuity.
5. **Prototype freely; promote selectively.** Debug primitives, ugly technical sketches and rough shaders are acceptable research scaffolding when they test a meaningful idea. They are not the art-quality target and must not silently become the default experience without an art/refinement pass.
6. **Keep classical/deterministic baselines beside learned paths.** A research model is promoted only when it beats a simpler baseline on actual hardware or unlocks a qualitatively new effect.
7. **Measure latency and stability.** Prefer p50/p95/p99 timings, track age/confidence, render/readback cost, VRAM headroom and temporal residuals over vague speed claims.
8. **Hardware validation is separate from implementation.** Never claim a path is validated because code/CI exists.
9. **F11 toggles fullscreen; ESC exits only the child visual and returns to the same feature configuration with the same session values.** Launching must not pop/reset the configuration screen; testing a visual must never force the operator to re-enter settings.
10. **Keep the feature tracks updated.** Major work is incomplete until the appropriate `docs/feature_tracks/*.md` file and `ROADMAP.md` are updated.

## 3. Current hardware targets

Primary laptop test machine observed in logs:
- Linux 6.8 / X11
- NVIDIA RTX 4050 Laptop GPU
- 6141 MiB VRAM, ~5.6 GiB free idle
- Python 3.10 supported

Stronger desktop target:
- RTX 4080
- Windows path is especially relevant for Spout/shared-texture workflows and heavier neural modes.

Design 6 GiB profiles conservatively. Do not let optional TensorRT/xFormers/model caches consume all free VRAM.

## 4. Important hardware findings / fixes

### Linux camera
An old camera implementation selected DirectShow merely because the OpenCV constant existed. Fixed: Windows uses DSHOW/MSMF/ANY, Linux uses V4L2/ANY, macOS AVFoundation/ANY.

### Linux system audio
System loopback was confirmed working through the native Pulse/PipeWire monitor path (`parec`). Keep that path first on Linux with SoundCard as fallback.

### Audio spectral resolution
Never tie FFT size to capture block size. A 256-sample FFT at 48 kHz has 187.5 Hz bin spacing and is useless for a 35–180 Hz bass control. Current design keeps 128/256-sample capture possible while rolling ~2048 samples for spectral analysis.

### Neural Mirror xFormers failure
A real test showed SD-Turbo loaded, then StreamDiffusion failed specifically when xFormers was requested but unavailable. xFormers is optional; the backend now falls back to native PyTorch attention rather than treating it as mandatory.

### Mixed-reality asset launch failure
The first MR asset TUI test exited in argparse because the asset field was empty and `--asset` was required. That was a product/registry contract bug, not an OpenGL/RTMPose/render failure. The stage now defaults to built-in procedural meshes so the pipeline can be smoke-tested without an external GLB.

### ModernGL packaging warning
Desktop packaging previously omitted the graphics extra/context package. `moderngl` + `glcontext` are now explicit; Linux context creation probes EGL first. Use `experiments/18_graphics_probe.py` when graphics availability is ambiguous.

### Control-deck lag and child cleanup
The original Textual deck reread the complete growing log multiple times per 350 ms tick and repainted
the hidden dashboard while an operator scrolled a configuration screen. Long sessions therefore became
progressively laggy. Log reads are now incremental/bounded and hidden-screen repaint is suppressed.
The primary operator surface is now the localhost browser deck (`projection-ui`); Textual remains the
`projection-tui` fallback. A separate lifecycle bug allowed POSIX helpers to survive when the direct
renderer parent exited normally. The launcher now retains and sweeps the dedicated process group on
normal exit, Stop, replacement launch and shutdown. CI has an automated 20-cycle no-survivor test;
actual RTX RAM/VRAM return-to-baseline still requires hardware measurement.

### Manual surface-mapping baseline
The first operator-usable spatial mapping slice is `experiments/33_surface_mapper.py`, exposed as
**Surface Mapper / Corner Pin**. It supports multiple draggable projector-space quads, normalized
source UVs, polygon masks, opacity, distance-based feathering and autosaved JSON profiles. The
reusable `SurfaceMapProcessor` is the CPU reference path for other frame pipelines. This is manual
planar registration and has CI coverage; it is not projector-validated dense calibration or lens
correction. Keep it as the geometry editor and CPU reference for the GPU playback path below.

### GPU-native mapped-scene vertical slice
`experiments/34_gpu_mapped_scene.py` consumes the same surface-map JSON profile and renders a
promoted Shader Scene Lab world into a GPU texture, then applies per-surface homography, convex mask,
opacity and pixel-consistent feathering in a second shader before presenting directly through a
GLFW-owned swapchain. The frame loop performs no framebuffer readback or OpenCV resize. This path
also uses actual GLFW monitor enumeration instead of the legacy `display * 1920` heuristic. Shader
compilation/offscreen composition is CI-tested on available OpenGL; the native window, monitor
selection, VSync behavior and projector result still require physical-machine validation. Keep the
CPU Surface Mapper as the editor/reference until GPU-side live editing is implemented.

### Shader preset vault and scene diversity
Shader Scene Lab now contains 12 GPU scene families. Crystal Cavern, Solar Loom, Abyssal Garden and
Prism Mirage extend the earlier radial/plasma set with faceted, filament, bioluminescent-organic and
folded spectral architecture. A shared 12-look authored preset vault drives both normal Shader Scene
Lab and GPU-Mapped Shader Scene; each look fixes scene, speed, intensity and chaos, while `custom`
preserves direct controls. Registry choice labels keep human-readable names in both the primary
browser deck and Textual fallback without changing stable CLI IDs. All looks compile and render in
the software OpenGL probe and show temporal motion; projector beauty/readability remains unvalidated.
User feedback after the diversity pass still ranks the liquid shaders as the strongest visual family.
Treat this as a broader material preference—not loyalty to only one preset: prioritize evolving
fluid metallic surfaces, caustic folds, refractive/emissive flow and liquid motion hierarchy. New
families should either learn from that material depth and coherence or clearly outperform it.

## 5. Rejected promoted directions / lessons — do not repeat blindly

These are not bans on experimentation. They describe implementations that failed as promoted/default experiences. A new experiment may revisit an underlying idea if it changes the failure mechanism and documents why.

### Fake semantic hands from silhouette extrema
The first Cyber Mage treated upper-silhouette left/right extrema as hands. Gesture logic such as hands-together therefore frequently did nothing. Never build semantic gesture behavior on guessed silhouette extrema.

### Generic OpenCV Cyber Mage aesthetics
Circles, straight lines and debug-like geometry were rejected as visually cheap as final presentation. They remain acceptable diagnostic scaffolding. The active promoted direction is real point/landmark tracking + GPU particles + analytic SDF/GLSL effects.

### Generic template shader scenes
Several early procedural/shader scenes looked like stock demos and failed the artistic bar. In particular, the first Cathedral scene read as nearly static. The lesson is not “never make an ugly shader”; it is “do not stop at the first technically functioning shader.” If the underlying spatial/math idea has potential, keep it in research/incubation and iterate composition, palette, motion and materials. Rewrite/demote/retire only when appropriate.

### Muddy particle tone mapping
The first GPU particle material looked as if a grey shade/film covered the vivid colors. Causes include broad low-threshold bloom, persistent low-energy feedback and per-channel Reinhard compression. Current direction: white-hot cores, saturated shells, thresholded bloom, clean black floor and hue-preserving exponential display transform.

## 6. Art direction — this matters as much as plumbing

The user supplied an older casual ModernGL shader playground made after roughly two hours of shader experimentation. Despite being technically simple, its visible result was judged **substantially more aesthetic, vivid and colorful** than several of this repository's earlier shader templates. Treat that as a benchmark and a warning: complexity is not artistic quality.

Useful properties of that reference:
- aspect-correct centered coordinates;
- radial distance as the primary spatial language;
- repeated domains / layered harmonics;
- cosine palettes with strong saturated color travel;
- narrow inverse-distance luminous contours;
- simple coherent time motion;
- black background and obvious bright structures;
- no apologetic grey fog covering the image.

Current visual target:
- vivid emissive color;
- strong negative space;
- white-hot local cores, not globally whitened frames;
- mathematical coherence and symmetry where appropriate;
- motion hierarchy: continuous field motion + sparse strong events;
- projection-readable macro forms with high-frequency detail layered on top;
- no random rainbow noise merely to create complexity.

### Experimental art philosophy
Technical interest is valuable even before the art is good. Use three gates:

1. **Prototype/research:** allowed to be ugly, crude or unstable if it tests a meaningful rendering, mathematical, tracking, spatial, interaction or neural idea.
2. **Incubation/art pass:** if there is potential, invest. Improve composition, palette, material/light hierarchy, motion, transitions and post-processing. User criticism/projector feedback is iteration data.
3. **Promotion/default:** only after the idea is visually convincing, robust and worth sustained projection/recording.

Do not prematurely delete a promising experiment because its first visual pass is weak. Preserve the useful technical seed and keep pushing the art. Conversely, do not defend a mediocre promoted visual merely because the implementation is clever.

Read `docs/ART_DIRECTION.md` before creating/promoting a new visual scene.

## 7. Current renderer / visual lanes

### Song Studio
The highest-potential branch. Musical analysis produces `MusicalSignals`; a GPU particle stage turns them into persistent choreography. Current direction includes section/phrase-aware Journey control, analytic/math backdrops, and authored cosmic vector fields (nebula advection, binary-star gravity, event-horizon collapse, wandering multi-well flow). Music should conduct a scene, not twitch every pixel.

### Performer FX
Preferred open performer-effects path:
`RTMPose/whole-body -> semantic anchors -> SpellGrammar -> GPU particles + SDF spell geometry -> optional generated assets -> projector`.

Generic LK point tracking remains useful for fabric, hair, props and non-semantic motion even when real landmarks are present.

### Polar Math Lab
Analytic vivid radial shader branch with five equation families:
- rose lattice;
- hypotrochoid engine;
- log-spiral interference;
- phyllotaxis reactor;
- Bessel wave chamber.

This branch exists specifically to raise the art bar beyond generic procedural templates.

### Shader Scene Lab
Keep as a scene-research branch, not sacred legacy. Event Horizon/Aurora/Liquid can evolve; Cathedral was rewritten once already because the original was too static. Promising technical ideas should be incubated and improved; weak promoted defaults should be rewritten or demoted rather than preserved out of inertia.

### Neural Mirror
Use neural video as semantic/material skin, not as the source of exact hand/room geometry. Existing baseline flow-warps previous neural output between sparse AI keyframes and measures residuals.

### Mixed Reality assets
Built-in assets make bring-up possible without files; external GLB/glTF/OBJ can come from Genforge or other content pipelines. The current mesh renderer is geometry/normals/emissive-first; PBR textures, skins and animation are future work.

## 8. Current generated/built-in asset vocabulary

Built-in MR mesh names should stay usable as test fixtures:
- `builtin:cyber_orb`
- `builtin:energy_ring`
- `builtin:crystal`
- `builtin:relic`
- `builtin:drone`
- `builtin:sigil_totem`
- `builtin:summon_proxy`

VFX packs should retain generator/model/prompt/seed/provenance/license metadata when available.

## 9. Song Studio design rules

- Continuous bass/mids/highs modulate broad field properties; they do not all trigger discrete events.
- Highs are detail, not the global clock.
- Strong visual events use adaptive gates + refractory spacing.
- One captured audio block can trigger an event at most once even if the display loop reads it multiple times.
- Scene/choreography changes prefer phrase boundaries; drops may override dwell for an urgent change.
- Particle state should survive choreography transitions rather than resetting.
- Default particle background can be pure black. If a Polar Math background is enabled, blend it as restrained emissive structure, not haze.
- Record useful operating points in `docs/feature_tracks/audio_visual.md`.

## 10. Neural/video continuity ladder

1. deterministic high-rate geometry/points/landmarks;
2. previous-frame optical-flow warp;
3. blend fresh neural keyframes against motion prediction;
4. stable seed/style/prompt interpolation;
5. mask-aware compositing;
6. prior-style/latent/state reuse where the backend allows;
7. pose/depth/edge/semantic control maps;
8. TemporalNet/StreamV2V/causal video experiments;
9. newer video models only when they beat the measured baseline on latency/VRAM/stability.

Never claim a generative model mathematically guarantees frame consistency.

## 11. Useful commands

Typical development setup:

```bash
git pull
source .venv/bin/activate
python -m pip install -e '.[ui,vision,audio,graphics,performer,assets3d,interop,dev]'
projection-ui
```

Equivalent browser-deck module command: `python -m projection_mapping.web_ui`. Use
`projection-tui` only as the Textual fallback.

Graphics probe:

```bash
python experiments/18_graphics_probe.py
```

High-end visual shader/material probe:

```bash
python experiments/21_visual_probe.py
```

Run tests:

```bash
python -m pytest -q
python -m ruff check src tests --select E9,F63,F7,F82
```

## 12. Handoff protocol for future agents

Before changing a subsystem:
1. Read this file.
2. Read `ROADMAP.md`.
3. Read the subsystem feature track.
4. Inspect current implementation and recent hardware logs before proposing a rewrite.
5. Separate facts observed on hardware from hypotheses.
6. Preserve good presets and rejected-path lessons in the track.
7. Implement a measurable baseline before adding a research-heavy model.
8. Update tests and registry/dependency declarations when adding a runnable artifact.
9. Update the roadmap/track with what is **implemented**, **CI-tested**, and **still speculative**.
10. Experiment broadly beneath the surface, but prefer finishing one visually convincing vertical slice at a time for the promoted/default experience.

## 13. Immediate quality priorities

1. Validate the vivid particle material overhaul on the RTX 4050/projector; tune bloom/black floor from actual footage.
2. Validate all five Polar Math modes and identify which deserve deeper art investment; do not discard interesting math solely for an ugly first pass.
3. Make Song Studio Journey reliably move between choreography banks at musically sensible boundaries.
4. Continue improving GPU spell/SDF geometry and generated assets.
5. Validate RTMPose hand/body anchors and performer FX latency.
6. Add PBR/animated generated-asset rendering and the Genforge exporter contract.
7. Remove GL -> CPU readback once the visual language is worth preserving.
8. Then integrate performer/audio/room state and neural skinning into one coherent stage system.

The standard for promoted work is not merely “works”. The standard is **worth filming and projecting**. The standard for an early experiment is different: **does it teach us something or open a path worth refining?**
