# Monthly research watch

The project has a monthly research sweep intended to keep the roadmap fresh without turning every new paper or flashy demo into a dependency.

## What the sweep looks for

- projection mapping and spatial augmented reality
- projector-camera calibration and appearance compensation
- realtime generative graphics / audiovisual systems
- realtime diffusion and video generation
- neural rendering, Gaussian splats, NeRF-like spatial representations
- dynamic projection mapping and low-latency tracking
- TouchDesigner, MadMapper, Spout, Syphon, NDI, and alternative transport/compositor tooling
- open-source interactive-media projects with reusable code

## Triage criteria

A finding is more likely to be promoted when it is:

- technically novel or materially better than the current baseline;
- visually compelling for the project's "Visual Madness" direction;
- actively maintained;
- reproducible from public code or a usable release;
- licensed clearly enough to study/integrate;
- compatible with the current architecture;
- realistic on home-scale hardware or valuable enough to justify a new hardware path.

## Automatic integration policy

The monthly sweep may implement an integration automatically when all of these are true:

1. the project is open-source with a clear license;
2. the code/release is sufficiently mature to reproduce;
3. the integration is small/medium in scope and does not destabilize core dependencies;
4. there is a clear milestone or visual use case;
5. platform/hardware requirements can be documented honestly;
6. tests or a deterministic smoke path can be added.

If any of those are uncertain, the finding should be added to `ROADMAP.md` as a research candidate instead of silently entering the runtime.

## What should never be marked complete automatically

Hardware claims that require the actual projector/camera/GPU rig stay **pending validation**. Examples:

- measured motion-to-photon latency;
- zero-copy transport verification;
- projector radiometric accuracy;
- camera exposure synchronization;
- actual RTX 4080 TensorRT throughput;
- physical registration accuracy.

The automation can prepare code and experiments for these, but the roadmap should distinguish implementation from hardware validation.

## Expected monthly output

A useful sweep should leave the repo with some combination of:

- roadmap entries with source links and rationale;
- a short note about what was rejected/deferred and why;
- OS/hardware compatibility notes;
- prototype integrations when mature enough;
- tests/config/UI registry entries for promoted features;
- updated documentation and progress status.

The goal is **curated technical evolution**, not collecting GitHub links.
