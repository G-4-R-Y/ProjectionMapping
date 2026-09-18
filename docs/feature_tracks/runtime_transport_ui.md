# Track — Runtime / GPU Transport / Control Deck / Packaging

## North star
A reliable visual-performance appliance: one persistent control deck, clean child-process isolation, hot controls/presets, correct fullscreen placement, zero-stale-frame inference, measured GPU/latency behavior, and one-click platform-native distribution.

## Current state
- Responsive localhost browser control deck + Textual fallback, both driven by the modular feature registry.
- Child process tree isolation, persistent logs, GPU snapshots and cleanup. POSIX normal-exit cleanup
  now sweeps surviving process-group helpers instead of only reaping the direct renderer parent.
- Incremental bounded log reads replace repeated whole-log reads; the Textual fallback pauses hidden
  dashboard repaint while a configuration screen is active.
- F11 fullscreen toggle in shared sink and ESC exit behavior.
- Latest-frame-wins async worker.
- Spout abstraction/diagnostics on Windows; fullscreen fallback elsewhere.
- PyInstaller onedir builds and CI packaging; native installer polish incomplete.

## Quality ladder
- **Prototype:** launch Python scripts manually.
- **Usable:** browser deck and TUI fallback launch/kill/log features safely. **Current.**
- **Polished:** proper monitor enumeration, live parameter IPC, persistent preset banks, richer
  dependency/preflight UX and native installers.
- **Advanced:** zero/low-copy CUDA<->texture transport, stage timestamps, OSC/MIDI/phone control, compositor integration.
- **Ridiculous:** distributed multi-projector/session system with automatic recovery, recording/replay of performance state and deterministic benchmark captures.

## Next queue
1. Hardware-run the 20-cycle launch/stop soak test and record RAM/VRAM return-to-baseline measurements.
2. Replace `display * 1920` assumptions with real monitor enumeration/geometry.
3. Add live IPC for parameter changes without renderer restart.
4. Add preset save/load/A-B/morph and performance banks shared by features.
5. Add structured stage/status protocol so both control decks show model download/load/warmup/runtime progress consistently.
6. Add per-stage timestamp telemetry and p50/p95/p99 latency reports.
7. Validate Spout->TouchDesigner on Windows and count copies/readbacks.
8. Implement CUDA/shared-texture path if measurement justifies it.
9. Add standalone Linux installer/AppImage, Windows Setup.exe, polished macOS `.app`/DMG.
10. Add crash-safe last-run diagnostics and optional automatic safe-profile retry.

## Metrics
Launch time, crash recovery, stale process/GPU-context count, display FPS, copy count, capture->scanout latency, log completeness, setup clicks/time, installer success rate.
