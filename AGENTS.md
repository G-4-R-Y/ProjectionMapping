# AGENTS.md — ProjectionMapping agent bootstrap

Before making non-trivial changes in this repository, read these files in order:

1. `MEMORY.md` — durable project memory, hardware findings, rejected approaches and non-negotiable rules.
2. `ROADMAP.md` — canonical milestone/progress plan.
3. `docs/ART_DIRECTION.md` — visual-quality contract. This project is judged on projected/recorded output, not code complexity.
4. The relevant file under `docs/feature_tracks/` for the subsystem being changed.

## Working rules

- Distinguish **implemented**, **CI-tested**, and **hardware/projector-validated**. Never collapse these into one claim.
- Inspect current code and recent run logs before proposing a rewrite.
- Preserve deterministic tracking/geometry/state as the owner of spatial and temporal continuity; neural generation is an optional semantic/style layer.
- Neural inference is latest-frame-wins; do not queue stale visual frames.
- Keep 6 GiB GPU operation conservative and explicit about VRAM headroom.
- Preserve F11 fullscreen toggle and ESC child-exit behavior.
- Do not promote OpenCV/debug lines/circles or generic template shaders as final art.
- Prefer one visually convincing, measurable vertical slice over many mediocre demo branches.
- When hardware feedback rejects a visual/technical direction, record why in the relevant feature track before replacing it.
- Update `ROADMAP.md` + the relevant feature track whenever a meaningful milestone moves.
- Add/adjust registry entries, dependencies and tests for new runnable artifacts.

## Visual standard

A simple coherent shader with vivid color, dark negative space, elegant motion and clean emissive contours can be better than a technically elaborate shader. Read `docs/ART_DIRECTION.md` and compare new work against the current best visuals, not against the oldest prototype.

## Handoff note

When ending a substantial work session, leave enough durable state in `MEMORY.md`, `ROADMAP.md` and the feature track that another capable agent can answer:
- what was attempted;
- what actually worked;
- what failed and why;
- what hardware has or has not validated it;
- which operating points/presets are worth preserving;
- what the next highest-value experiment is.
