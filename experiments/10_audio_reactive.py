from __future__ import annotations

import argparse
import math
import time

import cv2
import numpy as np

from projection_mapping.audio_reactive import AudioFeatureStream, format_device_table, list_audio_devices
from projection_mapping.music_reactivity import MusicalEventMapper
from projection_mapping.runtime import FullscreenSink


PALETTES = {
    "cyan_magenta": np.array([[0.005, 0.02, 0.04], [0.00, 0.96, 1.00], [0.16, 0.34, 1.00], [1.00, 0.02, 0.78]], np.float32),
    "neon_aurora": np.array([[0.01, 0.07, 0.14], [0.00, 0.88, 1.00], [0.55, 0.18, 1.00], [1.00, 0.08, 0.67]], np.float32),
    "solar_flare": np.array([[0.08, 0.01, 0.03], [1.00, 0.16, 0.05], [1.00, 0.63, 0.00], [1.00, 0.10, 0.48]], np.float32),
    "bioluminescent": np.array([[0.00, 0.06, 0.08], [0.00, 0.95, 0.66], [0.05, 0.45, 1.00], [0.57, 0.20, 1.00]], np.float32),
    "intelli": np.array([[0.03, 0.02, 0.08], [0.00, 0.78, 1.00], [0.82, 0.10, 0.78], [1.00, 0.78, 0.56]], np.float32),
    "mono_accent": np.array([[0.005, 0.008, 0.015], [0.12, 0.17, 0.23], [0.18, 0.78, 1.00], [0.92, 0.98, 1.00]], np.float32),
    "prismatic": np.array([[0.03, 0.00, 0.08], [0.00, 0.90, 1.00], [1.00, 0.08, 0.50], [1.00, 0.82, 0.08]], np.float32),
}


def palette_sample(palette: np.ndarray, x: np.ndarray) -> np.ndarray:
    x = np.clip(x, 0.0, 0.9999)
    scaled = x * (len(palette) - 1)
    i = np.floor(scaled).astype(np.int32)
    f = (scaled - i)[..., None]
    return palette[i] * (1.0 - f) + palette[np.minimum(i + 1, len(palette) - 1)] * f


class AudioVisualRenderer:
    def __init__(self, width: int, height: int, preset: str, palette: str, madness: float) -> None:
        self.width = int(width)
        self.height = int(height)
        self.preset = preset
        self.palette = PALETTES[palette]
        self.madness = float(np.clip(madness, 0.0, 1.0))
        y, x = np.mgrid[0:self.height, 0:self.width].astype(np.float32)
        aspect = self.width / max(self.height, 1)
        self.x = (x / max(self.width - 1, 1) - 0.5) * 2.0 * aspect
        self.y = (y / max(self.height - 1, 1) - 0.5) * 2.0
        self.r = np.sqrt(self.x * self.x + self.y * self.y) + 1e-5
        self.a = np.arctan2(self.y, self.x)
        rng = np.random.default_rng(1138)
        self.star_seed = rng.random((self.height, self.width), dtype=np.float32)
        self._phase = 0.0
        self._last_t: float | None = None

    def _finish(self, energy: np.ndarray, chroma: np.ndarray, s) -> np.ndarray:
        color = palette_sample(self.palette, np.mod(chroma + s.color * 0.18, 1.0))
        rgb = color * np.clip(energy, 0.0, 2.2)[..., None]
        # Rare strong event gets a coherent white-hot lift instead of random flicker.
        rgb += (0.65 * s.ascension + 0.24 * s.strike) * np.exp(-self.r[..., None] * 1.7)
        vignette = np.clip(1.12 - self.r * 0.34, 0.30, 1.0)
        rgb *= vignette[..., None]
        # Soft filmic shoulder.
        rgb = rgb / (0.78 + rgb)
        return (np.clip(rgb, 0.0, 1.0) * 255).astype(np.uint8)

    def spectral_bloom(self, t: float, s) -> np.ndarray:
        qx = self.x + 0.18 * np.sin(self.y * 2.2 + self._phase)
        qy = self.y + 0.16 * np.sin(self.x * 2.7 - self._phase * 0.8)
        b1 = np.exp(-((qx - 0.45 * np.sin(t * 0.31)) ** 2 + (qy - 0.28 * np.cos(t * 0.27)) ** 2) * (2.4 - 0.8 * s.bass))
        b2 = np.exp(-((qx + 0.52 * np.cos(t * 0.23)) ** 2 + (qy + 0.35 * np.sin(t * 0.36)) ** 2) * 2.8)
        petals = 0.5 + 0.5 * np.sin(self.a * (5.0 + 3.0 * self.madness) + self.r * 8.0 - t * (0.5 + s.mids))
        bloom = (b1 + b2) * (0.34 + 0.78 * s.loudness) + petals * b1 * (0.2 + 0.55 * s.mids)
        shock = np.exp(-np.square(self.r - (0.25 + (t * 0.55) % 1.35)) / 0.003) * s.strike
        return self._finish(bloom + shock * 1.4, 0.08 + petals * 0.42 + t * 0.018, s)

    def ribbon_cathedral(self, t: float, s) -> np.ndarray:
        bend = self.x + 0.20 * np.sin(self.y * (4.0 + 3.0 * s.mids) + t * 0.42)
        columns = np.power(np.clip(0.5 + 0.5 * np.cos(bend * math.pi * 5.0), 0.0, 1.0), 10.0)
        arches_r = np.sqrt((np.mod(self.x + 0.70, 1.40) - 0.70) ** 2 + (self.y + 0.12) ** 2)
        arches = np.exp(-46.0 * np.abs(arches_r - (0.52 + 0.05 * s.bass)))
        ribbons = np.power(np.clip(0.5 + 0.5 * np.sin(self.x * 8.5 + np.sin(self.y * 5.2 - t * 0.5) * (1.2 + s.mids * 2.2)), 0.0, 1.0), 4.0)
        energy = (columns * 0.50 + arches * 1.2 + ribbons * (0.22 + 0.62 * s.loudness))
        energy += np.exp(-np.square(self.r - ((t * 0.45) % 1.5)) / 0.0025) * s.strike * 1.5
        return self._finish(energy, 0.48 + 0.20 * self.y + 0.08 * np.sin(t * 0.2), s)

    def pulse_tunnel(self, t: float, s) -> np.ndarray:
        z = 1.0 / self.r
        spin = self.a + t * (0.12 + 0.45 * s.mids)
        ribs = np.cos(spin * (10.0 + 8.0 * self.madness) + z * 2.0)
        tunnel = np.sin(z * (16.0 + 5.0 * s.bass) - t * (3.0 + 4.0 * s.beat) + ribs)
        depth = np.clip((0.5 + 0.5 * tunnel) ** 3, 0.0, 1.0)
        rings = np.power(np.clip(0.5 + 0.5 * np.sin(z * 12.0 - t * (1.6 + 4.5 * s.beat)), 0.0, 1.0), 8.0)
        core = np.exp(-self.r * (3.8 - 1.3 * s.bass))
        energy = depth * (0.22 + 0.75 * s.loudness) + rings * (0.16 + 0.90 * s.beat) + core * (0.25 + s.bass)
        return self._finish(energy, 0.12 + spin / (2 * math.pi) + 0.15 * z, s)

    def caustic_field(self, t: float, s) -> np.ndarray:
        w1 = np.sin(self.x * (9.0 + 5.0 * s.mids) + np.sin(self.y * 6.0 + t * 0.42) * 2.7)
        w2 = np.sin(self.y * (12.0 + 4.0 * s.bass) + np.sin(self.x * 5.0 - t * 0.37) * 2.2)
        caustic = np.power(np.clip(0.5 + 0.5 * w1 * w2, 0.0, 1.0), 5.0)
        broad = 0.5 + 0.5 * np.sin(self.x * 2.0 + self.y * 2.7 + t * 0.20)
        glints = np.power(np.clip(0.5 + 0.5 * np.sin(self.x * 31.0 + self.y * 27.0 + t * 2.5), 0.0, 1.0), 15.0) * s.highs
        energy = caustic * (0.28 + 0.90 * s.loudness) + broad * 0.12 + glints * 1.25
        energy += np.exp(-np.square(self.r - ((t * 0.60) % 1.45)) / 0.002) * s.strike
        return self._finish(energy, 0.55 + broad * 0.20 + caustic * 0.12, s)

    def constellation(self, t: float, s) -> np.ndarray:
        twinkle = 0.5 + 0.5 * np.sin(t * 1.7 + self.star_seed * 18.0)
        stars = (self.star_seed > (0.992 - 0.004 * s.highs)).astype(np.float32) * np.power(twinkle, 4.0)
        stars = cv2.GaussianBlur(stars, (0, 0), 0.7)
        filaments = np.exp(-18.0 * np.abs(np.sin(self.x * 2.5 + np.sin(self.y * 3.1 + t * 0.24))))
        orbit = np.exp(-np.square(self.r - (0.48 + 0.12 * np.sin(t * 0.33))) / 0.0018)
        event_ring = np.exp(-np.square(self.r - ((t * 0.75) % 1.55)) / 0.0015) * s.strike
        energy = stars * (0.45 + 1.4 * s.highs) + filaments * (0.08 + 0.38 * s.mids) + orbit * (0.15 + 0.60 * s.bass) + event_ring * 1.8
        return self._finish(energy, self.star_seed * 0.35 + self.a / (2 * math.pi), s)

    def mechanical_sync(self, t: float, s) -> np.ndarray:
        teeth = 0.5 + 0.5 * np.sign(np.sin(self.a * 20.0 + t * (0.6 + 2.2 * s.mids)))
        gear = np.exp(-55.0 * np.abs(self.r - (0.52 + teeth * (0.035 + 0.035 * s.beat))))
        inner = np.exp(-75.0 * np.abs(self.r - (0.27 + 0.03 * s.bass)))
        gx = np.power(np.clip(0.5 + 0.5 * np.sin(self.x * 17.0 + t), 0.0, 1.0), 9.0)
        gy = np.power(np.clip(0.5 + 0.5 * np.sin(self.y * 13.0 - t * 0.7), 0.0, 1.0), 9.0)
        sparks = np.power(np.clip(0.5 + 0.5 * np.sin(self.x * 51.0 + self.y * 43.0 + t * 5.0), 0.0, 1.0), 20.0) * s.highs
        energy = gear * (0.55 + s.beat) + inner * (0.35 + 0.8 * s.bass) + gx * gy * (0.10 + 0.55 * s.mids) + sparks
        energy += np.exp(-np.square(self.r - ((t * 0.70) % 1.5)) / 0.0018) * s.strike * 1.8
        return self._finish(energy, 0.78 + gear * 0.12 + sparks * 0.2, s)

    def __call__(self, t: float, s) -> np.ndarray:
        if self._last_t is None:
            dt = 1 / 60
        else:
            dt = float(np.clip(t - self._last_t, 1e-4, 0.1))
        self._last_t = t
        self._phase += dt * (0.14 + 0.28 * s.mids + 0.25 * self.madness)
        return getattr(self, self.preset)(t, s)


PRESETS = ["spectral_bloom", "ribbon_cathedral", "pulse_tunnel", "caustic_field", "constellation", "mechanical_sync"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["mic", "system"], default="system")
    ap.add_argument("--device", default=None)
    ap.add_argument("--list-devices", action="store_true")
    ap.add_argument("--preset", choices=PRESETS, default="spectral_bloom")
    ap.add_argument("--palette", choices=sorted(PALETTES), default="cyan_magenta")
    ap.add_argument("--reactivity", choices=["smooth", "balanced", "punchy", "chaotic"], default="balanced")
    ap.add_argument("--event-threshold", type=float, default=0.62)
    ap.add_argument("--beat-threshold", type=float, default=0.50)
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
    ap.add_argument("--exclusive-mode", action="store_true")
    args = ap.parse_args()

    if args.list_devices:
        print(format_device_table(list_audio_devices()))
        return

    sink = FullscreenSink(window="ProjectionMapping-AudioStudio", display=args.display, fullscreen=True)
    renderer = AudioVisualRenderer(args.render_width, args.render_height, args.preset, args.palette, args.madness)
    mapper = MusicalEventMapper(
        mode=args.reactivity,
        event_threshold=args.event_threshold,
        beat_threshold=args.beat_threshold,
        madness=args.madness,
    )
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
            print(
                f"[audio-studio] preset={args.preset} palette={args.palette} reactivity={args.reactivity} "
                f"event_threshold={args.event_threshold:.2f} beat_threshold={args.beat_threshold:.2f}",
                flush=True,
            )
            while True:
                now = time.perf_counter()
                if audio.error is not None:
                    raise RuntimeError("audio capture failed") from audio.error
                f = audio.latest
                s = mapper.update(f, now)
                small = renderer(now - t0, s)
                frame = cv2.resize(small, (args.projector_width, args.projector_height), interpolation=cv2.INTER_CUBIC)
                if sink(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)) is False:
                    break
                frames += 1
                if now - report_t >= 2.0:
                    print(
                        f"fps={frames / (now-report_t):5.1f} source={args.source} device={audio.selected_device_name!r} "
                        f"bass={s.bass:.2f} mids={s.mids:.2f} highs={s.highs:.2f} "
                        f"beat={s.beat:.2f} strike={s.strike:.2f} ascension={s.ascension:.2f}",
                        flush=True,
                    )
                    frames = 0
                    report_t = now
    finally:
        sink.close()


if __name__ == "__main__":
    main()
