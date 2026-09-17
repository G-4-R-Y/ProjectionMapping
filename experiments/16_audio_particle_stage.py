"""Song Studio vNext: musical-state-driven GPU particle choreography.

The particle stage has a section-aware Journey conductor, reusable emissive particle materials,
and optional music-reactive Polar Math, Famous Math, wave-optics, hyperbolic, geometry-field,
topology, or structured-chaos Shader Scene backdrops. F11 toggles fullscreen; ESC exits.
"""

from __future__ import annotations

import argparse
import time

import cv2
import numpy as np

from projection_mapping.audio_music_features import RollingMusicFeatureExtractor
from projection_mapping.audio_reactive import (
    AudioFeatureStream,
    format_device_table,
    list_audio_devices,
)
from projection_mapping.famous_math import MATH_MODES, MATH_PALETTES, FamousMathRenderer
from projection_mapping.geometry_fields import GEOMETRY_MODES, GeometryFieldRenderer
from projection_mapping.gpu_particles import GPUParticleField
from projection_mapping.hyperbolic_geometry import HYPERBOLIC_MODES, HyperbolicGeometryRenderer
from projection_mapping.music_reactivity import MusicalEventMapper
from projection_mapping.music_structure import (
    MusicStructureTracker,
    ParticleJourneyController,
    ParticleJourneyCrossfade,
)
from projection_mapping.particle_choreography import BANKS, blend_choreographies, choreography
from projection_mapping.polar_math import POLAR_MODES, POLAR_PALETTES, PolarMathRenderer
from projection_mapping.runtime import FullscreenSink
from projection_mapping.shader_scenes import SCENE_IDS, ShaderSceneRenderer
from projection_mapping.topology_worlds import TOPOLOGY_MODES, TopologyWorldRenderer
from projection_mapping.wave_optics import OPTICS_MODES, WaveOpticsRenderer

_BACKDROP_BY_BANK = {
    "orbit_reactor": "bessel_wave_chamber",
    "dual_comet": "scene:wormhole_choir",
    "cathedral_rain": "scene:neon_cathedral",
    "vortex_gate": "scene:event_horizon",
    "constellation_bloom": "hyper:schottky_inversions",
    "reactor_bloom": "scene:plasma_singularity",
    "polar_gate": "hyper:poincare_orbifold",
    "ritual_rain": "optics:multi_source_interference",
    "helix_fountain": "topo:helicoid",
    "nebula_bloom": "math:riemann_zeta",
    "techno_lattice": "scene:liquid_chrome",
    "lissajous_storm": "geo:penrose_interference",
    "singularity_crown": "math:mandelbrot_julia",
    "prism_shards": "optics:moire_gratings",
}

_BACKDROP_CHOICES = (
    "none",
    "auto",
    *POLAR_MODES,
    *(f"scene:{scene}" for scene in SCENE_IDS),
    *(f"math:{mode}" for mode in MATH_MODES),
    *(f"optics:{mode}" for mode in OPTICS_MODES),
    *(f"hyper:{mode}" for mode in HYPERBOLIC_MODES),
    *(f"geo:{mode}" for mode in GEOMETRY_MODES),
    *(f"topo:{mode}" for mode in TOPOLOGY_MODES),
)


def _screen_blend(fg: np.ndarray, bg: np.ndarray, amount: float) -> np.ndarray:
    a = fg.astype(np.float32) / 255.0
    b = bg.astype(np.float32) / 255.0 * float(np.clip(amount, 0.0, 1.0))
    out = 1.0 - (1.0 - a) * (1.0 - b)
    peak = np.max(out, axis=2, keepdims=True)
    gate = np.clip((peak - 0.008) / 0.045, 0.0, 1.0)
    out *= gate
    return np.clip(out * 255.0, 0, 255).astype(np.uint8)


def _frame_crossfade(source: np.ndarray, target: np.ndarray, mix: float) -> np.ndarray:
    m = float(np.clip(mix, 0.0, 1.0))
    out = source.astype(np.float32) * (1.0 - m) + target.astype(np.float32) * m
    return np.clip(out, 0, 255).astype(np.uint8)


def _tempo_norm(signals) -> float:
    if signals.beat_confidence > 0.15 and signals.tempo_bpm > 0.0:
        return float(np.clip((signals.tempo_bpm - 70.0) / 100.0, 0.0, 1.0))
    return 0.35


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["system", "mic"], default="system")
    ap.add_argument("--device", default=None)
    ap.add_argument("--list-devices", action="store_true")
    ap.add_argument("--bank", choices=("journey", *BANKS), default="journey")
    ap.add_argument("--backdrop", choices=_BACKDROP_CHOICES, default="none")
    ap.add_argument("--backdrop-palette", choices=POLAR_PALETTES, default="spectral")
    ap.add_argument("--math-palette", choices=MATH_PALETTES, default="spectral")
    ap.add_argument("--backdrop-intensity", type=float, default=0.28)
    ap.add_argument("--backdrop-chaos", type=float, default=1.20)
    ap.add_argument("--transition-seconds", type=float, default=2.4)
    ap.add_argument(
        "--reactivity", choices=["smooth", "balanced", "punchy", "chaotic"], default="balanced"
    )
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
    renderers: dict[str, object] = {}

    def get_renderer(kind: str):
        if kind in renderers:
            return renderers[kind]
        if kind == "polar":
            renderer = PolarMathRenderer(
                args.render_width,
                args.render_height,
                mode="rose_lattice",
                palette=args.backdrop_palette,
            )
        elif kind == "scene":
            renderer = ShaderSceneRenderer(args.render_width, args.render_height)
        elif kind == "math":
            renderer = FamousMathRenderer(
                args.render_width,
                args.render_height,
                mode="mandelbrot_julia",
                palette=args.math_palette,
            )
        elif kind == "optics":
            renderer = WaveOpticsRenderer(
                args.render_width,
                args.render_height,
                mode="multi_source_interference",
                palette=args.math_palette,
            )
        elif kind == "hyper":
            renderer = HyperbolicGeometryRenderer(
                args.render_width,
                args.render_height,
                mode="poincare_orbifold",
                palette=args.math_palette,
            )
        elif kind == "geo":
            renderer = GeometryFieldRenderer(
                args.render_width,
                args.render_height,
                mode="voronoi_flow",
                palette=args.math_palette,
                site_count=18,
            )
        elif kind == "topo":
            renderer = TopologyWorldRenderer(
                args.render_width, args.render_height, mode="torus_knot", palette=args.math_palette
            )
        else:
            raise ValueError(kind)
        renderers[kind] = renderer
        return renderer

    def render_backdrop(
        backdrop: str,
        *,
        t: float,
        speed: float,
        intensity: float,
        chaos: float,
        signals,
    ):
        if backdrop in POLAR_MODES:
            return get_renderer("polar").render(
                t=t * speed,
                mode=backdrop,
                palette=args.backdrop_palette,
                intensity=intensity,
                chaos=chaos,
                signals=signals,
            )
        if backdrop.startswith("scene:"):
            return get_renderer("scene").render(
                backdrop.split(":", 1)[1],
                t=t * speed,
                intensity=intensity,
                chaos=chaos,
            )
        if backdrop.startswith("math:"):
            return get_renderer("math").render(
                t=t * speed,
                mode=backdrop.split(":", 1)[1],
                palette=args.math_palette,
                intensity=intensity,
                chaos=chaos,
                signals=signals,
            )
        if backdrop.startswith("optics:"):
            return get_renderer("optics").render(
                t=t * speed,
                mode=backdrop.split(":", 1)[1],
                palette=args.math_palette,
                intensity=intensity,
                chaos=chaos,
            )
        if backdrop.startswith("hyper:"):
            return get_renderer("hyper").render(
                t=t * speed,
                mode=backdrop.split(":", 1)[1],
                palette=args.math_palette,
                intensity=intensity,
                chaos=chaos,
            )
        if backdrop.startswith("geo:"):
            return get_renderer("geo").render(
                t=t * speed,
                mode=backdrop.split(":", 1)[1],
                palette=args.math_palette,
                intensity=intensity,
                chaos=chaos,
                scale=0.88 + 0.28 * signals.bass,
                relax_strength=0.40 + 0.35 * signals.section_energy,
            )
        if backdrop.startswith("topo:"):
            return get_renderer("topo").render(
                t=t * speed,
                mode=backdrop.split(":", 1)[1],
                palette=args.math_palette,
                intensity=intensity,
                chaos=chaos,
                scale=0.92 + 0.18 * signals.bass,
                param_a=0.20 + 0.68 * signals.bass,
                param_b=0.20 + 0.68 * signals.highs,
            )
        return None

    sink = FullscreenSink(
        window="ProjectionMapping-AudioParticles", display=args.display, fullscreen=True
    )
    mapper = MusicalEventMapper(
        mode=args.reactivity,
        event_threshold=args.event_threshold,
        beat_threshold=args.beat_threshold,
        madness=args.madness,
    )
    structure_tracker = MusicStructureTracker()
    journey = ParticleJourneyController()
    journey_crossfade = ParticleJourneyCrossfade(
        initial=journey.bank if args.bank == "journey" else args.bank,
        duration=args.transition_seconds,
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
                active_bank = (
                    journey.update(structure, now) if args.bank == "journey" else args.bank
                )
                transition = journey_crossfade.update(active_bank, now)
                source_c = choreography(transition.source_bank, s, elapsed, args.madness)
                target_c = choreography(transition.target_bank, s, elapsed, args.madness)
                c = blend_choreographies(source_c, target_c, transition.mix)
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
                chaos = args.backdrop_chaos * (
                    0.66 + 0.30 * s.section_energy + 0.20 * s.mids + 0.34 * s.drop
                )
                intensity = 0.70 + 0.34 * s.section_energy + 0.16 * s.drop
                speed = 0.80 + 0.24 * _tempo_norm(s)
                amount = args.backdrop_intensity * (0.56 + 0.42 * s.section_energy)
                background = None
                if requested != "none":
                    backdrop_mode = requested
                    if args.backdrop == "auto" and transition.active:
                        source_backdrop = _BACKDROP_BY_BANK.get(
                            transition.source_bank, "rose_lattice"
                        )
                        target_backdrop = _BACKDROP_BY_BANK.get(
                            transition.target_bank, "rose_lattice"
                        )
                        source_frame = render_backdrop(
                            source_backdrop,
                            t=elapsed,
                            speed=speed,
                            intensity=intensity,
                            chaos=chaos,
                            signals=s,
                        )
                        target_frame = render_backdrop(
                            target_backdrop,
                            t=elapsed,
                            speed=speed,
                            intensity=intensity,
                            chaos=chaos,
                            signals=s,
                        )
                        if source_frame is not None and target_frame is not None:
                            background = _frame_crossfade(
                                source_frame, target_frame, transition.mix
                            )
                            backdrop_mode = f"{source_backdrop}->{target_backdrop}"
                    else:
                        background = render_backdrop(
                            requested,
                            t=elapsed,
                            speed=speed,
                            intensity=intensity,
                            chaos=chaos,
                            signals=s,
                        )

                if background is not None:
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
                        f"[audio-particles] fps={frames / (now - report):.1f} bank={active_bank} material={c.material} "
                        f"section={structure.section} phrase={structure.phrase_phase:.2f} backdrop={backdrop_mode} "
                        f"emit={c.emission_rate:.0f}/s bass={s.bass:.2f} beat={s.beat:.2f} "
                        f"strike={s.strike:.2f} drop={s.drop:.2f} tempo={tempo} "
                        f"conf={s.beat_confidence:.2f} phase={s.beat_phase:.2f}",
                        flush=True,
                    )
                    report = now
                    frames = 0
    finally:
        for renderer in renderers.values():
            close = getattr(renderer, "close", None)
            if close is not None:
                close()
        field.close()
        sink.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
