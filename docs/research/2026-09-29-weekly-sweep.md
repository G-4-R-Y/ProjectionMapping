# Weekly research sweep — 2026-09-29

Window: 2026-09-22 through 2026-09-29. The previous sweep already covered Brush,
SuperSplat Editor viewport-warp work and Spark; those were not counted again.

## Promoted: output-space surface masks

Source: https://github.com/bhoffmann93/three-projection-mapper

On 2026-09-26, three-projection-mapper changed polygon and feather masking so the
mask is evaluated over the warped content and the polygon stays fixed in output
space. That is directly relevant to Room Skin and the existing M4 requirement for
calibrated surface masks: a light-leak mask should describe the projector output,
not move because source content or a calibration warp changed.

Upstream is MIT-licensed but explicitly alpha / breaking-change territory, and it
is a Three.js runtime. We therefore did not add it as a dependency or copy its
implementation. This sweep adds a small native NumPy baseline instead:

- src/projection_mapping/surface_mask.py
- normalized output-space polygon masks
- pixel-space polygon feathering
- projector-frame edge feathering
- optional background composition
- cached callable processor for runtime pipelines
- unit coverage in tests/test_surface_mask.py

This is an implementation baseline, not hardware validation. It still needs to be
wired into a calibrated Room Skin/projector compositor and checked for leakage,
edge quality and cost on the actual projector.

## Watch: Fosfora 2.0 and post-release fixes

Source: https://github.com/kevinraymond/fosfora

Fosfora 2.0 landed on 2026-09-27 and is unusually aligned with this project:
Rust/wgpu, 56 live-editable WGSL effects, an eight-layer VJ stack, MIDI/OSC/phone
control, audio analysis, Spout/Syphon/NDI/virtual-camera output, scene cues and
headless signal analysis. The project is dual MIT/Apache-2.0.

The most useful changes after 2.0 are architectural references rather than a good
dependency fit for the current Python/ModernGL runtime:

- 2026-09-28: a default-on photosensitivity flash limiter with 3 flashes/s and a
  stricter reduced-motion mode.
- 2026-09-28: shader time wraps hourly in f64 before conversion to f32 to avoid
  long-show precision stutter.
- 2026-09-28/29: OSC, MIDI, web and audio queues use drop-oldest semantics so the
  newest control/audio state wins after render stalls.
- 2026-09-29: remote-control hardening and pinned/checksummed model/runtime
  downloads.

Deferred rather than integrated wholesale: Fosfora is a second full rendering
engine with a Rust 1.97+/wgpu/Vulkan-or-Metal stack. Importing it would duplicate
the renderer and dependency surface. The flash limiter is worth implementing as
a separate projector-output safety pass later. The shader-clock fix also deserves
a native solution, but a simple modulo would introduce an hourly phase jump in
our existing GLSL worlds; use a continuity-safe clock representation before
changing promoted scenes.

## Watch: SuperSplat Viewer 1.36.0 stochastic renderer

Source: https://github.com/playcanvas/supersplat-viewer

SuperSplat Viewer added an experimental WebGPU stochastic splat renderer on
2026-09-26 and released 1.36.0 on 2026-09-28 with smaller TAA history, sky and
near-plane fixes, and renderer debug tools. The viewer is MIT-licensed and the
new path renders unsorted, depth-tested splats with a WebGPU-only stochastic
mode.

This is a strong reference for M10 volumetric/spatial work, but it stays a
research note: it is a PlayCanvas/TypeScript/WebGPU renderer, not a small adapter
to the current ModernGL pipeline. Revisit when the project has a dedicated
volumetric layer or when a browser/WebGPU renderer becomes an intentional
transport target.


## Watch: Spektral 0.17.1

Source: https://github.com/kaltwrk/spektral

Spektral 0.17.1 landed on 2026-09-27. It is an MIT-licensed, focused WebGPU
runtime for fullscreen WGSL, feedback and compute rather than a full 3D engine.
The current-week release is mainly stability work around canvas pointer setup,
shader-error overlays and the browser playground, while the underlying 0.17
series provides render/feedback/compute passes, source-mapped WGSL diagnostics
and inspectable render-graph snapshots.

This is a strong future browser/WebGPU shader-runtime reference, but not a good
small integration today: it requires a modern Node/WebGPU path and would fork
the existing Python/ModernGL renderer. Keep it in view for a deliberate WebGPU
preview/output target rather than introducing a second shader runtime casually.

## Watch: vgpu WebGPU performance work

Source: https://github.com/vercel-labs/vgpu

vgpu is MIT-licensed and exposes typed WGSL, explicit render passes, browser and
headless Node backends, plus a deterministic mock adapter for tests. On
2026-09-23 it changed persistent-uniform handling so unused frame uniforms defer
uploads while one-shot draws/dispatches flush pending values, with regression
and native-GPU coverage.

The performance/testing ideas are useful for a future WebGPU transport or shader
test harness, but the TypeScript/Node/Dawn stack is intentionally deferred for
the same reason as Spektral: it should arrive only if WebGPU becomes a deliberate
runtime target, not as a parallel dependency tree beside ModernGL.

## Repository notes from this sweep

The architecture remains coherent: deterministic tracking/geometry/shaders own
spatial continuity; slower neural systems are additive; child renderers remain
isolated; hardware claims stay pending real-rig validation.

The roadmap still mentioned hosted cross-platform and Mesa visual-smoke CI even
though GitHub Actions was intentionally removed on 2026-09-27. This sweep updates
that wording to local/on-demand smoke coverage and does not add any workflow.
