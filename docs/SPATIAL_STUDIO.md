# Spatial Memories / Projection Studio — first vertical slice (2026-11-05)

## Run

From a checkout of ProjectionMapping, with Python 3.10–3.13 and the project installed:

```bash
python -m pip install -e .
projection-studio
# or: python -m projection_mapping.studio_server
```

This starts a **loopback-only** static server (`127.0.0.1`, random free port) and opens the browser. Use a current browser with WebGL 2 enabled. No GPU model download, network service, or Actions workflow is involved. The server has no upload, exec or arbitrary-file endpoint. Camera and microphone require explicit permission, and are processed in the browser; they are not streamed to the server.

If desired, **publish only the three static studio assets** (`index.html`, `studio.css`, `studio.js`) to a normal static host over HTTPS, not the local operator server. No remote-control or projector API is exposed. This is a public **preview/gallery** rather than a remotely operated projection control panel.

## Desktop executable, Windows

Run `scripts/build_studio_windows.ps1` **locally on Windows** with Python 3.12 and PyInstaller. It builds `dist/ProjectionStudio/ProjectionStudio.exe` as a one-directory launcher that hosts the read-only studio at a random loopback port and opens a browser. Keep the entire output directory; no installer, code signing or generated `.exe` has been validated in this environment. The existing Textual `projection-ui` remains available unchanged. Later, migrate the operator to a trusted WebView/Tauri shell and authenticated IPC, after local WebGL/gallery quality is accepted.

## Experiences

1. **Spatial Memories**: GPU-resident procedural tree passage with moving-camera illusion, perspective ground lines, fog and opt-in vortex/dissolve warps. Default monochrome/true-black floor; cyan-magenta and amber variations.
2. **Spectral Reactor**: frequency-by-time point-cloud landscape, synthetic demonstrator until the user explicitly enables microphone (Web Audio API). This is a browser preview, **not** the full existing beat/section-aware Song Studio.
3. **Human Cloud**: browser camera-only edge/motion point preview; this is *not* semantic pose tracking, depth estimation or a recovered person point cloud. Next: connect RTMPose landmarks/IDs, opt-in segmentation/depth, and emitter continuity via localhost IPC.

Supports drag and drop, native file picker, `Ctrl+V` images, and the Paste button (`navigator.clipboard.read` with HTTPS/localhost secure-context requirements). Accepts PNG/JPEG/WebP as **2.5D grayscale-intensity reliefs**, not true 3D reconstruction. Point inputs: `.xyz`, `.pts`, ASCII PLY, binary little-endian PLY with x/y/z plus optional RGB. Unsupported variants (LAZ/LAS, big-endian PLY, Gaussian splat payloads, meshes) are rejected explicitly. Preview loads up to 40 MB / 130k points. These caps avoid unbounded browser memory; large scans need streaming octrees/LOD.

### Important boundaries

- A 2D image does not contain measured depth. Don't label the image relief a LiDAR scan.
- The web preview is **not projector-calibrated** and has not been tested against real fullscreen/multi-monitor/projection hardware.
- WebGL2 scene quality and performance have not been visually validated on target RTX GPUs; perform a recorded 60-second art test before promotion.
- Native ModernGL/OpenCV modes remain separate from the browser runtime. Reuse scene datasets and controls through explicit serialization/IPC later.
- No executable file, authenticated remote control, public hosting, live pose tracking or GPU zero-copy bridge is being claimed here.

## Art/QA protocol

Compare black floor and highlights against the reported gray attractor screenshot. For each scene, test 60 seconds at 1280x720 and 1920x1080, several palettes, drag/orbit, file paste/import, fullscreen, and device permission on Windows/Linux. Record minimum/median/p95 FPS, startup, GPU memory, black-pixel fraction, contrast, eye-line, and camera privacy behavior. Cap unsupported GPUs and test DPR/device resize.

## Language choices

**Do not rewrite the entire repo.** Python is sufficient for orchestration, research, calibration, and model integrations, while ModernGL/GLSL already handles hot-path visualization. The web preview uses zero external JS dependencies as a safe proof of interaction and style. A dedicated Rust/wgpu core makes sense **after** profiling point-decoding, LOD streaming, buffer management and GPU transport on real devices. Tauri can then ship this core to Windows/Linux/macOS and WASM to browsers; do not adopt Rust only for presumed speedups. Keep the current Textual and optional PyInstaller path until replacement actually meets feature parity.

## Reproduction / manual checks

```bash
python -m pytest -q tests/test_studio_server.py
node --check src/projection_mapping/studio_static/studio.js
node tests/test_studio_web.cjs
python -m projection_mapping.studio_server --no-open
```

Web smoke uses a mocked WebGL2 interface to verify loading and ASCII/binary PLY, *not* real shader compilation. Run the visual/GPU test locally. GitHub Actions CI must remain disabled.
