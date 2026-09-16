"""Song Studio vNext: musical-state-driven GPU particle choreography.

The particle stage has a section-aware Journey conductor, reusable emissive particle materials,
and optional music-reactive Polar Math or structured-chaos Shader Scene backdrops.
F11 toggles fullscreen; ESC exits.
"""
from __future__ import annotations

import argparse
import time

import cv2
import numpy as np

from projection_mapping.audio_music_features import RollingMusicFeatureExtractor
from projection_mapping.audio_reactive import AudioFeatureStream, format_device_table, list_audio_devices
from projection_mapping.gpu_particles import GPUParticleField
from projection_mapping.music_reactivity import MusicalEventMapper
from projection_mapping.music_structure import MusicStructureTracker, ParticleJourneyController
from projection_mapping.particle_choreography import BANKS, choreography
from projection_mapping.polar_math import POLAR_MODES, POLAR_PALETTES, PolarMathRenderer
from projection_mapping.runtime import FullscreenSink
from projection_mapping.shader_scenes import SCENE_IDS, ShaderSceneRenderer


_BACKDROP_BY_BANK = {
    "orbit_reactor": "bessel_wave_chamber",
    "dual_comet": "scene:wormhole_choir",
    "cathedral_rain": "scene:neon_cathedral",
    "vortex_gate": "scene:event_horizon",
    "constellation_bloom": "phyllotaxis_reactor",
    "reactor_bloom": "scene:plasma_singularity",
    "polar_gate": "scene:vortex_crown",
    "ritual_rain": "rose_lattice",
    "helix_fountain": "scene:collapse_flower",
    "nebula_bloom": "scene:aurora_void",
    "techno_lattice": "scene:liquid_chrome",
}

_BACKDROP_CHOICES = (
    "none",
    "auto",
    *POLAR_MODES,
    *(f"scene:{scene}" for scene in SCENE_IDS),
)


def _screen_blend(fg: np.ndarray, bg: np.ndarray, amount: float) -> np.ndarray:
    a = fg.astype(np.float32) / 255.0
    b = bg.astype(np.float32) / 255.0 * float(np.clip(amount, 0.0, 1.0))
    out = 1.0 - (1.0 - a) * (1.0 - b)
    peak = np.max(out, axis=2, keepdims=True)
    gate = np.clip((peak - 0.008) / 0.045, 0.0, 1.0)
    out *= gate
    return np.clip(out * 255.0, 0, 255).astype(np.uint8)


def _need_polar(backdrop: str) -> bool:
    return backdrop == "auto" or backdrop in POLAR_MODES


def _need_scene(backdrop: str) -> bool:
    return backdrop == "auto" or backdrop.startswith("scene:")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["system", "mic"], default="system")
    ap.add_argument("--device", default=None)
    ap.add_argument("--list-devices", action="store_true")
    ap.add_argument("--bank", choices=("journey", *BANKS), default="journey")
    ap.add_argument("--backdrop", choices=_BACKDROP_CHOICES, default="none")
    ap.add_argument("--backdrop-palette", choices=POLAR_PALETTES, default="spectral")
    ap.add_argument("--backdrop-intensity", type=float, default=0.28)
    ap.add_argument("--backdrop-chaos", type=float, default=1.20)
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
    polar = (
        PolarMathRenderer(
            args.render_width,
            args.render_height,
            mode="rose_lattice",
            palette=args.backdrop_palette,
        )
        if _need_polar(args.backdrop)
        else None
    )
    scene_renderer = (
        ShaderSceneRenderer(args.render_width, args.render_height)
        if _need_scene(args.backdrop)
        else None
    )
    sink = FullscreenSink(window="ProjectionMapping-AudioParticles", display=args.display, fullscreen=True)
    mapper = MusicalEventMapper(
        mode=args.reactivity,
        event_threshold=args.event_threshold,
        beat_threshold=args.beat_threshold,
        madness=args.madness,
    )
    structure_tracker = MusicStructureTracker()
    journey = ParticleJourneyController()
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
        f"[audio-particles] bank={args.bank} particles={field.capacity} backdrop={args.backdrop} "
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
                elapsed = now - t0
                dt = min(max(now - last, 1e-4), 0.08)
                last = now
                if audio.error is not None:
                    raise RuntimeError("audio capture failed") from audio.error
                f = audio.latest
                s = mapper.update(f, now)
                structure = structure_tracker.update(s, now)
                active_bank = journey.update(structure, now) if args.bank == "journey" else args.bank
                c = choreography(active_bank, s, elapsed, args.madness)
                field.palette = field.PALETTES[c.palette]
                field.set_material(c.material)
                small = field.render(
                    list(c.emitters),
                    t=elapsed,
                    dt=dt,
                    emission_rate=c.emission_rate,
                    turbulence=c.turbulence,
                    drag=c.drag,
                    feedback=c.feedback,
                    bloom=c.bloom,
                    energy=0.72 + 0.86 * s.loudness,
                    bass=s.bass,
                    strike=s.strike,
                    drop=s.drop,
                )

                backdrop_mode = "none"
                requested = (
                    _BACKDROP_BY_BANK.get(active_bank, "rose_lattice")
                    if args.backdrop == "auto"
                    else args.backdrop
                )
                if requested in POLAR_MODES and polar is not None:
                    backdrop_mode = requested
                    # The same conductor that changes particle choreography now changes the
                    # *structure* of the math field: builds/mids introduce cross-harmonic warp;
                    # drops can briefly push it much harder without flattening it into noise.
                    polar_chaos = args.backdrop_chaos * (
                        0.66 + 0.30 * s.section_energy + 0.20 * s.mids + 0.34 * s.drop
                    )
                    background = polar.render(
                        t=elapsed,
                        mode=requested,
                        palette=args.backdrop_palette,
                        intensity=0.76 + 0.42 * s.section_energy,
                        chaos=polar_chaos,
                        signals=s,
                    )
                    amount = args.backdrop_intensity * (0.66 + 0.34 * s.section_energy)
                    small = _screen_blend(small, background, amount)
                elif requested.startswith("scene:") and scene_renderer is not None:
                    scene_name = requested.split(":", 1)[1]
                    backdrop_mode = requested
                    # Keep the scene subordinate to particles, but make drops/builds increase
                    # structural instability rather than merely brighten the whole frame.
                    chaos = args.backdrop_chaos * (
                        0.72 + 0.34 * s.section_energy + 0.22 * s.mids + 0.32 * s.drop
                    )
                    tempo_norm = (
                        float(np.clip((s.tempo_bpm - 70.0) / 100.0, 0.0, 1.0))
                        if s.beat_confidence > 0.15 and s.tempo_bpm > 0.0
                        else 0.35
                    )
                    background = scene_renderer.render(
                        scene_name,
                        t=elapsed * (0.82 + 0.24 * tempo_norm),
                        intensity=0.72 + 0.34 * s.section_energy + 0.18 * s.drop,
                        chaos=chaos,
                    )
                    amount = args.backdrop_intensity * (0.58 + 0.42 * s.section_energy)
                    small = _screen_blend(small, background, amount)

                out = cv2.resize(
                    small,
                    (args.projector_width, args.projector_height),
                    interpolation=cv2.INTER_CUBIC,
                )
                if sink(cv2.cvtColor(out, cv2.COLOR_RGB2BGR)) is False:
                    break
                frames += 1
                if now - report >= 2.0:
                    tempo = f"{s.tempo_bpm:.1f}" if s.beat_confidence > 0.15 else "--"
                    print(
                        f"[audio-particles] fps={frames/(now-report):.1f} bank={active_bank} material={c.material} "
                        f"section={structure.section} phrase={structure.phrase_phase:.2f} backdrop={backdrop_mode} "
                        f"emit={c.emission_rate:.0f}/s bass={s.bass:.2f} beat={s.beat:.2f} "
                        f"strike={s.strike:.2f} drop={s.drop:.2f} tempo={tempo} "
                        f"conf={s.beat_confidence:.2f} phase={s.beat_phase:.2f}",
                        flush=True,
                    )
                    report = now
                    frames = 0
    finally:
        if scene_renderer is not None:
            scene_renderer.close()
        if polar is not None:
            polar.close()
        field.close()
        sink.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
