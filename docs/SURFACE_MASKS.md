# Experimental projector-space surface masks (Room Skin)

**Status: implemented / isolated unit-smoked; not hardware validated.** This optional output matte clips Room Skin visuals to a manually traced outline, inspired by the traced-zone feature introduced in [Projection Mapper's Nov 7, 2026 update](https://github.com/atul016/projection-mapper/commit/879de56ef840) (MIT). Our implementation is independently written with OpenCV; no third-party shader, binaries or assets are copied.

## Run

Requires Python 3.10–3.13 and the existing Room Skin vision extra:

```bash
python -m pip install -e '.[vision,ui]'
python experiments/09_room_skin.py --camera 0 --display 1 \
  --projector-width 1920 --projector-height 1080 \
  --surface-mask configs/surface_shapes/demo_arch.json --surface-feather-px 8
```

Or open `projection-ui` → **Room Skin**, enter the same JSON file path and adjust **Inner feather**. An empty path keeps the original full-frame output exactly as before.

The JSON uses **normalized projector-output coordinates** (top-left `[0,0]`, bottom-right `[1,1]`). It is *not* referenced to the camera sensor or physically calibrated wall geometry:

```json
{
  "space": "normalized",
  "outlines": [
    [[0.1, 0.1], [0.9, 0.1], [0.9, 0.9], [0.1, 0.9]],
    [[0.4, 0.4], [0.6, 0.4], [0.6, 0.6], [0.4, 0.6]]
  ]
}
```

The second polygon makes a hole by even–odd parity. More nested/overlapping outlines toggle the fill. Use 1–16 outlines of 3–512 finite vertices each; values must be in 0–1, and JSON may not exceed 128 KiB. Self-intersecting drawings have implementation-defined rasterization; trace simple contours. **Always measure the shape against projected geometry before a performance**. The sample arch is a synthetic fixture, *not* a calibrated room dataset.

Feather is 0–256 output pixels, **inside** the outline so it does not emit beyond the marked surface. The matte is built once at startup and applied after camera-frame rendering is resized to projector resolution. RGB black outside the mask is strictly zero; the path is an additional CPU compositing pass and does not provide native GPU transport or multi-projector edge blending.

## Verification

Standalone test completed on a generic test environment:

```bash
PYTHONPATH=src python -m pytest -q tests/test_surface_masks.py  # 10 passed
```

This was on NumPy 2.3.5 + OpenCV 4.13.0, **not** the repository's pinned NumPy 1.26/OpenCV <4.12. Re-run on the pinned development stack, plus:

```bash
python -m pytest -q tests/test_feature_registry.py
python -m ruff check src tests --select E9,F63,F7,F82
```

Then verify with real projector, camera and GPU at 1920×1080: manually align the outline, compare full-frame/off + hard mask + feather 4/12 over 60s; record black-level leakage, frame-time p50/p95 and F11/ESC lifecycle. The current experiment does not claim calibrated homography, projector-camera spatial alignment, occlusion, antialiased physical contour accuracy, brightness compensation, or a browser tracing editor.
