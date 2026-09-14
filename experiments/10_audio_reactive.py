from __future__ import annotations

import argparse
import math
import time

import cv2
import numpy as np

from projection_mapping.audio_reactive import AudioFeatureStream, format_device_table, list_audio_devices
from projection_mapping.runtime import FullscreenSink


def render_field(width: int, height: int, t: float, f, madness: float) -> np.ndarray:
    # Render low-res and upscale: latency matters more than wasting CPU on per-pixel 1080p math.
    y, x = np.mgrid[0:height, 0:width].astype(np.float32)
    nx = (x - width * 0.5) / max(width, 1)
    ny = (y - height * 0.5) / max(height, 1)
    r = np.sqrt(nx * nx + ny * ny)
    a = np.arctan2(ny, nx)

    bass = f.bass
    mid = f.mid
    treble = f.treble
    onset = f.onset
    centroid = f.centroid

    rings = np.sin((r * (34.0 + 20.0 * madness) - t * (4.0 + bass * 12.0)) * math.pi)
    spokes = np.sin(a * (6.0 + int(10 * madness)) + t * (1.5 + mid * 7.0))
    interference = np.sin((nx * (10 + 25 * treble) + ny * (8 + 18 * mid) + t * 2.0) * math.pi)
    pulse = np.exp(-((r - (0.14 + 0.22 * math.sin(t * 0.7))) ** 2) / (0.004 + 0.025 * (1.0 - bass)))

    v1 = 0.48 + 0.26 * rings + 0.18 * spokes + onset * 0.8 * pulse
    v2 = 0.50 + 0.30 * interference + bass * 0.35 - 0.15 * rings
    v3 = 0.45 + 0.28 * np.sin(spokes + rings * 1.6) + treble * 0.45

    hue_shift = centroid * 1.8 + t * 0.04
    c1 = (np.sin(v1 * 3.2 + hue_shift) * 0.5 + 0.5)
    c2 = (np.sin(v2 * 3.5 + hue_shift + 2.1) * 0.5 + 0.5)
    c3 = (np.sin(v3 * 3.8 + hue_shift + 4.2) * 0.5 + 0.5)
    rgb = np.dstack([c1, c2, c3])

    gain = 0.32 + 0.85 * np.clip(f.rms + onset * 0.6, 0.0, 1.0)
    rgb = np.clip(rgb * gain + onset * 0.18, 0.0, 1.0)
    return (rgb * 255).astype(np.uint8)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["mic", "system"], default="mic")
    ap.add_argument("--device", default=None, help="device name/id substring")
    ap.add_argument("--list-devices", action="store_true")
    ap.add_argument("--display", type=int, default=1)
    ap.add_argument("--projector-width", type=int, default=1920)
    ap.add_argument("--projector-height", type=int, default=1080)
    ap.add_argument("--render-width", type=int, default=640)
    ap.add_argument("--render-height", type=int, default=360)
    ap.add_argument("--sample-rate", type=int, default=48000)
    ap.add_argument("--blocksize", type=int, default=256)
    ap.add_argument("--attack-ms", type=float, default=6.0)
    ap.add_argument("--release-ms", type=float, default=85.0)
    ap.add_argument("--sensitivity", type=float, default=1.7)
    ap.add_argument("--madness", type=float, default=0.72)
    ap.add_argument("--exclusive-mode", action="store_true", help="experimental Windows WASAPI low-latency mode")
    args = ap.parse_args()

    if args.list_devices:
        print(format_device_table(list_audio_devices()))
        return

    sink = FullscreenSink(window="ProjectionMapping-AudioReactive", display=args.display)
    t0 = time.perf_counter()
    frames = 0
    report_t = t0

    with AudioFeatureStream(
        source=args.source,
        device=args.device,
        sample_rate=args.sample_rate,
        blocksize=args.blocksize,
        attack_ms=args.attack_ms,
        release_ms=args.release_ms,
        sensitivity=args.sensitivity,
        exclusive_mode=args.exclusive_mode,
    ) as audio:
        while True:
            now = time.perf_counter()
            if audio.error is not None:
                raise RuntimeError("audio capture failed") from audio.error
            f = audio.latest
            small = render_field(args.render_width, args.render_height, now - t0, f, args.madness)
            frame = cv2.resize(small, (args.projector_width, args.projector_height), interpolation=cv2.INTER_LINEAR)
            # FullscreenSink consumes BGR.
            if sink(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)) is False:
                break
            frames += 1
            if now - report_t >= 2.0:
                fps = frames / (now - report_t)
                age_ms = (now - f.timestamp) * 1000.0
                print(
                    f"fps={fps:5.1f} feature_age={age_ms:5.1f}ms "
                    f"rms={f.rms:.2f} bass={f.bass:.2f} mid={f.mid:.2f} "
                    f"treble={f.treble:.2f} onset={f.onset:.2f}"
                )
                frames = 0
                report_t = now

    sink.close()


if __name__ == "__main__":
    main()
