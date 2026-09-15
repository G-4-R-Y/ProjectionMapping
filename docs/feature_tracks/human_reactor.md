# Track — Human Reactor

## North star
Turn dance/body motion into a camera-ready artistic rendering system: expressive silhouette energy, controllable temporal echoes/trails, pose-aware body FX, high-quality recording, and eventually composition with Cyber Mage + neural style layers.

## Current state
- Foreground segmentation + optical-flow motion energy.
- Styles: plasma, outline, ghost, ember, xray.
- Palettes: neon, jade, ember, ice, violet, mono.
- Independent edge glow, motion energy, body aura/fill, sparks, feedback, temporal echoes, camera underlay, mirror.
- Rendered-video recording path.
- Projector/fullscreen runtime and telemetry.

## Quality ladder
- **Prototype:** glowing moving silhouette.
- **Usable:** stable feedback/trails and recording.
- **Polished:** strong style/palette controls, clean dance-video output, tunable temporal echoes. **Current.**
- **Advanced:** body-part anchors, pose-aware emissions, gesture events, depth-aware layering, camera/FX compositing modes.
- **Ridiculous:** choreographic event language, multi-performer IDs, skeletal energy networks, neural material skins, beat/gesture fusion, spatial projector lock.

## Open problems
- MOG2 segmentation quality depends strongly on background/lighting.
- No body landmark identity yet; effects are silhouette-level.
- No automatic crop/framing, output codec/profile control, or high-bitrate recording presets.
- No multi-person identity or occlusion policy.

## Next queue
1. Share `PerformerRig` anchors with Cyber Mage.
2. Add optional pose/hand backend while preserving classical fallback.
3. Add anchor-driven joint emitters, limb trails, body-axis ribbons and skeleton arcs.
4. Add recording profiles: vertical 9:16, landscape 16:9, clean alpha/mask sidecar where possible.
5. Add background replacement / matte export and post-production metadata.
6. Add multi-performer tracking/IDs and per-person palette/effect assignment.
7. Add beat/gesture fusion: musical accent changes effect state only when performer motion supports it.

## Metrics
Segmentation stability, motion-to-effect latency, anchor jitter, temporal-echo stability, recording FPS/drop rate, subjective readability of movement, setup time.

## Preset vault
- Ghost + Violet + feedback ~0.92 + 7 echoes — dance afterimage statement.
- Plasma + Neon + camera mix ~0.15 — music-video portrait.
