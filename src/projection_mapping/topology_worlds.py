from __future__ import annotations

import numpy as np

from .graphics_runtime import create_context


TOPOLOGY_MODES = (
    "torus_knot",
    "hopf_link_field",
    "gyroid",
    "schwarz_p",
    "helicoid",
    "mobius_ribbon",
)
TOPOLOGY_PALETTES = ("cyan_magenta", "spectral", "electric", "solar", "bio", "ultraviolet", "icefire")

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
uniform float u_param_a;
uniform float u_param_b;
uniform int u_mode;
uniform int u_palette;
in vec2 v_uv;
out vec4 fragColor;
#define PI 3.141592653589793
#define TAU 6.283185307179586

vec3 pal(float t){
    if(u_palette==0) return vec3(.5+.5*cos(TAU*(t+.50)), .5+.5*cos(TAU*(t+.00)), .5+.5*cos(TAU*(t+.50)));
    t=fract(t);
    if(u_palette==2)$1 .50+.50*cos(TAU*(vec3(1.0,.82,.63)*t+vec3(.56,.11,.02)));
    if(u_palette==3)$1 .50+.50*cos(TAU*(vec3(1.0,.74,.55)*t+vec3(.02,.08,.16)));
    if(u_palette==4)$1 .50+.50*cos(TAU*(vec3(.84,1.0,.70)*t+vec3(.42,.03,.20)));
    if(u_palette==5)$1 .50+.50*cos(TAU*(vec3(.94,.74,1.0)*t+vec3(.72,.21,.03)));
    if(u_palette==6)$1 .50+.50*cos(TAU*(vec3(1.0,.72,.82)*t+vec3(.55,.90,.12)));
    return .50+.50*cos(TAU*(vec3(1.0,.87,.72)*t+vec3(.01,.17,.44)));
}

vec3 rotate3(vec3 p,float ax,float ay){
    float cx=cos(ax),sx=sin(ax),cy=cos(ay),sy=sin(ay);
    p.yz=mat2(cx,-sx,sx,cx)*p.yz;
    p.xz=mat2(cy,-sy,sy,cy)*p.xz;
    return p;
}
vec2 project3(vec3 p){
    float z=2.8+p.z;
    return p.xy/max(z,.55)*1.65;
}
float glow(float d,float w){return exp(-d/max(w,1e-5));}

vec3 torusKnot(vec2 p,float t){
    float pFreq=max(2.0,floor(2.0+u_param_a*4.0));
    float qFreq=max(3.0,floor(3.0+u_param_b*5.0));
    float minD=10.0;
    float phase=0.0;
    for(int i=0;i<72;i++){
        float u=TAU*float(i)/72.0;
        float rr=.62+.22*cos(qFreq*u);
        vec3 q=vec3(rr*cos(pFreq*u),rr*sin(pFreq*u),.22*sin(qFreq*u));
        q=rotate3(q,t*.17+.35,t*.11+.72);
        vec2 s=project3(q);
        float d=length(p-s);
        if(d<minD){minD=d;phase=u/TAU;}
    }
    float line=glow(minD,.012+.006*u_chaos);
    float halo=glow(minD,.055+.016*u_chaos);
    vec3 c=pal(phase+t*.008)*(line*.90+halo*.28);
    c+=vec3(1.0,.98,.94)*pow(line,5.0)*.24;
    return c;
}

vec3 hopfLinks(vec2 p,float t){
    float e=0.0; float cp=0.0;
    for(int j=0;j<11;j++){
        float fj=float(j);
        float tilt=(fj-5.0)*.095;
        float radius=.42+.035*sin(fj*1.71+t*.07);
        for(int i=0;i<48;i++){
            float u=TAU*float(i)/48.0;
            vec3 q=vec3(radius*cos(u),radius*sin(u),.22*sin(u+fj*.57));
            q.x+=.27*cos(fj*TAU/11.0);
            q.y+=.27*sin(fj*TAU/11.0);
            q=rotate3(q,t*.09+tilt,t*.13+fj*.11);
            float d=length(p-project3(q));
            float g=glow(d,.012+.002*u_chaos);
            if(g>e){e=g;cp=fj/11.0+u/TAU*.18;}
        }
    }
    vec3 c=pal(cp+t*.006)*(pow(e,.62)*.96);
    c+=vec3(1.0,.98,.94)*pow(e,6.0)*.16;
    return c;
}

float gyroidF(vec3 p){return sin(p.x)*cos(p.y)+sin(p.y)*cos(p.z)+sin(p.z)*cos(p.x);}
float schwarzF(vec3 p){return cos(p.x)+cos(p.y)+cos(p.z);}

vec3 implicitVolume(vec2 p,float t,bool gyroidMode){
    float acc=0.0; float depth=0.0; float hot=0.0;
    float scale=4.2+1.5*u_param_a+u_chaos*.65;
    for(int i=0;i<32;i++){
        float z=-1.5+3.0*float(i)/31.0;
        vec3 q=vec3(p*1.05,z);
        q=rotate3(q,t*.08,t*.061+.45);
        q*=scale;
        float f=gyroidMode?gyroidF(q):schwarzF(q);
        float g=exp(-abs(f)*(4.0+1.5*u_param_b));
        g*=.045;
        acc+=g*(1.0-acc);
        hot=max(hot,g);
        depth+=g*float(i)/31.0;
    }
    float ph=depth/max(acc,.001);
    vec3 c=pal(ph*.48+t*.006+p.x*.04)*acc*1.42;
    c+=vec3(1.0,.98,.94)*pow(clamp(hot*18.0,0.0,1.0),4.0)*.11;
    return c;
}

vec3 helicoid(vec2 p,float t){
    float acc=0.0; float phase=0.0;
    for(int i=0;i<34;i++){
        float z=-1.3+2.6*float(i)/33.0;
        vec3 q=rotate3(vec3(p,z),t*.07,t*.05+.5);
        float theta=atan(q.y,q.x);
        float f=sin(theta-(1.6+u_param_a*2.4)*q.z+sin(length(q.xy)*3.0-t*.12)*u_chaos*.18);
        float sheet=exp(-abs(f)*(10.0+3.0*u_param_b))*exp(-abs(length(q.xy)-.62)*.5);
        float g=sheet*.047;
        acc+=g*(1.0-acc);
        phase+=g*float(i)/33.0;
    }
    vec3 c=pal(phase/max(acc,.001)+t*.007)*acc*1.65;
    return c;
}

vec3 mobius(vec2 p,float t){
    float minD=10.0; float ph=0.0; float stripe=0.0;
    for(int i=0;i<72;i++){
        float u=TAU*float(i)/72.0;
        for(int j=0;j<3;j++){
            float v=(float(j)-1.0)*.18;
            vec3 q=vec3((.64+v*cos(u*.5))*cos(u),(.64+v*cos(u*.5))*sin(u),v*sin(u*.5));
            q=rotate3(q,t*.11+.32,t*.073+.63);
            float d=length(p-project3(q));
            if(d<minD){minD=d;ph=u/TAU;stripe=abs(v)/.18;}
        }
    }
    float edge=glow(minD,.016+.004*u_chaos);
    float halo=glow(minD,.065);
    vec3 c=pal(ph+stripe*.16+t*.006)*(edge*.86+halo*.24);
    c+=vec3(1.0,.98,.94)*pow(edge,5.0)*.18;
    return c;
}

void main(){
    vec2 p=(gl_FragCoord.xy*2.0-u_resolution)/u_resolution.y;
    p*=max(u_scale,.05);
    vec3 col;
    if(u_mode==0)col=torusKnot(p,u_time);
    else if(u_mode==1)col=hopfLinks(p,u_time);
    else if(u_mode==2)col=implicitVolume(p,u_time,true);
    else if(u_mode==3)col=implicitVolume(p,u_time,false);
    else if(u_mode==4)col=helicoid(p,u_time);
    else col=mobius(p,u_time);
    col*=.76+.48*u_intensity;
    col=vec3(1.0)-exp(-max(col,vec3(0.0))*1.25);
    col=pow(col,vec3(.79));
    fragColor=vec4(clamp(col,0.0,1.0),1.0);
}
"""


class TopologyWorldRenderer:
    """GPU knot/link/minimal-surface studies with explicit mathematical identity."""

    def __init__(self, width: int, height: int, *, mode: str = "torus_knot", palette: str = "cyan_magenta") -> None:
        import moderngl

        if mode not in TOPOLOGY_MODES:
            raise ValueError(mode)
        if palette not in TOPOLOGY_PALETTES:
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

    def render(self, *, t: float, mode: str | None = None, palette: str | None = None, intensity: float = 1.0, chaos: float = 1.0, scale: float = 1.0, param_a: float = 0.5, param_b: float = 0.5) -> np.ndarray:
        mode = mode or self.mode
        palette = palette or self.palette
        if mode not in TOPOLOGY_MODES:
            raise ValueError(mode)
        if palette not in TOPOLOGY_PALETTES:
            raise ValueError(palette)
        p = self.program
        p["u_time"].value = float(t)
        p["u_intensity"].value = float(max(intensity, 0.0))
        p["u_chaos"].value = float(np.clip(chaos, 0.0, 2.5))
        p["u_scale"].value = float(np.clip(scale, 0.2, 3.0))
        p["u_param_a"].value = float(np.clip(param_a, 0.0, 1.0))
        p["u_param_b"].value = float(np.clip(param_b, 0.0, 1.0))
        p["u_mode"].value = TOPOLOGY_MODES.index(mode)
        p["u_palette"].value = TOPOLOGY_PALETTES.index(palette)
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


__all__ = ["TOPOLOGY_MODES", "TOPOLOGY_PALETTES", "TopologyWorldRenderer"]
