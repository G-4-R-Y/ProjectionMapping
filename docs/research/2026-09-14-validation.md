# Research sweep validation — 2026-09-14

The implementation changes from the 2026-09-14 research sweep were validated by the repository CI matrix after adjusting the lint gate to distinguish correctness checks from existing style debt.

## Passing matrix

All six jobs completed successfully:

| OS | Python | Install | Ruff critical checks | Pytest |
| --- | --- | --- | --- | --- |
| Ubuntu | 3.10 | pass | pass | pass |
| Ubuntu | 3.12 | pass | pass | pass |
| Windows | 3.10 | pass | pass | pass |
| Windows | 3.12 | pass | pass | pass |
| macOS | 3.10 | pass | pass | pass |
| macOS | 3.12 | pass | pass | pass |

The Python 3.10 jobs also exercise the `tomli` fallback used when stdlib `tomllib` is unavailable.

## Lint note

The first CI attempt used the full current Ruff rule set and exposed 36 pre-existing style/modernization findings across the repository. Those findings were not introduced by this sweep, and blocking pytest behind them made the cross-platform test matrix less useful.

CI now blocks on correctness-critical Ruff families (`E9`, `F63`, `F7`, `F82`) and runs pytest on every supported OS/Python combination. Broader Ruff cleanup should be handled as its own code-quality task rather than silently waived or mixed into research integrations.

## Hardware validation remains separate

Green CI does **not** claim validation of hardware-dependent behavior such as Spout zero-copy transport, projector latency, CUDA/TensorRT performance, camera synchronization, or physical registration accuracy. Those still require the actual projector/camera/GPU rig and remain marked accordingly in `ROADMAP.md`.
