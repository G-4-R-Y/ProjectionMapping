# Track — Mathematical Worlds / Algorithmic Art

## North star
Build a deep library of projector-native mathematical worlds where each visual has a real algorithmic identity rather than being another palette/noise variant. Complex analysis, dynamical systems, PDEs, topology, geometry, number theory, cellular systems and optimization should become reusable high-rate visual primitives that can stand alone, react to music/performers, attach to calibrated room surfaces, and serve as deterministic structure underneath neural style layers.

The artistic bar remains `docs/ART_DIRECTION.md`: famous equations are not exempt from looking good. A mathematically interesting scene that reads like a textbook plot is still unfinished.

## Current state

### Famous Math Lab — implemented
Eight GPU shader worlds:
- `mandelbrot_julia` — animated quadratic complex dynamics with orbit trapping and a continuous Mandelbrot<->Julia morph.
- `newton_basins` — Newton iteration for `z^3 - 1`, convergence bands and luminous root-basin boundaries.
- `riemann_zeta` — domain coloring from a finite alternating Dirichlet-eta approximation converted to zeta; zero-like low-magnitude structure is highlighted. This is an artistic finite approximation, not a numerical zeta research package.
- `chladni_plate` — interacting membrane/plate eigenmode nodal patterns.
- `quasicrystal_5fold` — five-fold plane-wave interference with golden-ratio secondary modulation.
- `logistic_bifurcation` — realtime bifurcation-density view of the logistic map with a Lyapunov-style chaos cue.
- `superformula` — Gielis superformula families with nested contours and controlled morphing.
- `complex_domain` — domain coloring of a time-varying complex function built from `sin(z^2 + a/z)`-type structure.

All eight expose palette, intensity, speed and structured-chaos controls and can run standalone in the control deck. The same renderer can consume `MusicalSignals`.

### Stateful PDE branch — implemented baseline
`ReactionDiffusionRenderer` implements Gray-Scott reaction-diffusion with persistent ping-pong GPU textures. Current morphology presets: coral, mitosis, worms, maze, solitons and waves. The display pass emphasizes chemical boundaries as emissive contours instead of showing a flat scientific heatmap. `R` live-reseeds the standalone lab.

### Cellular Worlds — implemented baseline
`CellularWorldRenderer` adds four discrete stateful GPU automata using the same persistent ping-pong texture architecture:
- Conway's Game of Life.
- Brian's Brain three-state excitable automaton.
- 8-state cyclic cellular automaton.
- Seeds (`B2/S0`).

The standalone lab supports deterministic reseeding, controllable initial density, generations-per-frame and a sparse installation-drive term that can keep long-running visuals alive without replacing the underlying rule system with frame noise. Current output uses crisp nearest-neighbour projection and emissive edge/color treatment.

### Strange Attractor Lab — implemented baseline
Dense additive point-cloud sculptures for:
- Lorenz
- Rossler
- Aizawa
- Thomas
- Halvorsen
- Clifford
- De Jong
- Ikeda

ODE/map trajectories are generated once, robustly normalized, uploaded to GPU memory and then animated at display rate with 3D camera orbit, emissive point material and bloom. This is intentionally different from full-screen shader textures: it adds sparse luminous geometric sculpture to the visual vocabulary. A fixed-point-collapse test now guards registered attractors after the first Ikeda parameter choice was found to converge to one point instead of producing the desired chaotic set.

### Song Studio convergence — implemented
Song Studio can use `math:<mode>` Famous Math worlds as music-reactive backdrop/conductor layers in addition to Polar Math and Shader Scene Lab scenes. Current automatic research pairings include quasicrystal/Lissajous, Mandelbrot-Julia/Singularity Crown, complex-domain/Prism Shards and zeta/Constellation Bloom. These are experiments, not all promoted presets.

### Reusable content
`assets/packs/mathematical_worlds/manifest.toml` exposes the current shader/PDE/cellular/attractor families as reusable procedural assets.

## Quality ladder
- **Prototype:** equation/algorithm renders correctly.
- **Usable:** stable GPU implementation, controllable parameters, fullscreen output, no obvious seams/divergence.
- **Polished:** projector-tuned composition, black floor, antialiasing, HDR/bloom, coherent camera/motion, curated palettes and presets. **Current work is between usable and polished; projector verdict pending.**
- **Advanced:** stateful PDE/CA worlds, smooth cross-family morphing, room-surface coordinates, audio/performer modulation, direct GL output, reusable field/geometry operators.
- **Ridiculous:** a mathematical-world compiler/conductor where symbolic equations, PDEs, attractors, topology and optimization fields can be composed live, differentiated/optimized against room geometry or music, and optionally neural-stylized without sacrificing deterministic temporal ownership.

## Research directions

### Complex dynamics / complex analysis
- Multibrot families, Burning Ship, Phoenix fractal, Nova fractal, Lyapunov fractals.
- Newton/Halley/Householder basins for higher-degree polynomials and rational maps.
- orbit traps, distance estimators, perturbation theory for deep zooms, arbitrary precision offline keyframes.
- Möbius transformations, Schwarz-Christoffel / conformal mapping, circle inversion and Schottky groups.
- elliptic/theta functions, modular forms and modular-domain tilings.
- complex potential flow as a bridge between conformal maps and fluid-looking vector fields.

### Number theory / discrete mathematics
- Ulam prime spiral / prime residue fields as sparse event geometry.
- modular arithmetic tilings, quadratic residues, Gaussian/Eisenstein integer lattices.
- continued fractions / Ford circles / Farey trees.
- zeta/eta/theta domain coloring and explicit-formula-inspired visual studies, carefully labelled as artistic finite approximations unless numerically rigorous.

### Dynamical systems / chaos
- Duffing oscillator, double pendulum, Rabinovich-Fabrikant, Chen and Dadras systems.
- standard map / Chirikov map, Hénon map, Baker map, Arnold cat map.
- Poincare sections, KAM islands/tori and Hamiltonian phase portraits.
- bifurcation continuation and Lyapunov-exponent fields.
- flow-map / finite-time Lyapunov exponent textures for coherent-structure visualization.

### PDEs / morphogenesis / field simulation
- Gray-Scott parameter-space morphing and spatially varying feed/kill fields.
- FitzHugh-Nagumo / Barkley excitable media.
- wave equation / damped wave membranes / cymatic mode synthesis.
- reaction-advection-diffusion driven by performer/audio vector fields.
- shallow-water equations, stable fluids, vorticity confinement, lattice-Boltzmann experiments.
- wave interference, diffraction/Fresnel fields, caustics and optical flow analogues.
- neural cellular automata / differentiable CA only after classical stateful baselines are solid.

### Cellular systems
Implemented classical baselines: Conway Life, Brian's Brain, cyclic-8 and Seeds.
Next research:
- larger-totalistic Life-like rule families and live `B/S` rule morphs.
- Wireworld and excitable-media automata.
- Lenia / continuous cellular automata and SmoothLife.
- elementary 1D CA spacetime tapes as texture/geometry generators.
- Margolus reversible cellular automata for conservation-like motion.
- performer/audio-driven local rule fields while keeping state evolution coherent.

### Geometry / tilings / optimization
- Voronoi / Delaunay, Lloyd relaxation and centroidal Voronoi tessellation.
- weighted/power diagrams and anisotropic Voronoi fields.
- Penrose, Ammann-Beenker and substitution tilings.
- hyperbolic tilings in the Poincare disk / upper half plane.
- circle packing, Apollonian gaskets, sphere packing and blue-noise / Poisson-disk fields.
- optimal transport / Sinkhorn morphs between point distributions as choreography.

### Topology / differential geometry / 3D SDF
- torus knots, Lissajous knots, braids and knot-energy relaxations.
- Hopf fibration projections and linked-fiber fields.
- Möbius strip, Klein bottle, Boy surface and Roman surface studies.
- minimal surfaces: catenoid/helicoid family; Schwarz P/D and gyroid implicit surfaces.
- superquadrics / superellipsoids / generalized cylinders.
- raymarched signed-distance architecture with smooth boolean operators and deformation fields.

### Spectral / graph / physical geometry
- Laplace-Beltrami eigenfunctions on meshes/surfaces.
- graph Laplacian modes, diffusion maps and spectral clustering as visual structure.
- Chladni/cymatic modes driven by real room/surface geometry rather than only rectangles.
- modal synthesis where audio frequency bands excite spatial eigenmodes.

### Generative / differentiable research
- differentiable procedural shaders and PDE parameter fitting to target images/room surfaces.
- inverse design: optimize Gray-Scott/feed fields, attractor parameters or SDF geometry for a desired projected pattern.
- symbolic regression / equation discovery as an operator-assist tool for inventing new visual equations.
- differentiable rendering + projector compensation jointly optimizing visual field and emitted image.
- LLM/program-synthesis candidate generation only behind automatic compile/render/continuity/performance checks; generated code never bypasses the visual promotion bar.

## Open problems
- Fullscreen path still reads ModernGL output back to CPU/OpenCV; direct GL swapchain/shared texture remains the major transport improvement.
- Famous Math modes need real projector footage: some may be mathematically strong but aesthetically weak or too dense.
- Logistic and complex-iteration shaders have relatively high per-pixel loop cost; benchmark 4050/4080 before raising resolution/iterations.
- Zeta mode uses a finite eta-series approximation and should remain explicitly described that way.
- Reaction diffusion currently uses periodic boundaries and fixed rectangular simulation coordinates; calibrated wall/surface masks and boundary conditions are future work.
- Gray-Scott parameter transitions can destabilize or collapse patterns; morph parameters slowly and preserve state.
- Cellular worlds currently use periodic boundaries and discrete nearest-neighbour output; continuous CA / Lenia and room-boundary rules remain open.
- Attractor point clouds are static trajectories with animated camera, not continuously re-integrated parameter morphs yet.
- No common field algebra yet: shader, PDE, CA, particle and SDF modules cannot currently compose arbitrary vector/scalar fields without bespoke code.
- No live hot-reload of mathematical parameters from TUI/OSC yet.

## Next implementation queue
1. Hardware-test all Famous Math modes and aggressively delete/rewrite modes that look like scientific plots rather than installation art.
2. Hardware-test Reaction Diffusion at 320x180, 640x360 and 960x540 with 4/8/12 simulation steps; record update/readback p50/p95 and morphology speed.
3. Hardware-test Cellular Worlds at multiple grid sizes and generations/frame; identify which rules sustain compelling long-run structure instead of decaying into noise/static.
4. Hardware-test all eight attractors at 12k/25k/50k/90k points; tune point size/exposure/bloom for projector black floor.
5. Add smooth parameter morphing and preset snapshots instead of only launch-time parameters.
6. Add a shared scalar/vector-field abstraction so particles, reaction diffusion, cellular systems, SDFs and room surfaces can consume the same mathematical fields.
7. Implement hyperbolic tiling + circle inversion / Schottky group lab.
8. Implement Voronoi/Lloyd/power-diagram lab with performer/audio points as moving sites.
9. Implement wave-equation/cymatics lab and route live audio frequencies into mode amplitudes.
10. Implement Lenia/SmoothLife and reversible Margolus branches next to the discrete CA baseline.
11. Implement torus-knot/Hopf-fibration/minimal-surface SDF geometry branch.
12. Add attractor parameter morphing, Poincare slices and audio-controlled bifurcation/chaos transitions.
13. Add Song Studio crossfades between math worlds; avoid hard identity changes at section boundaries.
14. Add calibrated projector-coordinate masks/boundary conditions so mathematical fields can live on wall/floor/ceiling independently.
15. Add direct GL display/shared texture and keep state on GPU end-to-end.
16. Evaluate differentiable/inverse-design experiments only after runtime metrics and projector-art baselines exist.

## Metrics
GPU compile time; per-mode frame time; PDE/CA update time per step; readback time; p50/p95/p99 display frame time; attractor generation time; active point count; black-level/contrast; highlight saturation; temporal continuity; visible branch cuts/seams; parameter reproducibility; field stability under long runs; projector readability; subjective footage promotion score.

## Preset / operating-point vault
Pending projector validation. Initial candidates:
- Mandelbrot-Julia / ultraviolet / chaos ~1.0.
- Newton Basins / electric / chaos ~0.9.
- Chladni Plate / spectral / chaos ~0.7.
- Quasicrystal 5-fold / electric / chaos 1.0–1.4.
- Complex Domain / ultraviolet or icefire.
- Gray-Scott Coral / ultraviolet / 640x360 / 8 steps.
- Gray-Scott Mitosis / bio / 640x360 / 8 steps.
- Cyclic-8 / electric / 512x288 / 1–2 generations per frame.
- Brian's Brain / ultraviolet / 512x288 / 1 generation per frame.
- Lorenz / spectral / 50k points.
- Aizawa / ultraviolet / 50k points.
- Clifford / electric / 50k points.

## Promotion rule
A mathematical mode is promoted only when it passes three gates: (1) correct/stable enough not to exhibit accidental seams/divergence or collapse, (2) realtime on target hardware at a useful operating point, and (3) visually compelling on projector/recorded footage for sustained viewing. Mathematical fame alone is not a promotion criterion.
