# Track — Runtime / GPU Transport / Control Deck / Packaging

## North star
A reliable visual-performance appliance: one persistent control deck, clean child-process isolation, hot controls/presets, correct fullscreen placement, zero-stale-frame inference, measured GPU/latency behavior, and one-click platform-native distribution.

## Current state
- Textual TUI + modular feature registry/fragments.
- Child process tree isolation, persistent logs, GPU snapshots, cleanup.
- F11 fullscreen toggle in shared sink and ESC exit behavior.
- Latest-frame-wins async worker.
- Spout abstraction/diagnostics on Windows; fullscreen fallback elsewhere.
- PyInstaller onedir build tooling and manual/local packaging checks; GitHub Actions CI and desktop-build automation intentionally removed by 2026-10-27. Native installer polish incomplete.

## Quality ladder
- **Prototype:** launch Python scripts manually.
- **Usable:** TUI launches/kills/logs features safely. **Current.**
- **Polished:** proper monitor enumeration, live parameter IPC, preset banks, dependency/preflight UX, native installers.
- **Advanced:** zero/low-copy CUDA<->texture transport, stage timestamps, OSC/MIDI/phone control, compositor integration.
- **Ridiculous:** distributed multi-projector/session system with automatic recovery, recording/replay of performance state and deterministic benchmark captures.

## 2026-11-05 — Spatial Studio browser/desktop slice

- **Implemented on feature branch:** portable local-loopback read-only Python HTTP entrypoint + browser WebGL2 studio; static assets package with setuptools; manual Windows PyInstaller wrapper; import/clipboard, three primary preview lanes and tests. Not merged or hardware-validated until acceptance.
- Do not confuse this local studio with the existing Textual projector control plane. A public deployment may use only static assets, not arbitrary remote process launch.
- **Next:** real browser/shader screenshot test, Windows one-dir .exe build, polished projector/multi-monitor routing, live IPC with authentication and same-origin guards, backpressure and GPU point streaming, native shell evaluation.
- **Rust/C++ decision:** avoid wholesale rewrite. Profile Rust/wgpu point parsing/LOD or shared-texture transport before introducing another runtime; keep Python research/calibration/ML.

## Next queue
1. Replace `display * 1920` assumptions with real monitor enumeration/geometry.
2. Add live IPC for parameter changes without renderer restart.
3. Add preset save/load/A-B/morph and performance banks shared by features.
4. Add structured stage/status protocol so TUI shows model download/load/warmup/runtime progress consistently.
5. Add per-stage timestamp telemetry and p50/p95/p99 latency reports.
6. Validate Spout->TouchDesigner on Windows and count copies/readbacks.
7. Implement CUDA/shared-texture path if measurement justifies it.
8. Add standalone Linux installer/AppImage, Windows Setup.exe, polished macOS `.app`/DMG.
9. Add crash-safe last-run diagnostics and optional automatic safe-profile retry.

## Metrics
Launch time, crash recovery, stale process/GPU-context count, display FPS, copy count, capture->scanout latency, log completeness, setup clicks/time, installer success rate.

## 2026-11-14 — optional Varda launcher and transport comparison

- The MIT-licensed [Varda VJ](https://github.com/im-knots/varda) [v0.10.0 release (2026-11-08)](https://github.com/im-knots/varda/releases/tag/v0.10.0) ships separate Windows x64 ZIP, macOS universal DMG and Linux x86_64 AppImage/Flatpak builds. Optional manifest `configs/features.d/varda_external.toml` launches Varda only if `varda` is already available on PATH. No bundled dependency, SDK, source copy or native texture bridge was introduced. Flag contract tests were added but the full repo suite/hardware tests remain pending.
- The feature's `fullscreen = false` is intentional: Varda owns its output/projector displays, while the ProjectionMapping control deck owns only the child-process launch and cleanup. Source-path flags are opt-in; no sample media or network service is fetched or launched automatically.
- On **Windows** use upstream's Spout capability only after real same-GPU sender/receiver validation; on **macOS** Syphon is upstream functionality rather than our native backend; on **Linux** use the released Vulkan Varda build/direct display, not Spout or Syphon. Optional NDI requires its own SDK/runtime and network/performance review on each OS.
- Reproduction gate: install a trusted v0.10.0 release and put its executable on PATH; verify launch/exit, existing scene routing, OSC off/on behavior, focus/ESC return to deck, GPU allocation cleanup, copied frame count, p50/p95 scanout and native output on projector. Do **not** mark M2 complete from the manifest test. Details and deferred competitors: [2026-11-14 report](../research/2026-11-14.md).
