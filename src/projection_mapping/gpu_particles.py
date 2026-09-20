from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np

from .graphics_runtime import create_context
from .performance_bus import AnchorState


@dataclass(frozen=True)
class ParticleEmitter:
    x: float
    y: float
    vx: float = 0.0
    vy: float = 0.0
    energy: float = 1.0
    hue: float = 0.5
    radius: float = 0.012

    @classmethod
    def from_anchor(
        cls,
        anchor: AnchorState,
        *,
        energy: float = 1.0,
        hue: float = 0.5,
        radius: float = 0.012,
    ) -> "ParticleEmitter":
        return cls(
            anchor.position.x,
            anchor.position.y,
            anchor.velocity.x,
            anchor.velocity.y,
            energy,
            hue,
            radius,
        )


_FULLSCREEN_VERTEX = r"""
#version 330
in vec2 in_pos;
out vec2 v_uv;
void main() {
    v_uv = in_pos * 0.5 + 0.5;
    gl_Position = vec4(in_pos, 0.0, 1.0);
}
"""

_UPDATE_FRAGMENT = r"""
#version 330
uniform sampler2D u_state0;
uniform sampler2D u_state1;
uniform float u_time;
uniform float u_dt;
uniform float u_emit_rate;
uniform float u_turbulence;
uniform float u_drag;
uniform float u_bass;
uniform float u_strike;
uniform float u_drop;
uniform int u_field_mode;
uniform float u_field_strength;
uniform float u_field_scale;
uniform float u_field_spin;
uniform float u_well_strength;
uniform float u_nebula_mix;
uniform int u_capacity;
uniform int u_emitter_count;
uniform vec4 u_emitters[8]; // x,y,vx,vy
uniform vec4 u_emit_meta[8]; // energy,hue,radius,reserved
layout(location=0) out vec4 out_state0; // x,y,life,seed
layout(location=1) out vec4 out_state1; // vx,vy,hue,size

float hash11(float p) {
    p = fract(p * .1031);
    p *= p + 33.33;
    p *= p + p;
    return fract(p);
}
vec2 hash21(float p) {
    return vec2(hash11(p+17.0), hash11(p+71.0));
}
vec2 safeNorm(vec2 v) {
    return v / max(length(v), 1e-5);
}
vec2 curlFlow(vec2 p, float t) {
    float scale=max(u_field_scale,.10);
    vec2 q=(p-.5)*scale;
    float a = sin(q.x*8.0 + t*.73) + cos(q.y*7.0 - t*.61);
    float b = cos((q.x+q.y)*6.0 - t*.47) - sin((q.x-q.y)*5.0 + t*.53);
    return safeNorm(vec2(b, -a));
}
vec2 well(vec2 p, vec2 center, float spin) {
    vec2 d=center-p;
    float r2=dot(d,d)+.0035;
    float fall=clamp(.020/r2,0.0,1.75);
    vec2 radial=safeNorm(d);
    vec2 tangent=vec2(-radial.y,radial.x);
    return (radial + tangent*spin)*fall;
}
vec2 field(vec2 p, float t) {
    vec2 base=curlFlow(p,t);
    float spin=u_field_spin;
    if(u_field_mode==0) return base;

    if(u_field_mode==1) {
        vec2 q=(p-.5)*max(u_field_scale,.10);
        float a=sin(q.x*11.0+t*.37)+sin((q.x+q.y)*7.0-t*.29);
        float b=cos(q.y*10.0-t*.31)-cos((q.x-q.y)*8.0+t*.23);
        vec2 cloud=safeNorm(vec2(b,-a));
        vec2 slow=safeNorm(vec2(
            sin(q.y*3.2+t*.09)+cos(q.x*2.4-t*.07),
            cos(q.x*3.0-t*.08)-sin(q.y*2.2+t*.11)
        ));
        return safeNorm(mix(base,cloud,.72)+slow*(.24+.34*u_nebula_mix));
    }

    if(u_field_mode==2) {
        float orbit=t*(.20+.12*spin);
        vec2 c1=.5+vec2(cos(orbit),sin(orbit))*(.16+.035*u_bass);
        vec2 c2=.5-vec2(cos(orbit),sin(orbit))*(.16+.035*u_bass);
        vec2 wells=well(p,c1,.82*spin)+well(p,c2,-.82*spin);
        return base*.16+wells*(.42+.58*u_well_strength);
    }

    if(u_field_mode==3) {
        vec2 c=.5+.028*vec2(sin(t*.17),cos(t*.13));
        vec2 d=c-p;
        float r2=dot(d,d)+.005;
        vec2 radial=safeNorm(d);
        vec2 tangent=vec2(-radial.y,radial.x);
        float fall=clamp(.018/r2,0.0,1.65);
        float inward=.44+.42*u_bass+.35*u_drop;
        float swirl=(.70+.48*u_drop)*spin;
        return base*.12+(radial*inward+tangent*swirl)*fall;
    }

    if(u_field_mode==5) {
        // Circuit field: stylized curl flow quantized toward orthogonal data-lane motion.
        vec2 f=base;
        vec2 cardinal=abs(f.x)>abs(f.y)?vec2(sign(f.x),0.0):vec2(0.0,sign(f.y));
        float lane=.72+.28*sin((p.x*18.0+p.y*14.0)*6.2831853+t*2.2);
        vec2 gridPull=vec2(
            sin((p.y-.5)*6.2831853*12.0+t*.31),
            cos((p.x-.5)*6.2831853*12.0-t*.27)
        )*.18;
        return safeNorm(mix(f,cardinal,.82)+gridPull)*lane;
    }

    vec2 c1=.5+.25*vec2(cos(t*.071),sin(t*.093));
    vec2 c2=.5+.20*vec2(cos(t*.113+2.1),sin(t*.087+1.4));
    vec2 c3=.5+.16*vec2(cos(t*.053+4.0),sin(t*.129+3.1));
    vec2 wells=well(p,c1,.55*spin)+well(p,c2,-.72*spin)+well(p,c3,.91*spin);
    vec2 q=(p-.5)*max(u_field_scale,.10);
    vec2 mist=safeNorm(vec2(
        sin(q.y*5.0+t*.13)+cos((q.x+q.y)*3.7-t*.11),
        cos(q.x*4.6-t*.10)-sin((q.x-q.y)*4.1+t*.15)
    ));
    return base*.12+mist*(.30+.34*u_nebula_mix)+wells*(.30+.42*u_well_strength);
}
void main() {
    int id = int(gl_FragCoord.x);
    vec4 s0 = texelFetch(u_state0, ivec2(id,0), 0);
    vec4 s1 = texelFetch(u_state1, ivec2(id,0), 0);
    vec2 pos = s0.xy;
    float life = s0.z;
    float seed = s0.w;
    vec2 vel = s1.xy;
    float hue = s1.z;
    float size = s1.w;

    life -= u_dt;
    if (life <= 0.0) {
        float cycle = floor(u_time * 120.0);
        float r = hash11(float(id)*13.17 + cycle*1.31);
        float spawnP = clamp(u_emit_rate * u_dt / max(float(u_capacity),1.0), 0.0, .92);
        if (u_emitter_count > 0 && r < spawnP) {
            float r2 = hash11(float(id)*7.91 + cycle*2.07);
            int ei = min(int(floor(r2 * float(u_emitter_count))), u_emitter_count-1);
            vec4 e = u_emitters[ei];
            vec4 m = u_emit_meta[ei];
            vec2 rr = hash21(float(id)*4.77 + cycle) - .5;
            float ang = hash11(float(id)*9.13 + cycle)*6.2831853;
            vec2 radial = vec2(cos(ang), sin(ang));
            float radius = max(m.z, .002);
            pos = e.xy + rr * radius * 2.0;
            float launch = .12 + .58*m.x + .28*u_strike;
            vel = e.zw*.18 + radial*launch*(.35 + hash11(float(id)+cycle));
            life = .45 + 1.55*hash11(float(id)*1.73 + cycle*3.11);
            seed = hash11(float(id)*5.17 + cycle);
            hue = fract(m.y + seed*.13 + u_bass*.06);
            size = 1.3 + 4.6*(.25 + m.x*.75)*(1.0 + .35*u_strike);
        } else {
            pos = vec2(-10.0);
            vel = vec2(0.0);
            life = 0.0;
        }
    } else {
        vec2 f = field(pos, u_time + seed*1.7);
        vel += f * u_turbulence * u_field_strength * u_dt * (.30 + .70*seed);
        vel *= exp(-u_drag*u_dt);
        pos += vel*u_dt;
        if (pos.x < -.08) pos.x = 1.08;
        if (pos.x > 1.08) pos.x = -.08;
        if (pos.y < -.08) pos.y = 1.08;
        if (pos.y > 1.08) pos.y = -.08;
    }
    out_state0 = vec4(pos, life, seed);
    out_state1 = vec4(vel, hue, size);
}
"""

_PARTICLE_VERTEX = r"""
#version 330
uniform sampler2D u_state0;
uniform sampler2D u_state1;
uniform float u_energy;
uniform vec2 u_resolution;
uniform int u_material;
out float v_life;
out float v_hue;
out float v_seed;
out float v_speed;
out vec2 v_vel;
void main() {
    int id = gl_VertexID;
    vec4 s0 = texelFetch(u_state0, ivec2(id,0), 0);
    vec4 s1 = texelFetch(u_state1, ivec2(id,0), 0);
    vec2 p = s0.xy;
    float life = s0.z;
    if (life <= 0.0) p = vec2(-10.0);
    gl_Position = vec4(p.x*2.0-1.0, 1.0-p.y*2.0, 0.0, 1.0);
    float speed=length(s1.xy);
    float speedLift=smoothstep(.10,.95,speed);
    float aspectScale = clamp(min(u_resolution.x,u_resolution.y)/720.0, .6, 2.2);
    float materialScale = u_material==5 ? .42 : 1.0;
    gl_PointSize = clamp(s1.w * aspectScale * (.72 + .50*u_energy) * (1.0+.75*speedLift) * materialScale, 1.0, 34.0);
    v_life = life;
    v_hue = s1.z;
    v_seed = s0.w;
    v_speed = speed;
    v_vel = s1.xy;
}
"""

_PARTICLE_FRAGMENT = r"""
#version 330
in float v_life;
in float v_hue;
in float v_seed;
in float v_speed;
in vec2 v_vel;
uniform int u_palette;
uniform int u_material;
uniform float u_strike;
out vec4 fragColor;
#define TAU 6.28318530718

vec3 satPalette(float t) {
    t=fract(t);
    if (u_palette == 1) {
        vec3 a=vec3(1.00,.12,.015), b=vec3(1.00,.72,.04), c=vec3(1.00,.02,.26);
        return mix(mix(a,b,smoothstep(0.0,.48,t)),c,smoothstep(.48,1.0,t));
    }
    if (u_palette == 2) {
        vec3 a=vec3(.01,1.00,.34), b=vec3(.00,.88,1.00), c=vec3(.40,.06,1.00);
        return mix(mix(a,b,smoothstep(0.0,.52,t)),c,smoothstep(.52,1.0,t));
    }
    if (u_palette == 3) {
        return .54 + .54*cos(TAU*(vec3(1.0,.78,.58)*t+vec3(.00,.17,.43)));
    }
    if (u_palette == 4) {
        vec3 a=vec3(.08,.00,.32), b=vec3(.55,.04,1.00), c=vec3(1.00,.02,.74);
        return mix(mix(a,b,smoothstep(0.0,.52,t)),c,smoothstep(.52,1.0,t));
    }
    if (u_palette == 5) {
        vec3 a=vec3(.00,.10,.22), b=vec3(.00,.72,1.00), c=vec3(.10,.97,1.00);
        return mix(mix(a,b,smoothstep(0.0,.55,t)),c,smoothstep(.55,1.0,t));
    }
    if (u_palette == 6) {
        vec3 a=vec3(.20,.02,.30), b=vec3(1.00,.03,.58), c=vec3(1.00,.66,.05);
        return mix(mix(a,b,smoothstep(0.0,.50,t)),c,smoothstep(.50,1.0,t));
    }
    vec3 a=vec3(.00,.92,1.00), b=vec3(.12,.20,1.00), c=vec3(1.00,.03,.78);
    return mix(mix(a,b,smoothstep(0.0,.46,t)),c,smoothstep(.46,1.0,t));
}

void main() {
    vec2 q = gl_PointCoord*2.0-1.0;
    float rawR=length(q);
    if(u_material!=5 && rawR>1.0) discard;
    float speedLift=smoothstep(.10,.95,v_speed);
    vec2 dir=normalize(v_vel+vec2(1e-5));
    vec2 perp=vec2(-dir.y,dir.x);
    vec2 aligned=vec2(dot(q,dir),dot(q,perp));
    float life=smoothstep(0.0,.16,v_life);
    vec3 base=max(satPalette(v_hue+v_seed*.035),vec3(0.0));
    vec3 hot=vec3(1.0,.985,.94);

    float core=0.0;
    float shell=0.0;
    float halo=0.0;
    float accent=0.0;

    if(u_material==1){
        // Comet streak: velocity-oriented luminous capsule inside the point sprite.
        float stretch=1.0+2.65*speedLift;
        float r=length(vec2(aligned.x/stretch,aligned.y*1.35));
        core=1.0-smoothstep(.00,.14,r);
        shell=exp(-pow((r-.20)*5.4,2.0));
        halo=exp(-r*3.6);
        float tail=smoothstep(.86,-.72,aligned.x)*exp(-abs(aligned.y)*8.0)*(0.22+.78*speedLift);
        accent=tail;
    } else if(u_material==2){
        // Pulse spark: sharp cross/star highlights with a compact colored halo.
        float r=rawR;
        core=1.0-smoothstep(.00,.105,r);
        shell=exp(-r*5.4);
        halo=exp(-r*2.8)*.55;
        float axis=max(exp(-abs(q.x)*28.0)*exp(-abs(q.y)*2.2),exp(-abs(q.y)*28.0)*exp(-abs(q.x)*2.2));
        float diag=max(exp(-abs(q.x-q.y)*19.0),exp(-abs(q.x+q.y)*19.0))*exp(-r*3.0);
        accent=axis*.75+diag*.28;
    } else if(u_material==3){
        // Plasma mote: softer spherical energy pearl, useful for constellation/ambient fields.
        float r=rawR;
        core=exp(-r*r*38.0);
        shell=exp(-pow((r-.30)*4.2,2.0));
        halo=exp(-r*2.35)*.72;
        accent=.08*(.5+.5*cos((r*12.0-v_seed*TAU)));
    } else if(u_material==4){
        // Shock ring: hollow expanding-looking sprite; best on sparse high-energy bursts.
        float r=rawR;
        float ring=exp(-abs(r-.48)*23.0);
        core=exp(-abs(r-.43)*42.0)*.45;
        shell=ring*1.35;
        halo=exp(-abs(r-.50)*6.5)*.55;
        accent=(1.0-smoothstep(.0,.22,r))*.20;
    } else if(u_material==5){
        // Data point: tiny hard-edged photon/pixel with restrained glow.
        float box=max(abs(q.x),abs(q.y));
        core=1.0-smoothstep(.00,.22,box);
        shell=exp(-box*6.5)*.42;
        halo=exp(-box*2.8)*.18;
        accent=(exp(-abs(q.x)*18.0)+exp(-abs(q.y)*18.0))*exp(-box*4.0)*(.06+.20*speedLift);
    } else {
        // Plasma: default premium point material.
        float r=rawR;
        core=1.0-smoothstep(.00,.18,r);
        shell=exp(-pow((r-.25)*4.6,2.0));
        halo=exp(-r*3.15)+exp(-r*1.55)*.055;
        accent=(exp(-abs(q.x)*24.0)+exp(-abs(q.y)*24.0))*exp(-r*2.4)*(.10+.32*speedLift);
    }

    vec3 col=base*(shell*1.58+halo*.70);
    col+=hot*core*(2.18+.78*u_strike);
    col+=mix(base,hot,.52)*accent*(.30+.32*u_strike);
    col*=life*(.88+.22*speedLift);
    float a=life*clamp(core+shell*.70+halo*.26+accent*.14,0.0,1.0);
    fragColor=vec4(col,a);
}
"""

_COMPOSITE_FRAGMENT = r"""
#version 330
uniform sampler2D u_prev;
uniform sampler2D u_particles;
uniform vec2 u_resolution;
uniform float u_feedback;
uniform float u_time;
uniform float u_bloom;
uniform float u_strike;
uniform float u_drop;
in vec2 v_uv;
out vec4 fragColor;

vec3 brightOnly(vec3 c,float threshold){
    float m=max(c.r,max(c.g,c.b));
    float k=max((m-threshold)/max(m,1e-4),0.0);
    return c*k;
}

void main(){
    vec2 uv=v_uv;
    vec2 p=uv-.5;
    vec2 px=1.0/u_resolution;
    vec2 flow=vec2(sin(uv.y*9.0+u_time*.21),cos(uv.x*8.0-u_time*.17));
    vec3 prev=texture(u_prev,uv-flow*px*(.75+.55*u_bloom)).rgb;
    prev*=u_feedback*.965;
    prev=max(prev-vec3(.0016),vec3(0.0));

    vec3 cur=texture(u_particles,uv).rgb;
    vec3 bloom=vec3(0.0);
    vec2 taps[12]=vec2[12](
        vec2(2,0),vec2(-2,0),vec2(0,2),vec2(0,-2),
        vec2(4,4),vec2(-4,4),vec2(4,-4),vec2(-4,-4),
        vec2(8,0),vec2(-8,0),vec2(0,8),vec2(0,-8)
    );
    for(int i=0;i<12;++i) bloom+=brightOnly(texture(u_particles,uv+px*taps[i]).rgb,.16);
    bloom*=(u_bloom/12.0)*.74;

    vec3 col=prev+cur*1.24+bloom;
    col*=1.0+.24*u_strike+.32*u_drop;
    col=vec3(1.0)-exp(-max(col,vec3(0.0))*1.28);
    col=pow(col,vec3(.76));
    float vignette=1.0-smoothstep(.18,.98,length(p));
    col*=mix(.80,1.0,vignette);
    float peak=max(col.r,max(col.g,col.b));
    col*=smoothstep(.012,.055,peak);
    fragColor=vec4(clamp(col,0.0,1.0),1.0);
}
"""


class GPUParticleField:
    """OpenGL 3.3 particle simulation/render pipeline with reusable emissive materials."""

    PALETTES={"cyan_magenta":0,"cyber":0,"solar":1,"bio":2,"prismatic":3,"ultraviolet":4,"deep_ocean":5,"sunset_neon":6}
    MATERIALS={"plasma":0,"comet":1,"spark":2,"mote":3,"shock_ring":4,"data_point":5}
    FIELD_MODES={"flow":0,"nebula":1,"binary_star":2,"event_horizon":3,"cosmic_roam":4,"circuit":5}

    def __init__(
        self,
        width:int,
        height:int,
        *,
        capacity:int=32768,
        palette:str="cyan_magenta",
        material:str="plasma",
    )->None:
        import moderngl

        self.moderngl=moderngl
        self.width=int(width)
        self.height=int(height)
        self.capacity=int(np.clip(capacity,1024,131072))
        self.palette=self.PALETTES.get(palette,0)
        self.material=self.MATERIALS.get(material,0)
        self.ctx,info=create_context(require=330)
        self.backend=info.backend
        self.context_info=info

        tri=np.asarray([-1.0,-1.0,3.0,-1.0,-1.0,3.0],dtype="f4")
        self.tri_vbo=self.ctx.buffer(tri.tobytes())
        self.update_program=self.ctx.program(vertex_shader=_FULLSCREEN_VERTEX,fragment_shader=_UPDATE_FRAGMENT)
        self.update_vao=self.ctx.simple_vertex_array(self.update_program,self.tri_vbo,"in_pos")
        self.particle_program=self.ctx.program(vertex_shader=_PARTICLE_VERTEX,fragment_shader=_PARTICLE_FRAGMENT)
        self.particle_vao=self.ctx.vertex_array(self.particle_program,[])
        self.composite_program=self.ctx.program(vertex_shader=_FULLSCREEN_VERTEX,fragment_shader=_COMPOSITE_FRAGMENT)
        self.composite_vao=self.ctx.simple_vertex_array(self.composite_program,self.tri_vbo,"in_pos")

        zero=np.zeros((1,self.capacity,4),dtype=np.float32)
        self.state0=[self.ctx.texture((self.capacity,1),4,zero.tobytes(),dtype="f4") for _ in range(2)]
        self.state1=[self.ctx.texture((self.capacity,1),4,zero.tobytes(),dtype="f4") for _ in range(2)]
        self.state_fbo=[self.ctx.framebuffer(color_attachments=[self.state0[i],self.state1[i]]) for i in range(2)]
        self.state_index=0
        self.particle_tex=self.ctx.texture((self.width,self.height),4,dtype="f1")
        self.particle_fbo=self.ctx.framebuffer(color_attachments=[self.particle_tex])
        self.feedback_tex=[self.ctx.texture((self.width,self.height),3,dtype="f1") for _ in range(2)]
        self.feedback_fbo=[self.ctx.framebuffer(color_attachments=[t]) for t in self.feedback_tex]
        self.feedback_index=0
        for fbo in self.feedback_fbo:
            fbo.clear(0.0,0.0,0.0,1.0)

        self.update_program["u_state0"].value=0
        self.update_program["u_state1"].value=1
        self.particle_program["u_state0"].value=0
        self.particle_program["u_state1"].value=1
        self.composite_program["u_prev"].value=0
        self.composite_program["u_particles"].value=1

    @staticmethod
    def _emitter_arrays(emitters:list[ParticleEmitter])->tuple[np.ndarray,np.ndarray]:
        body=np.zeros((8,4),dtype=np.float32)
        meta=np.zeros((8,4),dtype=np.float32)
        for i,e in enumerate(emitters[:8]):
            body[i]=(e.x,e.y,e.vx,e.vy)
            meta[i]=(max(e.energy,0.0),e.hue%1.0,max(e.radius,0.001),0.0)
        return body,meta

    def set_material(self,material:str)->None:
        if material not in self.MATERIALS:
            raise ValueError(f"unknown particle material {material!r}; choices: {', '.join(self.MATERIALS)}")
        self.material=self.MATERIALS[material]

    def render(
        self,
        emitters:list[ParticleEmitter],
        *,
        t:float,
        dt:float,
        emission_rate:float=6000.0,
        turbulence:float=0.22,
        drag:float=1.1,
        feedback:float=0.925,
        bloom:float=1.0,
        energy:float=1.0,
        bass:float=0.0,
        strike:float=0.0,
        drop:float=0.0,
        field_mode:str="flow",
        field_strength:float=1.0,
        field_scale:float=1.0,
        field_spin:float=1.0,
        well_strength:float=0.0,
        nebula_mix:float=0.0,
    )->np.ndarray:
        m=self.moderngl
        dt=float(np.clip(dt,1e-4,0.08))
        src=self.state_index
        dst=1-src
        body,meta=self._emitter_arrays(emitters)

        self.state0[src].use(0)
        self.state1[src].use(1)
        p=self.update_program
        p["u_time"].value=float(t)
        p["u_dt"].value=dt
        p["u_emit_rate"].value=float(max(emission_rate,0.0))
        p["u_turbulence"].value=float(max(turbulence,0.0))
        p["u_drag"].value=float(max(drag,0.0))
        p["u_bass"].value=float(np.clip(bass,0.0,1.0))
        p["u_strike"].value=float(np.clip(strike,0.0,1.0))
        p["u_drop"].value=float(np.clip(drop,0.0,1.0))
        if field_mode not in self.FIELD_MODES:
            raise ValueError(f"unknown particle field {field_mode!r}; choices: {', '.join(self.FIELD_MODES)}")
        p["u_field_mode"].value=self.FIELD_MODES[field_mode]
        p["u_field_strength"].value=float(np.clip(field_strength,0.0,4.0))
        p["u_field_scale"].value=float(np.clip(field_scale,0.10,6.0))
        p["u_field_spin"].value=float(np.clip(field_spin,-3.0,3.0))
        p["u_well_strength"].value=float(np.clip(well_strength,0.0,4.0))
        p["u_nebula_mix"].value=float(np.clip(nebula_mix,0.0,3.0))
        p["u_capacity"].value=self.capacity
        p["u_emitter_count"].value=min(len(emitters),8)
        p["u_emitters"].write(body.tobytes())
        p["u_emit_meta"].write(meta.tobytes())
        self.state_fbo[dst].use()
        self.ctx.viewport=(0,0,self.capacity,1)
        self.ctx.disable(m.BLEND)
        self.update_vao.render(mode=m.TRIANGLES)
        self.state_index=dst

        self.particle_fbo.use()
        self.ctx.viewport=(0,0,self.width,self.height)
        self.particle_fbo.clear(0.0,0.0,0.0,0.0)
        self.state0[dst].use(0)
        self.state1[dst].use(1)
        pp=self.particle_program
        pp["u_energy"].value=float(max(energy,0.0))
        pp["u_resolution"].value=(float(self.width),float(self.height))
        pp["u_material"].value=self.material
        pp["u_palette"].value=self.palette
        pp["u_strike"].value=float(np.clip(strike,0.0,1.0))
        self.ctx.enable(m.BLEND)
        self.ctx.blend_func=(m.ONE,m.ONE)
        self.particle_vao.render(mode=m.POINTS,vertices=self.capacity)
        self.ctx.disable(m.BLEND)

        prev=self.feedback_index
        nxt=1-prev
        self.feedback_tex[prev].use(0)
        self.particle_tex.use(1)
        cp=self.composite_program
        cp["u_resolution"].value=(float(self.width),float(self.height))
        cp["u_feedback"].value=float(np.clip(feedback,0.0,0.995))
        cp["u_time"].value=float(t)
        cp["u_bloom"].value=float(max(bloom,0.0))
        cp["u_strike"].value=float(np.clip(strike,0.0,1.0))
        cp["u_drop"].value=float(np.clip(drop,0.0,1.0))
        self.feedback_fbo[nxt].use()
        self.ctx.viewport=(0,0,self.width,self.height)
        self.composite_vao.render(mode=m.TRIANGLES)
        self.feedback_index=nxt

        data=self.feedback_fbo[nxt].read(components=3,alignment=1)
        frame=np.frombuffer(data,dtype=np.uint8).reshape(self.height,self.width,3)
        return np.flipud(frame).copy()

    def close(self)->None:
        objects=[
            *self.state_fbo,*self.state0,*self.state1,self.particle_fbo,self.particle_tex,
            *self.feedback_fbo,*self.feedback_tex,self.update_vao,self.particle_vao,
            self.composite_vao,self.update_program,self.particle_program,self.composite_program,
            self.tri_vbo,
        ]
        for obj in objects:
            try:
                obj.release()
            except Exception:
                pass
        try:
            self.ctx.release()
        except Exception:
            pass


__all__=["ParticleEmitter","GPUParticleField"]
