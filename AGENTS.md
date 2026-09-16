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
- **Do experiment.** A technically interesting prototype is allowed to be rough or ugly if it tests a meaningful rendering, interaction, mathematical, spatial, or neural idea.
- Judge prototypes on **potential + information gained**; judge promoted visuals on **artistic quality + robustness**. Do not confuse the two gates.
- If a rough experiment has a strong idea underneath it, iterate the composition, palette, material, motion hierarchy and post stack before abandoning it.
- When hardware feedback rejects the current look, treat that as iteration data. Record why it failed and either improve the promising idea or explicitly retire it if the concept itself is a dead end.
- Update `ROADMAP.md` + the relevant feature track whenever a meaningful milestone moves.
- Add/adjust registry entries, dependencies and tests for new runnable artifacts.

## Visual standard

A simple coherent shader with vivid color, dark negative space, elegant motion and clean emissive contours can be better than a technically elaborate shader. At the same time, technical exploration is valuable: the project should tolerate ugly early experiments when they open a genuinely interesting path, then invest in making the promising ones beautiful. Read `docs/ART_DIRECTION.md` and compare promoted work against the current best visuals, not against the oldest prototype.

## Handoff note

When ending a substantial work session, leave enough durable state in `MEMORY.md`, `ROADMAP.md` and the feature track that another capable agent can answer:
- what was attempted;
- what actually worked;
- what failed and why;
- what hardware has or has not validated it;
- which operating points/presets are worth preserving;
- what the next highest-value experiment is.
