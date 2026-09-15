# Track — Semantic Room

## North star
A persistent scene graph where walls, ceiling, floor, furniture, plants, doors, people and tracked body parts have stable identities and independently controllable visual behaviors that obey geometry/occlusion.

## Current state
- Concept and effect-routing direction documented.
- Building blocks exist separately: masks, optical flow, Room Skin, Human Reactor, Cyber Mage anchors, procedural scenes, calibration infrastructure.
- No persistent scene graph runtime yet.

## Quality ladder
- **Prototype:** manual region masks.
- **Usable:** semantic masks + per-region effects.
- **Polished:** persistent object IDs, occlusion rules, live controls, saved behavior map.
- **Advanced:** depth-aware scene graph, per-object generative/procedural pipelines, interaction between person and room surfaces.
- **Ridiculous:** room-scale spatial hallucination instrument where performer gestures/audio alter persistent materials/portals/lighting across calibrated surfaces with closed-loop compensation.

## Next queue
1. Static room reference + manually named surface masks as baseline.
2. Add semantic segmentation and persistent region IDs.
3. Add depth ordering/occlusion graph.
4. Route independent procedural scenes/materials per region.
5. Integrate PerformerRig as person/body subgraph.
6. Allow Cyber Mage spells to target room nodes (wall portal, floor glyph, bookshelf machinery, ceiling starfield).
7. Add per-node prompts/styles and sparse neural keyframes.
8. Add OSC/MIDI/phone performance controls and scene snapshots.
9. Close the loop with calibrated projection and compensation.

## Metrics
ID persistence, mask leakage, occlusion correctness, region registration, effect latency, scene load/save reproducibility, frame rate with N active nodes.
