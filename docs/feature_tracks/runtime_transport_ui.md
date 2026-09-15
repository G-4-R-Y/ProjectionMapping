# Track — Runtime / GPU Transport / Control Deck / Packaging

## North star
A reliable visual-performance appliance: one persistent control deck, clean child-process isolation, hot controls/presets, correct fullscreen placement, zero-stale-frame inference, measured GPU/latency behavior, and one-click platform-native distribution.

## Current state
- Textual TUI + modular feature registry/fragments.
- Child process tree isolation, persistent logs, GPU snapshots, cleanup.
- F11 fullscreen toggle in shared sink and ESC exit behavior.
- Latest-frame-wins async worker.
- Spout abstraction/diagnostics on Windows; fullscreen fallback elsewhere.
- PyInstaller onedir builds and CI packaging; native installer polish incomplete.

## Quality ladder
- **Prototype:** launch Python scripts manually.
- **Usable:** TUI launches/kills/logs features safely. **Current.**
- **Polished:** proper monitor enumeration, live parameter IPC, preset banks, dependency/preflight UX, native installers.
- **Advanced:** zero/low-copy CUDA<->texture transport, stage timestamps, OSC/MIDI/phone control, compositor integration.
- **Ridiculous:** distributed multi-projector/session system with automatic recovery, recording/replay of performance state and deterministic benchmark captures.

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
