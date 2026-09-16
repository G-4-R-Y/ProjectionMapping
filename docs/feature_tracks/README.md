# Feature Tracks

This directory is the no-forgetting research ledger for ProjectionMapping. `ROADMAP.md` remains the milestone-level canonical plan; these files preserve the finer-grained path from prototype -> usable -> polished -> advanced -> ridiculous / research-grade for each feature category.

Before substantial work, agents should also read:
- [`../../MEMORY.md`](../../MEMORY.md) — durable project/hardware/rejected-path handoff memory.
- [`../ART_DIRECTION.md`](../ART_DIRECTION.md) — visual-quality contract and promotion bar.
- [`../../AGENTS.md`](../../AGENTS.md) — repository-level continuation protocol.

Every track should keep the same sections so visual ambition, engineering debt, measurements, and good presets do not disappear between experiments:

1. **North star / finished state** — what excellent looks like.
2. **Current state** — what is actually implemented now; hardware validation is stated separately.
3. **Quality ladder** — Prototype -> Usable -> Polished -> Advanced -> Ridiculous/SOTA-ish.
4. **Research directions** — promising techniques and references to evaluate.
5. **Open problems** — concrete failure modes, not vague TODOs.
6. **Next implementation queue** — ordered actionable work.
7. **Metrics** — latency, temporal stability, registration, frame rate, setup friction, etc.
8. **Preset / operating-point vault** — known-good parameter combinations worth preserving.
9. **Promotion rule** — when a research experiment is allowed into the normal TUI/runtime.

## Tracks

- [`performer_fx.md`](performer_fx.md) — umbrella performer/mixed-reality VFX engine: shared semantic bus, real hands/pose, GPU particles, spell grammar, generated 2D/3D assets, room interactions and neural skinning.
- [`audio_visual.md`](audio_visual.md) — system-audio capture, musical event extraction, shader worlds, particle choreography, MIDI/OSC/latent control.
- [`human_reactor.md`](human_reactor.md) — dance/performance silhouette rendering, recording, pose-aware extensions.
- [`cyber_mage.md`](cyber_mage.md) — generic tracked-point SFX research plus semantic performer effects now converging into Performer FX.
- [`procedural_scenes.md`](procedural_scenes.md) — projector-native procedural worlds, shaders, particles, feedback and stable high-rate visual layers.
- [`neural_mirror.md`](neural_mirror.md) — StreamDiffusion, lightweight GPU profiles, temporal consistency, control maps.
- [`room_skin.md`](room_skin.md) — spatially locked material hallucination and geometry-aware generation.
- [`calibration_mapping.md`](calibration_mapping.md) — structured light, projector/camera geometry, dynamic/multi-projector mapping.
- [`compensation.md`](compensation.md) — radiometry, learned inverse display, closed-loop optimization.
- [`runtime_transport_ui.md`](runtime_transport_ui.md) — fullscreen/runtime, GPU transport, TUI, packaging, diagnostics, reliability.
- [`semantic_room.md`](semantic_room.md) — persistent scene graph and independently controlled room/object behaviors.

## Cross-track rule

Prefer **deterministic spatial ownership first, generative stylization second**. Tracking, geometry, persistent IDs, masks and temporal state should own consistency; neural models decorate or semantically transform those stable structures. Neural output should normally run as sparse/latest-frame-wins semantic updates while procedural/shader/feedback layers maintain high-rate motion.

The shared `PerformanceState` / `TrackingState` / `MusicalSignals` contracts are the cross-feature boundary: Song Studio, Performer FX, Human Reactor, Cyber Mage, Room Skin and Neural Mirror should consume the same semantic state rather than each implementing incompatible tracking/audio logic.
