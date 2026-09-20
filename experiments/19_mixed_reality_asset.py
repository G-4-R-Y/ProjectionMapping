"""Generated Asset Stage: attach a built-in or generated mesh to performer/world anchors.

The stage always has a runnable procedural mesh (`builtin:cyber_orb`) so graphics/tracking can be
validated before a Genforge/export pipeline is connected. External GLB/glTF/OBJ/etc paths are
loaded through the optional trimesh backend. RTMPose supplies semantic anchors; our ModernGL
renderer handles mesh + optional GPU particle aura. F11 toggles fullscreen; ESC exits.
"""
from __future__ import annotations

import argparse
import math
import time

import cv2
import numpy as np

from projection_mapping.capture import Camera
from projection_mapping.gpu_mesh import GPUMeshRenderer
from projection_mapping.gpu_particles import GPUParticleField, ParticleEmitter
from projection_mapping.mesh_assets import BUILTIN_MESHES
from projection_mapping.pose_tracking import RTMPoseWholeBodyTracker
from projection_mapping.runtime import FullscreenSink


STYLES = {
    "cyan_magenta": ((0.02, 0.10, 0.18), (1.00, 0.02, 0.78), "cyan_magenta"),
    "cyber": ((0.05, 0.18, 0.30), (0.05, 0.82, 1.00), "cyber"),
    "bio": ((0.04, 0.22, 0.16), (0.15, 1.00, 0.55), "bio"),
    "solar": ((0.26, 0.08, 0.03), (1.00, 0.48, 0.06), "solar"),
    "prismatic": ((0.16, 0.06, 0.22), (0.82, 0.22, 1.00), "prismatic"),
}


def _anchor_world(anchor, aspect: float) -> tuple[float, float, float]:
    # Approximate screen-anchored MR placement until calibrated camera/world geometry lands.
    x = (anchor.position.x - 0.5) * 1.85 * aspect
    y = (0.5 - anchor.position.y) * 1.85
    z = float(np.clip(-anchor.position.z * 0.8, -0.65, 0.65))
    return x, y, z


def _composite(background: np.ndarray, mesh: np.ndarray, particles: np.ndarray | None) -> np.ndarray:
    out = background.astype(np.float32)
    if particles is not None:
        out = np.clip(out + particles.astype(np.float32) * 0.88, 0, 255)
    m = mesh.astype(np.float32)
    alpha = np.clip(np.max(m, axis=2, keepdims=True) / 165.0, 0.0, 1.0)
    alpha = np.power(alpha, 0.72)
    out = out * (1.0 - alpha) + np.clip(m * 1.20, 0, 255) * alpha
    return np.clip(out, 0, 255).astype(np.uint8)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--asset",
        default="builtin:cyber_orb",
        help=(
            "Generated GLB/glTF/OBJ/etc path, or a procedural test asset: "
            + ", ".join(BUILTIN_MESHES)
        ),
    )
    ap.add_argument("--anchor", choices=["world", "left_palm", "right_palm", "chest", "head"], default="right_palm")
    ap.add_argument("--camera", type=int, default=0)
    ap.add_argument("--display", type=int, default=1)
    ap.add_argument("--capture-width", type=int, default=640)
    ap.add_argument("--capture-height", type=int, default=360)
    ap.add_argument("--render-width", type=int, default=768)
    ap.add_argument("--render-height", type=int, default=432)
    ap.add_argument("--projector-width", type=int, default=1920)
    ap.add_argument("--projector-height", type=int, default=1080)
    ap.add_argument("--scale", type=float, default=0.34)
    ap.add_argument("--spin-speed", type=float, default=0.65)
    ap.add_argument("--style", choices=sorted(STYLES), default="cyan_magenta")
    ap.add_argument("--camera-mix", type=float, default=0.72)
    ap.add_argument("--particles", type=int, default=16384)
    ap.add_argument("--particle-aura", action="store_true")
    ap.add_argument("--mirror", action="store_true")
    args = ap.parse_args()

    asset = str(args.asset).strip() or "builtin:cyber_orb"
    base, emissive, particle_palette = STYLES[args.style]
    tracker = None
    if args.anchor != "world":
        tracker = RTMPoseWholeBodyTracker(mode="lightweight", backend="onnxruntime", device="cpu")
    mesh_renderer = GPUMeshRenderer(args.render_width, args.render_height)
    try:
        model = mesh_renderer.upload(asset)
    except Exception as exc:
        mesh_renderer.close()
        choices = ", ".join(BUILTIN_MESHES)
        raise SystemExit(
            f"[mr-asset] could not load asset {asset!r}: {type(exc).__name__}: {exc}\n"
            f"Use a generated mesh path, or test immediately with one of: {choices}"
        ) from exc

    particle_field = (
        GPUParticleField(args.render_width, args.render_height, capacity=args.particles, palette=particle_palette)
        if args.particle_aura
        else None
    )
    sink = FullscreenSink(window="ProjectionMapping-MixedRealityAsset", display=args.display, fullscreen=True)

    print(
        f"[mr-asset] asset={asset!r} anchor={args.anchor} primitives={len(model.primitives)} "
        f"bounds={model.asset.bounds_min}->{model.asset.bounds_max} "
        f"gl={mesh_renderer.context_info.gl_version} renderer={mesh_renderer.context_info.renderer}",
        flush=True,
    )

    t0 = time.perf_counter()
    last = t0
    report = t0
    frames = 0
    aspect = args.render_width / max(args.render_height, 1)
    last_anchor = (0.0, 0.0, 0.0)
    anchor_conf = 1.0 if args.anchor == "world" else 0.0

    try:
        with Camera(args.camera, args.capture_width, args.capture_height) as cam:
            while True:
                now = time.perf_counter()
                t = now - t0
                dt = float(np.clip(now - last, 1e-4, 0.08))
                last = now
                frame = cam.read()
                frame = cv2.resize(frame, (args.capture_width, args.capture_height), interpolation=cv2.INTER_AREA)
                if args.mirror:
                    frame = cv2.flip(frame, 1)

                semantic_anchor = None
                if tracker is not None:
                    state = tracker.update(frame, now)
                    semantic_anchor = state.anchor(args.anchor, 0.30)
                    if semantic_anchor is not None:
                        last_anchor = _anchor_world(semantic_anchor, aspect)
                        anchor_conf = semantic_anchor.confidence
                    else:
                        anchor_conf *= math.exp(-dt * 3.0)
                else:
                    state = None
                    last_anchor = (0.0, 0.0, 0.0)

                rotation = (t * args.spin_speed * 0.31, t * args.spin_speed, math.sin(t * 0.37) * 0.18)
                mesh = mesh_renderer.render(
                    model,
                    t=t,
                    screen_position=last_anchor,
                    rotation=rotation,
                    scale=args.scale * (0.72 + 0.28 * max(anchor_conf, 0.25)),
                    base_color=base,
                    emissive=emissive,
                    energy=0.75 + 0.75 * anchor_conf,
                )

                particle_rgb = None
                if particle_field is not None:
                    if semantic_anchor is not None:
                        emit = ParticleEmitter.from_anchor(
                            semantic_anchor,
                            energy=0.45 + 0.75 * anchor_conf,
                            hue={"cyan_magenta": 0.93, "cyber": 0.93, "bio": 0.36, "solar": 0.05, "prismatic": 0.90}[args.style],
                            radius=0.030,
                        )
                        emitters = [emit]
                    elif args.anchor == "world":
                        emitters = [ParticleEmitter(0.5, 0.5, 0.0, -0.04, 0.7, 0.78, 0.035)]
                    else:
                        emitters = []
                    particle_rgb = particle_field.render(
                        emitters,
                        t=t,
                        dt=dt,
                        emission_rate=3500.0 + 5500.0 * anchor_conf,
                        turbulence=0.19,
                        drag=1.05,
                        feedback=0.945,
                        bloom=1.1,
                        energy=1.0,
                    )

                cam_rgb = cv2.cvtColor(
                    cv2.resize(frame, (args.render_width, args.render_height), interpolation=cv2.INTER_AREA),
                    cv2.COLOR_BGR2RGB,
                )
                background = (cam_rgb.astype(np.float32) * float(np.clip(args.camera_mix, 0.0, 1.0))).astype(np.uint8)
                composed = _composite(background, mesh, particle_rgb)
                out = cv2.resize(composed, (args.projector_width, args.projector_height), interpolation=cv2.INTER_CUBIC)
                if sink(cv2.cvtColor(out, cv2.COLOR_RGB2BGR)) is False:
                    break

                frames += 1
                if now - report >= 2.0:
                    print(
                        f"[mr-asset] fps={frames/(now-report):.1f} anchor={args.anchor} "
                        f"conf={anchor_conf:.2f} pos=({last_anchor[0]:+.2f},{last_anchor[1]:+.2f},{last_anchor[2]:+.2f})",
                        flush=True,
                    )
                    frames = 0
                    report = now
    finally:
        if tracker is not None:
            tracker.close()
        if particle_field is not None:
            particle_field.close()
        mesh_renderer.close()
        sink.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
