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
uniform float u_chaos;
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

mat2 rot2(float a) {
    float c=cos(a), s=sin(a);
    return mat2(c,-s,s,c);
}

vec2 cmul(vec2 a, vec2 b) {
    return vec2(a.x*b.x-a.y*b.y, a.x*b.y+a.y*b.x);
}

vec2 harmonic(vec2 unitDir, int n) {
    vec2 z=vec2(1.0,0.0);
    for(int i=0;i<32;i++) {
        if(i<n) z=cmul(z,unitDir);
    }
    return z;
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

vec2 analyticWarp(vec2 p, float t) {
    float chaos=clamp(u_chaos,0.0,2.5);
    float r=length(p)+1e-5;
    vec2 d=p/r;
    vec2 h3=harmonic(d,3);
    vec2 h7=harmonic(d,7);
    float swirl=chaos*(.020*sin(r*10.0-t*.31)+.016*h3.y+.010*h7.x);
    vec2 q=rot2(swirl)*p;
    vec2 cart=vec2(
        sin(q.y*7.0+t*.27)+.45*sin(q.y*15.0-t*.19),
        cos(q.x*8.0-t*.23)+.40*cos(q.x*13.0+t*.17)
    );
    q += cart*(.004+.010*chaos);
    return q;
}

vec3 roseLattice(vec2 p, float t) {
    float chaos=clamp(u_chaos,0.0,2.5);
    float r=length(p)+1e-5;
    float a=atan(p.y,p.x);
    vec2 dir=p/r;
    vec2 h5=harmonic(dir,5);
    vec2 h9=harmonic(dir,9);
    vec2 h17=harmonic(dir,17);
    vec3 col=vec3(0.0);
    float bass=.06*u_bass;
    for(int i=0;i<5;i++) {
        float fi=float(i);
        float k=5.0+fi*2.0;
        float phase=t*(.20+fi*.045)*(mod(fi,2.0)<1.0?1.0:-1.0);
        float rose=.23+fi*.105+(.072+bass*.42)*cos(k*a+phase);
        rose+=.018*sin((k+3.0)*a-t*.31+fi);
        rose+=chaos*(.008*sin((k+8.0)*a+t*.21+fi)+.006*cos((k*2.0+1.0)*a-t*.17));
        float d=r-rose;
        float line=glowLine(d,.0030+fi*.0004,66.0-fi*5.0);
        float pulse=.70+.30*cos(TAU*(r*1.35-t*.065-fi*.08)+h9.y*.45*chaos);
        float hueAxis=.5+.5*(.55*h5.x+.30*h9.y+.15*h17.x);
        vec3 hue=palette(fi*.135+hueAxis*.15+t*.018+u_mids*.08);
        col+=vividGlow(hue,line*pulse*(.72+.18*fi),aaLine(d,.0022)*(.30+.13*fi));
    }
    float spokes=pow(.5+.5*cos(a*24.0+t*.18+h5.y*chaos*.7),18.0)*exp(-r*1.8);
    col+=palette(.64+.13*h9.x+t*.01)*spokes*(.12+.42*u_highs+.10*chaos);
    float fractured=pow(.5+.5*cos(r*46.0-t*.52+h17.y*2.2),24.0)*exp(-r*1.2);
    col+=palette(.22+.10*h17.x+t*.015)*fractured*.12*chaos;
    float center=exp(-r*10.0)*(.18+.60*u_beat+.32*u_drop);
    col+=vec3(1.0,.96,.92)*center;
    return col;
}

vec2 hypoPoint(float q, float R, float rr, float d, float spin) {
    float k=(R-rr)/rr;
    return vec2(
        (R-rr)*cos(q+spin)+d*cos(k*q-spin*1.41),
        (R-rr)*sin(q+spin)-d*sin(k*q-spin*1.41)
    );
}

vec3 hypotrochoidEngine(vec2 p, float t) {
    float chaos=clamp(u_chaos,0.0,2.5);
    vec3 col=vec3(0.0);
    float spin=t*.13+u_bass*.08;
    for(int layer=0;layer<4;layer++) {
        float fl=float(layer);
        float R=.37+fl*.105;
        float rr=.115+fl*.017;
        float d=.18+fl*.031+.035*u_mids;
        float md=10.0;
        vec2 prev=hypoPoint(0.0,R,rr,d,spin*(1.0+fl*.17));
        for(int j=1;j<=52;j++) {
            float q=TAU*float(j)/52.0;
            vec2 cur=hypoPoint(q,R,rr,d,spin*(1.0+fl*.17));
            cur+=vec2(sin(q*7.0+t*.21+fl),cos(q*5.0-t*.17+fl))*.006*chaos*(1.0+fl*.18);
            vec2 pa=p-prev, ba=cur-prev;
            float h=clamp(dot(pa,ba)/max(dot(ba,ba),1e-6),0.0,1.0);
            md=min(md,length(pa-ba*h));
            prev=cur;
        }
        float g=exp(-md*(58.0-fl*6.0))+aaLine(md,.0032)*1.18;
        vec3 hue=palette(.12+fl*.19+t*.022+u_highs*.08);
        col+=vividGlow(hue,g*(1.03-fl*.10),aaLine(md,.0021)*.44);
    }
    float r=length(p)+1e-5;
    float a=atan(p.y,p.x);
    vec2 dir=p/r;
    vec2 h6=harmonic(dir,6);
    vec2 h18=harmonic(dir,18);
    float gear=pow(.5+.5*cos(a*18.0-t*.36+u_bass*2.4*h6.y+chaos*.8*h18.y),18.0);
    float ring=exp(-70.0*abs(r-(.63+.018*sin(t*.29)+.008*chaos*h6.x)));
    col+=palette(.38+.12*h6.x+t*.01)*gear*ring*(.65+.55*u_beat+.12*chaos);
    col+=vec3(1.0,.95,.90)*exp(-r*13.0)*(.18+.72*u_drop);
    return col;
}

vec3 logSpiralInterference(vec2 p, float t) {
    float chaos=clamp(u_chaos,0.0,2.5);
    float r=length(p)+.012;
    float a=atan(p.y,p.x);
    vec2 dir=p/r;
    vec2 h3=harmonic(dir,3);
    vec2 h7=harmonic(dir,7);
    vec2 h9=harmonic(dir,9);
    vec2 h13=harmonic(dir,13);
    float lr=log(r);
    float warp=.16*h7.y+.08*harmonic(dir,11).y;
    warp+=chaos*(.08*h3.x+.05*h13.y)*sin(r*9.0-t*.27);
    float ph1=14.0*lr-7.0*a-t*1.15+warp*4.0;
    float ph2=11.0*lr+9.0*a+t*.84-warp*3.2;
    float ph3=18.0*lr-13.0*a-t*.63+warp*5.1;
    float s1=pow(.5+.5*cos(ph1),18.0);
    float s2=pow(.5+.5*cos(ph2),16.0);
    float s3=pow(.5+.5*cos(ph3),22.0)*chaos*.55;
    float interference=pow(sat(s1+s2+s3*.55),1.35);
    float rings=pow(.5+.5*cos(r*(48.0+10.0*u_bass)-t*1.7+h3.y*chaos*2.0),22.0);
    float radial=exp(-r*(1.18-.22*u_bass));
    vec3 c1=palette(.18+.12*h7.x+r*.24+t*.025);
    vec3 c2=palette(.62+.11*h9.y+r*.41-t*.019);
    vec3 c3=palette(.36+.10*h13.x-r*.18+t*.013);
    vec3 col=(c1*s1+c2*s2+c3*s3)*radial*1.22;
    col+=palette(r*.52+t*.016)*rings*(.20+.52*u_beat+.12*chaos)*radial;
    float core=exp(-r*9.5)*(1.0+.85*u_drop);
    col+=vec3(1.0,.95,.90)*core*.50;
    col+=palette(t*.03+.82)*interference*(.10+.22*u_highs);
    return col;
}

vec3 phyllotaxisReactor(vec2 p, float t) {
    float chaos=clamp(u_chaos,0.0,2.5);
    vec3 col=vec3(0.0);
    float best=10.0;
    float bestId=0.0;
    float scale=.90+.06*sin(t*.17);
    for(int i=1;i<=96;i++) {
        float fi=float(i);
        float rn=sqrt(fi/96.0)*.84*scale;
        rn+=chaos*.010*sin(fi*.91+t*.37)+chaos*.008*sin(fi*.23-t*.19);
        float a=fi*GOLDEN_ANGLE+t*(.12+.035*u_mids)+.14*sin(fi*.31+t*.23);
        a+=chaos*(.018*sin(fi*.73+t*.11)+.012*sin(fi*.17-t*.29));
        vec2 q=vec2(cos(a),sin(a))*rn;
        float d=length(p-q);
        if(d<best){best=d;bestId=fi;}
    }
    float dotCore=exp(-best*205.0);
    float dotHalo=exp(-best*58.0);
    float idn=bestId/96.0;
    vec3 hue=palette(idn*.92+t*.018+u_bass*.10);
    col+=vividGlow(hue,dotHalo*1.05,dotCore*.88);

    float r=length(p)+1e-5;
    float a=atan(p.y,p.x);
    vec2 dir=p/r;
    vec2 h5=harmonic(dir,5);
    vec2 h13=harmonic(dir,13);
    vec2 h21=harmonic(dir,21);
    float arms=pow(.5+.5*cos(a*13.0-r*33.0+t*.48+chaos*h5.y*1.2),18.0);
    float ring=pow(.5+.5*cos(r*54.0-t*.75+h21.x*chaos*.85),28.0);
    col+=palette(.31+.12*h13.x+r*.35+t*.011)*arms*ring*(.12+.35*u_highs+.08*chaos);
    float filigree=pow(.5+.5*h21.y,18.0)*exp(-r*1.8)*chaos*.16;
    col+=palette(.72+.08*h5.x+t*.014)*filigree;
    float reactor=exp(-r*12.0)*(.25+.95*u_beat+.65*u_drop);
    col+=vec3(1.0,.94,.88)*reactor;
    return col;
}

float besselJ0(float x) {
    float ax=abs(x);
    if(ax<3.0) {
        float y=x*x;
        return 1.0-y*.25+y*y*.015625-y*y*y*.0004340278+y*y*y*y*.00000678168;
    }
    return sqrt(2.0/(PI*ax))*cos(ax-PI*.25);
}

vec3 besselWaveChamber(vec2 p, float t) {
    float chaos=clamp(u_chaos,0.0,2.5);
    float r=length(p)+1e-5;
    float a=atan(p.y,p.x);
    vec2 dir=p/r;
    vec2 h6=harmonic(dir,6);
    vec2 h12=harmonic(dir,12);
    vec2 h18=harmonic(dir,18);
    vec3 col=vec3(0.0);
    for(int i=0;i<5;i++) {
        float fi=float(i);
        float k=13.0+fi*5.5+u_bass*3.0;
        float angularPhase=a*(4.0+fi*2.0)+t*.19+chaos*(h6.y+h12.x*.5)*.55;
        float j=besselJ0(k*r+sin(angularPhase)*(.9+fi*.18));
        float target=.18-fi*.044;
        float contour=pow(sat(1.0-abs(j-target)*7.6),6.0);
        float node=pow(abs(j),3.0);
        float angular=.55+.45*cos(a*(6.0+fi*4.0)+t*(.16+fi*.04)+h18.y*chaos*.6);
        float hueAxis=.5+.5*(.55*h6.x+.30*h12.y+.15*h18.x);
        vec3 hue=palette(fi*.16+r*.26+hueAxis*.10+t*.012);
        col+=hue*(contour*.82+node*.12)*angular;
    }
    float lattice=pow(.5+.5*cos(r*68.0+h12.y*(2.0+chaos*1.2)-t*.52),24.0);
    col+=palette(.48+.11*h12.x+t*.02)*lattice*exp(-r*.82)*(.16+.44*u_highs+.08*chaos);
    float crosswave=pow(.5+.5*cos(r*39.0-t*.31+h18.x*3.0),20.0)*pow(.5+.5*h6.y,8.0);
    col+=palette(.18+.09*h18.y+t*.017)*crosswave*exp(-r*1.1)*.11*chaos;
    float center=exp(-r*8.2)*(.12+.50*u_beat+.72*u_drop);
    col+=vec3(1.0,.96,.94)*center;
    return col;
}

void main() {
    vec2 p=(gl_FragCoord.xy*2.0-u_resolution)/u_resolution.y;
    float t=u_time;
    p*=.94+.035*sin(t*.17)-.025*u_bass;
    float baseRot=.025*sin(t*.11)+.018*u_mids;
    p=rot2(baseRot)*p;
    p=analyticWarp(p,t);

    vec3 col;
    if(u_mode==0) col=roseLattice(p,t);
    else if(u_mode==1) col=hypotrochoidEngine(p,t);
    else if(u_mode==2) col=logSpiralInterference(p,t);
    else if(u_mode==3) col=phyllotaxisReactor(p,t);
    else col=besselWaveChamber(p,t);

    col*=.86+.42*u_intensity;
    col*=1.0+.18*u_beat+.28*u_drop;
    float r=length(p);
    float vignette=1.0-smoothstep(.12,1.25,r);
    col*=mix(.70,1.0,vignette);
    col=vec3(1.0)-exp(-max(col,vec3(0.0))*1.16);
    col=pow(col,vec3(.78));
    float peak=max(col.r,max(col.g,col.b));
    col*=smoothstep(.006,.035,peak);
    fragColor=vec4(clamp(col,0.0,1.0),1.0);
}
"""


class PolarMathRenderer:
    """Five vivid analytic polar-coordinate shader scenes.

    The renderer deliberately uses mathematical contours + emissive inverse-distance/glow language
    instead of fog-heavy procedural backgrounds. ``chaos`` adds analytic cross-harmonic warping
    without replacing the scene's underlying equation family with generic noise.
    """

    def __init__(
        self,
        width: int,
        height: int,
        *,
        mode: str = "rose_lattice",
        palette: str = "spectral",
    ) -> None:
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
        vertices = np.asarray([-1.0, -1.0, 3.0, -1.0, -1.0, 3.0], dtype="f4")
        self.vbo = self.ctx.buffer(vertices.tobytes())
        self.vao = self.ctx.simple_vertex_array(self.program, self.vbo, "in_pos")
        self.target = self.ctx.texture((self.width, self.height), 3, dtype="f1")
        self.fbo = self.ctx.framebuffer(color_attachments=[self.target])
        self.program["u_resolution"].value = (float(self.width), float(self.height))

    def render(
        self,
        *,
        t: float,
        mode: str | None = None,
        palette: str | None = None,
        intensity: float = 1.0,
        chaos: float = 0.85,
        signals=None,
    ) -> np.ndarray:
        mode = mode or self.mode
        palette = palette or self.palette
        if mode not in POLAR_MODES:
            raise ValueError(mode)
        if palette not in POLAR_PALETTES:
            raise ValueError(palette)
        bass = mids = highs = beat = drop = 0.0
        if signals is not None:
            bass = float(getattr(signals, "bass", 0.0))
            mids = float(getattr(signals, "mids", 0.0))
            highs = float(getattr(signals, "highs", 0.0))
            beat = float(getattr(signals, "beat", 0.0))
            drop = float(getattr(signals, "drop", 0.0))
        p = self.program
        p["u_time"].value = float(t)
        p["u_intensity"].value = float(max(intensity, 0.0))
        p["u_chaos"].value = float(np.clip(chaos, 0.0, 2.5))
        p["u_bass"].value = float(np.clip(bass, 0.0, 1.0))
        p["u_mids"].value = float(np.clip(mids, 0.0, 1.0))
        p["u_highs"].value = float(np.clip(highs, 0.0, 1.0))
        p["u_beat"].value = float(np.clip(beat, 0.0, 1.0))
        p["u_drop"].value = float(np.clip(drop, 0.0, 1.0))
        p["u_mode"].value = POLAR_MODES.index(mode)
        p["u_palette"].value = POLAR_PALETTES.index(palette)
        self.fbo.use()
        self.ctx.viewport = (0, 0, self.width, self.height)
        self.fbo.clear(0.0, 0.0, 0.0, 1.0)
        self.vao.render(mode=self.moderngl.TRIANGLES)
        data = self.fbo.read(components=3, alignment=1)
        return np.flipud(
            np.frombuffer(data, dtype=np.uint8).reshape(self.height, self.width, 3)
        ).copy()

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


__all__ = ["POLAR_MODES", "POLAR_PALETTES", "PolarMathRenderer"]
