# Personalization and Control-Surface Contract

ProjectionMapping is becoming an instrument, not a list of scripts. Every visual may expose many parameters, but the operator should not have to mentally separate hardware setup from artistic intent every time a feature opens.

The console therefore groups parameters by **operator intent**. New registry entries may set `group = "..."` explicitly; old entries are automatically inferred into the same boxes so the whole control deck improves without a flag day.

## Canonical control boxes

### System & Input
Things describing **where signals come from** rather than what the artwork should look like.

Typical controls:
- system audio vs microphone
- audio device / loopback source
- input sensitivity / gain
- camera device and capture source
- tracking/model source when it behaves like an input dependency

Example:

```toml
[[feature.param]]
key = "source"
flag = "--source"
label = "Audio source"
type = "choice"
default = "system"
choices = ["system", "mic"]
group = "System & Input"
```

### Output & Resolution
Things describing **where and at what raster size the visual is rendered/projected**.

Typical controls:
- projector/display index
- internal render width/height
- projector/output width/height
- fullscreen/output-routing settings

These should stay visually separated from shader equations. Changing a projector resolution is not an artistic mutation.

### Design Customization
The main creative box: **what the visual is**.

Typical controls:
- equation / mathematical family
- palette/material/style
- structural equation parameters (`μ`, `σ`, knot frequencies, optical scale, symmetry count, etc.)
- backdrop family
- world scale
- compositional intensity
- particle material/choreography

Mathematical labs should prefer **named interpretable parameters** over anonymous `param1/param2` where possible. Generic A/B parameters are acceptable during incubation, but promoted experiences should rename them according to the actual equation.

Example:

```toml
[[feature.param]]
key = "growth_center"
flag = "--growth-center"
label = "Growth center μ"
type = "float"
default = 0.28
min = 0.02
max = 0.95
group = "Design Customization"
help = "Lenia-style preferred neighborhood mass."
```

### Behavior & Reactivity
Controls describing **how the visual moves or responds**.

Typical controls:
- audio reactivity mode
- calm ↔ madness
- thresholds/gates
- feedback / trail persistence
- smoothing
- animation speed
- decay / damping / excitation / drive
- transition time

A useful distinction: equation structure belongs in Design Customization; how quickly/strongly that structure responds belongs here.

### Performance & Advanced
Controls that mostly trade quality, latency, stability, or GPU/CPU cost.

Typical controls:
- particle capacity
- simulation steps per frame
- attractor point count
- FFT analysis window / capture block size
- iteration counts
- acceleration/precision choices
- VRAM reserve / advanced backend switches

These should not be the first controls an artist sees when deciding how a scene should feel.

## Automatic grouping

`FeatureParam.ui_group` uses explicit TOML `group` metadata when present. Otherwise the registry infers a sensible box from the parameter key/flag. This keeps legacy features organized while allowing carefully designed experiences to override the fallback.

Stable box order:

1. System & Input
2. Output & Resolution
3. Design Customization
4. Behavior & Reactivity
5. Performance & Advanced

Custom group names are allowed for specialist tools, but reusable public-facing experiences should prefer the canonical boxes.

## Personalization levels

The long-term control model has four layers:

### Hardware profile
Persistent machine/room settings that should eventually be inherited globally:
- projector/display
- camera/audio devices
- calibration bundle
- render/output resolution
- transport backend

### Experience preset
Named artistic snapshot for one feature:
- equation/mode
- palette/material
- structural parameters
- choreography/backdrop
- reactivity curve

Examples: `Acid Afterhours`, `Violet Gyroid`, `Schottky Rain`, `Lissajous Storm`.

### Performance macros
Small high-level controls that fan out to many low-level parameters:
- **MADNESS** — structured complexity, turbulence, event density
- **ENERGY** — emissive intensity / particle population / forcing
- **DEPTH** — scale, parallax, feedback, volumetric density
- **LOCK** — temporal/spatial stability vs free motion

Macros should never destroy access to expert controls; they are an expressive front layer.

### Live modulation
Signals that continuously modulate a saved preset:
- `MusicalSignals`
- performer anchors/velocity/gesture events
- room-surface events
- MIDI/OSC/gamepad/phone controls
- future semantic/neural control signals

A saved preset is the base state; live modulation is additive/temporary rather than silently rewriting the preset.

## Design rules for new features

1. **Separate environment from art.** Input/output controls should never be mixed randomly between palette/equation controls.
2. **Expose meaningful math.** If a shader has a beautiful parameter space, make the useful axes editable and name them.
3. **Curate defaults.** Default values are an art decision and should produce something worth looking at immediately.
4. **Keep expert escape hatches.** Simulation steps, resolution and iteration counts remain available but live in Performance & Advanced.
5. **Add help text where a parameter is non-obvious.** The console renders `help` below the relevant control.
6. **Prefer ranges with known safe/stable operating regions.** Do not expose a numerical instability as a normal artistic slider without guardrails.
7. **Preserve reproducibility.** Seeds, preset names and generated-asset metadata should make a good result recoverable.
8. **Promote only after projector testing.** A technically valid parameter space may still need a strong curated subrange before becoming a default experience.

## Song Studio example

Song Studio is the reference for the taxonomy:

```text
SYSTEM & INPUT
  Audio source
  Audio device
  Input sensitivity

OUTPUT & RESOLUTION
  Projector display
  Particle render resolution
  Projector resolution

DESIGN CUSTOMIZATION
  Particle choreography
  Backdrop / conductor world
  Particle/math palettes
  Backdrop mix
  Backdrop structured chaos

BEHAVIOR & REACTIVITY
  Musical reactivity
  Calm ↔ madness
  onset / beat gates

PERFORMANCE & ADVANCED
  GPU particle capacity
  FFT analysis window
  audio capture block
```

The goal is that a performer can find creative controls immediately while a technical operator can still reach the system and performance settings in the same screen.

## Next personalization work

- persistent global hardware profiles
- named per-feature presets and A/B snapshots
- preset export/import as TOML/JSON
- favorites and curated preset banks
- live parameter IPC so changing a control does not restart the visual
- collapsible groups and an optional `basic / expert` control level
- per-parameter MIDI/OSC mapping
- random/mutation explorer constrained to safe artistic ranges
- scene playlists and beat/phrase-synchronous preset morphs
- generated-asset browser with thumbnails/tags/license metadata
- automatic capture of a preset when the user marks a visual as worth keeping

The control deck should eventually feel like a synthesizer and VJ console whose oscillators happen to include PDEs, complex analysis, geometry, particles, neural generation and calibrated room surfaces.
