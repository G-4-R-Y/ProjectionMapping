"""Performance Director: one musical conductor for shader materials + GPU particles.

The director combines the existing stable music feature/event pipeline, phrase/section tracker,
Shader Performance Deck, and persistent GPU particle choreography. A single smoothed MADNESS
macro drives both visual layers; cue transitions are timed, musical, or hybrid.

F11 toggles fullscreen; ESC exits.
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
from projection_mapping.gpu_particles import GPUParticleField
from projection_mapping.music_reactivity import MusicalEventMapper
from projection_mapping.music_structure import MusicStructureTracker
from projection_mapping.particle_choreography import blend_choreographies, choreography
from projection_mapping.performance_director import (
    PERFORMANCE_CUES,
    PERFORMANCE_JOURNEYS,
    PerformanceDirector,
)
from projection_mapping.runtime import FullscreenSink
from projection_mapping.shader_scenes import SHADER_SCENE_PRESETS, ShaderSceneRenderer


def _screen_blend(fg: np.ndarray, bg: np.ndarray, amount: float) -> np.ndarray:
    a = fg.astype(np.float32) / 255.0
    b = bg.astype(np.float32) / 255.0 * float(np.clip(amount, 0.0, 1.0))
    out = 1.0 - (1.0 - a) * (1.0 - b)
    peak = np.max(out, axis=2, keepdims=True)
    gate = np.clip((peak - 0.006) / 0.040, 0.0, 1.0)
    out *= gate
    return np.clip(out * 255.0, 0, 255).astype(np.uint8)


def _crossfade(a: np.ndarray, b: np.ndarray, mix: float) -> np.ndarray:
    m = float(np.clip(mix, 0.0, 1.0))
    out = a.astype(np.float32) * (1.0 - m) + b.astype(np.float32) * m
    return np.clip(out, 0, 255).astype(np.uint8)


def _tempo_scale(signals) -> float:
    if signals.beat_confidence >= 0.18 and signals.tempo_bpm > 0.0:
        return float(np.clip(signals.tempo_bpm / 122.0, 0.62, 1.55))
    return 1.0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["system", "mic"], default="system")
    ap.add_argument("--device", default=None)
    ap.add_argument("--list-devices", action="store_true")
    ap.add_argument("--journey", choices=sorted(PERFORMANCE_JOURNEYS), default="liquid_arc")
    ap.add_argument("--director-mode", choices=["hybrid", "musical", "timed"], default="hybrid")
    ap.add_argument("--cue-seconds", type=float, default=24.0)
    ap.add_argument("--transition-seconds", type=float, default=3.0)
    ap.add_argument("--minimum-dwell", type=float, default=5.0)
    ap.add_argument("--madness", type=float, default=0.45)
    ap.add_argument("--reactivity", choices=["smooth", "balanced", "punchy", "chaotic"], default="balanced")
    ap.add_argument("--event-threshold", type=float, default=0.62)
    ap.add_argument("--beat-threshold", type=float, default=0.48)
    ap.add_argument("--sensitivity", type=float, default=1.20)
    ap.add_argument("--sample-rate", type=int, default=48_000)
    ap.add_argument("--blocksize", type=int, default=256)
    ap.add_argument("--analysis-size", type=int, default=2048)
    ap.add_argument("--capacity", type=int, default=32768)
    ap.add_argument("--display", type=int, default=1)
    ap.add_argument("--render-width", type=int, default=768)
    ap.add_argument("--render-height", type=int, default=432)
    ap.add_argument("--projector-width", type=int, default=1920)
    ap.add_argument("--projector-height", type=int, default=1080)
    args = ap.parse_args()

    if args.list_devices:
        print(format_device_table(list_audio_devices()))
        return

    shader = ShaderSceneRenderer(args.render_width, args.render_height)
    particles = GPUParticleField(
        args.render_width,
        args.render_height,
        capacity=args.capacity,
        palette="cyan_magenta",
    )
    sink = FullscreenSink(
        window="ProjectionMapping-PerformanceDirector",
        display=args.display,
        fullscreen=True,
    )

    mapper = MusicalEventMapper(
        mode=args.reactivity,
        event_threshold=args.event_threshold,
        beat_threshold=args.beat_threshold,
        madness=args.madness,
    )
    structure_tracker = MusicStructureTracker()
    director = PerformanceDirector(
        journey=args.journey,
        mode=args.director_mode,
        base_madness=args.madness,
        cue_seconds=args.cue_seconds,
        transition_seconds=args.transition_seconds,
        minimum_dwell=args.minimum_dwell,
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

    def render_shader_cue(cue_name: str, *, elapsed: float, signals, macro) -> np.ndarray:
        cue = PERFORMANCE_CUES[cue_name]
        preset = SHADER_SCENE_PRESETS[cue.shader_preset]
        tempo = _tempo_scale(signals)
        scene_mix = float(
            np.clip(
                preset.scene_mix
                + 0.08 * signals.mids
                + 0.10 * signals.drop
                - 0.03 * (1.0 - macro.madness),
                0.0,
                1.0,
            )
        )
        chaos = float(np.clip(preset.chaos * 0.50 + macro.shader_chaos * 0.58, 0.0, 2.5))
        intensity = float(np.clip(preset.intensity * macro.shader_intensity, 0.0, 3.0))
        palette_rate = preset.palette_cycle + macro.palette_rate
        return shader.render(
            preset.scene,
            t=elapsed * preset.speed * tempo,
            intensity=intensity,
            chaos=chaos,
            palette=preset.palette,
            palette_shift=elapsed * palette_rate + signals.color * 0.08,
            scene_b=preset.scene_b,
            scene_mix=scene_mix,
        )

    print(
        f"[director] journey={args.journey} mode={args.director_mode} particles={particles.capacity} "
        f"shader_gl={shader.context_info.gl_version} particle_gl={particles.context_info.gl_version}",
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
                dt = float(np.clip(now - last, 1e-4, 0.08))
                last = now
                if audio.error is not None:
                    raise RuntimeError("audio capture failed") from audio.error

                features = audio.latest
                signals = mapper.update(features, now)
                structure = structure_tracker.update(signals, now)
                state = director.update(structure, signals, now)
                macro = state.macro

                source_cue = PERFORMANCE_CUES[state.source_cue]
                target_cue = PERFORMANCE_CUES[state.target_cue]
                source_particles = choreography(
                    source_cue.particle_bank,
                    signals,
                    elapsed,
                    macro.madness,
                )
                target_particles = choreography(
                    target_cue.particle_bank,
                    signals,
                    elapsed,
                    macro.madness,
                )
                choreo = blend_choreographies(source_particles, target_particles, state.mix)

                particles.palette = particles.PALETTES.get(
                    choreo.palette,
                    particles.PALETTES["cyan_magenta"],
                )
                particles.set_material(choreo.material)
                particle_frame = particles.render(
                    list(choreo.emitters),
                    t=elapsed,
                    dt=dt,
                    emission_rate=choreo.emission_rate * macro.particle_emission,
                    turbulence=choreo.turbulence * macro.particle_turbulence,
                    drag=choreo.drag,
                    feedback=choreo.feedback,
                    bloom=choreo.bloom * macro.particle_bloom,
                    energy=0.70 + 0.68 * macro.madness + 0.32 * signals.loudness,
                    bass=signals.bass,
                    strike=signals.strike,
                    drop=signals.drop,
                    field_mode=choreo.field_mode,
                    field_strength=choreo.field_strength * macro.field_force,
                    field_scale=choreo.field_scale,
                    field_spin=choreo.field_spin * (0.82 + 0.30 * signals.mids),
                    well_strength=choreo.well_strength * (0.78 + 0.42 * macro.madness + 0.34 * signals.bass),
                    nebula_mix=choreo.nebula_mix * (0.82 + 0.34 * macro.madness + 0.22 * signals.highs),
                )

                if state.active_transition:
                    shader_a = render_shader_cue(
                        state.source_cue,
                        elapsed=elapsed,
                        signals=signals,
                        macro=macro,
                    )
                    shader_b = render_shader_cue(
                        state.target_cue,
                        elapsed=elapsed,
                        signals=signals,
                        macro=macro,
                    )
                    shader_frame = _crossfade(shader_a, shader_b, state.mix)
                else:
                    shader_frame = render_shader_cue(
                        state.target_cue,
                        elapsed=elapsed,
                        signals=signals,
                        macro=macro,
                    )

                small = _screen_blend(
                    particle_frame,
                    shader_frame,
                    macro.composite_mix,
                )
                out = cv2.resize(
                    small,
                    (args.projector_width, args.projector_height),
                    interpolation=cv2.INTER_CUBIC,
                )
                if sink(cv2.cvtColor(out, cv2.COLOR_RGB2BGR)) is False:
                    break

                frames += 1
                if now - report >= 2.0:
                    tempo = f"{signals.tempo_bpm:.1f}" if signals.beat_confidence >= 0.18 else "--"
                    transition = (
                        f"{state.source_cue}->{state.target_cue}:{state.mix:.2f}"
                        if state.active_transition
                        else state.target_cue
                    )
                    print(
                        f"[director] fps={frames / (now - report):.1f} cue={transition} "
                        f"section={structure.section} macro={macro.madness:.2f} energy={macro.energy:.2f} "
                        f"shader_mix={macro.composite_mix:.2f} bank={target_cue.particle_bank} "
                        f"beat={signals.beat:.2f} drop={signals.drop:.2f} tempo={tempo}",
                        flush=True,
                    )
                    report = now
                    frames = 0
    finally:
        particles.close()
        shader.close()
        sink.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
