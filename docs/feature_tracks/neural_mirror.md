# Track — Neural Mirror / Streaming Generative Video

## North star
Realtime semantic transformation that preserves performer/room structure over time, scales from a safe 6 GB laptop profile to a stronger desktop path, and never compromises display responsiveness or process stability.

## Current state
- Daydream StreamDiffusion backend with latest-frame-wins async worker.
- 6 GB safe profile and optional-acceleration fallback.
- VRAM guard, process isolation, cleanup, stage diagnostics, benchmark harness.
- Live camera img2img path; model/prompt runtime integration exists.

## Quality ladder
- **Prototype:** live frame -> diffusion -> display.
- **Usable:** safe startup, bounded latency, 6 GB operating point, native-attention fallback. **Current.**
- **Polished:** prompt/style presets, smooth prompt transitions, similarity skipping, temporal stabilization, mask-aware compositing.
- **Advanced:** flow/latent propagation, pose/depth/edge controls, TemporalNet/StreamV2V evaluation, identity/style persistence.
- **Ridiculous:** structure-preserving streaming video editing integrated with calibrated room geometry and deterministic 60+ FPS FX between neural semantic keyframes.

## How temporal consistency should be built
Video generation does not provide a hard guarantee; consistency comes from accumulating constraints:
1. Reuse previous frame/latent/state instead of independent frames.
2. Warp prior output with optical flow before the next neural update.
3. Keep seed/style/prompt changes continuous and denoise strength limited.
4. Condition on stable structure: segmentation, pose, depth, edges, object IDs.
5. Use temporal/cross-frame attention or video models when they beat the simpler flow/state baseline.
6. Composite neural output only where it adds value; deterministic renderer owns fast motion and exact anchors.

## Open problems
- Actual measured operating points still required per GPU/model/acceleration.
- Temporal flicker/drift not yet quantified.
- No previous-output flow warp or persistent latent strategy in the live loop.
- No ControlNet/depth/pose path promoted to normal runtime.
- Startup/model-download UX still needs richer progress reporting from external libraries.

## Next queue
1. Benchmark 512x288 safe profile on RTX 4050 Laptop; record p50/p95 inference, VRAM and dropped submissions.
2. Benchmark 768x432+ xformers/TensorRT on RTX 4080.
3. Add input similarity filter and adaptive submit rate.
4. Add previous-neural-frame optical-flow warp and blend baseline; measure flicker before any video-model integration.
5. Add stable seed/style bank and gradual prompt interpolation.
6. Add mask-aware neural compositing for person/background/energy regions.
7. Add pose/edge/depth control maps.
8. Evaluate TemporalNet and StreamV2V; compare latency, VRAM and temporal metrics to flow-warp baseline.
9. Evaluate newer streaming video editing models only in isolated environments until they materially beat the baseline.

## Metrics
Inference FPS, p50/p95 inference time, neural frame age, submissions dropped, VRAM peak/free reserve, temporal flicker, warped-frame residual, identity/structure drift, display FPS, crash/recovery behavior.
