from __future__ import annotations

import numpy as np

from .graphics_runtime import create_context


GEOMETRY_MODES = (
    "voronoi_flow",
    "power_diagram",
    "lloyd_relaxation",
    "delaunay_ridges",
    "apollonian_gasket",
    "penrose_interference",
)
GEOMETRY_PALETTES = ("cyan_magenta", "spectral", "electric", "solar", "bio", "ultraviolet", "icefire")


def lloyd_relax(points: np.ndarray, *, strength: float = 0.65, grid: int = 42) -> np.ndarray:
    """Approximate one centroidal Voronoi/Lloyd step on a regular sample grid."""
    pts = np.asarray(points, dtype=np.float32)
    if pts.ndim != 2 or pts.shape[1] != 2:
        raise ValueError("points must have shape (N, 2)")
    if len(pts) == 0:
        return pts.copy()
    axis = np.linspace(-1.0, 1.0, int(max(grid, 8)), dtype=np.float32)
    gx, gy = np.meshgrid(axis, axis)
    samples = np.stack([gx.ravel(), gy.ravel()], axis=1)
    d2 = np.sum((samples[:, None, :] - pts[None, :, :]) ** 2, axis=2)
    owner = np.argmin(d2, axis=1)
    out = pts.copy()
    a = float(np.clip(strength, 0.0, 1.0))
    for i in range(len(pts)):
        mask = owner == i
        if np.any(mask):
            centroid = samples[mask].mean(axis=0)
            out[i] = pts[i] * (1.0 - a) + centroid * a
    return np.clip(out, -0.98, 0.98)


_VERTEX = r"""
#version 330
in vec2 in_pos;
out vec2 v_uv;
void main(){v_uv=in_pos*.5+.5;gl_Position=vec4(in_pos,0.0,1.0);}
"""

_FRAGMENT = r"""
#version 330
uniform vec2 u_resolution;
uniform float u_time;
uniform float u_intensity;
uniform float u_chaos;
uniform float u_scale;
uniform int u_mode;
uniform int u_palette;
uniform int u_site_count;
uniform vec2 u_sites[32];
uniform float u_weights[32];
in vec2 v_uv;
out vec4 fragColor;
#define PI 3.141592653589793
#define TAU 6.283185307179586

vec3 pal(float t){
    if(u_palette==0) return mix(vec3(.00,.96,1.00),vec3(1.00,.02,.78),.5+.5*cos(TAU*t));
    t=fract(t);
    if(u_palette==2) return .50+.50*cos(TAU*(vec3(1.0,.82,.63)*t+vec3(.56,.11,.02)));
    if(u_palette==3) return .50+.50*cos(TAU*(vec3(1.0,.74,.55)*t+vec3(.02,.08,.16)));
    if(u_palette==4) return .50+.50*cos(TAU*(vec3(.84,1.0,.70)*t+vec3(.42,.03,.20)));
    if(u_palette==5) return .50+.50*cos(TAU*(vec3(.94,.74,1.0)*t+vec3(.72,.21,.03)));
    if(u_palette==6) return .50+.50*cos(TAU*(vec3(1.0,.72,.82)*t+vec3(.55,.90,.12)));
    return .50+.50*cos(TAU*(vec3(1.0,.87,.72)*t+vec3(.01,.17,.44)));
}

void nearestSites(vec2 p, bool weighted, out float d1, out float d2, out float idx){
    d1=1e9; d2=1e9; idx=0.0;
    for(int i=0;i<32;i++){
        if(i>=u_site_count)break;
        vec2 q=u_sites[i];
        float a=u_time*(.027+.002*float(i));
        float wobble=.025*u_chaos;
        q+=wobble*vec2(sin(a*2.0+float(i)*1.7),cos(a*1.3+float(i)*2.1));
        float d=dot(p-q,p-q);
        if(weighted)d-=u_weights[i]*(.10+.035*u_chaos);
        if(d<d1){d2=d1;d1=d;idx=float(i);}else if(d<d2){d2=d;}
    }
}

vec3 voronoiWorld(vec2 p,bool weighted,bool lloyd,bool delaunay){
    float d1,d2,idx; nearestSites(p,weighted,d1,d2,idx);
    float edge=exp(-abs(d2-d1)*(110.0+35.0*u_chaos));
    float site=exp(-sqrt(max(d1,0.0))*(18.0+4.0*u_chaos));
    float cell=.5+.5*cos(idx*1.618+sqrt(max(d1,0.0))*24.0-u_time*.15);
    float ridges=delaunay?pow(edge,.52):edge;
    float body=lloyd?.14+.24*cell:.08+.17*cell;
    vec3 c=pal(idx*.071+cell*.16+u_time*.006)*(body+ridges*.88+site*.27);
    c+=vec3(1.0,.985,.95)*pow(ridges,5.0)*.24;
    return c;
}

vec3 apollonian(vec2 p){
    vec2 z=p;
    float trap=10.0;
    float orbit=0.0;
    for(int i=0;i<14;i++){
        float r2=dot(z,z);
        if(r2<.24)z*=2.35;
        else if(r2<1.0)z/=max(r2,1e-5);
        z=z*1.18-vec2(.32+.04*sin(u_time*.07),.18*cos(u_time*.051));
        z=abs(z)-vec2(.43,.31);
        trap=min(trap,abs(length(z)-.34));
        orbit+=exp(-length(z)*2.1);
    }
    float web=exp(-trap*(75.0+18.0*u_chaos));
    float rings=.5+.5*cos(orbit*2.7+length(p)*19.0-u_time*.13);
    vec3 c=pal(orbit*.07+u_time*.006)*(web*.95+rings*.16);
    c+=vec3(1.0,.98,.94)*pow(web,4.0)*.22;
    return c;
}

vec3 penrose(vec2 p){
    float sum=0.0;
    float edge=0.0;
    for(int i=0;i<10;i++){
        float fi=float(i);
        float a=fi*PI/5.0+u_time*.014*(1.0+mod(fi,2.0));
        vec2 n=vec2(cos(a),sin(a));
        float w=cos(dot(p,n)*(10.0+1.8*u_chaos)+fi*1.256+u_time*.11);
        sum+=w;
        edge+=pow(abs(w),8.0);
    }
    float q=.5+.5*cos(sum*1.15);
    float fil=pow(clamp(edge/10.0,0.0,1.0),.55);
    vec3 c=pal(q*.34+atan(p.y,p.x)/TAU+u_time*.006)*(q*.38+fil*.72);
    return c;
}

void main(){
    vec2 p=(gl_FragCoord.xy*2.0-u_resolution)/u_resolution.y;
    p*=max(u_scale,.05);
    vec3 col;
    if(u_mode==0)col=voronoiWorld(p,false,false,false);
    else if(u_mode==1)col=voronoiWorld(p,true,false,false);
    else if(u_mode==2)col=voronoiWorld(p,false,true,false);
    else if(u_mode==3)col=voronoiWorld(p,false,false,true);
    else if(u_mode==4)col=apollonian(p);
    else col=penrose(p);
    col*=.76+.48*u_intensity;
    col=vec3(1.0)-exp(-max(col,vec3(0.0))*1.28);
    col=pow(col,vec3(.78));
    fragColor=vec4(clamp(col,0.0,1.0),1.0);
}
"""


class GeometryFieldRenderer:
    """Voronoi/power/Lloyd and geometric interference worlds."""

    def __init__(self, width: int, height: int, *, mode: str = "voronoi_flow", palette: str = "cyan_magenta", site_count: int = 18, seed: int = 13) -> None:
        import moderngl

        if mode not in GEOMETRY_MODES:
            raise ValueError(mode)
        if palette not in GEOMETRY_PALETTES:
            raise ValueError(palette)
        self.moderngl = moderngl
        self.width = int(width)
        self.height = int(height)
        self.mode = mode
        self.palette = palette
        self.site_count = int(np.clip(site_count, 4, 32))
        rng = np.random.default_rng(seed)
        self.sites = rng.uniform(-0.82, 0.82, size=(self.site_count, 2)).astype(np.float32)
        self.weights = rng.uniform(0.05, 0.95, size=(self.site_count,)).astype(np.float32)
        self._last_relax_t = -1e9
        self.ctx, self.context_info = create_context(require=330)
        self.backend = self.context_info.backend
        self.program = self.ctx.program(vertex_shader=_VERTEX, fragment_shader=_FRAGMENT)
        vertices = np.asarray([-1.0, -1.0, 3.0, -1.0, -1.0, 3.0], dtype="f4")
        self.vbo = self.ctx.buffer(vertices.tobytes())
        self.vao = self.ctx.simple_vertex_array(self.program, self.vbo, "in_pos")
        self.target = self.ctx.texture((self.width, self.height), 3, dtype="f1")
        self.fbo = self.ctx.framebuffer(color_attachments=[self.target])
        self.program["u_resolution"].value = (float(self.width), float(self.height))

    def _upload_sites(self) -> None:
        padded = np.zeros((32, 2), dtype=np.float32)
        padded[: self.site_count] = self.sites
        weights = np.zeros(32, dtype=np.float32)
        weights[: self.site_count] = self.weights
        self.program["u_sites"].write(padded.tobytes())
        self.program["u_weights"].write(weights.tobytes())
        self.program["u_site_count"].value = self.site_count

    def render(self, *, t: float, mode: str | None = None, palette: str | None = None, intensity: float = 1.0, chaos: float = 1.0, scale: float = 1.0, relax_strength: float = 0.52) -> np.ndarray:
        mode = mode or self.mode
        palette = palette or self.palette
        if mode not in GEOMETRY_MODES:
            raise ValueError(mode)
        if palette not in GEOMETRY_PALETTES:
            raise ValueError(palette)
        if mode == "lloyd_relaxation" and t - self._last_relax_t >= 0.08:
            self.sites = lloyd_relax(self.sites, strength=relax_strength, grid=44)
            self._last_relax_t = t
        self._upload_sites()
        p = self.program
        p["u_time"].value = float(t)
        p["u_intensity"].value = float(max(intensity, 0.0))
        p["u_chaos"].value = float(np.clip(chaos, 0.0, 2.5))
        p["u_scale"].value = float(np.clip(scale, 0.15, 4.0))
        p["u_mode"].value = GEOMETRY_MODES.index(mode)
        p["u_palette"].value = GEOMETRY_PALETTES.index(palette)
        self.fbo.use()
        self.ctx.viewport = (0, 0, self.width, self.height)
        self.fbo.clear(0.0, 0.0, 0.0, 1.0)
        self.vao.render(mode=self.moderngl.TRIANGLES)
        data = self.fbo.read(components=3, alignment=1)
        return np.flipud(np.frombuffer(data, dtype=np.uint8).reshape(self.height, self.width, 3)).copy()

    def close(self) -> None:
        for obj in (self.fbo, self.target, self.vao, self.vbo, self.program):
            try:
                obj.release()
            except Exception:
                pass
        try:
            self.ctx.release()
        except Exception:
            pass


__all__ = ["GEOMETRY_MODES", "GEOMETRY_PALETTES", "GeometryFieldRenderer", "lloyd_relax"]
