from __future__ import annotations

import math

import numpy as np

from .graphics_runtime import create_context


ATTRACTOR_MODES = (
    "lorenz",
    "rossler",
    "aizawa",
    "thomas",
    "halvorsen",
    "clifford",
    "de_jong",
    "ikeda",
)

ATTRACTOR_PALETTES = ("spectral", "electric", "solar", "bio", "ultraviolet")

_VERTEX = r"""
#version 330
in vec4 in_point;
uniform float u_time;
uniform float u_zoom;
uniform float u_point_size;
uniform int u_palette;
out vec3 v_color;
out float v_age;
#define TAU 6.28318530718

vec3 pal(float t){
    t=fract(t);
    if(u_palette==1) return .50+.50*cos(TAU*(vec3(1.0,.82,.63)*t+vec3(.56,.11,.02)));
    if(u_palette==2) return .50+.50*cos(TAU*(vec3(1.0,.75,.57)*t+vec3(.02,.07,.16)));
    if(u_palette==3) return .50+.50*cos(TAU*(vec3(.84,1.0,.70)*t+vec3(.42,.03,.20)));
    if(u_palette==4) return .50+.50*cos(TAU*(vec3(.94,.74,1.0)*t+vec3(.72,.21,.03)));
    return .50+.50*cos(TAU*(vec3(1.0,.87,.72)*t+vec3(.01,.17,.44)));
}

void main(){
    vec3 p=in_point.xyz;
    float a=u_time*.11;
    float b=.31*sin(u_time*.071);
    mat3 ry=mat3(cos(a),0.0,sin(a), 0.0,1.0,0.0, -sin(a),0.0,cos(a));
    mat3 rx=mat3(1.0,0.0,0.0, 0.0,cos(b),-sin(b), 0.0,sin(b),cos(b));
    p=rx*ry*p;
    float depth=2.25+.46*p.z;
    vec2 q=p.xy/max(depth,.55)*u_zoom;
    gl_Position=vec4(q,0.0,1.0);
    float depthLift=clamp(1.35-depth*.18,.62,1.18);
    gl_PointSize=u_point_size*depthLift*(.70+.55*sin(in_point.w*TAU*3.0+.8));
    v_age=in_point.w;
    v_color=pal(in_point.w*.82+p.z*.13+u_time*.012);
}
"""

_POINT_FRAGMENT = r"""
#version 330
in vec3 v_color;
in float v_age;
uniform float u_energy;
out vec4 fragColor;
void main(){
    vec2 q=gl_PointCoord*2.0-1.0;
    float r=length(q);
    if(r>1.0) discard;
    float core=exp(-r*r*18.0);
    float halo=exp(-r*3.2)*.42;
    float twinkle=.72+.28*sin(v_age*83.0);
    vec3 col=v_color*(halo+.55*core)*twinkle;
    col+=vec3(1.0,.985,.95)*core*.72;
    fragColor=vec4(col*u_energy,core+halo*.48);
}
"""

_POST_VERTEX = r"""
#version 330
in vec2 in_pos;
out vec2 v_uv;
void main(){v_uv=in_pos*.5+.5;gl_Position=vec4(in_pos,0.0,1.0);}
"""

_POST_FRAGMENT = r"""
#version 330
uniform sampler2D u_hdr;
uniform vec2 u_texel;
uniform float u_bloom;
uniform float u_intensity;
in vec2 v_uv;
out vec4 fragColor;

vec3 bright(vec3 c){
    float m=max(c.r,max(c.g,c.b));
    float k=max((m-.18)/max(m,1e-5),0.0);
    return c*k;
}

void main(){
    vec3 c=texture(u_hdr,v_uv).rgb;
    vec3 b=vec3(0.0);
    vec2 taps[12]=vec2[12](
        vec2(2,0),vec2(-2,0),vec2(0,2),vec2(0,-2),
        vec2(4,4),vec2(-4,4),vec2(4,-4),vec2(-4,-4),
        vec2(8,0),vec2(-8,0),vec2(0,8),vec2(0,-8)
    );
    for(int i=0;i<12;i++) b+=bright(texture(u_hdr,v_uv+taps[i]*u_texel).rgb);
    c+=b*(u_bloom/12.0)*.72;
    c*=.75+.48*u_intensity;
    c=vec3(1.0)-exp(-max(c,vec3(0.0))*1.22);
    c=pow(c,vec3(.78));
    float peak=max(c.r,max(c.g,c.b));
    c*=smoothstep(.006,.045,peak);
    fragColor=vec4(clamp(c,0.0,1.0),1.0);
}
"""


def _rk4_step(state: np.ndarray, dt: float, fn) -> np.ndarray:
    k1 = fn(state)
    k2 = fn(state + 0.5 * dt * k1)
    k3 = fn(state + 0.5 * dt * k2)
    k4 = fn(state + dt * k3)
    return state + dt * (k1 + 2 * k2 + 2 * k3 + k4) / 6.0


def _trajectory_3d(mode: str, count: int) -> np.ndarray:
    if mode == "lorenz":
        dt, skip, state = 0.005, 2200, np.array([0.1, 0.0, 0.0], dtype=np.float64)

        def fn(s):
            x, y, z = s
            return np.array([10.0 * (y - x), x * (28.0 - z) - y, x * y - (8.0 / 3.0) * z])

    elif mode == "rossler":
        dt, skip, state = 0.012, 2600, np.array([0.2, 0.1, 0.1], dtype=np.float64)

        def fn(s):
            x, y, z = s
            return np.array([-y - z, x + 0.2 * y, 0.2 + z * (x - 5.7)])

    elif mode == "aizawa":
        dt, skip, state = 0.008, 2200, np.array([0.1, 0.0, 0.0], dtype=np.float64)
        a, b, c, d, e, f = 0.95, 0.7, 0.6, 3.5, 0.25, 0.1

        def fn(s):
            x, y, z = s
            r2 = x * x + y * y
            return np.array([
                (z - b) * x - d * y,
                d * x + (z - b) * y,
                c + a * z - z**3 / 3.0 - r2 * (1.0 + e * z) + f * z * x**3,
            ])

    elif mode == "thomas":
        dt, skip, state = 0.035, 1800, np.array([0.1, 0.0, -0.1], dtype=np.float64)
        b = 0.208186

        def fn(s):
            x, y, z = s
            return np.array([math.sin(y) - b * x, math.sin(z) - b * y, math.sin(x) - b * z])

    else:
        dt, skip, state = 0.0045, 2600, np.array([0.2, 0.1, -0.1], dtype=np.float64)
        a = 1.4

        def fn(s):
            x, y, z = s
            return np.array([
                -a * x - 4.0 * y - 4.0 * z - y * y,
                -a * y - 4.0 * z - 4.0 * x - z * z,
                -a * z - 4.0 * x - 4.0 * y - x * x,
            ])

    out = np.empty((count, 3), dtype=np.float64)
    write = 0
    for i in range(skip + count):
        state = _rk4_step(state, dt, fn)
        if not np.isfinite(state).all():
            raise RuntimeError(f"{mode} attractor diverged")
        if i >= skip:
            out[write] = state
            write += 1
    return out


def _trajectory_2d(mode: str, count: int) -> np.ndarray:
    x, y = 0.1, 0.1
    skip = 1800
    out = np.empty((count, 3), dtype=np.float64)
    write = 0
    for i in range(skip + count):
        if mode == "clifford":
            a, b, c, d = -1.4, 1.6, 1.0, 0.7
            x, y = math.sin(a * y) + c * math.cos(a * x), math.sin(b * x) + d * math.cos(b * y)
        elif mode == "de_jong":
            a, b, c, d = 1.4, -2.3, 2.4, -2.1
            x, y = math.sin(a * y) - math.cos(b * x), math.sin(c * x) - math.cos(d * y)
        else:
            u = 0.918
            tt = 0.4 - 6.0 / (1.0 + x * x + y * y)
            ct, st = math.cos(tt), math.sin(tt)
            x, y = 1.0 + u * (x * ct - y * st), u * (x * st + y * ct)
        if i >= skip:
            out[write] = (x, y, 0.0)
            write += 1
    return out


def generate_attractor(mode: str, count: int = 50000) -> np.ndarray:
    if mode not in ATTRACTOR_MODES:
        raise ValueError(mode)
    count = max(1024, int(count))
    if mode in {"clifford", "de_jong", "ikeda"}:
        xyz = _trajectory_2d(mode, count)
    else:
        xyz = _trajectory_3d(mode, count)
    center = np.median(xyz, axis=0)
    centered = xyz - center
    radius = np.linalg.norm(centered, axis=1)
    scale = float(np.percentile(radius, 99.2))
    if not np.isfinite(scale) or scale <= 1e-8:
        scale = 1.0
    centered = np.clip(centered / scale, -1.45, 1.45)
    age = np.linspace(0.0, 1.0, count, endpoint=False, dtype=np.float64)[:, None]
    return np.concatenate([centered, age], axis=1).astype(np.float32)


class AttractorRenderer:
    """GPU point-cloud renderer for classic chaotic ODEs and iterative maps."""

    def __init__(
        self,
        width: int,
        height: int,
        *,
        mode: str = "lorenz",
        palette: str = "spectral",
        points: int = 50000,
    ) -> None:
        import moderngl

        if mode not in ATTRACTOR_MODES:
            raise ValueError(mode)
        if palette not in ATTRACTOR_PALETTES:
            raise ValueError(palette)
        self.moderngl = moderngl
        self.width = int(width)
        self.height = int(height)
        self.mode = mode
        self.palette = palette
        self.ctx, self.context_info = create_context(require=330)
        self.backend = self.context_info.backend
        self.point_program = self.ctx.program(vertex_shader=_VERTEX, fragment_shader=_POINT_FRAGMENT)
        self.post_program = self.ctx.program(vertex_shader=_POST_VERTEX, fragment_shader=_POST_FRAGMENT)
        point_data = generate_attractor(mode, points)
        self.point_count = len(point_data)
        self.point_vbo = self.ctx.buffer(point_data.tobytes())
        self.point_vao = self.ctx.simple_vertex_array(self.point_program, self.point_vbo, "in_point")
        vertices = np.asarray([-1.0, -1.0, 3.0, -1.0, -1.0, 3.0], dtype="f4")
        self.quad_vbo = self.ctx.buffer(vertices.tobytes())
        self.post_vao = self.ctx.simple_vertex_array(self.post_program, self.quad_vbo, "in_pos")
        self.hdr = self.ctx.texture((self.width, self.height), 4, dtype="f2")
        self.hdr_fbo = self.ctx.framebuffer(color_attachments=[self.hdr])
        self.target = self.ctx.texture((self.width, self.height), 3, dtype="f1")
        self.target_fbo = self.ctx.framebuffer(color_attachments=[self.target])
        self.post_program["u_hdr"].value = 0
        self.post_program["u_texel"].value = (1.0 / self.width, 1.0 / self.height)

    def render(
        self,
        *,
        t: float,
        palette: str | None = None,
        intensity: float = 1.0,
        zoom: float = 1.35,
        point_size: float = 2.2,
        bloom: float = 1.0,
        energy: float = 1.0,
    ) -> np.ndarray:
        palette = palette or self.palette
        if palette not in ATTRACTOR_PALETTES:
            raise ValueError(palette)
        planar = self.mode in {"clifford", "de_jong", "ikeda"}
        # Iterated 2-D maps occupy a razor-thin plane. Give them a denser luminous material than
        # volumetric ODE trajectories so the projector sees a sculpture rather than isolated dust.
        point_boost = 1.85 if self.mode == "ikeda" else (1.45 if planar else 1.0)
        energy_boost = 1.45 if self.mode == "ikeda" else (1.22 if planar else 1.0)
        p = self.point_program
        p["u_time"].value = float(t)
        p["u_zoom"].value = float(max(zoom, 0.1))
        p["u_point_size"].value = float(np.clip(point_size * point_boost, 0.5, 12.0))
        p["u_palette"].value = ATTRACTOR_PALETTES.index(palette)
        p["u_energy"].value = float(np.clip(energy * energy_boost, 0.0, 4.0))
        self.ctx.viewport = (0, 0, self.width, self.height)
        self.hdr_fbo.use()
        self.hdr_fbo.clear(0.0, 0.0, 0.0, 0.0)
        self.ctx.enable(self.moderngl.BLEND)
        self.ctx.blend_func = (self.moderngl.ONE, self.moderngl.ONE)
        self.point_vao.render(mode=self.moderngl.POINTS, vertices=self.point_count)
        self.ctx.disable(self.moderngl.BLEND)

        self.hdr.use(location=0)
        q = self.post_program
        q["u_bloom"].value = float(np.clip(bloom, 0.0, 3.0))
        q["u_intensity"].value = float(max(intensity, 0.0))
        self.target_fbo.use()
        self.target_fbo.clear(0.0, 0.0, 0.0, 1.0)
        self.post_vao.render(mode=self.moderngl.TRIANGLES)
        data = self.target_fbo.read(components=3, alignment=1)
        return np.flipud(np.frombuffer(data, dtype=np.uint8).reshape(self.height, self.width, 3)).copy()

    def close(self) -> None:
        for obj in (
            self.target_fbo,
            self.target,
            self.hdr_fbo,
            self.hdr,
            self.post_vao,
            self.quad_vbo,
            self.point_vao,
            self.point_vbo,
            self.post_program,
            self.point_program,
        ):
            try:
                obj.release()
            except Exception:
                pass
        try:
            self.ctx.release()
        except Exception:
            pass


__all__ = [
    "ATTRACTOR_MODES",
    "ATTRACTOR_PALETTES",
    "generate_attractor",
    "AttractorRenderer",
]
