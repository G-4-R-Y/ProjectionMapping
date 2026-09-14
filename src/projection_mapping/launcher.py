from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import os
import subprocess
from typing import Any, IO

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
    """Own one visual/experiment subprocess at a time."""

    def __init__(self, project_root: str | Path | None = None):
        if project_root is not None:
            root = Path(project_root)
        elif is_frozen():
            root = bundle_root()
        else:
            root = Path.cwd()
        self.project_root = root.resolve()
        self.runtime_dir = runtime_root()
        self.process: subprocess.Popen[str] | None = None
        self._log_handle: IO[str] | None = None
        self.state = LaunchState()

    def launch(self, feature: Feature, values: dict[str, Any]) -> LaunchState:
        if self.process is not None and self.process.poll() is None:
            self.stop()

        argv = feature.build_argv(values)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        log_path = self.runtime_dir / f"{stamp}-{feature.id}.log"
        self._log_handle = log_path.open("w", encoding="utf-8", buffering=1)

        creationflags = 0
        start_new_session = False
        if os.name == "nt":
            creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        else:
            start_new_session = True

        self.process = subprocess.Popen(
            argv,
            cwd=self.project_root,
            stdout=self._log_handle,
            stderr=subprocess.STDOUT,
            text=True,
            creationflags=creationflags,
            start_new_session=start_new_session,
        )
        self.state = LaunchState(
            feature_id=feature.id,
            feature_name=feature.name,
            argv=tuple(argv),
            pid=self.process.pid,
            started_at=datetime.now().isoformat(timespec="seconds"),
            returncode=None,
            log_path=log_path,
        )
        return self.state

    def poll(self) -> LaunchState:
        if self.process is None:
            return self.state
        rc = self.process.poll()
        if rc is not None and self.state.returncode is None:
            self.state.returncode = rc
            self._close_log()
        return self.state

    def stop(self) -> LaunchState:
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=3.0)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=2.0)
        if self.process is not None:
            self.state.returncode = self.process.returncode
        self._close_log()
        return self.state

    def read_log_tail(self, max_chars: int = 12000) -> str:
        path = self.state.log_path
        if path is None or not path.exists():
            return "No run log yet."
        text = path.read_text(encoding="utf-8", errors="replace")
        return text[-max_chars:]

    def _close_log(self) -> None:
        if self._log_handle is not None:
            self._log_handle.close()
            self._log_handle = None

    def close(self) -> None:
        self.stop()
