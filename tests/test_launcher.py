from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import pytest

from projection_mapping.feature_registry import Feature
from projection_mapping.launcher import FeatureLauncher


def _feature(script: Path, *args: str) -> Feature:
    return Feature(
        id="lifecycle_test",
        name="Lifecycle Test",
        category="Test",
        description="",
        command=(sys.executable, str(script), *args),
    )


def _pid_is_live(pid: int) -> bool:
    stat = Path(f"/proc/{pid}/stat")
    if stat.exists():
        fields = stat.read_text(encoding="utf-8").split()
        return len(fields) > 2 and fields[2] != "Z"
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False


def _wait_until(predicate, timeout: float = 5.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.025)
    return predicate()


@pytest.mark.skipif(os.name == "nt", reason="POSIX process-group lifecycle test")
def test_natural_parent_exit_sweeps_surviving_process_group(tmp_path, monkeypatch):
    monkeypatch.setattr("projection_mapping.launcher.runtime_root", lambda: tmp_path / "runtime")
    pid_path = tmp_path / "child.pid"
    script = tmp_path / "spawn_and_exit.py"
    script.write_text(
        "\n".join(
            [
                "import pathlib, subprocess, sys",
                "child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])",
                "pathlib.Path(sys.argv[1]).write_text(str(child.pid), encoding='utf-8')",
            ]
        ),
        encoding="utf-8",
    )
    launcher = FeatureLauncher(project_root=tmp_path)
    launcher.launch(_feature(script, str(pid_path)), {})
    assert _wait_until(pid_path.exists)
    child_pid = int(pid_path.read_text(encoding="utf-8"))
    assert _pid_is_live(child_pid)

    assert _wait_until(lambda: not launcher.poll().running)
    assert _wait_until(lambda: not _pid_is_live(child_pid))
    assert launcher.process is None
    assert launcher._log_handle is None


@pytest.mark.skipif(os.name == "nt", reason="POSIX process-group lifecycle test")
def test_twenty_launch_stop_cycles_leave_no_live_children(tmp_path, monkeypatch):
    monkeypatch.setattr("projection_mapping.launcher.runtime_root", lambda: tmp_path / "runtime")
    pid_path = tmp_path / "child.pid"
    script = tmp_path / "spawn_and_wait.py"
    script.write_text(
        "\n".join(
            [
                "import pathlib, subprocess, sys, time",
                "child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])",
                "pathlib.Path(sys.argv[1]).write_text(str(child.pid), encoding='utf-8')",
                "time.sleep(60)",
            ]
        ),
        encoding="utf-8",
    )
    launcher = FeatureLauncher(project_root=tmp_path)
    child_pids: list[int] = []
    for _ in range(20):
        pid_path.unlink(missing_ok=True)
        launcher.launch(_feature(script, str(pid_path)), {})
        assert _wait_until(pid_path.exists)
        child_pids.append(int(pid_path.read_text(encoding="utf-8")))
        launcher.stop(graceful_timeout=0.05)

    assert all(_wait_until(lambda pid=pid: not _pid_is_live(pid)) for pid in child_pids)
    assert launcher.process is None
    assert launcher._log_handle is None


def test_incremental_log_reads_are_bounded(tmp_path, monkeypatch):
    monkeypatch.setattr("projection_mapping.launcher.runtime_root", lambda: tmp_path / "runtime")
    launcher = FeatureLauncher(project_root=tmp_path)
    log_path = tmp_path / "large.log"
    log_path.write_text("a" * 100_000 + "\nlast-line\n", encoding="utf-8")
    launcher.state.log_path = log_path

    tail = launcher.read_log_tail(max_chars=32)
    first, offset = launcher.read_log_since(0, max_bytes=16)
    second, next_offset = launcher.read_log_since(offset, max_bytes=16)

    assert tail.endswith("last-line\n")
    assert len(tail) <= 32
    assert first == "a" * 16
    assert second == "a" * 16
    assert next_offset == 32
