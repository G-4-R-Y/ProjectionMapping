from __future__ import annotations

import pytest

from projection_mapping.vram import CudaVramGuard, GiB, VramSafetyError


class _DeviceContext:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class _FakeCuda:
    def __init__(self, free_gib: float, total_gib: float):
        self.free = int(free_gib * GiB)
        self.total = int(total_gib * GiB)
        self.fraction = None

    def is_available(self):
        return True

    def device(self, _device):
        return _DeviceContext()

    def mem_get_info(self, _device):
        return self.free, self.total

    def set_per_process_memory_fraction(self, fraction, _device):
        self.fraction = fraction

    def empty_cache(self):
        pass

    def ipc_collect(self):
        pass


class _FakeTorch:
    class OutOfMemoryError(RuntimeError):
        pass

    def __init__(self, free_gib: float, total_gib: float):
        self.cuda = _FakeCuda(free_gib, total_gib)
        self.cuda.OutOfMemoryError = self.OutOfMemoryError


def test_budget_reserves_larger_of_absolute_or_fraction(monkeypatch):
    guard = CudaVramGuard(reserve_gib=1.5, reserve_fraction=0.20)
    fake = _FakeTorch(free_gib=10.0, total_gib=12.0)
    monkeypatch.setattr(guard, "_torch", lambda: fake)

    snap = guard.snapshot()

    assert snap.reserve_gib == pytest.approx(2.4, abs=0.01)
    assert snap.budget_gib == pytest.approx(7.6, abs=0.01)


def test_arm_caps_allocator_below_current_safe_budget(monkeypatch):
    guard = CudaVramGuard(reserve_gib=1.5, reserve_fraction=0.15)
    fake = _FakeTorch(free_gib=8.0, total_gib=12.0)
    monkeypatch.setattr(guard, "_torch", lambda: fake)

    snap = guard.arm()

    assert fake.cuda.fraction is not None
    assert fake.cuda.fraction * snap.total_bytes < snap.budget_bytes


def test_unsafe_launch_is_blocked(monkeypatch):
    guard = CudaVramGuard(
        reserve_gib=1.5,
        reserve_fraction=0.15,
        minimum_budget_gib=2.0,
    )
    fake = _FakeTorch(free_gib=2.0, total_gib=12.0)
    monkeypatch.setattr(guard, "_torch", lambda: fake)

    with pytest.raises(VramSafetyError, match="Unsafe CUDA launch blocked"):
        guard.arm()
