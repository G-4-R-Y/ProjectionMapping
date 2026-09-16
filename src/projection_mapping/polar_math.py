from __future__ import annotations

import numpy as np

from .graphics_runtime import create_context


POLAR_MODES = (
    "rose_lattice",
    "hypotrochoid_engine",
    "log_spiral_interference",
    "phyllotaxis_reactor",
    "bessel_wave_chamber",
)

POLAR_PALETTES = ("spectral", "cyber", "solar", "bio", "ultraviolet")

_VERTEX = r"""
#version 330
in vec2 in_pos;
out vec2 v_uv;
void main() {
    v_uv = in_pos * 0.5 + 0.5;
    gl_Position = vec4(in_pos, 0.0, 1.0);
}
"""

_FRAGMENT = r"""
#version 330
uniform vec2 u_resolution;
uniform float u_time;
uniform float u_intensity;
uniform float u_bass;
uniform float u_mids;
uniform float u_highs;
uniform float u_beat;
uniform float u_drop;
uniform int u_mode;
uniform int u_palette;
in vec2 v_uv;
out vec4 fragColor;

#define PI 3.141592653589793
#define TAU 6.283185307179586
#define GOLDEN_ANGLE 2.399963229728653

float sat(float x) { return clamp(x, 0.0, 1.0); }
float aaLine(float d, float width) {
    float fw = max(fwidth(d), 0.00075);
    return 1.0 - smoothstep(width, width + fw * 1.75, abs(d));
}
float glowLine(float d, float width, float gain) {
    float x = abs(d);
    float core = aaLine(d, width);
    float halo = exp(-x * gain);
    return core * 1.35 + halo * 0.72;
}

vec3 cosinePalette(float t, vec3 a, vec3 b, vec3 c, vec3 d) {
    return a + b * cos(TAU * (c * t + d));
}
vec3 palette(float t) {
    t = fract(t);
    if (u_palette == 1)
        return cosinePalette(t, vec3(.52,.45,.58), vec3(.48,.50,.42), vec3(1.0,.83,.72), vec3(.58,.14,.01));
    if (u_palette == 2)
        return cosinePalette(t, vec3(.58,.34,.20), vec3(.46,.34,.26), vec3(1.0,.76,.58), vec3(.02,.08,.16));
    if (u_palette == 3)
        return cosinePalette(t, vec3(.32,.50,.42), vec3(.32,.50,.50), vec3(.88,1.0,.72), vec3(.43,.04,.18));
    if (u_palette == 4)
        return cosinePalette(t, vec3(.47,.34,.62), vec3(.49,.43,.42), vec3(.94,.76,1.0), vec3(.73,.22,.03));
    return cosinePalette(t, vec3(.55,.52,.56), vec3(.47,.48,.46), vec3(1.0,.87,.73), vec3(.02,.18,.46));
}

vec3 vividGlow(vec3 hue, float energy, float core) {
    vec3 saturated = hue * energy;
    vec3 hot = vec3(1.0, .985, .96) * core;
    return saturated + hot;
}

vec3 roseLattice(vec2 p, float t) {
    float r = length(p) + 1e-5;
    float a = atan(p.y, p.x);
    vec3 col = vec3(0.0);
    float bass = 0.06 * u_bass;
    for (int i=0; i<5; ++i) {
        float fi = float(i);
        float k = 5.0 + fi * 2.0;
        float phase = t * (0.20 + fi*.045) * (mod(fi,2.0) < 1.0 ? 1.0 : -1.0);
        float rose = 0.23 + fi*.105 + (0.072 + bass*.42) * cos(k*a + phase);
        rose += 0.018 * sin((k+3.0)*a - t*.31 + fi);
        float d = r - rose;
        float line = glowLine(d, .0030 + fi*.0004, 66.0 - fi*5.0);
        float pulse = .74 + .26*cos(TAU*(r*1.35 - t*.065 - fi*.08));
        vec3 hue = palette(fi*.135 + a/TAU*.18 + t*.018 + u_mids*.08);
        col += vividGlow(hue, line*pulse*(.72 + .18*fi), aaLine(d,.0022)*(.30+.13*fi));
    }
    float spokes = pow(.5+.5*cos(a*24.0 + t*.18), 18.0) * exp(-r*1.8);
    col += palette(a/TAU + .75) * spokes * (.12 + .42*u_highs);
    float center = exp(-r*10.0) * (.18 + .60*u_beat);
    col += vec3(1.0,.96,.92)*center;
    return col;
}

vec2 hypoPoint(float q, float R, float rr, float d, float spin) {
    float k = (R - rr) / rr;
    return vec2(
        (R-rr)*cos(q+spin) + d*cos(k*q-spin*1.41),
        (R-rr)*sin(q+spin) - d*sin(k*q-spin*1.41)
    );
}
vec3 hypotrochoidEngine(vec2 p, float t) {
    vec3 col = vec3(0.0);
    float spin = t*.13 + u_bass*.08;
    for (int layer=0; layer<3; ++layer) {
        float fl = float(layer);
        float R = .41 + fl*.12;
        float rr = .13 + fl*.018;
        float d = .20 + fl*.035 + .035*u_mids;
        float md = 10.0;
        vec2 prev = hypoPoint(0.0,R,rr,d,spin*(1.0+fl*.17));
        for (int j=1; j<=44; ++j) {
            float q = TAU * float(j) / 44.0;
            vec2 cur = hypoPoint(q,R,rr,d,spin*(1.0+fl*.17));
            vec2 pa = p-prev, ba = cur-prev;
            float h = clamp(dot(pa,ba)/max(dot(ba,ba),1e-6),0.0,1.0);
            md = min(md,length(pa-ba*h));
            prev = cur;
        }
        float g = exp(-md*(54.0-fl*7.0)) + aaLine(md,.0035)*1.15;
        vec3 hue = palette(.16+fl*.23+t*.022+u_highs*.08);
        col += vividGlow(hue,g*(1.00-fl*.13),aaLine(md,.0023)*.42);
    }
    float r=length(p), a=atan(p.y,p.x);
    float gear = pow(.5+.5*cos(a*(18.0+6.0*u_bass)-t*.36),18.0);
    float ring = exp(-70.0*abs(r-(.63+.018*sin(t*.29))));
    col += palette(a/TAU+t*.01)*gear*ring*(.65+.55*u_beat);
    col += vec3(1.0,.95,.90)*exp(-r*13.0)*(.18+.72*u_drop);
    return col;
}

vec3 logSpiralInterference(vec2 p, float t) {
    float r=length(p)+.012;
    float a=atan(p.y,p.x);
    float lr=log(r);
    float warp=.16*sin(a*5.0-t*.23)+.08*sin(a*11.0+t*.17);
    float ph1=14.0*lr - 7.0*a - t*1.15 + warp*4.0;
    float ph2=11.0*lr + 9.0*a + t*.84 - warp*3.2;
    float s1=pow(.5+.5*cos(ph1),18.0);
    float s2=pow(.5+.5*cos(ph2),16.0);
    float interference=pow(sat(s1+s2),1.4);
    float rings=pow(.5+.5*cos(r*(48.0+10.0*u_bass)-t*1.7),22.0);
    float radial=exp(-r*(1.18-.22*u_bass));
    vec3 c1=palette(a/TAU + r*.24 + t*.025);
    vec3 c2=palette(.54-a/TAU + r*.41 - t*.019);
    vec3 col=(c1*s1+c2*s2)*radial*1.25;
    col += palette(r*.52+t*.016)*rings*(.20+.52*u_beat)*radial;
    float core=exp(-r*9.5)*(1.0+.85*u_drop);
    col += vec3(1.0,.95,.90)*core*.50;
    col += palette(t*.03+.82)*interference*(.10+.22*u_highs);
    return col;
}

vec3 phyllotaxisReactor(vec2 p, float t) {
    vec3 col=vec3(0.0);
    float best=10.0;
    float bestId=0.0;
    float scale=.90+.06*sin(t*.17);
    for (int i=1;i<=72;++i) {
        float fi=float(i);
        float rn=sqrt(fi/72.0)*.82*scale;
        float a=fi*GOLDEN_ANGLE + t*(.12+.035*u_mids) + .14*sin(fi*.31+t*.23);
        vec2 q=vec2(cos(a),sin(a))*rn;
        float d=length(p-q);
        if(d<best){best=d;bestId=fi;}
    }
    float dotCore=exp(-best*190.0);
    float dotHalo=exp(-best*54.0);
    float idn=bestId/72.0;
    vec3 hue=palette(idn*.92+t*.018+u_bass*.10);
    col += vividGlow(hue,dotHalo*1.05,dotCore*.85);

    float r=length(p)+1e-5, a=atan(p.y,p.x);
    float arms=pow(.5+.5*cos(a*13.0-r*33.0+t*.48),18.0);
    float ring=pow(.5+.5*cos(r*54.0-t*.75),28.0);
    col += palette(a/TAU+r*.35+t*.011)*arms*ring*(.12+.35*u_highs);
    float reactor=exp(-r*12.0)*(.25+.95*u_beat+.65*u_drop);
    col += vec3(1.0,.94,.88)*reactor;
    return col;
}

float besselJ0(float x) {
    float ax=abs(x);
    if(ax<3.0){
        float y=x*x;
        return 1.0-y*.25+y*y*.015625-y*y*y*.0004340278+y*y*y*y*.00000678168;
    }
    return sqrt(2.0/(PI*ax))*cos(ax-PI*.25);
}
vec3 besselWaveChamber(vec2 p, float t) {
    float r=length(p)+1e-5;
    float a=atan(p.y,p.x);
    vec3 col=vec3(0.0);
    for(int i=0;i<4;++i){
        float fi=float(i);
        float k=14.0+fi*6.0+u_bass*3.0;
        float j=besselJ0(k*r + sin(a*(4.0+fi*2.0)+t*.19)*(.9+fi*.18));
        float contour=pow(sat(1.0-abs(j-(.18-fi*.055))*7.5),6.0);
        float node=pow(abs(j),3.0);
        float angular=.55+.45*cos(a*(6.0+fi*4.0)+t*(.16+fi*.04));
        vec3 hue=palette(fi*.19+r*.26+a/TAU*.09+t*.012);
        col += hue*(contour*.82+node*.12)*angular;
    }
    float lattice=pow(.5+.5*cos(r*68.0 + sin(a*12.0-t*.27)*2.0 - t*.52),24.0);
    col += palette(a/TAU+t*.02)*lattice*exp(-r*.82)*(.16+.44*u_highs);
    float center=exp(-r*8.2)*(.12+.50*u_beat+.72*u_drop);
    col += vec3(1.0,.96,.94)*center;
    return col;
}

void main(){
    vec2 p=(gl_FragCoord.xy*2.0-u_resolution)/u_resolution.y;
    float t=u_time;
    // Gentle breathing zoom keeps every scene alive without camera-like nausea.
    p *= .94 + .035*sin(t*.17) - .025*u_bass;
    float rot=.025*sin(t*.11)+.018*u_mids;
    mat2 R=mat2(cos(rot),-sin(rot),sin(rot),cos(rot));
    p=R*p;

    vec3 col;
    if(u_mode==0) col=roseLattice(p,t);
    else if(u_mode==1) col=hypotrochoidEngine(p,t);
    else if(u_mode==2) col=logSpiralInterference(p,t);
    else if(u_mode==3) col=phyllotaxisReactor(p,t);
    else col=besselWaveChamber(p,t);

    // Preserve saturated emissive color. Black stays black; only true highlights go white-hot.
    col *= .86 + .42*u_intensity;
    col *= 1.0 + .18*u_beat + .28*u_drop;
    float r=length(p);
    col *= mix(.70,1.0,smoothstep(1.25,.12,r));
    col = vec3(1.0) - exp(-max(col,vec3(0.0))*1.16);
    col = pow(col,vec3(.78));
    fragColor=vec4(clamp(col,0.0,1.0),1.0);
}
"""


class PolarMathRenderer:
    """Five vivid analytic polar-coordinate shader scenes.

    The renderer deliberately uses mathematical contours + emissive inverse-distance/glow language
    instead of fog-heavy procedural backgrounds. Optional MusicalSignals can modulate motion while
    the same renderer remains useful as a standalone scene lab.
    """

    def __init__(self, width: int, height: int, *, mode: str = "rose_lattice", palette: str = "spectral") -> None:
        import moderngl

        if mode not in POLAR_MODES:
            raise ValueError(f"unknown polar mode: {mode}")
        if palette not in POLAR_PALETTES:
            raise ValueError(f"unknown polar palette: {palette}")
        self.moderngl = moderngl
        self.width = int(width)
        self.height = int(height)
        self.mode = mode
        self.palette = palette
        self.ctx, self.context_info = create_context(require=330)
        self.backend = self.context_info.backend
        self.program = self.ctx.program(vertex_shader=_VERTEX, fragment_shader=_FRAGMENT)
        vertices=np.asarray([-1.0,-1.0,3.0,-1.0,-1.0,3.0],dtype="f4")
        self.vbo=self.ctx.buffer(vertices.tobytes())
        self.vao=self.ctx.simple_vertex_array(self.program,self.vbo,"in_pos")
        self.target=self.ctx.texture((self.width,self.height),3,dtype="f1")
        self.fbo=self.ctx.framebuffer(color_attachments=[self.target])
        self.program["u_resolution"].value=(float(self.width),float(self.height))

    def render(self, *, t: float, mode: str | None = None, palette: str | None = None, intensity: float = 1.0, signals=None) -> np.ndarray:
        mode = mode or self.mode
        palette = palette or self.palette
        if mode not in POLAR_MODES:
            raise ValueError(mode)
        if palette not in POLAR_PALETTES:
            raise ValueError(palette)
        bass=mids=highs=beat=drop=0.0
        if signals is not None:
            bass=float(getattr(signals,"bass",0.0))
            mids=float(getattr(signals,"mids",0.0))
            highs=float(getattr(signals,"highs",0.0))
            beat=float(getattr(signals,"beat",0.0))
            drop=float(getattr(signals,"drop",0.0))
        p=self.program
        p["u_time"].value=float(t)
        p["u_intensity"].value=float(max(intensity,0.0))
        p["u_bass"].value=float(np.clip(bass,0.0,1.0))
        p["u_mids"].value=float(np.clip(mids,0.0,1.0))
        p["u_highs"].value=float(np.clip(highs,0.0,1.0))
        p["u_beat"].value=float(np.clip(beat,0.0,1.0))
        p["u_drop"].value=float(np.clip(drop,0.0,1.0))
        p["u_mode"].value=POLAR_MODES.index(mode)
        p["u_palette"].value=POLAR_PALETTES.index(palette)
        self.fbo.use()
        self.ctx.viewport=(0,0,self.width,self.height)
        self.fbo.clear(0.0,0.0,0.0,1.0)
        self.vao.render(mode=self.moderngl.TRIANGLES)
        data=self.fbo.read(components=3,alignment=1)
        return np.flipud(np.frombuffer(data,dtype=np.uint8).reshape(self.height,self.width,3)).copy()

    def close(self) -> None:
        for obj in (self.fbo,self.target,self.vao,self.vbo,self.program):
            try:
                obj.release()
            except Exception:
                pass
        try:
            self.ctx.release()
        except Exception:
            pass


__all__=["POLAR_MODES","POLAR_PALETTES","PolarMathRenderer"]
