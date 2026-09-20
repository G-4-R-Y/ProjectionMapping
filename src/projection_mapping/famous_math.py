from __future__ import annotations

import numpy as np

from .graphics_runtime import create_context


MATH_MODES = (
    "mandelbrot_julia",
    "newton_basins",
    "riemann_zeta",
    "chladni_plate",
    "quasicrystal_5fold",
    "logistic_bifurcation",
    "superformula",
    "complex_domain",
)

MATH_PALETTES = ("cyan_magenta", "spectral", "electric", "solar", "bio", "ultraviolet", "icefire")

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

float sat(float x){ return clamp(x,0.0,1.0); }
vec2 cmul(vec2 a,vec2 b){ return vec2(a.x*b.x-a.y*b.y,a.x*b.y+a.y*b.x); }
vec2 cdiv(vec2 a,vec2 b){
    float d=max(dot(b,b),1e-9);
    return vec2(a.x*b.x+a.y*b.y,a.y*b.x-a.x*b.y)/d;
}
vec2 cpow2(vec2 z){ return cmul(z,z); }
vec2 cpow3(vec2 z){ return cmul(cmul(z,z),z); }

vec3 cosinePalette(float t,vec3 a,vec3 b,vec3 c,vec3 d){
    return a+b*cos(TAU*(c*t+d));
}
vec3 palette(float t){\n    if(u_palette==0) return vec3(.5+.5*cos(TAU*(t+.50)), .5+.5*cos(TAU*(t+.00)), .5+.5*cos(TAU*(t+.50)));
    t=fract(t);
    if(u_palette==6) return cosinePalette(t,vec3(.50),vec3(.50),vec3(1.0,.82,.62),vec3(.56,.10,.02));
    if(u_palette==6) return cosinePalette(t,vec3(.55,.32,.16),vec3(.48,.36,.20),vec3(1.0,.78,.55),vec3(.02,.05,.12));
    if(u_palette==6) return cosinePalette(t,vec3(.28,.50,.37),vec3(.31,.50,.48),vec3(.86,1.0,.72),vec3(.42,.03,.20));
    if(u_palette==6) return cosinePalette(t,vec3(.45,.30,.62),vec3(.50,.45,.42),vec3(.92,.72,1.0),vec3(.72,.21,.03));
    if(u_palette==6) return cosinePalette(t,vec3(.48,.42,.45),vec3(.48,.47,.52),vec3(1.0,.72,.82),vec3(.55,.90,.12));
    return cosinePalette(t,vec3(.54,.50,.55),vec3(.46,.48,.45),vec3(1.0,.87,.72),vec3(.01,.17,.44));
}

float hash21(vec2 p){
    p=fract(p*vec2(123.34,345.45));
    p+=dot(p,p+34.345);
    return fract(p.x*p.y);
}

vec3 mandelbrotJulia(vec2 p,float t){
    float chaos=clamp(u_chaos,0.0,2.5);
    p*=.86+.12*sin(t*.071)+.08*u_bass;
    p*=mat2(cos(t*.025),-sin(t*.025),sin(t*.025),cos(t*.025));
    p+=vec2(-.25+.07*sin(t*.043),.03*cos(t*.037));
    float morph=.5+.5*sin(t*.082);
    morph=smoothstep(.16,.84,morph);
    vec2 juliaC=vec2(-.745+.065*cos(t*.091),.113+.075*sin(t*.067));
    vec2 c=mix(p,juliaC,morph);
    vec2 z=mix(vec2(0.0),p,morph);
    float trap=10.0;
    float escaped=0.0;
    float it=0.0;
    for(int i=0;i<72;i++){
        z=cpow2(z)+c;
        float r2=dot(z,z);
        trap=min(trap,abs(length(z)-(.52+.08*sin(t*.11))));
        if(escaped<.5 && r2>64.0){
            escaped=1.0;
            it=float(i)+1.0-log2(log2(max(length(z),1.0001)));
        }
    }
    float interior=1.0-escaped;
    float bands=.5+.5*cos(it*.48+t*.31+chaos*sin(it*.21));
    float filaments=exp(-trap*(68.0+28.0*chaos));
    vec3 col=palette(it*.021+t*.012+trap*.7)*(.28+.92*bands)*escaped;
    col+=palette(.68+t*.018+trap*2.0)*filaments*(.55+.55*chaos);
    col+=vec3(.05,.008,.12)*interior;
    col+=vec3(1.0,.97,.92)*pow(filaments,4.0)*(.20+.38*u_drop);
    return col;
}

vec3 newtonBasins(vec2 p,float t){
    float chaos=clamp(u_chaos,0.0,2.5);
    p*=1.18+.08*sin(t*.09);
    p*=mat2(cos(t*.035),-sin(t*.035),sin(t*.035),cos(t*.035));
    vec2 z=p+(.025+.028*chaos)*vec2(sin(p.y*5.0+t*.17),cos(p.x*4.0-t*.13));
    float conv=28.0;
    float minStep=10.0;
    for(int i=0;i<28;i++){
        vec2 z2=cpow2(z);
        vec2 f=cmul(z2,z)-vec2(1.0,0.0);
        vec2 fp=3.0*z2;
        vec2 step=cdiv(f,fp);
        z-=step;
        minStep=min(minStep,length(step));
        if(length(step)<1e-5) conv=min(conv,float(i));
    }
    vec2 r0=vec2(1.0,0.0);
    vec2 r1=vec2(-.5,.8660254);
    vec2 r2=vec2(-.5,-.8660254);
    float d0=length(z-r0),d1=length(z-r1),d2=length(z-r2);
    float basin=0.0;
    float md=d0;
    if(d1<md){md=d1;basin=1.0;}
    if(d2<md){md=d2;basin=2.0;}
    float boundary=exp(-minStep*(90.0-18.0*chaos));
    float rings=.5+.5*cos(conv*.95+t*.28);
    vec3 col=palette(basin/3.0+conv*.016+t*.013)*(.35+.82*rings);
    col*=.55+.45*exp(-md*8.0);
    col+=palette(.82+basin*.11+t*.01)*boundary*(.48+.30*chaos);
    col+=vec3(1.0,.98,.92)*pow(boundary,5.0)*.24;
    return col;
}

vec2 zetaEta(vec2 s){
    vec2 eta=vec2(0.0);
    for(int n=1;n<=28;n++){
        float fn=float(n);
        float ln=log(fn);
        float amp=exp(-s.x*ln);
        float ph=-s.y*ln;
        float signv=(n%2==0)?-1.0:1.0;
        eta+=signv*amp*vec2(cos(ph),sin(ph));
    }
    float ln2=log(2.0);
    float amp=exp((1.0-s.x)*ln2);
    float ph=-s.y*ln2;
    vec2 denom=vec2(1.0,0.0)-amp*vec2(cos(ph),sin(ph));
    return cdiv(eta,denom);
}
vec3 riemannZeta(vec2 p,float t){
    float chaos=clamp(u_chaos,0.0,2.5);
    float sigma=.62+p.x*.72+.035*sin(p.y*4.0+t*.14)*chaos;
    float tau=p.y*(13.0+2.2*chaos)+t*(.26+.08*u_mids);
    vec2 z=zetaEta(vec2(sigma,tau));
    float mag=length(z);
    float phase=atan(z.y,z.x)/TAU;
    float zeroGlow=exp(-mag*(2.8+1.2*chaos));
    float logBands=.5+.5*cos(log(max(mag,1e-4))*5.2+phase*TAU*2.0);
    float critical=exp(-abs(sigma-.5)*10.0)*.12;
    vec3 col=palette(phase+t*.009+log(mag+1.0)*.08)*(.24+.84*logBands);
    col*=.42+.58*sat(mag*.55);
    col+=palette(.72+phase)*zeroGlow*(.75+.48*u_highs);
    col+=vec3(.18,.34,.75)*critical;
    col+=vec3(1.0,.97,.93)*pow(zeroGlow,5.0)*(.10+.35*u_drop);
    return col;
}

vec3 chladniPlate(vec2 p,float t){
    float chaos=clamp(u_chaos,0.0,2.5);
    vec2 q=p*(1.55+.08*u_bass);
    float x=(q.x+.5)*PI;
    float y=(q.y+.5)*PI;
    float a=sin(3.0*x)*sin(5.0*y)-sin(5.0*x)*sin(3.0*y);
    float b=sin(4.0*x)*sin(7.0*y)-sin(7.0*x)*sin(4.0*y);
    float c=sin(2.0*x)*sin(9.0*y)-sin(9.0*x)*sin(2.0*y);
    float mixv=.5+.5*sin(t*.17);
    float field=mix(a,b,smoothstep(.15,.85,mixv));
    field+=c*(.08+.12*chaos)*sin(t*.11);
    field+=.08*chaos*sin((q.x+q.y)*14.0-t*.41);
    float node=exp(-abs(field)*(22.0+11.0*chaos));
    float bands=.5+.5*cos(field*(15.0+6.0*chaos)-t*.52);
    float rim=exp(-18.0*abs(max(abs(q.x),abs(q.y))-.83));
    vec3 col=palette(field*.14+t*.018+length(q)*.16)*(bands*.34+node*1.25);
    col+=palette(.66+t*.012)*rim*.36;
    col+=vec3(1.0,.98,.94)*pow(node,6.0)*(.18+.42*u_beat);
    return col;
}

vec3 quasicrystal(vec2 p,float t){
    float chaos=clamp(u_chaos,0.0,2.5);
    vec2 q=p*(7.0+1.4*u_bass);
    float sum=0.0;
    float sum2=0.0;
    for(int i=0;i<5;i++){
        float a=float(i)*TAU/5.0+t*.031;
        vec2 d=vec2(cos(a),sin(a));
        float ph=dot(q,d)+t*(.17+.025*float(i));
        sum+=cos(ph+chaos*.28*sin(ph*.63+t*.09));
        sum2+=cos(ph*1.61803398875-float(i)*.73-t*.11);
    }
    sum/=5.0;
    sum2/=5.0;
    float field=mix(sum,sum2,.26+.12*sin(t*.07));
    float ridge=pow(sat(1.0-abs(field)*1.55),5.0);
    float cells=pow(.5+.5*cos(field*(13.0+3.0*chaos)+t*.21),9.0);
    float radial=.5+.5*cos(length(q)*1.9-t*.38);
    vec3 col=palette(field*.28+t*.012+sum2*.11)*(ridge*1.10+cells*.28*radial);
    float stars=pow(hash21(floor((p+.5)*u_resolution/5.0)),40.0);
    col+=palette(.83+t*.01)*stars*.20*u_highs;
    return col;
}

vec3 logisticBifurcation(vec2 p,float t){
    float chaos=clamp(u_chaos,0.0,2.5);
    float r=2.82+(p.x+.72)*.84;
    r+=.012*sin(t*.09+p.y*5.0)*chaos;
    float target=.5-p.y*.58;
    float x=.431+0.02*sin(t*.07);
    for(int i=0;i<36;i++) x=r*x*(1.0-x);
    float mind=10.0;
    float lyap=0.0;
    for(int i=0;i<44;i++){
        x=r*x*(1.0-x);
        mind=min(mind,abs(x-target));
        lyap+=log(abs(r*(1.0-2.0*x))+1e-5);
    }
    lyap/=44.0;
    float line=exp(-mind*(210.0+80.0*chaos));
    float chaosBand=smoothstep(-.08,.18,lyap);
    float periodBands=.5+.5*cos((x+target)*34.0-t*.33);
    vec3 col=palette(.12+r*.17+lyap*.08+t*.009)*line*(.78+.44*periodBands);
    col+=palette(.70+lyap*.12)*line*chaosBand*.42;
    float axis=exp(-abs(p.y+.36)*150.0)*.10;
    col+=vec3(.30,.42,.72)*axis;
    col+=vec3(1.0,.98,.94)*pow(line,7.0)*(.12+.30*u_beat);
    return col;
}

float superR(float a,float m,float n1,float n2,float n3){
    float t1=pow(abs(cos(m*a*.25)),n2);
    float t2=pow(abs(sin(m*a*.25)),n3);
    return pow(max(t1+t2,1e-5),-1.0/n1);
}
vec3 superformula(vec2 p,float t){
    float chaos=clamp(u_chaos,0.0,2.5);
    float r=length(p)+1e-5;
    float a=atan(p.y,p.x);
    float r5=superR(a,5.0,0.34+.08*sin(t*.13),1.55+.20*chaos,1.55+.20*chaos);
    float r8=superR(a,8.0,0.54+.10*cos(t*.11),1.15+.18*chaos,1.75+.16*chaos);
    float morph=.5+.5*sin(t*.083);
    float shape=mix(r5,r8,smoothstep(.12,.88,morph));
    shape*=.31+.035*sin(t*.21)+.025*u_bass;
    float d=r-shape;
    float edge=exp(-abs(d)*(62.0+16.0*chaos));
    float inner=0.0;
    for(int i=1;i<=5;i++){
        float fi=float(i);
        float rr=shape*(.20+.14*fi);
        inner+=exp(-abs(r-rr)*(54.0-fi*3.0))*(.22+.08*fi);
    }
    float spokes=pow(.5+.5*cos(a*(10.0+2.0*floor(chaos+.5))+t*.29),18.0)*exp(-r*1.6);
    vec3 col=palette(a/TAU+t*.016+r*.24)*(edge*1.20+inner*.42+spokes*.18);
    col+=vec3(1.0,.98,.93)*pow(edge,6.0)*(.20+.32*u_drop);
    return col;
}

vec2 csin(vec2 z){ return vec2(sin(z.x)*cosh(z.y),cos(z.x)*sinh(z.y)); }
vec3 complexDomain(vec2 p,float t){
    float chaos=clamp(u_chaos,0.0,2.5);
    vec2 z=p*(2.0+.15*u_bass);
    z*=mat2(cos(t*.021),-sin(t*.021),sin(t*.021),cos(t*.021));
    vec2 z2=cpow2(z);
    vec2 inv=cdiv(vec2(.35+.08*sin(t*.09),.06*cos(t*.07)),z+vec2(.025,0.0));
    vec2 w=csin(z2+inv+(.06+.08*chaos)*vec2(sin(z.y*4.0+t*.12),cos(z.x*4.0-t*.10)));
    float mag=length(w);
    float ph=atan(w.y,w.x)/TAU;
    float argBands=.5+.5*cos(ph*TAU*12.0);
    float magBands=.5+.5*cos(log(max(mag,1e-4))*8.0);
    float poles=sat(mag/4.0);
    vec3 col=palette(ph+t*.011)*(0.22+.52*argBands+.38*magBands);
    col*=.56+.44*sat(log(mag+1.0));
    col+=palette(.74+ph*.17)*pow(poles,.65)*.22;
    float realAxis=exp(-abs(w.y)*7.5)*.16;
    col+=vec3(.82,.92,1.0)*realAxis;
    return col;
}

void main(){
    vec2 p=(gl_FragCoord.xy*2.0-u_resolution)/u_resolution.y;
    float t=u_time;
    vec3 col;
    if(u_mode==0) col=mandelbrotJulia(p,t);
    else if(u_mode==1) col=newtonBasins(p,t);
    else if(u_mode==2) col=riemannZeta(p,t);
    else if(u_mode==3) col=chladniPlate(p,t);
    else if(u_mode==4) col=quasicrystal(p,t);
    else if(u_mode==5) col=logisticBifurcation(p,t);
    else if(u_mode==6) col=superformula(p,t);
    else col=complexDomain(p,t);

    col*=.82+.42*u_intensity;
    col*=1.0+.16*u_beat+.26*u_drop;
    float r=length(p);
    float vignette=1.0-smoothstep(.28,1.42,r);
    col*=mix(.73,1.0,vignette);
    col=vec3(1.0)-exp(-max(col,vec3(0.0))*1.18);
    col=pow(col,vec3(.79));
    fragColor=vec4(clamp(col,0.0,1.0),1.0);
}
"""


class FamousMathRenderer:
    """Projector-native GPU studies built from famous mathematical systems.

    The modes are deliberately different families rather than palette variants: complex dynamics,
    Newton root basins, a finite Dirichlet-eta approximation to zeta domain coloring, Chladni nodal
    modes, five-fold quasicrystal interference, the logistic-map bifurcation diagram, Gielis'
    superformula, and complex-function domain coloring.
    """

    def __init__(
        self,
        width: int,
        height: int,
        *,
        mode: str = "mandelbrot_julia",
        palette: str = "cyan_magenta",
    ) -> None:
        import moderngl

        if mode not in MATH_MODES:
            raise ValueError(f"unknown math mode: {mode}")
        if palette not in MATH_PALETTES:
            raise ValueError(f"unknown math palette: {palette}")
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
        chaos: float = 1.0,
        signals=None,
    ) -> np.ndarray:
        mode = mode or self.mode
        palette = palette or self.palette
        if mode not in MATH_MODES:
            raise ValueError(mode)
        if palette not in MATH_PALETTES:
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
        p["u_mode"].value = MATH_MODES.index(mode)
        p["u_palette"].value = MATH_PALETTES.index(palette)
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


__all__ = ["MATH_MODES", "MATH_PALETTES", "FamousMathRenderer"]
