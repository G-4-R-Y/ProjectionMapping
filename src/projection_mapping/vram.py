from __future__ import annotations

from dataclasses import dataclass
import gc


GiB = 1024**3


class VramSafetyError(RuntimeError):
    """Raised when a GPU workload would violate the configured VRAM safety policy."""


@dataclass(frozen=True)
class VramSnapshot:
    device: int
    free_bytes: int
    total_bytes: int
    reserve_bytes: int
    budget_bytes: int

    @property
    def free_gib(self) -> float:
        return self.free_bytes / GiB

    @property
    def total_gib(self) -> float:
        return self.total_bytes / GiB

    @property
    def reserve_gib(self) -> float:
        return self.reserve_bytes / GiB

    @property
    def budget_gib(self) -> float:
        return self.budget_bytes / GiB


@dataclass
class CudaVramGuard:
    """Conservative CUDA memory budget for interactive GPU workloads.

    The guard intentionally leaves VRAM unused. It combines an absolute reserve and a
    percentage reserve, then caps PyTorch's caching allocator below the currently free
    device memory. This protects the desktop/control process from workloads that would
    otherwise greedily consume all visible VRAM.

    CUDA/TensorRT/driver allocations can occur outside PyTorch's allocator and other
    processes can allocate concurrently, so callers must still catch CUDA OOM and fail
    gracefully. The guard provides ``run`` for that purpose.
    """

    device: int = 0
    reserve_gib: float = 1.5
    reserve_fraction: float = 0.15
    minimum_budget_gib: float = 2.0

    def _torch(self):
        try:
            import torch
        except ImportError as exc:
            raise VramSafetyError("PyTorch is required for CUDA VRAM management") from exc
        if not torch.cuda.is_available():
            raise VramSafetyError("CUDA is not available")
        return torch

    def snapshot(self) -> VramSnapshot:
        torch = self._torch()
        with torch.cuda.device(self.device):
            free_bytes, total_bytes = torch.cuda.mem_get_info(self.device)
        reserve_bytes = max(
            int(self.reserve_gib * GiB),
            int(total_bytes * self.reserve_fraction),
        )
        budget_bytes = max(0, free_bytes - reserve_bytes)
        return VramSnapshot(
            device=self.device,
            free_bytes=int(free_bytes),
            total_bytes=int(total_bytes),
            reserve_bytes=reserve_bytes,
            budget_bytes=budget_bytes,
        )

    def arm(self, *, required_gib: float | None = None) -> VramSnapshot:
        """Refuse unsafe starts and cap PyTorch below the current free-memory budget."""
        torch = self._torch()
        snap = self.snapshot()
        minimum = max(self.minimum_budget_gib, required_gib or 0.0)
        if snap.budget_bytes < int(minimum * GiB):
            raise VramSafetyError(
                "Unsafe CUDA launch blocked: "
                f"{snap.free_gib:.2f} GiB free / {snap.total_gib:.2f} GiB total, "
                f"{snap.reserve_gib:.2f} GiB reserved, only {snap.budget_gib:.2f} GiB usable; "
                f"this workload requires at least {minimum:.2f} GiB of safe budget."
            )

        # set_per_process_memory_fraction is expressed as a fraction of total device
        # memory, not currently-free memory. Use the smaller current-safe budget so a
        # busy GPU cannot accidentally receive a cap based on nominal capacity.
        fraction = min(1.0, snap.budget_bytes / snap.total_bytes)
        # Keep a small numerical gap below the measured budget.
        fraction = max(0.01, fraction * 0.98)
        torch.cuda.set_per_process_memory_fraction(fraction, self.device)
        return snap

    def ensure_headroom(self, *, minimum_free_gib: float = 0.5) -> VramSnapshot:
        """Block a new inference step when live free VRAM is below the emergency floor."""
        snap = self.snapshot()
        emergency = max(minimum_free_gib * GiB, snap.reserve_bytes)
        if snap.free_bytes <= emergency:
            raise VramSafetyError(
                "GPU headroom exhausted; inference step blocked before allocation: "
                f"{snap.free_gib:.2f} GiB free, safety reserve {emergency / GiB:.2f} GiB."
            )
        return snap

    def cleanup(self) -> None:
        torch = self._torch()
        gc.collect()
        with torch.cuda.device(self.device):
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()

    def run(self, fn, *args, **kwargs):
        """Execute a CUDA operation, converting OOM into a recoverable safety error."""
        torch = self._torch()
        self.ensure_headroom()
        try:
            return fn(*args, **kwargs)
        except torch.cuda.OutOfMemoryError as exc:
            self.cleanup()
            snap = self.snapshot()
            raise VramSafetyError(
                "CUDA OOM was contained and the cache was released. "
                f"Current free VRAM: {snap.free_gib:.2f} GiB. "
                "Reduce resolution/batch size or close other GPU applications."
            ) from exc
