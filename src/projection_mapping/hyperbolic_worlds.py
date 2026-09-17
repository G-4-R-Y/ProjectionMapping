from __future__ import annotations

import numpy as np

from .graphics_runtime import create_context


HYPERBOLIC_MODES = (
    "poincare_geodesics",
    "circle_inversion",
    "mobius_flow",
    "schottky_orbits",
    "hyperbolic_kaleidoscope",
)
HYPERBOLIC_PALETTES = ("spectral", "electric", "solar", "bio", "ultraviolet", "icefire")

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
uniform int u_mode;
uniform int u_palette;
in vec2 v_uv;
out vec4 fragColor;
#define PI 3.141592653589793
#define TAU 6.283185307179586

vec2 cmul(vec2 a,vec2 b){return vec2(a.x*b.x-a.y*b.y,a.x*b.y+a.y*b.x);}
vec2 cdiv(vec2 a,vec2 b){float d=max(dot(b,b),1e-6);return vec2(a.x*b.x+a.y*b.y,a.y*b.x-a.x*b.y)/d;}
vec3 pal(float t){
    t=fract(t);
    if(u_palette==1)return .50+.50*cos(TAU*(vec3(1.0,.82,.63)*t+vec3(.56,.11,.02)));
    if(u_palette==2)return .50+.50*cos(TAU*(vec3(1.0,.74,.55)*t+vec3(.02,.08,.16)));
    if(u_palette==3)return .50+.50*cos(TAU*(vec3(.84,1.0,.70)*t+vec3(.42,.03,.20)));
    if(u_palette==4)return .50+.50*cos(TAU*(vec3(.94,.74,1.0)*t+vec3(.72,.21,.03)));
    if(u_palette==5)return .50+.50*cos(TAU*(vec3(1.0,.72,.82)*t+vec3(.55,.90,.12)));
    return .50+.50*cos(TAU*(vec3(1.0,.87,.72)*t+vec3(.01,.17,.44)));
}
float lineGlow(float d,float w){return exp(-d*d/(w*w));}
float ring(vec2 p,vec2 c,float r,float w){return lineGlow(abs(length(p-c)-r),w);}

vec3 poincare(vec2 p,float t){
    float rr=length(p);
    if(rr>1.04)return vec3(0.0);
    float chaos=clamp(u_chaos,0.0,2.5);
    float g=0.0;
    for(int i=0;i<7;i++){
        float a=float(i)*PI/7.0+t*(.025+.004*float(i));
        float ca=cos(a),sa=sin(a);
        vec2 q=vec2(ca*p.x+sa*p.y,-sa*p.x+ca*p.y);
        float off=.30+.08*sin(t*.13+float(i)*1.31)*chaos;
        float R=sqrt(1.0+off*off);
        g+=ring(q,vec2(off,0.0),R,.010+.002*chaos);
        g+=ring(q,vec2(-off,0.0),R,.010+.002*chaos);
    }
    float boundary=lineGlow(abs(rr-1.0),.008)*1.8;
    float metric=1.0/max(1.0-rr*rr,.06);
    float pulse=.70+.30*cos(log(metric+1.0)*5.0-t*.55);
    vec3 c=pal(rr*.22+t*.009)*g*pulse*.46;
    c+=pal(.68+t*.006)*boundary*.72;
    c+=vec3(1.0,.98,.95)*pow(clamp(g*.11,0.0,1.0),4.0)*.30;
    return c;
}

vec2 invertCircle(vec2 p,vec2 c,float r){vec2 d=p-c;return c+d*(r*r/max(dot(d,d),1e-5));}
vec3 inversion(vec2 p,float t){
    float chaos=clamp(u_chaos,0.0,2.5);
    vec2 q=p;
    float accum=0.0;
    for(int i=0;i<5;i++){
        float fi=float(i);
        vec2 c=.44*vec2(cos(fi*TAU/5.0+t*.035),sin(fi*TAU/5.0+t*.035));
        float r=.28+.03*sin(t*.11+fi*2.1)+.01*chaos;
        float d=length(q-c);
        accum+=lineGlow(abs(d-r),.012);
        if(d<r) q=invertCircle(q,c,r);
        q*=.91+.025*sin(fi+t*.07);
    }
    float grid=pow(.5+.5*cos(q.x*(18.0+3.0*chaos)+sin(q.y*7.0)),5.0);
    grid+=pow(.5+.5*cos(q.y*(17.0+2.0*chaos)+sin(q.x*8.0)),5.0);
    float core=exp(-dot(q,q)*2.4);
    vec3 c=pal(length(q)*.20+t*.011+accum*.04)*(grid*.42+accum*.34+core*.16);
    c+=vec3(1.0,.98,.94)*pow(clamp(accum*.22,0.0,1.0),3.0)*.35;
    return c;
}

vec3 mobius(vec2 p,float t){
    float chaos=clamp(u_chaos,0.0,2.5);
    float a=.22*sin(t*.09); float b=.34*cos(t*.071);
    vec2 A=vec2(cos(a),sin(a));
    vec2 B=vec2(.22*cos(t*.05),.22*sin(t*.061));
    vec2 C=vec2((.24+.05*chaos)*cos(t*.041+b),(.24+.05*chaos)*sin(t*.053-b));
    vec2 D=vec2(cos(-a),sin(-a));
    vec2 z=cdiv(cmul(A,p)+B,cmul(C,p)+D);
    float gx=pow(.5+.5*cos(z.x*(16.0+2.5*chaos)+t*.18),8.0);
    float gy=pow(.5+.5*cos(z.y*(16.0+2.5*chaos)-t*.16),8.0);
    float rings=pow(.5+.5*cos(length(z)*21.0-t*.25),10.0);
    float density=clamp(gx+gy+rings,0.0,2.4);
    vec3 c=pal(length(z)*.12+atan(z.y,z.x)/TAU+t*.008)*density*.56;
    c+=vec3(1.0,.98,.95)*pow(clamp(density*.38,0.0,1.0),5.0)*.22;
    return c;
}

vec3 schottky(vec2 p,float t){
    float chaos=clamp(u_chaos,0.0,2.5);
    vec2 q=p;
    float trap=10.0;
    for(int k=0;k<9;k++){
        float best=1e9; vec2 bc=vec2(0.0); float br=.0;
        for(int i=0;i<4;i++){
            float fi=float(i);
            float a=fi*PI*.5+t*.018*(1.0+.2*fi);
            vec2 c=.50*vec2(cos(a),sin(a));
            float r=.25+.018*sin(t*.09+fi*1.7)*chaos;
            float d=abs(length(q-c)-r);
            if(d<best){best=d;bc=c;br=r;}
        }
        trap=min(trap,best);
        if(length(q-bc)<br)q=invertCircle(q,bc,br);
        q*=.94;
    }
    float orbit=lineGlow(trap,.012+.002*chaos);
    float fil=.5+.5*cos((q.x+q.y)*14.0+sin((q.x-q.y)*7.0)-t*.22);
    fil=pow(fil,7.0);
    vec3 c=pal(length(q)*.18+t*.01+orbit*.08)*(orbit*.72+fil*.22);
    c+=vec3(1.0,.99,.96)*pow(orbit,4.0)*.42;
    return c;
}

vec3 kaleidoscope(vec2 p,float t){
    float r=length(p);
    if(r>1.04)return vec3(0.0);
    float chaos=clamp(u_chaos,0.0,2.5);
    float a=atan(p.y,p.x);
    float n=7.0+floor(chaos*2.0);
    float sector=abs(fract(a/TAU*n+.5)*2.0-1.0);
    float hyper=log((1.0+r)/max(1.0-r,.015));
    float petals=.5+.5*cos(n*a + sin(hyper*(2.2+.25*chaos)-t*.44)*2.0);
    float bands=.5+.5*cos(hyper*(5.0+chaos)-t*.70+sector*PI*2.0);
    float ridge=pow(clamp(1.0-abs(petals-bands),0.0,1.0),8.0);
    float spokes=pow(petals,12.0)*(.35+.65*bands);
    float boundary=lineGlow(abs(r-1.0),.008);
    vec3 c=pal(hyper*.045+sector*.16+t*.011)*(ridge*.82+spokes*.38);
    c+=pal(.72+t*.007)*boundary*.72;
    c+=vec3(1.0,.98,.94)*pow(clamp(ridge,0.0,1.0),4.0)*.24;
    return c;
}

void main(){
    vec2 p=(gl_FragCoord.xy*2.0-u_resolution)/u_resolution.y;
    vec3 col;
    if(u_mode==0)col=poincare(p,u_time);
    else if(u_mode==1)col=inversion(p,u_time);
    else if(u_mode==2)col=mobius(p,u_time);
    else if(u_mode==3)col=schottky(p,u_time);
    else col=kaleidoscope(p,u_time);
    col*=.82+.42*u_intensity;
    col=vec3(1.0)-exp(-max(col,vec3(0.0))*1.28);
    col=pow(col,vec3(.78));
    fragColor=vec4(clamp(col,0.0,1.0),1.0);
}
"""


class HyperbolicWorldRenderer:
    """GPU conformal/hyperbolic visual studies with reusable projector-safe controls."""

    def __init__(self, width: int, height: int, *, mode: str = "hyperbolic_kaleidoscope", palette: str = "spectral") -> None:
        import moderngl

        if mode not in HYPERBOLIC_MODES:
            raise ValueError(mode)
        if palette not in HYPERBOLIC_PALETTES:
            raise ValueError(palette)
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

    def render(self, *, t: float, mode: str | None = None, palette: str | None = None, intensity: float = 1.0, chaos: float = 1.0) -> np.ndarray:
        mode = mode or self.mode
        palette = palette or self.palette
        if mode not in HYPERBOLIC_MODES:
            raise ValueError(mode)
        if palette not in HYPERBOLIC_PALETTES:
            raise ValueError(palette)
        p = self.program
        p["u_time"].value = float(t)
        p["u_intensity"].value = float(max(intensity, 0.0))
        p["u_chaos"].value = float(np.clip(chaos, 0.0, 2.5))
        p["u_mode"].value = HYPERBOLIC_MODES.index(mode)
        p["u_palette"].value = HYPERBOLIC_PALETTES.index(palette)
        self.fbo.use()
        self.ctx.viewport = (0, 0, self.width, self.height)
        self.fbo.clear(0, 0, 0, 1)
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


__all__ = ["HYPERBOLIC_MODES", "HYPERBOLIC_PALETTES", "HyperbolicWorldRenderer"]
