# Architecture

## Principle

Keep **physical calibration**, **vision/ML**, **artistic rendering**, and **display transport** separable. A model crash should not take down calibration; switching from diffusion to shaders should not require rewriting the projector output path.

## Layers

### Capture
Camera frames, timestamps, optional exposure/gain locking.

### Calibration
- planar homography for immediate experiments
- Gray-code / phase-shift structured light for dense projector-camera mapping
- reusable calibration bundles with resolution and camera/projector metadata

### Perception
- foreground masks
- optical flow
- optional depth / semantic segmentation / pose

### Generation
- shaders and procedural feedback for temporally stable high-rate motion
- diffusion/video generation for semantic transformation
- hybrid path: AI produces appearance/keyframes, graphics produce 60+ FPS dynamics

### Compensation
- geometric warp
- radiometric LUT baseline
- learned inverse-display network
- later: defocus and shadow compensation

### Transport
- direct fullscreen output for bring-up
- Spout for same-machine Windows GPU sharing
- NDI for networked/multi-machine setups

## Closed loop

Let P be projector pixels, C(P) the camera-observed physical result, and T the target. Optimize

`P* = argmin_P d(C(P), T) + lambda R(P)`

where `d` can combine pixel loss and learned features. For stable surfaces, learn an inverse model first; for dynamic scenes, combine online feedback with a prior model.

## Latency budget

Track capture, perception, generation, compositing, transport, projector scanout, and camera exposure separately. Dynamic mapping quality is dominated by end-to-end motion-to-photon latency, not just neural inference time.
