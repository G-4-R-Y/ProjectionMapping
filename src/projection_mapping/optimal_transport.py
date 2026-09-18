from __future__ import annotations

import math
import numpy as np

from .graphics_runtime import create_context


TRANSPORT_MODES = (
    "circle_to_spiral",
    "grid_to_disc",
    "rose_to_lissajous",
    "phyllotaxis_to_rose",
    "constellation_swap",
)
TRANSPORT_PALETTES = ("spectral", "electric", "solar", "bio", "ultraviolet", "icefire")


def sinkhorn_barycentric_map(source: np.ndarray, target: np.ndarray, *, epsilon: float = 0.08, iterations: int = 80) -> np.ndarray:
    """Return an entropic-OT barycentric target for each source point.

    Uniform masses are used. This is intentionally NumPy-only so the visual lab
    stays dependency-light while still using a real Sinkhorn transport plan.
    """
    x = np.asarray(source, dtype=np.float64)
    y = np.asarray(target, dtype=np.float64)
    if x.ndim != 2 or y.ndim != 2 or x.shape[1] != 2 or y.shape[1] != 2:
        raise ValueError("source and target must have shape (N, 2)/(M, 2)")
    if len(x) == 0 or len(y) == 0:
        raise ValueError("source and target must be non-empty")
    eps = max(float(epsilon), 1e-4)
    cost = np.sum((x[:, None, :] - y[None, :, :]) ** 2, axis=2)
    cost -= float(cost.min())
    kernel = np.exp(-cost / eps)
    kernel = np.maximum(kernel, 1e-300)
    a = np.full(len(x), 1.0 / len(x), dtype=np.float64)
    b = np.full(len(y), 1.0 / len(y), dtype=np.float64)
    u = np.ones_like(a)
    v = np.ones_like(b)
    for _ in range(max(1, int(iterations))):
        kv = kernel @ v
        u = a / np.maximum(kv, 1e-300)
        ktu = kernel.T @ u
        v = b / np.maximum(ktu, 1e-300)
    plan = (u[:, None] * kernel) * v[None, :]
    mass = np.maximum(plan.sum(axis=1, keepdims=True), 1e-300)
    mapped = (plan @ y) / mass
    return mapped.astype(np.float32)


def _normalize(points: np.ndarray, scale: float = 0.82) -> np.ndarray:
    pts = np.asarray(points, dtype=np.float32)
    pts = pts - pts.mean(axis=0, keepdims=True)
    radius = float(np.percentile(np.linalg.norm(pts, axis=1), 98))
    if radius > 1e-6:
        pts = pts / radius * scale
    return pts


def make_transport_shapes(mode: str, count: int = 384, seed: int = 17) -> tuple[np.ndarray, np.ndarray]:
    if mode not in TRANSPORT_MODES:
        raise ValueError(mode)
    n = int(max(32, count))
    t = np.arange(n, dtype=np.float32) / n
    a = t * (2.0 * np.pi)
    if mode == "circle_to_spiral":
        source = np.stack([np.cos(a), np.sin(a)], axis=1) * 0.72
        r = 0.05 + 0.80 * t
        target = np.stack([np.cos(a * 5.0) * r, np.sin(a * 5.0) * r], axis=1)
    elif mode == "grid_to_disc":
        side = int(math.ceil(math.sqrt(n)))
        gx, gy = np.meshgrid(np.linspace(-0.8, 0.8, side), np.linspace(-0.8, 0.8, side))
        source = np.stack([gx.ravel(), gy.ravel()], axis=1)[:n]
        rr = np.sqrt((np.arange(n, dtype=np.float32) + 0.5) / n) * 0.82
        ga = np.arange(n, dtype=np.float32) * (np.pi * (3.0 - np.sqrt(5.0)))
        target = np.stack([rr * np.cos(ga), rr * np.sin(ga)], axis=1)
    elif mode == "rose_to_lissajous":
        r = 0.74 * np.cos(5.0 * a)
        source = np.stack([r * np.cos(a), r * np.sin(a)], axis=1)
        target = np.stack([0.78 * np.sin(3.0 * a + 0.4), 0.72 * np.sin(4.0 * a)], axis=1)
    elif mode == "phyllotaxis_to_rose":
        ga = np.arange(n, dtype=np.float32) * (np.pi * (3.0 - np.sqrt(5.0)))
        rr = np.sqrt((np.arange(n, dtype=np.float32) + 0.5) / n) * 0.82
        source = np.stack([rr * np.cos(ga), rr * np.sin(ga)], axis=1)
        rose_r = 0.78 * np.cos(7.0 * a)
        target = np.stack([rose_r * np.cos(a), rose_r * np.sin(a)], axis=1)
    else:
        rng = np.random.default_rng(seed)
        source = rng.normal(0.0, 0.33, size=(n, 2)).astype(np.float32)
        rot = np.array([[0.28, -0.96], [0.96, 0.28]], dtype=np.float32)
        target = source @ rot.T
        target += 0.25 * np.stack([np.sin(a * 5.0), np.cos(a * 3.0)], axis=1)
    return _normalize(source), _normalize(target)


_VERTEX = r"""
#version 330
in vec2 in_pos;
in float in_phase;
uniform float u_point_size;
uniform float u_time;
out float v_phase;
void main(){
    gl_Position=vec4(in_pos,0.0,1.0);
    gl_PointSize=u_point_size*(.78+.42*(.5+.5*sin(in_phase*6.2831853+u_time*.7)));
    v_phase=in_phase;
}
"""

_FRAGMENT = r"""
#version 330
uniform int u_palette;
uniform float u_intensity;
in float v_phase;
out vec4 fragColor;
#define TAU 6.283185307179586
vec3 pal(float t){
    t=fract(t);
    if(u_palette==1)return .50+.50*cos(TAU*(vec3(1.0,.82,.63)*t+vec3(.56,.11,.02)));
    if(u_palette==2)return .50+.50*cos(TAU*(vec3(1.0,.74,.55)*t+vec3(.02,.08,.16)));
    if(u_palette==3)return .50+.50*cos(TAU*(vec3(.84,1.0,.70)*t+vec3(.42,.03,.20)));
    if(u_palette==4)return .50+.50*cos(TAU*(vec3(.94,.74,1.0)*t+vec3(.72,.21,.03)));
    if(u_palette==5)return .50+.50*cos(TAU*(vec3(1.0,.72,.82)*t+vec3(.55,.90,.12)));
    return .50+.50*cos(TAU*(vec3(1.0,.87,.72)*t+vec3(.01,.17,.44)));
}
void main(){
    vec2 q=gl_PointCoord*2.0-1.0;
    float r=length(q);
    if(r>1.0)discard;
    float core=exp(-r*r*18.0);
    float halo=exp(-r*r*3.0);
    vec3 c=pal(v_phase)*(halo*.52+core*1.28)*u_intensity;
    c+=vec3(1.0,.985,.95)*pow(core,3.0)*.55;
    fragColor=vec4(c,clamp(halo+core,0.0,1.0));
}
"""


class OptimalTransportRenderer:
    """Entropic Sinkhorn morphs rendered as coherent luminous point choreography."""

    def __init__(self, width: int, height: int, *, mode: str = "circle_to_spiral", palette: str = "spectral", points: int = 384, epsilon: float = 0.08, seed: int = 17) -> None:
        import moderngl

        if mode not in TRANSPORT_MODES:
            raise ValueError(mode)
        if palette not in TRANSPORT_PALETTES:
            raise ValueError(palette)
        self.moderngl = moderngl
        self.width = int(width)
        self.height = int(height)
        self.mode = mode
        self.palette = palette
        self.points = int(np.clip(points, 32, 2048))
        self.source, target = make_transport_shapes(mode, self.points, seed)
        self.target = sinkhorn_barycentric_map(self.source, target, epsilon=epsilon)
        self.phase = np.linspace(0.0, 1.0, self.points, endpoint=False, dtype=np.float32)
        self.ctx, self.context_info = create_context(require=330)
        self.backend = self.context_info.backend
        self.program = self.ctx.program(vertex_shader=_VERTEX, fragment_shader=_FRAGMENT)
        self.vbo = self.ctx.buffer(reserve=self.points * 3 * 4, dynamic=True)
        self.vao = self.ctx.vertex_array(self.program, [(self.vbo, "2f 1f", "in_pos", "in_phase")])
        self.target_tex = self.ctx.texture((self.width, self.height), 3, dtype="f1")
        self.fbo = self.ctx.framebuffer(color_attachments=[self.target_tex])

    def render(self, *, t: float, palette: str | None = None, intensity: float = 1.0, point_size: float = 7.0, arc: float = 0.18, cycles: float = 0.18) -> np.ndarray:
        palette = palette or self.palette
        if palette not in TRANSPORT_PALETTES:
            raise ValueError(palette)
        phase = 0.5 - 0.5 * np.cos((0.5 + 0.5 * np.sin(t * float(cycles))) * np.pi)
        pos = self.source * (1.0 - phase) + self.target * phase
        delta = self.target - self.source
        perp = np.stack([-delta[:, 1], delta[:, 0]], axis=1)
        norm = np.maximum(np.linalg.norm(perp, axis=1, keepdims=True), 1e-6)
        pos += perp / norm * (np.sin(np.pi * phase) * float(arc)) * np.sin(self.phase[:, None] * 17.0 + t * 0.37)
        data = np.column_stack([pos.astype(np.float32), self.phase]).astype(np.float32)
        self.vbo.write(data.tobytes())
        self.fbo.use()
        self.ctx.viewport = (0, 0, self.width, self.height)
        self.fbo.clear(0.0, 0.0, 0.0, 1.0)
        self.ctx.enable(self.moderngl.BLEND | self.moderngl.PROGRAM_POINT_SIZE)
        self.ctx.blend_func = (self.moderngl.SRC_ALPHA, self.moderngl.ONE)
        self.program["u_point_size"].value = float(np.clip(point_size, 1.0, 32.0))
        self.program["u_time"].value = float(t)
        self.program["u_palette"].value = TRANSPORT_PALETTES.index(palette)
        self.program["u_intensity"].value = float(max(intensity, 0.0))
        self.vao.render(mode=self.moderngl.POINTS, vertices=self.points)
        data = self.fbo.read(components=3, alignment=1)
        return np.flipud(np.frombuffer(data, dtype=np.uint8).reshape(self.height, self.width, 3)).copy()

    def close(self) -> None:
        for obj in (self.fbo, self.target_tex, self.vao, self.vbo, self.program):
            try:
                obj.release()
            except Exception:
                pass
        try:
            self.ctx.release()
        except Exception:
            pass


__all__ = ["TRANSPORT_MODES", "TRANSPORT_PALETTES", "OptimalTransportRenderer", "make_transport_shapes", "sinkhorn_barycentric_map"]
