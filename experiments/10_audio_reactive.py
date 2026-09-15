from __future__ import annotations

import argparse
import math
import time

import cv2
import numpy as np

from projection_mapping.audio_reactive import AudioFeatureStream, format_device_table, list_audio_devices
from projection_mapping.runtime import FullscreenSink


class SpectralFieldRenderer:
    """Audio-reactive caustic/ribbon field with restrained motion and sharp transients.

    The previous visual let every feature modulate everything at once, which made it
    noisy and weakly legible. This renderer gives each feature a distinct visual role:
    bass breathes the spatial field, mids bend ribbons, treble adds fine caustics,
    flux controls local instability, and onset emits short-lived shock fronts.
    """

    def __init__(self, width: int, height: int, madness: float) -> None:
        self.width = int(width)
        self.height = int(height)
        self.madness = float(np.clip(madness, 0.0, 1.0))
        y, x = np.mgrid[0:self.height, 0:self.width].astype(np.float32)
        self.nx = (x - self.width * 0.5) / max(self.width, 1)
        self.ny = (y - self.height * 0.5) / max(self.height, 1)
        self.radius = np.sqrt(self.nx * self.nx + self.ny * self.ny)
        self.angle = np.arctan2(self.ny, self.nx)
        self._onset_energy = 0.0
        self._phase = 0.0
        self._last_t: float | None = None

    def __call__(self, t: float, f) -> np.ndarray:
        if self._last_t is None:
            dt = 1.0 / 60.0
        else:
            dt = min(max(t - self._last_t, 1e-4), 0.1)
        self._last_t = t

        bass = float(np.clip(f.bass, 0.0, 1.0))
        mid = float(np.clip(f.mid, 0.0, 1.0))
        treble = float(np.clip(f.treble, 0.0, 1.0))
        flux = float(np.clip(f.flux, 0.0, 1.0))
        onset = float(np.clip(f.onset, 0.0, 1.0))
        rms = float(np.clip(f.rms, 0.0, 1.0))
        centroid = float(np.clip(f.centroid, 0.0, 1.0))

        self._onset_energy = max(self._onset_energy * math.exp(-dt * 5.5), onset)
        self._phase += dt * (0.16 + 0.42 * mid + 0.18 * self.madness)

        # A slow, breathing warp rather than continuous radial spinning.
        breath = 0.035 + 0.08 * bass
        warp_x = self.nx + breath * np.sin(self.ny * 8.0 + self._phase * 3.0)
        warp_y = self.ny + breath * np.sin(self.nx * 7.0 - self._phase * 2.4)
        rr = np.sqrt(warp_x * warp_x + warp_y * warp_y)
        aa = np.arctan2(warp_y, warp_x)

        # Broad flowing material structure, mostly mid-controlled.
        ribbon_phase = (
            warp_x * (7.0 + 2.5 * self.madness)
            + 0.72 * np.sin(warp_y * (8.0 + 4.0 * mid) + self._phase * 1.7)
            + 0.32 * np.sin(aa * 3.0 - self._phase)
        )
        ribbons = 0.5 + 0.5 * np.sin(ribbon_phase * math.pi)
        ribbons = np.power(np.clip(ribbons, 0.0, 1.0), 2.8)

        # Fine caustic interference appears only when upper frequencies are present.
        caustics = np.sin(
            (warp_x * (18.0 + 18.0 * treble) + warp_y * (13.0 + 10.0 * centroid))
            * math.pi
            + self._phase * (3.0 + 2.0 * flux)
        )
        caustics = np.power(np.clip(0.5 + 0.5 * caustics, 0.0, 1.0), 8.0)

        # Onsets launch a clean circular front instead of flashing the whole image.
        shock_radius = (self._phase * 0.42) % 0.72
        shock = np.exp(-np.square(rr - shock_radius) / 0.00075) * self._onset_energy

        # Bass creates a dark/bright central breathing mass without constant pulsation.
        core = np.exp(-np.square(rr / (0.17 + 0.06 * bass)))

        base = 0.08 + 0.62 * ribbons * (0.30 + 0.70 * rms)
        detail = caustics * (0.05 + 0.72 * treble)
        energy = np.clip(base + detail + shock * 1.3 + core * bass * 0.40, 0.0, 1.0)

        # Cyan/blue base with magenta highlights; centroid shifts emphasis subtly.
        cool = np.array([0.06, 0.32, 0.68], dtype=np.float32)
        hot = np.array([0.94, 0.08, 0.64], dtype=np.float32)
        white = np.array([0.82, 0.93, 1.00], dtype=np.float32)
        mix = np.clip(0.22 + 0.55 * centroid + 0.42 * shock, 0.0, 1.0)[..., None]
        rgb = cool[None, None, :] * (1.0 - mix) + hot[None, None, :] * mix
        rgb *= energy[..., None]
        rgb += white[None, None, :] * (detail[..., None] * 0.28 + shock[..., None] * 0.40)

        # Keep the background actually dark so projection contrast survives in-room.
        vignette = np.clip(1.15 - self.radius * 1.15, 0.18, 1.0)
        rgb *= vignette[..., None]
        return (np.clip(rgb, 0.0, 1.0) * 255).astype(np.uint8)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["mic", "system"], default="system")
    ap.add_argument("--device", default=None, help="device name/id substring")
    ap.add_argument("--list-devices", action="store_true")
    ap.add_argument("--display", type=int, default=1)
    ap.add_argument("--projector-width", type=int, default=1920)
    ap.add_argument("--projector-height", type=int, default=1080)
    ap.add_argument("--render-width", type=int, default=640)
    ap.add_argument("--render-height", type=int, default=360)
    ap.add_argument("--sample-rate", type=int, default=48000)
    ap.add_argument("--blocksize", type=int, default=256)
    ap.add_argument("--attack-ms", type=float, default=5.0)
    ap.add_argument("--release-ms", type=float, default=110.0)
    ap.add_argument("--sensitivity", type=float, default=1.8)
    ap.add_argument("--madness", type=float, default=0.45)
    ap.add_argument("--exclusive-mode", action="store_true", help="experimental Windows WASAPI low-latency mode")
    args = ap.parse_args()

    if args.list_devices:
        print(format_device_table(list_audio_devices()))
        return

    sink = FullscreenSink(window="ProjectionMapping-AudioReactive", display=args.display, fullscreen=True)
    renderer = SpectralFieldRenderer(args.render_width, args.render_height, args.madness)
    t0 = time.perf_counter()
    frames = 0
    report_t = t0

    try:
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
                small = renderer(now - t0, f)
                frame = cv2.resize(
                    small,
                    (args.projector_width, args.projector_height),
                    interpolation=cv2.INTER_LINEAR,
                )
                if sink(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)) is False:
                    break
                frames += 1
                if now - report_t >= 2.0:
                    fps = frames / (now - report_t)
                    age_ms = (now - f.timestamp) * 1000.0
                    print(
                        f"fps={fps:5.1f} feature_age={age_ms:5.1f}ms "
                        f"source={args.source} device={audio.selected_device_name!r} "
                        f"rms={f.rms:.2f} bass={f.bass:.2f} mid={f.mid:.2f} "
                        f"treble={f.treble:.2f} flux={f.flux:.2f} onset={f.onset:.2f}",
                        flush=True,
                    )
                    frames = 0
                    report_t = now
    finally:
        sink.close()


if __name__ == "__main__":
    main()
