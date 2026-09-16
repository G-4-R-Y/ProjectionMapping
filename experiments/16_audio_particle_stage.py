"""Song Studio vNext: musical-state-driven GPU particle choreography.

This uses the same MusicalSignals bus as the shader studio but drives a persistent GPU
particle field instead of mapping raw FFT bins to pixels. F11 toggles fullscreen; ESC exits.
"""
from __future__ import annotations

import argparse
import time

import cv2

from projection_mapping.audio_music_features import RollingMusicFeatureExtractor
from projection_mapping.audio_reactive import AudioFeatureStream, format_device_table, list_audio_devices
from projection_mapping.gpu_particles import GPUParticleField
from projection_mapping.music_reactivity import MusicalEventMapper
from projection_mapping.particle_choreography import BANKS, choreography
from projection_mapping.runtime import FullscreenSink


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["system", "mic"], default="system")
    ap.add_argument("--device", default=None)
    ap.add_argument("--list-devices", action="store_true")
    ap.add_argument("--bank", choices=BANKS, default="orbit_reactor")
    ap.add_argument("--reactivity", choices=["smooth", "balanced", "punchy", "chaotic"], default="balanced")
    ap.add_argument("--madness", type=float, default=0.45)
    ap.add_argument("--event-threshold", type=float, default=0.64)
    ap.add_argument("--beat-threshold", type=float, default=0.50)
    ap.add_argument("--display", type=int, default=1)
    ap.add_argument("--projector-width", type=int, default=1920)
    ap.add_argument("--projector-height", type=int, default=1080)
    ap.add_argument("--render-width", type=int, default=768)
    ap.add_argument("--render-height", type=int, default=432)
    ap.add_argument("--capacity", type=int, default=32768)
    ap.add_argument("--sample-rate", type=int, default=48_000)
    ap.add_argument("--blocksize", type=int, default=256)
    ap.add_argument("--analysis-size", type=int, default=2048)
    ap.add_argument("--sensitivity", type=float, default=1.20)
    args = ap.parse_args()

    if args.list_devices:
        print(format_device_table(list_audio_devices()))
        return

    field = GPUParticleField(args.render_width, args.render_height, capacity=args.capacity)
    sink = FullscreenSink(window="ProjectionMapping-AudioParticles", display=args.display, fullscreen=True)
    mapper = MusicalEventMapper(
        mode=args.reactivity,
        event_threshold=args.event_threshold,
        beat_threshold=args.beat_threshold,
        madness=args.madness,
    )
    audio = AudioFeatureStream(
        source=args.source,
        device=args.device or None,
        sample_rate=args.sample_rate,
        blocksize=args.blocksize,
        sensitivity=args.sensitivity,
    )
    audio.extractor = RollingMusicFeatureExtractor(
        sample_rate=args.sample_rate,
        analysis_size=args.analysis_size,
        sensitivity=args.sensitivity,
    )

    print(
        f"[audio-particles] bank={args.bank} particles={field.capacity} "
        f"gl={field.context_info.gl_version} renderer={field.context_info.renderer} backend={field.backend}",
        flush=True,
    )
    t0 = time.perf_counter()
    last = t0
    report = t0
    frames = 0
    try:
        with audio:
            while True:
                now = time.perf_counter()
                dt = min(max(now - last, 1e-4), 0.08)
                last = now
                if audio.error is not None:
                    raise RuntimeError("audio capture failed") from audio.error
                f = audio.latest
                s = mapper.update(f, now)
                c = choreography(args.bank, s, now - t0, args.madness)
                field.palette = field.PALETTES[c.palette]
                small = field.render(
                    list(c.emitters),
                    t=now - t0,
                    dt=dt,
                    emission_rate=c.emission_rate,
                    turbulence=c.turbulence,
                    drag=c.drag,
                    feedback=c.feedback,
                    bloom=c.bloom,
                    energy=0.65 + 0.75 * s.loudness,
                    bass=s.bass,
                    strike=s.strike,
                    drop=s.drop,
                )
                out = cv2.resize(small, (args.projector_width, args.projector_height), interpolation=cv2.INTER_CUBIC)
                if sink(cv2.cvtColor(out, cv2.COLOR_RGB2BGR)) is False:
                    break
                frames += 1
                if now - report >= 2.0:
                    tempo = f"{s.tempo_bpm:.1f}" if s.beat_confidence > 0.15 else "--"
                    print(
                        f"[audio-particles] fps={frames/(now-report):.1f} bank={args.bank} emit={c.emission_rate:.0f}/s "
                        f"bass={s.bass:.2f} beat={s.beat:.2f} strike={s.strike:.2f} drop={s.drop:.2f} "
                        f"tempo={tempo} conf={s.beat_confidence:.2f} phase={s.beat_phase:.2f}",
                        flush=True,
                    )
                    report = now
                    frames = 0
    finally:
        field.close()
        sink.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
