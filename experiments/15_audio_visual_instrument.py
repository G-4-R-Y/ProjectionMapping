"""GPU-first Audio Visual Instrument.

Low-latency capture uses tiny blocks, spectral analysis uses a longer rolling window, musical
state uses adaptive event gating + tempo/phase, and ModernGL renders coherent shader scenes.
F11 toggles fullscreen; ESC returns to the control deck.
"""
from __future__ import annotations

import argparse
import time

import cv2
import numpy as np

from projection_mapping.audio_music_features import RollingMusicFeatureExtractor
from projection_mapping.audio_presets import PRESETS
from projection_mapping.audio_reactive import AudioFeatureStream, format_device_table, list_audio_devices
from projection_mapping.audio_shader import AudioShaderRenderer, PALETTES, SCENES
from projection_mapping.music_reactivity import MusicalEventMapper
from projection_mapping.runtime import FullscreenSink


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["mic", "system"], default="system")
    ap.add_argument("--device", default=None)
    ap.add_argument("--list-devices", action="store_true")
    ap.add_argument("--performance-preset", choices=["custom", *sorted(PRESETS)], default="custom")
    ap.add_argument("--scene", choices=SCENES, default="journey")
    ap.add_argument("--palette", choices=PALETTES, default="neon_aurora")
    ap.add_argument("--reactivity", choices=["smooth", "balanced", "punchy", "chaotic"], default="balanced")
    ap.add_argument("--event-threshold", type=float, default=0.64)
    ap.add_argument("--beat-threshold", type=float, default=0.50)
    ap.add_argument("--madness", type=float, default=0.42)
    ap.add_argument("--display", type=int, default=1)
    ap.add_argument("--projector-width", type=int, default=1920)
    ap.add_argument("--projector-height", type=int, default=1080)
    ap.add_argument("--render-width", type=int, default=768)
    ap.add_argument("--render-height", type=int, default=432)
    ap.add_argument("--sample-rate", type=int, default=48_000)
    ap.add_argument("--blocksize", type=int, default=256)
    ap.add_argument("--analysis-size", type=int, default=2048)
    ap.add_argument("--attack-ms", type=float, default=7.0)
    ap.add_argument("--release-ms", type=float, default=125.0)
    ap.add_argument("--sensitivity", type=float, default=1.20)
    ap.add_argument("--transition-seconds", type=float, default=2.4)
    ap.add_argument("--auto-scene-seconds", type=float, default=28.0)
    ap.add_argument("--exclusive-mode", action="store_true")
    return ap.parse_args()


def apply_performance_preset(args: argparse.Namespace) -> None:
    if args.performance_preset == "custom":
        return
    preset = PRESETS[args.performance_preset]
    args.scene = preset.scene
    args.palette = preset.palette
    args.reactivity = preset.reactivity
    args.madness = preset.madness
    args.event_threshold = preset.event_threshold
    args.beat_threshold = preset.beat_threshold
    args.sensitivity = preset.sensitivity
    args.analysis_size = preset.analysis_size
    args.transition_seconds = preset.transition_seconds
    args.auto_scene_seconds = preset.auto_scene_seconds


def main() -> None:
    args = parse_args()
    if args.list_devices:
        print(format_device_table(list_audio_devices()))
        return
    apply_performance_preset(args)

    sink = FullscreenSink(window="ProjectionMapping-AudioInstrument", display=args.display, fullscreen=True)
    renderer = AudioShaderRenderer(
        args.render_width,
        args.render_height,
        scene=args.scene,
        palette=args.palette,
        madness=args.madness,
        transition_seconds=args.transition_seconds,
        auto_scene_seconds=args.auto_scene_seconds,
    )
    mapper = MusicalEventMapper(
        mode=args.reactivity,
        event_threshold=args.event_threshold,
        beat_threshold=args.beat_threshold,
        madness=args.madness,
    )

    # AudioFeatureStream owns the cross-platform/native capture thread. Replace its original
    # tiny-block FFT analyzer before starting so capture latency and spectral resolution are
    # independently tunable.
    audio = AudioFeatureStream(
        source=args.source,
        device=args.device or None,
        sample_rate=args.sample_rate,
        blocksize=args.blocksize,
        attack_ms=args.attack_ms,
        release_ms=args.release_ms,
        sensitivity=args.sensitivity,
        exclusive_mode=args.exclusive_mode,
    )
    audio.extractor = RollingMusicFeatureExtractor(
        sample_rate=args.sample_rate,
        analysis_size=args.analysis_size,
        attack_ms=args.attack_ms,
        release_ms=args.release_ms,
        sensitivity=args.sensitivity,
    )

    t0 = time.perf_counter()
    report_t = t0
    frames = 0
    strike_count = 0
    beat_count = 0
    drop_count = 0
    last_strike_high = False
    last_beat_high = False
    last_drop_high = False

    print(
        f"[audio-instrument] bank={args.performance_preset} scene={args.scene} palette={args.palette} "
        f"reactivity={args.reactivity} capture_block={args.blocksize} analysis={args.analysis_size} "
        f"render={args.render_width}x{args.render_height} gl_backend={renderer.backend}",
        flush=True,
    )

    try:
        with audio:
            while True:
                now = time.perf_counter()
                if audio.error is not None:
                    raise RuntimeError("audio capture failed") from audio.error

                f = audio.latest
                s = mapper.update(f, now)
                small = renderer.render(s, t=now - t0, now=now)
                frame = cv2.resize(
                    small,
                    (args.projector_width, args.projector_height),
                    interpolation=cv2.INTER_CUBIC,
                )
                if sink(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)) is False:
                    break

                strike_high = s.strike > 0.65
                beat_high = s.beat > 0.65
                drop_high = s.drop > 0.65
                if strike_high and not last_strike_high:
                    strike_count += 1
                if beat_high and not last_beat_high:
                    beat_count += 1
                if drop_high and not last_drop_high:
                    drop_count += 1
                last_strike_high = strike_high
                last_beat_high = beat_high
                last_drop_high = drop_high

                frames += 1
                elapsed = now - report_t
                if elapsed >= 2.0:
                    feature_age_ms = max(0.0, (now - f.timestamp) * 1000.0)
                    tempo = f"{s.tempo_bpm:5.1f}" if s.beat_confidence > 0.15 else "  -- "
                    print(
                        f"fps={frames/elapsed:5.1f} age={feature_age_ms:5.1f}ms "
                        f"scene={renderer.current_scene:<9} rms={f.rms:.2f} bass={s.bass:.2f} mids={s.mids:.2f} highs={s.highs:.2f} "
                        f"beat={s.beat:.2f} strike={s.strike:.2f} drop={s.drop:.2f} "
                        f"tempo={tempo} conf={s.beat_confidence:.2f} phase={s.beat_phase:.2f} "
                        f"events[beat/strike/drop]={beat_count}/{strike_count}/{drop_count}",
                        flush=True,
                    )
                    frames = 0
                    beat_count = strike_count = drop_count = 0
                    report_t = now
    finally:
        renderer.close()
        sink.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
