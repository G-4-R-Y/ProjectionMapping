from __future__ import annotations

import numpy as np

from .graphics_runtime import create_context


OPTICS_MODES = (
    "young_double_slit",
    "fresnel_zone_plate",
    "airy_diffraction",
    "multi_source_interference",
    "moire_gratings",
    "cusp_catastrophe",
)
OPTICS_PALETTES = ("spectral", "electric", "solar", "bio", "ultraviolet", "icefire")

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

float sinc(float x){return abs(x)<1e-4?1.0:sin(x)/x;}
vec3 pal(float t){
    t=fract(t);
    if(u_palette==1)return .50+.50*cos(TAU*(vec3(1.0,.82,.63)*t+vec3(.56,.11,.02)));
    if(u_palette==2)return .50+.50*cos(TAU*(vec3(1.0,.74,.55)*t+vec3(.02,.08,.16)));
    if(u_palette==3)return .50+.50*cos(TAU*(vec3(.84,1.0,.70)*t+vec3(.42,.03,.20)));
    if(u_palette==4)return .50+.50*cos(TAU*(vec3(.94,.74,1.0)*t+vec3(.72,.21,.03)));
    if(u_palette==5)return .50+.50*cos(TAU*(vec3(1.0,.72,.82)*t+vec3(.55,.90,.12)));
    return .50+.50*cos(TAU*(vec3(1.0,.87,.72)*t+vec3(.01,.17,.44)));
}

float besselJ1(float x){
    float ax=abs(x);
    float y;
    if(ax<3.0){
        float z=x*x;
        y=x*(.5-z*.0625+z*z*.0026041667-z*z*z*.0000542535);
    }else{
        y=sqrt(2.0/(PI*ax))*cos(ax-3.0*PI*.25);
        if(x<0.0)y=-y;
    }
    return y;
}

vec3 doubleSlit(vec2 p,float t){
    float chaos=clamp(u_chaos,0.0,2.5);
    float lambda=.18+.025*sin(t*.13)+.012*chaos;
    float slit=.18+.035*sin(t*.09);
    float screenDist=1.15+.08*cos(t*.07);
    float r1=sqrt((p.x-slit)*(p.x-slit)+(p.y+screenDist)*(p.y+screenDist));
    float r2=sqrt((p.x+slit)*(p.x+slit)+(p.y+screenDist)*(p.y+screenDist));
    float phase=TAU*(r1-r2)/lambda;
    float envelope=pow(sinc(p.x*(4.4+chaos)),2.0);
    float intensity=(.5+.5*cos(phase))*envelope;
    float vertical=.58+.42*cos((p.y+t*.06)*4.0);
    intensity*=.72+.28*vertical;
    float ridge=pow(intensity,3.2);
    vec3 c=pal(.12+p.x*.14+t*.011)*intensity*.78;
    c+=pal(.62+p.y*.08)*ridge*.74;
    c+=vec3(1.0,.98,.94)*pow(ridge,3.0)*.22;
    return c;
}

vec3 zonePlate(vec2 p,float t){
    float chaos=clamp(u_chaos,0.0,2.5);
    p*=mat2(cos(t*.025),-sin(t*.025),sin(t*.025),cos(t*.025));
    float r2=dot(p,p);
    float phase=r2*(58.0+9.0*chaos)-t*(1.1+.15*chaos);
    phase+=sin((p.x+p.y)*11.0-t*.21)*chaos*.45;
    float zones=.5+.5*cos(phase);
    float edges=pow(1.0-abs(2.0*zones-1.0),7.0);
    float focus=exp(-length(p)*5.6)*(.5+.5*cos(t*.62));
    vec3 c=pal(zones*.42+r2*.22+t*.009)*(pow(zones,2.2)*.74+edges*.82);
    c+=vec3(1.0,.98,.94)*focus*.55;
    return c;
}

vec3 airy(vec2 p,float t){
    float chaos=clamp(u_chaos,0.0,2.5);
    vec2 q=p+(.025+.025*chaos)*vec2(sin(p.y*5.0+t*.11),cos(p.x*4.0-t*.09));
    float r=length(q)+1e-5;
    float k=19.0+3.0*chaos+1.5*sin(t*.07);
    float x=k*r;
    float a=2.0*besselJ1(x)/max(x,1e-4);
    float airyI=a*a;
    float rings=pow(clamp(airyI*7.5,0.0,1.0),.58);
    float angular=.80+.20*cos(atan(q.y,q.x)*6.0+t*.17*chaos);
    vec3 c=pal(r*.48+t*.014)*rings*angular*1.25;
    c+=vec3(1.0,.985,.95)*pow(clamp(airyI*2.8,0.0,1.0),2.2)*.80;
    return c;
}

vec3 multiSource(vec2 p,float t){
    float chaos=clamp(u_chaos,0.0,2.5);
    float re=0.0,im=0.0;
    for(int i=0;i<7;i++){
        float fi=float(i);
        float a=fi*TAU/7.0+t*(.055+.006*fi);
        float radius=.30+.055*sin(t*.09+fi*1.7)+.03*chaos;
        vec2 src=vec2(cos(a),sin(a))*radius;
        float d=length(p-src)+.018;
        float ph=d*(31.0+4.5*chaos)-t*(1.0+.07*fi)+fi*.63;
        float amp=1.0/sqrt(1.0+d*4.0);
        re+=cos(ph)*amp;
        im+=sin(ph)*amp;
    }
    float intensity=(re*re+im*im)/18.0;
    float ridge=pow(clamp(intensity,0.0,1.0),1.5);
    vec3 c=pal(atan(im,re)/TAU+t*.008+length(p)*.17)*ridge*1.22;
    c+=vec3(1.0,.98,.94)*pow(ridge,4.0)*.18;
    return c;
}

vec3 moire(vec2 p,float t){
    float chaos=clamp(u_chaos,0.0,2.5);
    float a=.18+.09*sin(t*.071)+.045*chaos;
    vec2 q1=mat2(cos(a),-sin(a),sin(a),cos(a))*p;
    vec2 q2=mat2(cos(-a),-sin(-a),sin(-a),cos(-a))*p;
    float f=34.0+6.0*chaos;
    float g1=.5+.5*cos(q1.x*f+t*.34);
    float g2=.5+.5*cos(q2.x*f-t*.28);
    float g3=.5+.5*cos((p.x*.61+p.y*.79)*(f*.72)+t*.19);
    float interference=abs(g1-g2);
    float lattice=pow(clamp(g1*g2,0.0,1.0),2.2);
    float beats=pow(1.0-interference,4.0);
    vec3 c=pal(beats*.33+p.y*.08+t*.012)*(lattice*.55+beats*.78+g3*.12*chaos);
    return c;
}

vec3 cusp(vec2 p,float t){
    float chaos=clamp(u_chaos,0.0,2.5);
    // A catastrophe-optics-inspired cusp field: integrate a small family of cubic phase rays.
    float amp=0.0;
    float phaseSum=0.0;
    for(int i=0;i<18;i++){
        float u=-1.0+2.0*float(i)/17.0;
        float phase=8.0*(u*u*u/3.0 + p.x*u*u*.78 + p.y*u);
        phase+=t*(.22+.03*u)+chaos*.35*sin(u*7.0+t*.09);
        amp+=cos(phase);
        phaseSum+=sin(phase);
    }
    float intensity=(amp*amp+phaseSum*phaseSum)/(18.0*18.0);
    float cuspLine=exp(-abs(p.y*p.y*p.y+p.x*.55)*18.0);
    float glow=pow(clamp(intensity*2.8,0.0,1.0),1.2);
    vec3 c=pal(atan(phaseSum,amp)/TAU+t*.012+p.x*.07)*glow*1.12;
    c+=pal(.78+t*.007)*cuspLine*(.18+.20*chaos);
    c+=vec3(1.0,.98,.94)*pow(glow,4.0)*.18;
    return c;
}

void main(){
    vec2 p=(gl_FragCoord.xy*2.0-u_resolution)/u_resolution.y;
    float t=u_time;
    vec3 col;
    if(u_mode==0)col=doubleSlit(p,t);
    else if(u_mode==1)col=zonePlate(p,t);
    else if(u_mode==2)col=airy(p,t);
    else if(u_mode==3)col=multiSource(p,t);
    else if(u_mode==4)col=moire(p,t);
    else col=cusp(p,t);
    col*=.80+.44*u_intensity;
    float vignette=1.0-smoothstep(.22,1.45,length(p));
    col*=mix(.72,1.0,vignette);
    col=vec3(1.0)-exp(-max(col,vec3(0.0))*1.20);
    col=pow(col,vec3(.79));
    fragColor=vec4(clamp(col,0.0,1.0),1.0);
}
"""


class WaveOpticsRenderer:
    """GPU interference/diffraction scenes based on classic wave-optics mathematics."""

    def __init__(self,width:int,height:int,*,mode:str="multi_source_interference",palette:str="spectral")->None:
        import moderngl
        if mode not in OPTICS_MODES: raise ValueError(mode)
        if palette not in OPTICS_PALETTES: raise ValueError(palette)
        self.moderngl=moderngl
        self.width=int(width); self.height=int(height); self.mode=mode; self.palette=palette
        self.ctx,self.context_info=create_context(require=330)
        self.backend=self.context_info.backend
        self.program=self.ctx.program(vertex_shader=_VERTEX,fragment_shader=_FRAGMENT)
        vertices=np.asarray([-1.0,-1.0,3.0,-1.0,-1.0,3.0],dtype="f4")
        self.vbo=self.ctx.buffer(vertices.tobytes())
        self.vao=self.ctx.simple_vertex_array(self.program,self.vbo,"in_pos")
        self.target=self.ctx.texture((self.width,self.height),3,dtype="f1")
        self.fbo=self.ctx.framebuffer(color_attachments=[self.target])
        self.program["u_resolution"].value=(float(self.width),float(self.height))

    def render(self,*,t:float,mode:str|None=None,palette:str|None=None,intensity:float=1.0,chaos:float=1.0)->np.ndarray:
        mode=mode or self.mode; palette=palette or self.palette
        if mode not in OPTICS_MODES: raise ValueError(mode)
        if palette not in OPTICS_PALETTES: raise ValueError(palette)
        p=self.program
        p["u_time"].value=float(t)
        p["u_intensity"].value=float(max(intensity,0.0))
        p["u_chaos"].value=float(np.clip(chaos,0.0,2.5))
        p["u_mode"].value=OPTICS_MODES.index(mode)
        p["u_palette"].value=OPTICS_PALETTES.index(palette)
        self.fbo.use(); self.ctx.viewport=(0,0,self.width,self.height); self.fbo.clear(0,0,0,1)
        self.vao.render(mode=self.moderngl.TRIANGLES)
        data=self.fbo.read(components=3,alignment=1)
        return np.flipud(np.frombuffer(data,dtype=np.uint8).reshape(self.height,self.width,3)).copy()

    def close(self)->None:
        for obj in (self.fbo,self.target,self.vao,self.vbo,self.program):
            try: obj.release()
            except Exception: pass
        try: self.ctx.release()
        except Exception: pass


__all__=["OPTICS_MODES","OPTICS_PALETTES","WaveOpticsRenderer"]
