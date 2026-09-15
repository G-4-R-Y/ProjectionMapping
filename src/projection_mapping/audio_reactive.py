from __future__ import annotations

from dataclasses import dataclass
import math
import shutil
import subprocess
import sys
import threading
import time
from typing import Iterable

import numpy as np


@dataclass(frozen=True)
class AudioFeatures:
    timestamp: float
    rms: float = 0.0
    bass: float = 0.0
    mid: float = 0.0
    treble: float = 0.0
    centroid: float = 0.0
    flux: float = 0.0
    onset: float = 0.0


class AudioFeatureExtractor:
    """Small realtime spectral feature extractor designed for tiny audio blocks."""

    def __init__(
        self,
        sample_rate: int = 48_000,
        attack_ms: float = 8.0,
        release_ms: float = 90.0,
        sensitivity: float = 1.6,
    ) -> None:
        self.sample_rate = int(sample_rate)
        self.attack_ms = float(attack_ms)
        self.release_ms = float(release_ms)
        self.sensitivity = float(sensitivity)
        self._previous_spectrum: np.ndarray | None = None
        self._last_time: float | None = None
        self._smoothed = np.zeros(7, dtype=np.float32)
        self._noise_floor = 1e-4

    @staticmethod
    def _mono(block: np.ndarray) -> np.ndarray:
        x = np.asarray(block, dtype=np.float32)
        if x.ndim == 1:
            return x
        if x.ndim != 2:
            raise ValueError("audio block must be [frames] or [frames, channels]")
        if x.shape[1] == 0:
            return np.empty(0, dtype=np.float32)
        return x.mean(axis=1, dtype=np.float32)

    @staticmethod
    def _band(freqs: np.ndarray, spectrum: np.ndarray, lo: float, hi: float) -> float:
        mask = (freqs >= lo) & (freqs < hi)
        if not np.any(mask):
            return 0.0
        return float(np.sqrt(np.mean(np.square(spectrum[mask]))))

    def _envelope(self, previous: float, target: float, dt: float) -> float:
        tau_ms = self.attack_ms if target > previous else self.release_ms
        tau = max(tau_ms / 1000.0, 1e-4)
        alpha = 1.0 - math.exp(-max(dt, 1e-5) / tau)
        return previous + alpha * (target - previous)

    def process(self, block: np.ndarray, timestamp: float | None = None) -> AudioFeatures:
        now = float(timestamp if timestamp is not None else time.perf_counter())
        mono = self._mono(block)
        if mono.size < 16:
            return AudioFeatures(timestamp=now)

        mono = mono - float(np.mean(mono))
        rms_raw = float(np.sqrt(np.mean(np.square(mono)) + 1e-12))
        self._noise_floor = min(
            max(self._noise_floor * 0.999 + rms_raw * 0.001, 1e-5),
            max(rms_raw, 1e-5),
        )

        window = np.hanning(mono.size).astype(np.float32, copy=False)
        spectrum = np.abs(np.fft.rfft(mono * window)).astype(np.float32)
        spectrum /= max(float(mono.size), 1.0)
        freqs = np.fft.rfftfreq(mono.size, d=1.0 / self.sample_rate)

        bass_raw = self._band(freqs, spectrum, 35.0, 180.0)
        mid_raw = self._band(freqs, spectrum, 180.0, 2_000.0)
        treble_raw = self._band(freqs, spectrum, 2_000.0, 10_000.0)

        spec_sum = float(np.sum(spectrum)) + 1e-12
        centroid_raw = float(np.sum(freqs * spectrum) / spec_sum) / 10_000.0
        centroid_raw = float(np.clip(centroid_raw, 0.0, 1.0))

        if self._previous_spectrum is None or self._previous_spectrum.shape != spectrum.shape:
            flux_raw = 0.0
        else:
            positive = np.maximum(spectrum - self._previous_spectrum, 0.0)
            flux_raw = float(np.mean(positive))
        self._previous_spectrum = spectrum

        reference = max(self._noise_floor * 6.0, 0.01)
        scale = self.sensitivity / reference
        values = np.array(
            [
                np.clip(rms_raw * scale, 0.0, 1.0),
                np.clip(bass_raw * scale * 5.5, 0.0, 1.0),
                np.clip(mid_raw * scale * 5.5, 0.0, 1.0),
                np.clip(treble_raw * scale * 7.0, 0.0, 1.0),
                centroid_raw,
                np.clip(flux_raw * scale * 12.0, 0.0, 1.0),
                0.0,
            ],
            dtype=np.float32,
        )
        values[6] = float(np.clip(values[5] * 1.7 + max(values[0] - 0.18, 0.0) * 0.35, 0.0, 1.0))

        dt = 1.0 / 120.0 if self._last_time is None else max(now - self._last_time, 1e-5)
        self._last_time = now
        for i, target in enumerate(values):
            self._smoothed[i] = self._envelope(float(self._smoothed[i]), float(target), dt)

        return AudioFeatures(
            timestamp=now,
            rms=float(self._smoothed[0]),
            bass=float(self._smoothed[1]),
            mid=float(self._smoothed[2]),
            treble=float(self._smoothed[3]),
            centroid=float(self._smoothed[4]),
            flux=float(self._smoothed[5]),
            onset=float(self._smoothed[6]),
        )


def _pulse_sources() -> list[tuple[str, str]]:
    """Return Pulse/PipeWire-Pulse source (name, description-ish row) pairs."""
    pactl = shutil.which("pactl")
    if not pactl:
        return []
    try:
        result = subprocess.run(
            [pactl, "list", "short", "sources"],
            capture_output=True,
            text=True,
            timeout=3.0,
            check=False,
        )
    except Exception:
        return []
    sources: list[tuple[str, str]] = []
    for line in result.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) >= 2:
            sources.append((parts[1].strip(), line.strip()))
    return sources


def _linux_monitor_source(device: str | None = None) -> str:
    sources = _pulse_sources()
    if device:
        needle = device.lower()
        for name, row in sources:
            if needle in name.lower() or needle in row.lower():
                return name
        # Advanced users may pass an exact Pulse source name not visible to pactl yet.
        return device

    pactl = shutil.which("pactl")
    if pactl:
        try:
            result = subprocess.run(
                [pactl, "get-default-sink"],
                capture_output=True,
                text=True,
                timeout=2.0,
                check=False,
            )
            sink = result.stdout.strip()
            preferred = f"{sink}.monitor" if sink else ""
            if preferred and any(name == preferred for name, _ in sources):
                return preferred
        except Exception:
            pass

    monitors = [name for name, row in sources if ".monitor" in name.lower() or "monitor" in row.lower()]
    if monitors:
        return monitors[0]
    raise RuntimeError(
        "No Pulse/PipeWire monitor source found. Run `pactl list short sources` and verify "
        "that your active output has a `.monitor` source."
    )


def list_audio_devices() -> list[dict[str, str | bool | int]]:
    try:
        import soundcard as sc
    except ImportError as exc:
        raise RuntimeError("Install audio support with: python -m pip install -e '.[audio]'") from exc

    devices: list[dict[str, str | bool | int]] = []
    for index, mic in enumerate(sc.all_microphones(include_loopback=True)):
        devices.append(
            {
                "index": index,
                "name": str(mic.name),
                "id": str(mic.id),
                "loopback": bool(getattr(mic, "isloopback", False)),
                "channels": int(mic.channels),
            }
        )

    # SoundCard does not consistently label PipeWire/Pulse monitor sources as loopback.
    # Add native Pulse source names so the operator can copy an exact `.monitor` id.
    known_ids = {str(d["id"]) for d in devices}
    for name, _row in _pulse_sources():
        if name in known_ids:
            continue
        devices.append(
            {
                "index": len(devices),
                "name": name,
                "id": name,
                "loopback": ".monitor" in name.lower(),
                "channels": 2,
            }
        )
    return devices


def _looks_like_system_monitor(mic) -> bool:
    text = f"{getattr(mic, 'name', '')} {getattr(mic, 'id', '')}".lower()
    hints = (
        "monitor",
        ".monitor",
        "loopback",
        "stereo mix",
        "what u hear",
        "output monitor",
        "sink monitor",
    )
    return bool(getattr(mic, "isloopback", False)) or any(hint in text for hint in hints)


def _select_microphone(source: str, device: str | None):
    import soundcard as sc

    if source == "mic":
        if device:
            return sc.get_microphone(device, include_loopback=True)
        return sc.default_microphone()

    if source != "system":
        raise ValueError("source must be 'mic' or 'system'")

    all_mics = list(sc.all_microphones(include_loopback=True))
    if device:
        lowered = device.lower()
        matches = [m for m in all_mics if lowered in str(m.name).lower() or lowered in str(m.id).lower()]
        if matches:
            return matches[0]
        return sc.get_microphone(device, include_loopback=True)

    candidates = [m for m in all_mics if _looks_like_system_monitor(m)]
    if candidates:
        return candidates[0]

    try:
        speaker = sc.default_speaker()
        for selector in (getattr(speaker, "id", None), getattr(speaker, "name", None)):
            if selector:
                try:
                    mic = sc.get_microphone(selector, include_loopback=True)
                    if mic is not None:
                        return mic
                except Exception:
                    pass
    except Exception:
        pass

    raise RuntimeError("No system-audio loopback/monitor source was found. Use --list-devices.")


class AudioFeatureStream:
    """Background native-audio capture feeding only the latest feature vector."""

    def __init__(
        self,
        source: str = "mic",
        device: str | None = None,
        sample_rate: int = 48_000,
        blocksize: int = 256,
        channels: int = 2,
        attack_ms: float = 8.0,
        release_ms: float = 90.0,
        sensitivity: float = 1.6,
        exclusive_mode: bool = False,
    ) -> None:
        self.source = source
        self.device = device
        self.sample_rate = int(sample_rate)
        self.blocksize = int(blocksize)
        self.channels = int(channels)
        self.exclusive_mode = bool(exclusive_mode)
        self.extractor = AudioFeatureExtractor(sample_rate, attack_ms, release_ms, sensitivity)
        self._latest = AudioFeatures(timestamp=time.perf_counter())
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._error: BaseException | None = None
        self._capture_process: subprocess.Popen[bytes] | None = None
        self.selected_device_name: str | None = None
        self.selected_backend: str | None = None

    @property
    def latest(self) -> AudioFeatures:
        with self._lock:
            return self._latest

    @property
    def error(self) -> BaseException | None:
        return self._error

    def start(self) -> "AudioFeatureStream":
        if self._thread and self._thread.is_alive():
            return self
        self._error = None
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="audio-reactive-capture", daemon=True)
        self._thread.start()
        return self

    def stop(self, timeout: float = 1.0) -> None:
        self._stop.set()
        process = self._capture_process
        if process is not None and process.poll() is None:
            try:
                process.terminate()
            except OSError:
                pass
        if self._thread:
            self._thread.join(timeout=timeout)
        if process is not None and process.poll() is None:
            try:
                process.kill()
            except OSError:
                pass
        self._capture_process = None

    def __enter__(self) -> "AudioFeatureStream":
        return self.start()

    def __exit__(self, *_exc) -> None:
        self.stop()

    def _publish(self, block: np.ndarray) -> None:
        features = self.extractor.process(np.asarray(block))
        with self._lock:
            self._latest = features

    def _run_linux_system_native(self) -> None:
        parec = shutil.which("parec")
        pactl = shutil.which("pactl")
        if not parec or not pactl:
            raise RuntimeError("native Linux system capture requires `pactl` and `parec`")

        source = _linux_monitor_source(self.device)
        channels = min(max(self.channels, 1), 2)
        self.selected_backend = "parec/pulse"
        self.selected_device_name = source
        print(
            f"[audio] source=system backend={self.selected_backend} device={source}",
            flush=True,
        )
        cmd = [
            parec,
            f"--device={source}",
            "--format=s16le",
            f"--rate={self.sample_rate}",
            f"--channels={channels}",
            "--raw",
        ]
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self._capture_process = process
        assert process.stdout is not None
        bytes_per_block = self.blocksize * channels * 2

        while not self._stop.is_set():
            data = process.stdout.read(bytes_per_block)
            if not data:
                if process.poll() is not None:
                    stderr = b""
                    if process.stderr is not None:
                        stderr = process.stderr.read()
                    raise RuntimeError(
                        f"parec exited with {process.returncode}: {stderr.decode(errors='replace').strip()}"
                    )
                time.sleep(0.001)
                continue
            samples = np.frombuffer(data, dtype="<i2").astype(np.float32) / 32768.0
            frames = samples.size // channels
            if frames <= 0:
                continue
            block = samples[: frames * channels].reshape(frames, channels)
            self._publish(block)

    def _run_soundcard(self) -> None:
        import soundcard as sc  # noqa: F401

        mic = _select_microphone(self.source, self.device)
        self.selected_backend = "soundcard"
        self.selected_device_name = str(getattr(mic, "name", getattr(mic, "id", "unknown")))
        print(
            f"[audio] source={self.source} backend={self.selected_backend} device={self.selected_device_name}",
            flush=True,
        )
        recorder_kwargs = {
            "samplerate": self.sample_rate,
            "channels": min(max(self.channels, 1), max(int(mic.channels), 1)),
            "blocksize": self.blocksize,
        }
        if self.exclusive_mode:
            recorder_kwargs["exclusive_mode"] = True
        try:
            recorder_cm = mic.recorder(**recorder_kwargs)
        except TypeError:
            recorder_kwargs.pop("exclusive_mode", None)
            recorder_cm = mic.recorder(**recorder_kwargs)

        with recorder_cm as recorder:
            while not self._stop.is_set():
                # Request a concrete small block. `numframes=None` is backend-dependent
                # and can return silence/stale data on some Pulse/PipeWire combinations.
                block = recorder.record(numframes=self.blocksize)
                if block is None or len(block) == 0:
                    time.sleep(0.0005)
                    continue
                self._publish(np.asarray(block))

    def _run(self) -> None:
        try:
            if self.source == "system" and sys.platform.startswith("linux"):
                try:
                    self._run_linux_system_native()
                    return
                except BaseException as native_exc:
                    if self._stop.is_set():
                        return
                    print(
                        f"[audio] native Linux monitor capture failed: {type(native_exc).__name__}: {native_exc}; "
                        "falling back to SoundCard",
                        flush=True,
                    )
            self._run_soundcard()
        except BaseException as exc:
            if not self._stop.is_set():
                self._error = exc
            self._stop.set()
        finally:
            process = self._capture_process
            if process is not None and process.poll() is None:
                try:
                    process.terminate()
                except OSError:
                    pass
            self._capture_process = None


def format_device_table(devices: Iterable[dict[str, str | bool | int]]) -> str:
    lines = ["index | kind     | channels | name", "------+----------+----------+------------------------------"]
    for d in devices:
        kind = "loopback" if d["loopback"] else "input"
        lines.append(f"{d['index']:>5} | {kind:<8} | {d['channels']:>8} | {d['name']}")
    return "\n".join(lines)
