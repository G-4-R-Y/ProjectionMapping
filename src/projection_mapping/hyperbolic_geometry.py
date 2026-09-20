from __future__ import annotations

import numpy as np

from .graphics_runtime import create_context


HYPERBOLIC_MODES = (
    "poincare_orbifold",
    "hyperbolic_geodesics",
    "mobius_lattice",
    "schottky_inversions",
    "klein_chords",
    "modular_domain",
)
HYPERBOLIC_PALETTES = ("cyan_magenta", "spectral", "electric", "solar", "bio", "ultraviolet", "icefire")

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
vec2 cconj(vec2 z){return vec2(z.x,-z.y);}
vec2 cdiv(vec2 a,vec2 b){
    float d=max(dot(b,b),1e-7);
    return vec2(a.x*b.x+a.y*b.y,a.y*b.x-a.x*b.y)/d;
}
vec2 cinv(vec2 z){return cdiv(vec2(1.0,0.0),z);}
vec2 cis(float a){return vec2(cos(a),sin(a));}

vec3 pal(float t){\n    if(u_palette==0) return vec3(.5+.5*cos(TAU*(t+.50)), .5+.5*cos(TAU*(t+.00)), .5+.5*cos(TAU*(t+.50)));
    t=fract(t);
    if(u_palette==6)return .50+.50*cos(TAU*(vec3(1.0,.82,.63)*t+vec3(.56,.11,.02)));
    if(u_palette==6)return .50+.50*cos(TAU*(vec3(1.0,.74,.55)*t+vec3(.02,.08,.16)));
    if(u_palette==6)return .50+.50*cos(TAU*(vec3(.84,1.0,.70)*t+vec3(.42,.03,.20)));
    if(u_palette==6)return .50+.50*cos(TAU*(vec3(.94,.74,1.0)*t+vec3(.72,.21,.03)));
    if(u_palette==6)return .50+.50*cos(TAU*(vec3(1.0,.72,.82)*t+vec3(.55,.90,.12)));
    return .50+.50*cos(TAU*(vec3(1.0,.87,.72)*t+vec3(.01,.17,.44)));
}

float lineGlow(float d,float width){return exp(-abs(d)/max(width,1e-5));}

vec2 diskAutomorphism(vec2 z,vec2 a){
    // (z-a)/(1-conj(a)z), an automorphism of the Poincare disk.
    vec2 den=vec2(1.0,0.0)-cmul(cconj(a),z);
    return cdiv(z-a,den);
}

vec3 poincareOrbifold(vec2 p,float t){
    float r=length(p);
    if(r>=.995)return vec3(0.0);
    float chaos=clamp(u_chaos,0.0,2.5);
    vec2 a=.22*vec2(cos(t*.083),sin(t*.071));
    vec2 z=diskAutomorphism(p,a);
    r=min(length(z),.994);
    float theta=atan(z.y,z.x)+t*.035;
    float rho=log((1.0+r)/max(1.0-r,1e-4));
    float sectors=7.0+floor(chaos*1.2);
    float wedge=TAU/sectors;
    float folded=abs(mod(theta+.5*wedge,wedge)-.5*wedge);
    float angular=lineGlow(folded,.010+.004/(1.0+rho));
    float ring=lineGlow(sin(rho*(3.1+.35*chaos)-t*.16),.17);
    float cells=.5+.5*cos(rho*(4.0+.4*chaos)+folded*(17.0+rho*5.0));
    float edge=1.0-smoothstep(.88,.995,r);
    vec3 c=pal(cells*.30+rho*.07+t*.006)*(cells*.30+ring*.64+angular*.72);
    c+=vec3(1.0,.98,.94)*pow(max(angular,ring),5.0)*.20;
    return c*edge;
}

vec3 geodesics(vec2 p,float t){
    float r=length(p);
    if(r>=.995)return vec3(0.0);
    float chaos=clamp(u_chaos,0.0,2.5);
    float glow=0.0;
    float colorPhase=0.0;
    for(int i=0;i<9;i++){
        float fi=float(i);
        float phi=fi*TAU/9.0+t*(.025+.003*fi);
        float alpha=.47+.13*sin(t*.071+fi*1.37)+.025*chaos;
        float ca=max(cos(alpha),.12);
        vec2 center=cis(phi)/ca;
        float radius=abs(tan(alpha));
        float d=abs(length(p-center)-radius);
        float local=lineGlow(d,.0065+.002*r);
        glow+=local;
        colorPhase+=local*(fi/9.0);
    }
    float boundary=lineGlow(1.0-r,.007);
    float metric=1.0/max(1.0-r*r,.08);
    float nodes=.5+.5*cos(metric*(1.4+.25*chaos)-t*.11);
    vec3 c=pal(colorPhase/max(glow,.05)+t*.008)*(1.0-exp(-glow*.55))*(.72+.28*nodes);
    c+=pal(.78+t*.006)*boundary*.50;
    return c;
}

vec3 mobiusLattice(vec2 p,float t){
    float chaos=clamp(u_chaos,0.0,2.5);
    vec2 a=.38*vec2(cos(t*.071),sin(t*.053));
    vec2 b=.24*vec2(cos(t*.037+1.2),sin(t*.061+.7));
    vec2 z=cdiv(p-a,vec2(1.0,0.0)-cmul(cconj(b),p));
    z=cmul(z,cis(t*.043));
    float f=8.0+2.0*chaos;
    float gx=lineGlow(sin((z.x+z.y*.16)*f*PI),.11);
    float gy=lineGlow(sin((z.y-z.x*.13)*f*PI),.11);
    float circles=lineGlow(sin(length(z)*f*PI*.72-t*.21),.13);
    float g=max(max(gx,gy),circles*.72);
    float phase=atan(z.y,z.x)/TAU+log(1.0+length(z))*.18+t*.008;
    vec3 c=pal(phase)*g*.95;
    c+=vec3(1.0,.98,.94)*pow(g,6.0)*.18;
    return c;
}

vec2 circleInvert(vec2 z,vec2 c,float r){
    vec2 d=z-c;
    return c+d*(r*r/max(dot(d,d),1e-6));
}

vec3 schottky(vec2 p,float t){
    float chaos=clamp(u_chaos,0.0,2.5);
    vec2 z=p;
    float hits=0.0;
    float minBoundary=9.0;
    for(int k=0;k<11;k++){
        bool changed=false;
        for(int j=0;j<4;j++){
            float fj=float(j);
            float a=fj*TAU/4.0+t*.018*(1.0+fj*.17);
            vec2 c=cis(a)*(.62+.025*sin(t*.09+fj));
            float rr=.31+.015*chaos*sin(t*.05+fj*1.9);
            float d=length(z-c);
            minBoundary=min(minBoundary,abs(d-rr));
            if(d<rr){
                z=circleInvert(z,c,rr);
                hits+=1.0;
                changed=true;
            }
        }
        if(!changed)break;
        z*=.985;
    }
    float web=lineGlow(minBoundary,.008+.002*length(p));
    float orbit=.5+.5*cos(length(z)*(15.0+2.0*chaos)-hits*1.7+t*.08);
    float energy=web*.82+(1.0-exp(-hits*.35))*orbit*.62;
    vec3 c=pal(hits*.083+atan(z.y,z.x)/TAU+t*.006)*energy;
    c+=vec3(1.0,.98,.94)*pow(web,4.0)*.20;
    return c;
}

vec3 klein(vec2 p,float t){
    float r=length(p);
    if(r>=.995)return vec3(0.0);
    // Poincare-disk coordinate mapped to the Klein disk: k=2p/(1+|p|^2).
    vec2 k=2.0*p/(1.0+r*r);
    float chaos=clamp(u_chaos,0.0,2.5);
    float glow=0.0;
    float phase=0.0;
    for(int i=0;i<10;i++){
        float fi=float(i);
        float a=fi*PI/10.0+t*(.017+.0017*fi);
        vec2 n=cis(a);
        float off=.48*sin(fi*2.17+t*.037)*(1.0+.08*chaos);
        float d=dot(k,n)-off;
        float g=lineGlow(d,.008+.003*r);
        glow+=g;
        phase+=g*fi/10.0;
    }
    float diskEdge=lineGlow(1.0-r,.006);
    float fill=.5+.5*cos((k.x*k.y)*(18.0+3.0*chaos)+t*.09);
    vec3 c=pal(phase/max(glow,.05)+t*.007)*(1.0-exp(-glow*.52))*(.70+.30*fill);
    c+=pal(.64+t*.004)*diskEdge*.55;
    return c;
}

vec3 modular(vec2 p,float t){
    float chaos=clamp(u_chaos,0.0,2.5);
    // Upper half-plane coordinate, then repeatedly reduce by PSL(2,Z): T:z->z+n and S:z->-1/z.
    vec2 z=vec2(p.x*1.55+.16*sin(t*.041),exp((p.y*.90+.08*sin(t*.027))*1.45)*.42);
    float steps=0.0;
    float seam=9.0;
    for(int i=0;i<14;i++){
        float n=floor(z.x+.5);
        z.x-=n;
        seam=min(seam,abs(abs(z.x)-.5));
        float rr=dot(z,z);
        seam=min(seam,abs(sqrt(rr)-1.0));
        if(rr<1.0){
            z=-cinv(z);
            steps+=1.0;
        }else{
            steps+=abs(n)*.23;
        }
    }
    float fundamental=(abs(z.x)<=.5 && dot(z,z)>=1.0)?1.0:0.0;
    float boundary=lineGlow(seam,.010);
    float bands=.5+.5*cos(log(max(z.y,1e-4))*(8.0+chaos)+steps*1.1-t*.10);
    float energy=boundary*.76+bands*(.18+.30*fundamental);
    vec3 c=pal(steps*.071+atan(z.y,z.x)/TAU+t*.006)*energy;
    c+=vec3(1.0,.98,.94)*pow(boundary,5.0)*.18;
    return c;
}

void main(){
    vec2 p=(gl_FragCoord.xy*2.0-u_resolution)/u_resolution.y;
    float t=u_time;
    vec3 col;
    if(u_mode==0)col=poincareOrbifold(p,t);
    else if(u_mode==1)col=geodesics(p,t);
    else if(u_mode==2)col=mobiusLattice(p,t);
    else if(u_mode==3)col=schottky(p,t);
    else if(u_mode==4)col=klein(p,t);
    else col=modular(p,t);
    col*=.80+.45*u_intensity;
    col=vec3(1.0)-exp(-max(col,vec3(0.0))*1.23);
    col=pow(col,vec3(.79));
    fragColor=vec4(clamp(col,0.0,1.0),1.0);
}
"""


class HyperbolicGeometryRenderer:
    """GPU studies of disk geometry, Mobius maps, inversive groups and modular reduction."""

    def __init__(
        self,
        width: int,
        height: int,
        *,
        mode: str = "poincare_orbifold",
        palette: str = "cyan_magenta",
    ) -> None:
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

    def render(
        self,
        *,
        t: float,
        mode: str | None = None,
        palette: str | None = None,
        intensity: float = 1.0,
        chaos: float = 1.0,
    ) -> np.ndarray:
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


__all__ = ["HYPERBOLIC_MODES", "HYPERBOLIC_PALETTES", "HyperbolicGeometryRenderer"]
