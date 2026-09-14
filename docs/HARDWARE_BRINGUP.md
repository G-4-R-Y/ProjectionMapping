# Hardware bring-up

Run this sequence on the machine physically connected to the projector/camera and keep the generated reports/captures.

Platform notes:

- **Windows + NVIDIA:** full current path, including CUDA/TensorRT and Spout diagnostics.
- **Linux + NVIDIA:** CUDA/TensorRT path is valid; skip Spout and use direct fullscreen while Linux transport backends are developed.
- **macOS:** run calibration, radiometry, fullscreen and Room Skin steps; skip CUDA/TensorRT and Spout-specific steps.

See `docs/PLATFORMS.md` for the compatibility matrix.

## 1. Benchmark StreamDiffusion (Windows/Linux NVIDIA only)

Start with xformers, then repeat useful resolutions with TensorRT.

```text
python experiments/05_benchmark_streamdiffusion.py --model stabilityai/sd-turbo --width 512 --height 512 --acceleration xformers --output bench_512.json
python experiments/05_benchmark_streamdiffusion.py --model stabilityai/sd-turbo --width 768 --height 432 --acceleration xformers --output bench_768x432.json
python experiments/05_benchmark_streamdiffusion.py --model stabilityai/sd-turbo --width 960 --height 540 --acceleration xformers --output bench_960x540.json
```

Choose the operating point from p95 latency and visual quality, not peak FPS alone.

On macOS, skip this step until a Metal/MPS-compatible generator is implemented.

## 2. Verify local GPU transport

### Windows / Spout

In TouchDesigner create a Syphon Spout In TOP and select `ProjectionMapping-Diagnostic`.

```text
python experiments/06_spout_diagnostics.py --width 1920 --height 1080 --fps 60
```

Check sender discovery, stable frame order, no growing delay, and sane CPU/GPU load.

### Linux / macOS

Skip the Spout diagnostic. Use the direct fullscreen path for bring-up. Linux transport and macOS Syphon support are tracked separately in the roadmap.

## 3. Capture projector-camera calibration (all supported OSs)

Mount camera/projector rigidly and lock automatic camera controls when possible.

```text
python experiments/07_capture_calibration_bundle.py --projector-width 1920 --projector-height 1080 --camera 0 --display 1 --output calibration_data/room_v1
```

This records white/black references plus Gray-code and phase-shift sequences with metadata.

## 4. Capture radiometry data (all supported OSs)

```text
python experiments/08_capture_radiometry_dataset.py --projector-width 1920 --projector-height 1080 --camera 0 --display 1 --output calibration_data/radiometry_v1
```

Fit/evaluate the classical LUT baseline before the learned inverse-display model.

## 5. Test Room Skin geometry locking (all supported OSs)

```text
python experiments/09_room_skin.py --camera 0 --display 1 --projector-width 1920 --projector-height 1080
```

The fallback renderer isolates edge locking, optical-flow advection and temporal blending before adding a platform-specific generative backend.

## Final target

```text
camera
 -> calibrated projector coordinates
 -> segmentation / depth / optical flow
 -> newest-frame semantic generator (backend depends on OS/GPU)
 -> room-skin edge locking
 -> flow advection between AI frames
 -> shaders / particles / feedback at display rate
 -> learned radiometric compensation
 -> platform transport / fullscreen -> compositor -> projector
 -> physical room -> camera feedback
```

The visual objective is not a rectangular AI video. Physical edges should remain anchored while materials, light and motion become increasingly impossible.
