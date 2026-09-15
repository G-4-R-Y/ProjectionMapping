# Track — Cyber Mage

## North star
A stable, performer-owned techno-magic system: tracked hands/body anchors drive sigils, runes, arcs, trails, portals, auras, floor glyphs and gesture-triggered spell states. Deterministic realtime rendering owns spatial consistency; neural video/diffusion is a slower semantic/style skin layered on top.

## Current state
- `PerformerRig` classical baseline with persistent semantic anchors: head, chest/core, left/right hands, left/right feet.
- Gesture baseline: arms spread, hands together, hands raised, motion burst.
- Persistent `SpellStateMachine`: charge/charged -> release, shield, ascension and motion-cast energies with cooldown/decay.
- Deterministic renderer: palm/chest sigils, hand/core plasma arcs, trails, aura, charge orb, release shock ring, shield rings, ascension halo, cast pulses and ground glyph.
- Palettes: arcane, solar, void, jade.
- TUI feature: `Cyber Mage`, including charge-time control.

## Quality ladder
- **Prototype:** camera silhouette with magic-circle overlays.
- **Usable:** persistent anchors, smoothing, body-owned effects, temporal spell states, clean fullscreen operation. **Current baseline.**
- **Polished:** real pose/hand landmarks, robust gestures, effect modules with fine-grained controls, good presets, graceful loss/reacquisition.
- **Advanced:** predictive tracking, depth/occlusion, multi-layer particles/SDF glyphs, room-surface portals, audio+gesture state machine, multi-performer IDs.
- **Ridiculous:** deterministic 60+ FPS spatial rig + lower-rate ControlNet/StreamV2V/temporal neural skin, projector-calibrated room interaction, semantic spell choreography, generative material changes attached to body and room surfaces.

## Architecture contract
`camera -> segmentation/pose/hands/flow -> PerformerRig -> gesture/event state -> SpellStateMachine -> deterministic FX modules -> optional neural style skin -> projector warp/compensation`

Effects must consume semantic anchors/state, not raw pixel positions scattered through renderer code. A learned tracker may replace the anchor estimator without changing effect modules.

## Effect modules to split out
- `SigilRenderer`: concentric runes, arc segments, SDF glyph rings, rotating seals.
- `ArcRenderer`: hand-hand, hand-core, limb/room lightning/plasma.
- `TrailRenderer`: palm/staff/limb ribbons with history and decay.
- `EmitterRenderer`: sparks, embers, particles, fluid seeds from joints.
- `AuraRenderer`: silhouette plasma, halo, inner/outer glow.
- `PortalRenderer`: palm/chest/shoulder/floor portals.
- `GroundGlyphRenderer`: perspective/depth-aware circles locked under performer.

## Gesture vocabulary
Implemented baseline: charge = hands together; shield/summon = arms spread; ascension = hands raised; generic cast = motion burst. Next gestures: directed thrust, swipe, spin, jump and crouch. Gestures need confidence, hysteresis, cooldowns and explicit state transitions rather than one-frame booleans.

## Temporal consistency strategy
1. Persistent tracked IDs/anchors.
2. EMA/Kalman/predictive smoothing using measured motion-to-photon latency.
3. Persistent spell/effect state and particle IDs.
4. Optical-flow/pose warping of previous style layers.
5. Stable prompt/seed/style bank and low denoise for neural layer.
6. Cross-frame/video model conditioning only after deterministic ownership works.

## Neural style-skin path
Feed current camera + performer mask + pose/edge/depth + deterministic energy mask + flow-warped previous stylized frame into low-strength streaming img2img/video diffusion. Keep AI inference latest-frame-wins at modest resolution on 6 GB cards; deterministic renderer continues at projector refresh. Evaluate TemporalNet/StreamV2V/ControlNet/IP-Adapter on stronger hardware.

## Open problems
- Classical contour anchors are approximations, especially for crossed arms/occlusion.
- No real hand landmarks/finger gestures yet.
- Current spell gestures are coarse body-shape/motion events, not directional hand kinematics.
- No depth-aware occlusion or room calibration in Cyber Mage path.
- Sigils are OpenCV primitives; need proper GLSL/SDF glyph system for higher quality.
- No live preset morph or audio fusion yet.

## Next queue
1. Optional MediaPipe pose + hand backend behind `PerformerRig` interface; retain classical fallback.
2. Landmark confidence/loss handling and per-anchor prediction.
3. Derive hand velocity/direction and add thrust/swipe/spin/jump/crouch detectors to state machine.
4. Split effect renderer into composable modules and expose per-module enable/intensity/scale/color controls.
5. Add SDF/GLSL rune/glyph atlas and particle field.
6. Fuse audio events with gestures: music can arm/intensify a spell, performer motion decides release.
7. Add depth/segmentation occlusion and floor-plane estimation.
8. Add calibrated room anchors: portal on wall, floor glyph in projector coordinates, hand-emitted light hitting surfaces.
9. Add neural style-skin prototype with previous-frame flow warp + low-denoise StreamDiffusion.
10. Evaluate temporal video models only if they improve stability at acceptable latency/VRAM.

## Metrics
Anchor jitter in pixels, reacquisition time, gesture precision/false trigger rate, spell-state trigger precision, motion-to-effect latency, effect ownership under fast motion, display FPS, neural keyframe age, temporal flicker, VRAM, projector registration error.
