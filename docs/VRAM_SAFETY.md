# VRAM safety policy

ProjectionMapping treats GPU memory as a shared, finite realtime resource. Neural renderers must not intentionally consume all visible VRAM.

## Policy

The StreamDiffusion backend uses `CudaVramGuard` before loading the model and before CUDA-heavy operations.

Default policy:

- reserve at least **1.5 GiB** of VRAM for the OS/compositor/driver and other allocations;
- also reserve at least **15% of total VRAM**; the larger reserve wins;
- refuse to start when the remaining safe budget is below **2 GiB**;
- cap PyTorch's per-process caching allocator below the safe budget measured at startup;
- re-check live free VRAM before inference steps;
- catch `torch.cuda.OutOfMemoryError`, clear reclaimable caches, and convert it to a recoverable `VramSafetyError` rather than allowing the control deck to crash.

The visual renderer runs in a child process, so a rejected/failed GPU workload returns control to the ProjectionMapping UI and leaves the operator console alive.

## Why this cannot be a mathematical zero-OOM guarantee

CUDA memory is not controlled exclusively by PyTorch. TensorRT, CUDA libraries, graphics APIs, the display compositor, the driver, and other processes can allocate VRAM concurrently. Memory can also become fragmented between a safety check and a later allocation.

Therefore the application guarantees a conservative **allocation policy and containment strategy**, not that the CUDA driver can never emit an OOM condition. Residual OOMs are trapped and treated as recoverable safety failures.

## Tuning

`DaydreamStreamConfig` exposes:

- `vram_device`
- `vram_reserve_gib`
- `vram_reserve_fraction`
- `vram_minimum_budget_gib`

Do not reduce the reserve merely to make a model fit. Prefer reducing render resolution, denoising batch size, frame buffer size, ControlNet/IP-Adapter count, or selecting a smaller model.

For installation hardware, leave additional headroom if the same GPU also drives the projector/compositor or another realtime application.
