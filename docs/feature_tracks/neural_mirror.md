# Track — Neural Mirror / Streaming Generative Video

## North star
Realtime semantic transformation that preserves performer/room structure over time, scales from a safe 6 GB laptop profile to a stronger desktop path, and never compromises display responsiveness or process stability.

## Current state
- Daydream StreamDiffusion backend with latest-frame-wins async worker.
- 6 GB safe profile and optional-acceleration fallback.
- VRAM guard, process isolation, cleanup, stage diagnostics, benchmark harness.
- Live camera img2img path; model/prompt runtime integration exists.
- Display-side optical-flow temporal stabilizer: the last neural frame is warped forward with camera motion between sparse AI keyframes; fresh neural keyframes are blended against the warped prediction.
- Temporal telemetry includes warp residual and neural-keyframe residual.

## Quality ladder
- **Prototype:** live frame -> diffusion -> display.
- **Usable:** safe startup, bounded latency, 6 GB operating point, native-attention fallback, deterministic flow-warp temporal baseline. **Current.**
- **Polished:** prompt/style presets, smooth prompt transitions, similarity skipping, measured temporal stabilization, mask-aware compositing.
- **Advanced:** latent/state propagation, pose/depth/edge controls, TemporalNet/StreamV2V evaluation, identity/style persistence.
- **Ridiculous:** structure-preserving streaming video editing integrated with calibrated room geometry and deterministic 60+ FPS FX between neural semantic keyframes.

## How temporal consistency should be built
Video generation does not provide a hard guarantee; consistency comes from accumulating constraints:
1. Reuse previous frame/latent/state instead of independent frames.
2. Warp prior output with optical flow before the next neural update. **Display-side baseline implemented.**
3. Keep seed/style/prompt changes continuous and denoise strength limited.
4. Condition on stable structure: segmentation, pose, depth, edges, object IDs.
5. Use temporal/cross-frame attention or video models when they beat the simpler flow/state baseline.
6. Composite neural output only where it adds value; deterministic renderer owns fast motion and exact anchors.

## Open problems
- Actual measured operating points still required per GPU/model/acceleration.
- Flow warp is currently display-side; it does not yet condition the diffusion model itself.
- Temporal flicker/drift and residual metrics need real-camera benchmark interpretation.
- No persistent latent/state reuse yet.
- No ControlNet/depth/pose path promoted to normal runtime.
- Startup/model-download UX still needs richer progress reporting from external libraries.

## Next queue
1. Benchmark 512x288 safe profile on RTX 4050 Laptop; record p50/p95 inference, VRAM, dropped submissions, warp residual and keyframe residual.
2. Compare temporal warp on/off on identical camera motion and tune keyframe blend.
3. Benchmark 768x432+ xformers/TensorRT on RTX 4080.
4. Add input similarity filter and adaptive submit rate.
5. Add stable seed/style bank and gradual prompt interpolation.
6. Feed flow-warped previous stylized output into neural conditioning where the backend permits, rather than display only.
7. Add mask-aware neural compositing for person/background/energy regions.
8. Add pose/edge/depth control maps.
9. Evaluate TemporalNet and StreamV2V; compare latency, VRAM and temporal metrics to flow-warp baseline.
10. Evaluate newer streaming video editing models only in isolated environments until they materially beat the baseline.

## Metrics
Inference FPS, p50/p95 inference time, neural frame age, submissions dropped, VRAM peak/free reserve, temporal flicker, warped-frame residual, neural-keyframe residual, identity/structure drift, display FPS, crash/recovery behavior.
