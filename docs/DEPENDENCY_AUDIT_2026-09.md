# Dependency audit — 2026-09-15

This audit distinguishes the portable application from optional native/ML inference stacks. Hardware-specific claims remain unvalidated unless explicitly measured on the target machine.

## Decision summary

- Keep **Python 3.12** as the recommended runtime and keep package support at `>=3.10,<3.14` for now. PyTorch itself has moved well beyond this baseline and recent releases support Python 3.14, but the complete optional stack does not have one uniformly validated Python 3.14 combination. StreamDiffusionV2's published setup still uses Python 3.10, and TensorRT 11.1 calls Windows Python 3.14 support preliminary.
- Keep **NumPy `>=1.26,<2`**. NumPy 2.x is mature (2.5 supports Python 3.12-3.14), but NumPy 2.0 introduced a C-ABI break. The blocker is downstream binary compatibility, especially MediaPipe/InsightFace-style native stacks and older optional integrations, not ProjectionMapping's own ndarray code.
- Keep **OpenCV `>=4.9,<5`**. OpenCV 5 is now real and supports NumPy 2.x, but it is a major API/platform transition. Test calibration, HighGUI/fullscreen, camera/video I/O, optical flow, ArUco/structured-light and PyInstaller bundles before removing the ceiling.
- Raise **SoundCard** from `>=0.4.5` to `>=0.4.6`; 0.4.6 is the current release and remains a pure-Python package. Native Pulse/PipeWire `parec` capture remains the preferred Linux system-audio path in this repo, so SoundCard hardware behavior is still fallback-dependent.
- Leave **Textual `>=0.70`** unchanged. Current Textual 8.2.x supports Python 3.9-3.14; the existing lower bound intentionally permits current versions and there is no evidence that a forced major-version floor benefits the project.
- Leave **PyInstaller `>=6.10`** unchanged. Current 6.22.x is available; if pinning PyInstaller later, keep `pyinstaller-hooks-contrib` approximately in sync as upstream recommends. Desktop bundles remain CI validation, not projector/camera hardware validation.
- Leave **ModernGL `<6`** until the render/display path is exercised against any future major release.

## ML / native stack

### PyTorch + torchvision

PyTorch has advanced substantially (2.10 added Python 3.14 `torch.compile` support; later releases continue newer-Python work). PyTorch 2.6 also changed Linux extension ABI/build assumptions to CXX11 ABI=1 and manylinux_2_28, so custom CUDA/C++ extensions must match the selected torch build. Do not globally raise the `torch>=2.2` floor solely to chase the newest release: StreamDiffusion/xformers/TensorRT combinations are tighter than core torch. Install torch/torchvision as a matched pair for the chosen CUDA runtime.

### StreamDiffusion

The existing Daydream StreamDiffusion integration should remain an isolated inference environment. Do not encode its volatile transitive stack into the portable `pyproject.toml`. StreamDiffusionV2 is now public and its documented environment uses Linux + NVIDIA GPU + Python 3.10; it recommends torch 2.11 / torchvision 0.26 for Blackwell and has an optional flash-attn extra. Evaluate V2 as a separate backend rather than an in-place dependency bump.

### diffusers / transformers / xformers

Treat these as backend-owned dependencies. Their compatibility is determined by the selected StreamDiffusion revision, torch/CUDA wheel and attention backend. Do not add broad unconstrained versions to the main package. For reproducible hardware benchmarks, record exact versions in the benchmark result/environment lock.

### TensorRT

TensorRT 11.1 is current in this audit. Python 3.13/3.14 bindings exist on supported platforms, but NVIDIA documents Python samples as not supporting 3.13/3.14 and Windows 3.14 as preliminary. TensorRT engines are not portable artifacts across arbitrary TensorRT/GPU/platform combinations. Rebuild and benchmark engines after TensorRT/CUDA/driver changes. No repo-wide pin changed.

### ONNX / onnxruntime

ONNX Runtime 1.24.x is a current line with ongoing platform fixes (including Windows Arm64 Python CPU packaging and native-library loading fixes). It is not a direct project dependency today. Add/pin it only when an ONNX backend becomes executable in-tree, then CI CPU providers separately from CUDA/TensorRT providers.

### MediaPipe

Do not make MediaPipe a portable-core dependency yet. Its packaging/API has moved significantly: the 0.10.x line had NumPy `<2` packaging friction and newer releases have moved away from legacy `solutions`-style assumptions. Any pose/hand implementation should target the current Tasks/Landmarker API and get its own tested dependency extra. This is a principal blocker to declaring NumPy 2 + newest Python safe for the *full* perception stack.

### InsightFace

Keep isolated until an actual face pipeline is merged. It pulls native ONNX/runtime/model dependencies and has historically been sensitive to NumPy/native wheel changes. Validate a concrete InsightFace + ONNX Runtime + NumPy 2 matrix before adding it to project extras.

## Platform transports

- **Windows Spout:** validate the actual Python binding/DLL, bitness, GL context ownership and zero-copy path on Windows hardware before pinning a transport package. OpenCV fullscreen remains fallback.
- **Linux:** native Pulse/PipeWire `parec` is intentionally an external executable/runtime dependency for system-audio capture; SoundCard is fallback. Direct fullscreen is current output. Verify distro packages and PipeWire/Pulse compatibility on target machines.
- **macOS:** direct fullscreen is current. Syphon remains planned; no dependency should be added until a concrete backend is implemented and tested.
- **NDI:** planned; runtime licensing/native SDK availability must be reviewed before making it an install extra.

## NumPy 2 / OpenCV 5 / Python 3.14 gate

Do **not** lift the current ceilings as a single change. A safe migration requires a dedicated matrix with at least:

1. Python 3.12/3.13/3.14 × NumPy 1.26/2.x × OpenCV 4.x/5.x for portable unit tests.
2. Camera capture, HighGUI fullscreen/F11, calibration/Gray-code, optical flow, Room Skin and ModernGL interop smoke tests on Windows/Linux/macOS.
3. PyInstaller bundles on all three OSes.
4. A separate NVIDIA matrix for matched torch/torchvision + xformers + selected StreamDiffusion + TensorRT, with import, one-frame inference and sustained benchmark tests.
5. MediaPipe Tasks and InsightFace/ONNX Runtime smoke tests under NumPy 2 before calling the full perception stack compatible.
6. Real Spout/PipeWire/projector/camera tests where those capabilities are claimed.

Until that matrix passes, Python 3.12 + NumPy 1.26 + OpenCV 4.x remains the conservative integration baseline.

## Next check

Re-run this audit after a material StreamDiffusionV2/MediaPipe/InsightFace integration, or before intentionally enabling Python 3.14 / NumPy 2 / OpenCV 5 in CI. Dependency freshness alone is not sufficient reason to cross native ABI or major-API boundaries.
