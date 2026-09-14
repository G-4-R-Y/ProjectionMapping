# Hardware bring-up

Run this sequence on the Windows RTX 4080 machine and keep the generated reports/captures.

## 1. Benchmark StreamDiffusion

Start with xformers, then repeat useful resolutions with TensorRT.

```powershell
python experiments/05_benchmark_streamdiffusion.py --model stabilityai/sd-turbo --width 512 --height 512 --acceleration xformers --output bench_512.json
python experiments/05_benchmark_streamdiffusion.py --model stabilityai/sd-turbo --width 768 --height 432 --acceleration xformers --output bench_768x432.json
python experiments/05_benchmark_streamdiffusion.py --model stabilityai/sd-turbo --width 960 --height 540 --acceleration xformers --output bench_960x540.json
```

Choose the operating point from p95 latency and visual quality, not peak FPS alone.

## 2. Verify Spout

In TouchDesigner create a Syphon Spout In TOP and select `ProjectionMapping-Diagnostic`.

```powershell
python experiments/06_spout_diagnostics.py --width 1920 --height 1080 --fps 60
```

Check sender discovery, stable frame order, no growing delay, and sane CPU/GPU load.

## 3. Capture projector-camera calibration

Mount camera/projector rigidly and lock automatic camera controls when possible.

```powershell
python experiments/07_capture_calibration_bundle.py --projector-width 1920 --projector-height 1080 --camera 0 --display 1 --output calibration_data/room_v1
```

This records white/black references plus Gray-code and phase-shift sequences with metadata.

## 4. Capture radiometry data

```powershell
python experiments/08_capture_radiometry_dataset.py --projector-width 1920 --projector-height 1080 --camera 0 --display 1 --output calibration_data/radiometry_v1
```

Fit/evaluate the classical LUT baseline before the learned inverse-display model.

## 5. Test room-skin geometry locking

```powershell
python experiments/09_room_skin.py --camera 0 --display 1 --projector-width 1920 --projector-height 1080
```

The fallback renderer isolates edge locking, optical-flow advection and temporal blending before adding diffusion.

## Final target

```text
camera
 -> calibrated projector coordinates
 -> segmentation / depth / optical flow
 -> latest-frame StreamDiffusion semantic keyframes
 -> room-skin edge locking
 -> flow advection between AI frames
 -> shaders / particles / feedback at display rate
 -> learned radiometric compensation
 -> Spout -> TouchDesigner -> projector
 -> physical room -> camera feedback
```

The visual objective is not a rectangular AI video. Physical edges should remain anchored while materials, light and motion become increasingly impossible.
