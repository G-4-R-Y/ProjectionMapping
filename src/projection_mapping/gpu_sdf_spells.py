from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np

from .graphics_runtime import create_context


@dataclass(frozen=True)
class SDFSpell:
    kind: str
    x: float
    y: float
    radius: float
    intensity: float = 1.0
    rotation: float = 0.0
    hue: float = 0.75
    aspect_y: float = 1.0


_KINDS = {"orb": 0, "portal": 1, "shield": 2, "ascension": 3, "impact": 4}

_VERTEX = r"""
#version 330
in vec2 in_pos;
out vec2 v_uv;
void main() {
    v_uv = in_pos * .5 + .5;
    gl_Position = vec4(in_pos,0.0,1.0);
}
"""

_FRAGMENT = r"""
#version 330
uniform vec2 u_resolution;
uniform float u_time;
uniform int u_count;
uniform vec4 u_spell0; uniform vec4 u_meta0;
uniform vec4 u_spell1; uniform vec4 u_meta1;
uniform vec4 u_spell2; uniform vec4 u_meta2;
uniform vec4 u_spell3; uniform vec4 u_meta3;
uniform vec4 u_spell4; uniform vec4 u_meta4;
uniform vec4 u_spell5; uniform vec4 u_meta5;
uniform vec4 u_spell6; uniform vec4 u_meta6;
uniform vec4 u_spell7; uniform vec4 u_meta7;
in vec2 v_uv;
out vec4 fragColor;
#define TAU 6.28318530718

vec4 spellAt(int i) {
    if (i==0) return u_spell0; if (i==1) return u_spell1; if (i==2) return u_spell2; if (i==3) return u_spell3;
    if (i==4) return u_spell4; if (i==5) return u_spell5; if (i==6) return u_spell6; return u_spell7;
}
vec4 metaAt(int i) {
    if (i==0) return u_meta0; if (i==1) return u_meta1; if (i==2) return u_meta2; if (i==3) return u_meta3;
    if (i==4) return u_meta4; if (i==5) return u_meta5; if (i==6) return u_meta6; return u_meta7;
}
vec3 pal(float t) {
    vec3 a=vec3(.44,.39,.52), b=vec3(.46,.42,.44), c=vec3(.96,.80,.72), d=vec3(.57,.11,.01);
    return a+b*cos(TAU*(c*t+d));
}
float ring(float r,float target,float width){ return exp(-abs(r-target)/max(width,1e-4)); }
float hash11(float p){ p=fract(p*.1031); p*=p+33.33; p*=p+p; return fract(p); }

vec3 renderSpell(vec2 uv, vec4 s, vec4 m) {
    // s = x,y,radius,intensity ; m = kind,rotation,hue,aspectY
    vec2 q=uv-s.xy;
    q.x *= u_resolution.x/max(u_resolution.y,1.0);
    q.y *= max(m.w,.15);
    float r=length(q);
    float a=atan(q.y,q.x)+m.y;
    float I=max(s.w,0.0);
    int kind=int(m.x+.5);
    vec3 color=pal(m.z);
    vec3 hot=mix(color,vec3(1.0,.96,1.0),.62);
    float e=0.0;

    if(kind==0){ // orb: dense core + rotating magnetic filaments
        float core=exp(-r*r/max(s.z*s.z*.55,.0004));
        float shell=ring(r,s.z,.010+s.z*.035);
        float fil=ring(r,s.z*(.68+.08*sin(a*6.0+u_time*2.2)),.009);
        e=core*.72+shell*1.2+fil*.55;
        return color*e*I + hot*pow(core,2.0)*I*.55;
    }
    if(kind==1){ // portal: seamless integer harmonics + radial rune ticks
        float shell=ring(r,s.z,.007+s.z*.020);
        float outer=ring(r,s.z*1.18,.005+s.z*.012);
        float inner=ring(r,s.z*.78,.004+s.z*.010);
        float sectors=24.0;
        float sector=fract((a/TAU)*sectors+.5);
        float tick=exp(-abs(sector-.5)*24.0);
        float tickBand=ring(r,s.z*1.08,.014)*tick;
        float harmonic=.5+.5*sin(a*8.0+u_time*.75)+.35*sin(a*12.0-u_time*.43);
        float glyph=ring(r,s.z*.91,.006)*smoothstep(.58,.92,harmonic);
        e=shell*1.15+outer*.45+inner*.32+tickBand*.78+glyph*.62;
        return color*e*I + hot*shell*I*.38;
    }
    if(kind==2){ // shield: sparse dome arcs + interference lattice
        float shell=ring(r,s.z,.012+s.z*.018);
        float arcs=ring(r,s.z*(.72+.07*sin(a*6.0+u_time*.8)),.010);
        float lattice=pow(.5+.5*cos(a*12.0+u_time*.25),8.0)*ring(r,s.z*.88,.026);
        e=shell*.72+arcs*.46+lattice*.34;
        return mix(color,vec3(.56,.90,1.0),.42)*e*I;
    }
    if(kind==3){ // ascension halo: multiple elegant rotating rings
        float r1=ring(r,s.z,.007);
        float r2=ring(r,s.z*.74,.006);
        float r3=ring(r,s.z*1.26,.004);
        float crown=pow(.5+.5*cos(a*10.0-u_time*.65),12.0)*ring(r,s.z*1.15,.020);
        e=r1+.55*r2+.30*r3+.65*crown;
        return color*e*I + hot*r1*I*.28;
    }
    // impact: expanding high-energy radial blades
    float shell=ring(r,s.z,.013);
    float blades=pow(max(0.0,cos(a*8.0+u_time*.5)),14.0)*exp(-r/max(s.z*1.6,.02));
    e=shell+blades*.72;
    return color*e*I + hot*shell*I*.55;
}

void main(){
    vec3 col=vec3(0.0);
    for(int i=0;i<8;i++){
        if(i>=u_count) break;
        col += renderSpell(v_uv, spellAt(i), metaAt(i));
    }
    // Soft local glow from already-analytic fields; intentionally preserve black background.
    col=col/(1.0+col*.72);
    fragColor=vec4(clamp(col,0.0,1.0),1.0);
}
"""


class SDFSpellRenderer:
    """Analytic shader-quality runes/portals/shields over a transparent-black canvas."""

    def __init__(self, width: int, height: int) -> None:
        import moderngl

        self.moderngl = moderngl
        self.width = int(width)
        self.height = int(height)
        self.ctx, self.context_info = create_context(require=330)
        self.backend = self.context_info.backend
        self.program = self.ctx.program(vertex_shader=_VERTEX, fragment_shader=_FRAGMENT)
        tri = np.asarray([-1.0,-1.0,3.0,-1.0,-1.0,3.0],dtype="f4")
        self.vbo = self.ctx.buffer(tri.tobytes())
        self.vao = self.ctx.simple_vertex_array(self.program,self.vbo,"in_pos")
        self.texture = self.ctx.texture((self.width,self.height),3,dtype="f1")
        self.fbo = self.ctx.framebuffer(color_attachments=[self.texture])

    def render(self, spells: list[SDFSpell], *, t: float) -> np.ndarray:
        selected=spells[:8]
        p=self.program
        p["u_resolution"].value=(float(self.width),float(self.height))
        p["u_time"].value=float(t)
        p["u_count"].value=len(selected)
        zero=(0.0,0.0,0.0,0.0)
        for i in range(8):
            if i < len(selected):
                s=selected[i]
                kind=float(_KINDS.get(s.kind,0))
                p[f"u_spell{i}"].value=(float(s.x),float(s.y),float(max(s.radius,.001)),float(max(s.intensity,0.0)))
                p[f"u_meta{i}"].value=(kind,float(s.rotation),float(s.hue%1.0),float(max(s.aspect_y,.15)))
            else:
                p[f"u_spell{i}"].value=zero
                p[f"u_meta{i}"].value=zero
        self.fbo.use()
        self.ctx.viewport=(0,0,self.width,self.height)
        self.fbo.clear(0.0,0.0,0.0,1.0)
        self.vao.render(mode=self.moderngl.TRIANGLES)
        data=self.fbo.read(components=3,alignment=1)
        frame=np.frombuffer(data,dtype=np.uint8).reshape(self.height,self.width,3)
        return np.flipud(frame).copy()

    def close(self)->None:
        for obj in (self.fbo,self.texture,self.vao,self.vbo,self.program):
            try: obj.release()
            except Exception: pass
        try: self.ctx.release()
        except Exception: pass


__all__=["SDFSpell","SDFSpellRenderer"]
