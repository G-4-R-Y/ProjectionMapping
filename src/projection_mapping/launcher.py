from __future__ import annotations

import os
import platform
import shutil
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import IO, Any

from .app_runtime import bundle_root, is_frozen, runtime_root
from .feature_registry import Feature


@dataclass
class LaunchState:
    feature_id: str | None = None
    feature_name: str | None = None
    argv: tuple[str, ...] = ()
    pid: int | None = None
    started_at: str | None = None
    returncode: int | None = None
    log_path: Path | None = None

    @property
    def running(self) -> bool:
        return self.pid is not None and self.returncode is None


class FeatureLauncher:
    """Own one visual/experiment subprocess at a time.

    Each run is isolated in its own process group/session. This is important for
    CUDA/TensorRT workers: stopping a visual tears down the whole process tree so
    child CUDA contexts cannot linger and hold VRAM/RAM.

    Every run also gets a persistent, unbuffered diagnostic log under the runtime
    directory. The TUI may tail that log while the process is still alive.
    """

    def __init__(self, project_root: str | Path | None = None):
        if project_root is not None:
            root = Path(project_root)
        elif is_frozen():
            root = bundle_root()
        else:
            root = Path.cwd()
        self.project_root = root.resolve()
        self.runtime_dir = runtime_root()
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self.process: subprocess.Popen[str] | None = None
        self._posix_pgid: int | None = None
        self._log_handle: IO[str] | None = None
        self.state = LaunchState()

    def launch(self, feature: Feature, values: dict[str, Any]) -> LaunchState:
        # ``stop`` also sweeps descendants when the direct parent already exited.
        if self.process is not None:
            self.stop()

        argv = feature.build_argv(values)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        log_path = self.runtime_dir / f"{stamp}-{feature.id}.log"
        self._log_handle = log_path.open("w", encoding="utf-8", buffering=1)
        self._write_log_header(feature, argv, values)

        creationflags = 0
        start_new_session = False
        if os.name == "nt":
            creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        else:
            start_new_session = True

        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        env["PYTHONFAULTHANDLER"] = "1"
        env["PROJECTION_MAPPING_RUN_LOG"] = str(log_path)

        try:
            self.process = subprocess.Popen(
                argv,
                cwd=self.project_root,
                stdout=self._log_handle,
                stderr=subprocess.STDOUT,
                text=True,
                env=env,
                creationflags=creationflags,
                start_new_session=start_new_session,
            )
            self._posix_pgid = self.process.pid if start_new_session else None
        except Exception:
            import traceback

            self._log("[launcher] subprocess creation failed")
            self._log(traceback.format_exc().rstrip())
            self._close_log()
            raise

        self.state = LaunchState(
            feature_id=feature.id,
            feature_name=feature.name,
            argv=tuple(argv),
            pid=self.process.pid,
            started_at=datetime.now().isoformat(timespec="seconds"),
            returncode=None,
            log_path=log_path,
        )
        self._log(f"[launcher] child pid={self.process.pid}")
        return self.state

    def _write_log_header(self, feature: Feature, argv: list[str], values: dict[str, Any]) -> None:
        interesting_env = {
            key: os.environ.get(key)
            for key in (
                "DISPLAY",
                "WAYLAND_DISPLAY",
                "XDG_SESSION_TYPE",
                "CUDA_VISIBLE_DEVICES",
                "NVIDIA_VISIBLE_DEVICES",
            )
            if os.environ.get(key) is not None
        }
        lines = [
            "=== ProjectionMapping run ===",
            f"timestamp: {datetime.now().isoformat(timespec='seconds')}",
            f"feature_id: {feature.id}",
            f"feature_name: {feature.name}",
            f"frozen: {is_frozen()}",
            f"platform: {platform.platform()}",
            f"python: {sys.version.replace(chr(10), ' ')}",
            f"executable: {sys.executable}",
            f"cwd: {self.project_root}",
            f"argv: {argv!r}",
            f"values: {values!r}",
            f"environment: {interesting_env!r}",
        ]
        self._log("\n".join(lines))
        self._write_gpu_snapshot("before launch")
        self._log("--- child output ---")

    def _write_gpu_snapshot(self, label: str) -> None:
        nvidia_smi = shutil.which("nvidia-smi")
        if not nvidia_smi:
            self._log(f"[gpu:{label}] nvidia-smi not found")
            return
        try:
            result = subprocess.run(
                [
                    nvidia_smi,
                    "--query-gpu=index,name,memory.total,memory.used,memory.free,utilization.gpu",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                timeout=3.0,
                check=False,
            )
            output = (result.stdout or result.stderr).strip()
            self._log(f"[gpu:{label}] index, name, totalMiB, usedMiB, freeMiB, util%")
            self._log(output or f"nvidia-smi returned {result.returncode} without output")
        except Exception as exc:
            self._log(f"[gpu:{label}] snapshot failed: {type(exc).__name__}: {exc}")

    def _log(self, text: str) -> None:
        if self._log_handle is not None:
            self._log_handle.write(text + "\n")
            self._log_handle.flush()

    def poll(self) -> LaunchState:
        if self.process is None:
            return self.state
        rc = self.process.poll()
        if rc is not None and self.state.returncode is None:
            self.state.returncode = rc
            self._log(f"[launcher] child exited returncode={rc}")
            # A renderer can exit while leaving ffmpeg/audio/model helpers alive. Because POSIX
            # children inherit the renderer's dedicated session, sweep that group even after its
            # leader has gone away. Process exit remains the hard CUDA/RAM cleanup boundary.
            if os.name != "nt":
                self._stop_posix_group(self.process, timeout=0.35)
            self._write_gpu_snapshot("after exit")
            self._close_log()
            self.process = None
            self._posix_pgid = None
        return self.state

    def stop(self, graceful_timeout: float = 3.0) -> LaunchState:
        """Stop the complete child process group, not just its parent."""
        process = self.process
        if process is None:
            self._close_log()
            return self.state

        if process.poll() is None:
            self._log("[launcher] stop requested; terminating complete process tree")
        elif os.name != "nt" and self._posix_group_exists():
            self._log("[launcher] parent exited; terminating surviving process-group members")

        if os.name == "nt":
            if process.poll() is None:
                self._stop_windows_tree(process, graceful_timeout)
        else:
            self._stop_posix_group(process, graceful_timeout)

        self.state.returncode = process.poll()
        self._log(f"[launcher] cleanup complete returncode={self.state.returncode}")
        self._write_gpu_snapshot("after cleanup")
        self._close_log()
        self.process = None
        self._posix_pgid = None
        return self.state

    def _posix_group_exists(self) -> bool:
        pgid = self._posix_pgid
        if pgid is None:
            return False
        proc_root = Path("/proc")
        if proc_root.is_dir():
            # Linux keeps an exited orphan visible briefly as a zombie. A zombie owns no CUDA/RAM
            # resources and cannot receive signals, so do not burn the force-kill timeout on it.
            for entry in proc_root.iterdir():
                if not entry.name.isdigit():
                    continue
                try:
                    raw = (entry / "stat").read_text(encoding="utf-8")
                    fields = raw[raw.rfind(")") + 2 :].split()
                    state = fields[0]
                    process_group = int(fields[2])
                except (FileNotFoundError, IndexError, PermissionError, ValueError):
                    continue
                if process_group == pgid and state != "Z":
                    return True
            return False
        try:
            os.killpg(pgid, 0)
            return True
        except ProcessLookupError:
            return False
        except PermissionError:
            return True

    def _wait_for_posix_group_exit(self, timeout: float) -> bool:
        deadline = time.monotonic() + max(timeout, 0.0)
        while self._posix_group_exists() and time.monotonic() < deadline:
            time.sleep(0.02)
        return not self._posix_group_exists()

    def _stop_posix_group(self, process: subprocess.Popen[str], timeout: float) -> None:
        pgid = self._posix_pgid
        if pgid is None and process.poll() is None:
            try:
                pgid = os.getpgid(process.pid)
                self._posix_pgid = pgid
            except (ProcessLookupError, OSError):
                pgid = None
        if pgid is None:
            return

        if self._posix_group_exists():
            try:
                os.killpg(pgid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            if not self._wait_for_posix_group_exit(timeout):
                self._log("[launcher] graceful timeout; SIGKILL process group")
                try:
                    os.killpg(pgid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                if not self._wait_for_posix_group_exit(2.0):
                    self._log("[launcher] warning: process group survived SIGKILL")

        if process.poll() is None:
            try:
                process.wait(timeout=0.25)
            except subprocess.TimeoutExpired:
                self._log("[launcher] warning: process-group leader was not reaped")

    def _stop_windows_tree(self, process: subprocess.Popen[str], timeout: float) -> None:
        ctrl_break = getattr(signal, "CTRL_BREAK_EVENT", None)
        if ctrl_break is not None:
            try:
                process.send_signal(ctrl_break)
                process.wait(timeout=timeout)
                return
            except (OSError, subprocess.TimeoutExpired):
                self._log("[launcher] graceful Windows stop failed/timed out; forcing tree cleanup")

        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            stdout=self._log_handle or subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        try:
            process.wait(timeout=2.0)
        except subprocess.TimeoutExpired:
            self._log("[launcher] warning: taskkill returned but parent still appears alive")
            try:
                process.kill()
            except OSError:
                pass

    def read_log(self) -> str:
        """Return the complete persisted log for the current/last run."""
        path = self.state.log_path
        if path is None or not path.exists():
            return "No run log yet."
        return path.read_text(encoding="utf-8", errors="replace")

    def read_log_tail(self, max_chars: int = 20000) -> str:
        path = self.state.log_path
        if path is None or not path.exists():
            return "No run log yet."
        # Reading the complete, ever-growing run log on every UI tick made Textual scrolling
        # progressively slower. Seek from the end so refresh cost remains bounded.
        max_bytes = max(max_chars * 4, 4096)
        with path.open("rb") as handle:
            size = handle.seek(0, os.SEEK_END)
            handle.seek(max(size - max_bytes, 0))
            text = handle.read().decode("utf-8", errors="replace")
        return text[-max_chars:]

    def read_log_since(self, offset: int = 0, max_bytes: int = 65536) -> tuple[str, int]:
        """Read a bounded incremental log chunk for responsive terminal/browser UIs."""
        path = self.state.log_path
        if path is None or not path.exists():
            return "", 0
        with path.open("rb") as handle:
            size = handle.seek(0, os.SEEK_END)
            safe_offset = offset if 0 <= offset <= size else 0
            handle.seek(safe_offset)
            data = handle.read(max(1, max_bytes))
            next_offset = handle.tell()
        return data.decode("utf-8", errors="replace"), next_offset

    def _close_log(self) -> None:
        if self._log_handle is not None:
            self._log_handle.close()
            self._log_handle = None

    def close(self) -> None:
        self.stop()
