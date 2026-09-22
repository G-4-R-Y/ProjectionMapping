"""Performance Director: one musical conductor for shader materials + GPU particles.

The director combines the existing stable music feature/event pipeline, phrase/section tracker,
Shader Performance Deck, and persistent GPU particle choreography. A single smoothed MADNESS
macro drives both visual layers; cue transitions are timed, musical, or hybrid.

F11 toggles fullscreen; ESC exits.
"""
from __future__ import annotations

import argparse
from dataclasses import replace
import time

import cv2
import numpy as np

from projection_mapping.ableton_link import AbletonLinkClock
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
from projection_mapping.performance_control import (
    MIDIControlInput,
    MIDIStateOutput,
    OSCControlServer,
    PerformanceControlBus,
    PerformanceSnapshot,
    PerformanceStateStore,
    keyboard_events,
)
from projection_mapping.performance_dashboard import (
    LivePerformanceState,
    LiveStateHub,
    OSCStateBroadcaster,
    PerformanceDashboardServer,
)
from projection_mapping.performance_director import (
    PERFORMANCE_CUES,
    PERFORMANCE_JOURNEYS,
    PerformanceDirector,
)
from projection_mapping.performance_timing import PerformanceCueLooper, PerformanceQuantizer
from projection_mapping.piano_performance import PianoExpression
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
    ap.add_argument("--list-midi", action="store_true")
    ap.add_argument("--osc-host", default="127.0.0.1")
    ap.add_argument("--osc-port", type=int, default=9000)
    ap.add_argument("--midi", action="store_true")
    ap.add_argument("--midi-device", default=None)
    ap.add_argument("--midi-madness-cc", type=int, default=1)
    ap.add_argument("--midi-note-base", type=int, default=36)
    ap.add_argument("--midi-output", action="store_true")
    ap.add_argument("--midi-output-device", default=None)
    ap.add_argument("--midi-feedback-cc-base", type=int, default=20)
    ap.add_argument("--midi-mode", choices=["controls", "piano"], default="controls")
    ap.add_argument("--piano-hot-cues", action="store_true")
    ap.add_argument("--piano-cue-note-base", type=int, default=21)
    ap.add_argument("--quantize", choices=["off", "beat", "bar"], default="beat")
    ap.add_argument("--dashboard-host", default="127.0.0.1")
    ap.add_argument("--dashboard-port", type=int, default=8765)
    ap.add_argument("--osc-state-host", default="127.0.0.1")
    ap.add_argument("--osc-state-port", type=int, default=9001)
    ap.add_argument("--ableton-link", action="store_true")
    ap.add_argument("--link-tempo", type=float, default=120.0)
    ap.add_argument("--state-file", default=None)
    ap.add_argument("--user-journey", default=None)
    ap.add_argument("--load-snapshot", default=None)
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
    if args.list_midi:
        print("MIDI inputs:")
        for index, name in enumerate(MIDIControlInput.list_devices()):
            print(f"  {index}: {name}")
        print("MIDI outputs:")
        for index, name in enumerate(MIDIStateOutput.list_devices()):
            print(f"  {index}: {name}")
        return

    store = PerformanceStateStore(args.state_file)
    saved_journeys = store.journeys()
    invalid_journeys = {
        name: cues
        for name, cues in saved_journeys.items()
        if any(cue not in PERFORMANCE_CUES for cue in cues)
    }
    for name in invalid_journeys:
        saved_journeys.pop(name, None)
        print(f"[director-control] ignoring invalid saved journey={name!r}", flush=True)

    active_journey = args.user_journey or args.journey
    if active_journey not in PERFORMANCE_JOURNEYS and active_journey not in saved_journeys:
        raise SystemExit(
            f"unknown journey {active_journey!r}; builtins={sorted(PERFORMANCE_JOURNEYS)} "
            f"saved={sorted(saved_journeys)}"
        )

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
        journey=active_journey,
        mode=args.director_mode,
        base_madness=args.madness,
        cue_seconds=args.cue_seconds,
        transition_seconds=args.transition_seconds,
        minimum_dwell=args.minimum_dwell,
        journeys=saved_journeys,
    )
    controls = PerformanceControlBus()
    quantizer = PerformanceQuantizer(args.quantize)
    looper = PerformanceCueLooper()
    live_state = LiveStateHub()

    def snapshot(name: str) -> PerformanceSnapshot:
        return PerformanceSnapshot(
            name=name,
            cue=director.current_cue,
            journey=director.journey,
            mode=director.mode,
            madness=director.base_madness,
        )

    def ensure_saved_journey(name: str) -> bool:
        if name in director.journey_names:
            return True
        sequence = store.journeys().get(name)
        if not sequence:
            return False
        try:
            director.register_journey(name, sequence)
        except ValueError as exc:
            print(f"[director-control] invalid saved journey {name!r}: {exc}", flush=True)
            return False
        return True

    def apply_snapshot(name: str, now: float) -> None:
        saved = store.get_snapshot(name)
        if saved is None:
            print(f"[director-control] snapshot {name!r} does not exist", flush=True)
            return
        if ensure_saved_journey(saved.journey):
            director.set_journey(saved.journey, now, trigger_first=False)
        director.set_mode(saved.mode)
        director.set_base_madness(saved.madness)
        director.trigger_cue(saved.cue, now)
        print(
            f"[director-control] loaded snapshot={name} cue={saved.cue} "
            f"journey={saved.journey} madness={saved.madness:.2f}",
            flush=True,
        )

    def execute_control(event, now: float, beat_position: float, *, record: bool = True) -> None:
        action = event.action
        args_ = event.args
        try:
            if action == "madness":
                director.set_base_madness(float(args_[0]))
            elif action == "madness_delta":
                director.set_base_madness(director.base_madness + float(args_[0]))
            elif action == "cue":
                director.trigger_cue(str(args_[0]), now)
            elif action == "next":
                director.next_cue(now)
            elif action == "mode":
                director.set_mode(str(args_[0]))
            elif action == "journey":
                name = str(args_[0])
                if not ensure_saved_journey(name):
                    print(f"[director-control] unknown journey={name!r}", flush=True)
                    return
                director.set_journey(name, now)
            elif action == "journey_save":
                name = str(args_[0])
                cues = tuple(str(cue) for cue in args_[1:])
                director.register_journey(name, cues)
                store.save_journey(name, cues)
                print(f"[director-control] saved journey={name} cues={','.join(cues)}", flush=True)
            elif action == "snapshot_save":
                name = str(args_[0])
                saved = snapshot(name)
                store.save_snapshot(saved)
                print(
                    f"[director-control] saved snapshot={name} cue={saved.cue} "
                    f"journey={saved.journey} madness={saved.madness:.2f}",
                    flush=True,
                )
            elif action == "snapshot_load":
                apply_snapshot(str(args_[0]), now)
            elif action == "quantize":
                quantizer.set_mode(str(args_[0]))
            elif action == "loop_record_toggle":
                if looper.recording:
                    looper.stop_record(beat_position, auto_play=True)
                else:
                    looper.start_record(beat_position)
            elif action == "loop_stop":
                looper.stop()
            elif action == "loop_clear":
                looper.clear()
            else:
                print(f"[director-control] ignored unknown action={action!r}", flush=True)
                return

            if record and action in looper.RECORDABLE_ACTIONS:
                looper.record(event, beat_position)
        except (ValueError, IndexError, TypeError) as exc:
            print(f"[director-control] rejected {action}: {exc}", flush=True)

    def route_control(event, now: float, signals, beat_position: float) -> None:
        if event.action in {"quantize", "loop_record_toggle", "loop_stop", "loop_clear"}:
            execute_control(event, now, beat_position)
            return
        if quantizer.submit(event, now, signals):
            execute_control(event, now, beat_position)

    if args.load_snapshot:
        apply_snapshot(args.load_snapshot, time.perf_counter())

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

    def render_shader_cue(cue_name: str, *, elapsed: float, signals, macro, piano: PianoExpression) -> np.ndarray:
        cue = PERFORMANCE_CUES[cue_name]
        preset = SHADER_SCENE_PRESETS[cue.shader_preset]
        tempo = _tempo_scale(signals)
        scene_mix = float(
            np.clip(
                preset.scene_mix
                + 0.08 * signals.mids
                + 0.10 * signals.drop
                + 0.08 * piano.spread
                + 0.06 * piano.tension
                - 0.03 * (1.0 - macro.madness),
                0.0,
                1.0,
            )
        )
        chaos = float(
            np.clip(
                preset.chaos * 0.50
                + macro.shader_chaos * 0.58
                + 0.38 * piano.tension
                + 0.18 * piano.density,
                0.0,
                2.5,
            )
        )
        intensity = float(
            np.clip(
                preset.intensity
                * macro.shader_intensity
                * (1.0 + 0.32 * piano.velocity + 0.45 * piano.strike - 0.12 * piano.soft),
                0.0,
                3.0,
            )
        )
        palette_rate = preset.palette_cycle + macro.palette_rate + 0.015 * piano.density
        return shader.render(
            preset.scene,
            t=elapsed * preset.speed * tempo,
            intensity=intensity,
            chaos=chaos,
            palette=preset.palette,
            palette_shift=elapsed * palette_rate + signals.color * 0.08 + piano.pitch * 0.18 + piano.bend * 0.04,
            scene_b=preset.scene_b,
            scene_mix=scene_mix,
        )

    osc = None
    midi = None
    midi_out = None
    dashboard = None
    osc_state = None
    link_clock = None
    if args.ableton_link:
        try:
            link_clock = AbletonLinkClock(args.link_tempo).start()
            print(
                f"[director-control] Ableton Link enabled initial_tempo={args.link_tempo:.1f}",
                flush=True,
            )
        except RuntimeError as exc:
            print(f"[director-control] Ableton Link disabled: {exc}", flush=True)

    if args.osc_port > 0:
        try:
            osc = OSCControlServer(controls, host=args.osc_host, port=args.osc_port).start()
            print(
                f"[director-control] OSC listening udp://{args.osc_host}:{args.osc_port}",
                flush=True,
            )
        except RuntimeError as exc:
            print(f"[director-control] OSC disabled: {exc}", flush=True)
    if args.midi:
        try:
            midi = MIDIControlInput(
                controls,
                device=args.midi_device,
                madness_cc=args.midi_madness_cc,
                note_base=args.midi_note_base,
                journey_names=director.journey_names,
                mode=args.midi_mode,
                piano_hot_cues=args.piano_hot_cues,
                piano_cue_note_base=args.piano_cue_note_base,
            ).start()
            print(
                f"[director-control] MIDI input={midi.device} mode={args.midi_mode} "
                f"cc={args.midi_madness_cc} note_base={args.midi_note_base}",
                flush=True,
            )
        except RuntimeError as exc:
            print(f"[director-control] MIDI disabled: {exc}", flush=True)

    if args.midi_output:
        try:
            midi_out = MIDIStateOutput(
                device=args.midi_output_device,
                cc_base=args.midi_feedback_cc_base,
            ).start()
            print(
                f"[director-control] MIDI feedback output={midi_out.device} "
                f"cc={args.midi_feedback_cc_base}-{args.midi_feedback_cc_base + 4}",
                flush=True,
            )
        except RuntimeError as exc:
            print(f"[director-control] MIDI feedback disabled: {exc}", flush=True)

    if args.dashboard_port > 0:
        try:
            dashboard = PerformanceDashboardServer(
                controls,
                live_state,
                host=args.dashboard_host,
                port=args.dashboard_port,
            ).start()
            print(f"[director-control] dashboard={dashboard.url}", flush=True)
        except OSError as exc:
            print(f"[director-control] dashboard disabled: {exc}", flush=True)
    if args.osc_state_port > 0:
        try:
            osc_state = OSCStateBroadcaster(args.osc_state_host, args.osc_state_port).start()
            print(
                f"[director-control] OSC state -> udp://{args.osc_state_host}:{args.osc_state_port}",
                flush=True,
            )
        except RuntimeError as exc:
            print(f"[director-control] OSC state disabled: {exc}", flush=True)

    print(
        f"[director] journey={director.journey} mode={director.mode} particles={particles.capacity} "
        f"shader_gl={shader.context_info.gl_version} particle_gl={particles.context_info.gl_version}",
        flush=True,
    )
    print(
        "[director-control] keyboard 1-8=hot cues N=next [ ]=MADNESS "
        "a/A=save/load A b/B=save/load B",
        flush=True,
    )

    t0 = time.perf_counter()
    last = t0
    report = t0
    last_feedback = t0
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
                clock_signals = signals
                clock_source = "audio"
                link_state = link_clock.state(now=now) if link_clock is not None else None
                if link_state is not None and link_state.enabled and link_state.pulses > 0:
                    link_bar_phase = (link_state.beat % 4.0) / 4.0
                    clock_signals = replace(
                        signals,
                        tempo_bpm=link_state.bpm,
                        beat_phase=link_state.phase,
                        bar_phase=link_bar_phase,
                        beat_confidence=1.0,
                    )
                    clock_source = "link"

                structure = structure_tracker.update(clock_signals, now)
                beat_position = (
                    link_state.beat
                    if link_state is not None and link_state.enabled and link_state.pulses > 0
                    else looper.beat_position(structure, clock_signals)
                )

                for event in controls.drain():
                    route_control(event, now, clock_signals, beat_position)
                for event in quantizer.pop_due(now):
                    execute_control(event, now, beat_position)
                for event in looper.tick(beat_position):
                    execute_control(event, now, beat_position, record=False)

                state = director.update(structure, signals, now)
                macro = state.macro
                piano = (
                    midi.piano_expression(now=now)
                    if midi is not None and args.midi_mode == "piano"
                    else None
                )
                if piano is None:
                    piano = PianoExpression()

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
                    emission_rate=choreo.emission_rate
                    * macro.particle_emission
                    * (1.0 + 0.42 * piano.velocity + 0.72 * piano.strike),
                    turbulence=choreo.turbulence
                    * macro.particle_turbulence
                    * (1.0 + 0.34 * piano.tension + 0.20 * piano.density),
                    drag=choreo.drag,
                    feedback=float(np.clip(choreo.feedback + 0.032 * piano.sustain, 0.0, 0.985)),
                    bloom=choreo.bloom
                    * macro.particle_bloom
                    * (1.0 + 0.26 * piano.velocity + 0.34 * piano.strike),
                    energy=0.70
                    + 0.68 * macro.madness
                    + 0.32 * signals.loudness
                    + 0.28 * piano.velocity
                    + 0.42 * piano.strike,
                    bass=signals.bass,
                    strike=signals.strike,
                    drop=signals.drop,
                    field_mode=choreo.field_mode,
                    field_strength=choreo.field_strength
                    * macro.field_force
                    * (1.0 + 0.30 * piano.spread + 0.22 * piano.tension),
                    field_scale=choreo.field_scale * (1.0 + 0.12 * piano.density),
                    field_spin=choreo.field_spin
                    * (0.82 + 0.30 * signals.mids + 0.20 * piano.bend),
                    well_strength=choreo.well_strength * (0.78 + 0.42 * macro.madness + 0.34 * signals.bass),
                    nebula_mix=choreo.nebula_mix * (0.82 + 0.34 * macro.madness + 0.22 * signals.highs),
                )

                if state.active_transition:
                    shader_a = render_shader_cue(
                        state.source_cue,
                        elapsed=elapsed,
                        signals=signals,
                        macro=macro,
                        piano=piano,
                    )
                    shader_b = render_shader_cue(
                        state.target_cue,
                        elapsed=elapsed,
                        signals=signals,
                        macro=macro,
                        piano=piano,
                    )
                    shader_frame = _crossfade(shader_a, shader_b, state.mix)
                else:
                    shader_frame = render_shader_cue(
                        state.target_cue,
                        elapsed=elapsed,
                        signals=signals,
                        macro=macro,
                        piano=piano,
                    )

                small = _screen_blend(
                    particle_frame,
                    shader_frame,
                    float(np.clip(macro.composite_mix + 0.08 * piano.sustain + 0.04 * piano.spread, 0.0, 1.0)),
                )
                out = cv2.resize(
                    small,
                    (args.projector_width, args.projector_height),
                    interpolation=cv2.INTER_CUBIC,
                )
                if sink(cv2.cvtColor(out, cv2.COLOR_RGB2BGR)) is False:
                    break
                for event in keyboard_events(sink.last_key):
                    controls.emit(event.action, *event.args)

                loop_label = (
                    "recording"
                    if looper.recording
                    else "playing"
                    if looper.playing
                    else "idle"
                )
                telemetry = LivePerformanceState(
                    cue=state.target_cue,
                    journey=director.journey,
                    mode=director.mode,
                    section=structure.section,
                    macro=macro.madness,
                    energy=macro.energy,
                    bpm=clock_signals.tempo_bpm if clock_signals.beat_confidence >= 0.18 else 0.0,
                    beat_confidence=clock_signals.beat_confidence,
                    clock=clock_source,
                    quantize=quantizer.mode,
                    pending=quantizer.pending_count,
                    loop=loop_label,
                    loop_events=len(looper.events),
                    chord=piano.chord,
                    notes=len(piano.active_notes),
                    sustain=piano.sustain,
                    piano_velocity=piano.velocity,
                    piano_strike=piano.strike,
                )
                live_state.set(telemetry)
                if now - last_feedback >= 0.10:
                    if osc_state is not None:
                        osc_state.send(telemetry)
                    if midi_out is not None:
                        midi_out.send(
                            madness=telemetry.macro,
                            cue=telemetry.cue,
                            section=telemetry.section,
                            energy=telemetry.energy,
                            quantize=telemetry.quantize,
                        )
                    last_feedback = now

                frames += 1
                if now - report >= 2.0:
                    tempo = f"{clock_signals.tempo_bpm:.1f}" if clock_signals.beat_confidence >= 0.18 else "--"
                    transition = (
                        f"{state.source_cue}->{state.target_cue}:{state.mix:.2f}"
                        if state.active_transition
                        else state.target_cue
                    )
                    print(
                        f"[director] fps={frames / (now - report):.1f} cue={transition} "
                        f"journey={director.journey} mode={director.mode} base={director.base_madness:.2f} "
                        f"section={structure.section} macro={macro.madness:.2f} energy={macro.energy:.2f} "
                        f"shader_mix={macro.composite_mix:.2f} bank={target_cue.particle_bank} "
                        f"beat={signals.beat:.2f} drop={signals.drop:.2f} tempo={tempo} "
                        f"piano={piano.chord}/{len(piano.active_notes)} sustain={piano.sustain:.2f} "
                        f"quantize={quantizer.mode} loop={loop_label} clock={clock_source}",
                        flush=True,
                    )
                    report = now
                    frames = 0
    finally:
        if link_clock is not None:
            link_clock.close()
        if midi is not None:
            midi.close()
        if midi_out is not None:
            midi_out.close()
        if dashboard is not None:
            dashboard.close()
        if osc_state is not None:
            osc_state.close()
        if osc is not None:
            osc.close()
        particles.close()
        shader.close()
        sink.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
