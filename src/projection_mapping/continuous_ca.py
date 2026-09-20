from __future__ import annotations

import numpy as np

from .graphics_runtime import create_context


CONTINUOUS_CA_MODES = (
    "lenia_ring",
    "smoothlife",
    "continuous_life",
    "cyclic_lenia",
    "excitable_garden",
    "orbium_study",
)
CONTINUOUS_CA_PALETTES = ("cyan_magenta", "spectral", "electric", "solar", "bio", "ultraviolet", "icefire")

_VERTEX = r"""
#version 330
in vec2 in_pos;
out vec2 v_uv;
void main(){v_uv=in_pos*.5+.5;gl_Position=vec4(in_pos,0.0,1.0);}
"""

_UPDATE = r"""
#version 330
uniform sampler2D u_state;
uniform vec2 u_texel;
uniform float u_time;
uniform float u_dt;
uniform float u_mu;
uniform float u_sigma;
uniform float u_radius;
uniform float u_drive;
uniform int u_mode;
in vec2 v_uv;
out float out_state;
#define PI 3.141592653589793
#define TAU 6.283185307179586

float sampleState(vec2 uv){return texture(u_state,uv).r;}
float sigmoid(float x,float k){return 1.0/(1.0+exp(-x*k));}

float ringMean(vec2 uv,float radius){
    float s=0.0;
    for(int i=0;i<16;i++){
        float a=TAU*(float(i)+.5)/16.0;
        vec2 o=vec2(cos(a),sin(a))*u_texel*radius;
        s+=sampleState(uv+o);
    }
    return s/16.0;
}
float innerMean(vec2 uv,float radius){
    float s=sampleState(uv)*.22;
    for(int i=0;i<8;i++){
        float a=TAU*float(i)/8.0;
        vec2 o=vec2(cos(a),sin(a))*u_texel*radius*.48;
        s+=sampleState(uv+o)*.0975;
    }
    return s;
}

void main(){
    vec2 uv=v_uv;
    float a=sampleState(uv);
    float outer=ringMean(uv,u_radius);
    float inner=innerMean(uv,u_radius);
    float next=a;
    if(u_mode==0 || u_mode==5){
        float mu=u_mu+(u_mode==5?.015*sin(u_time*.061):0.0);
        float sig=max(u_sigma,0.008);
        float growth=2.0*exp(-.5*pow((outer-mu)/sig,2.0))-1.0;
        float inertia=u_mode==5?.78:1.0;
        next=clamp(a+u_dt*growth*inertia,0.0,1.0);
    }else if(u_mode==1){
        float birth=sigmoid(outer-.278,32.0)*(1.0-sigmoid(outer-.365,32.0));
        float survive=sigmoid(outer-.235,28.0)*(1.0-sigmoid(outer-.405,28.0));
        float target=mix(birth,survive,sigmoid(inner-.50,18.0));
        next=mix(a,target,clamp(u_dt*3.0,0.0,1.0));
    }else if(u_mode==2){
        float target=sigmoid(outer-.31,22.0)*(1.0-sigmoid(outer-.58,20.0));
        target=mix(target,1.0-target,.15*sin(u_time*.11+inner*TAU));
        next=clamp(a+(target-a)*u_dt*2.0,0.0,1.0);
    }else if(u_mode==3){
        float phase=.5+.5*sin(outer*TAU*3.0+u_time*(.35+.8*u_drive));
        float growth=2.0*exp(-.5*pow((outer-(u_mu+.05*(phase-.5)))/max(u_sigma,.01),2.0))-1.0;
        next=clamp(a+u_dt*growth,0.0,1.0);
    }else{
        float excite=sigmoid(outer-.34,30.0)*(1.0-a);
        float recover=sigmoid(a-.68,24.0)*(.45+.55*inner);
        next=clamp(a+u_dt*(excite*1.7-recover*.92-.08*a),0.0,1.0);
    }
    // Gentle performer/audio-style drive: rare local seed source rather than global flashing.
    vec2 p=uv*2.0-1.0;
    vec2 c=.38*vec2(sin(u_time*.083),cos(u_time*.067));
    float source=exp(-dot(p-c,p-c)*110.0)*u_drive*.012;
    next=clamp(next+source,0.0,1.0);
    out_state=next;
}
"""

_DISPLAY = r"""
#version 330
uniform sampler2D u_state;
uniform vec2 u_texel;
uniform float u_time;
uniform float u_intensity;
uniform int u_palette;
in vec2 v_uv;
out vec4 fragColor;
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
void main(){
    float a=texture(u_state,v_uv).r;
    float gx=texture(u_state,v_uv+vec2(u_texel.x,0)).r-texture(u_state,v_uv-vec2(u_texel.x,0)).r;
    float gy=texture(u_state,v_uv+vec2(0,u_texel.y)).r-texture(u_state,v_uv-vec2(0,u_texel.y)).r;
    float edge=clamp(length(vec2(gx,gy))*4.5,0.0,1.0);
    float body=pow(clamp(a,0.0,1.0),1.45);
    vec3 col=pal(a*.47+edge*.18+u_time*.004)*(body*.50+edge*.95);
    col+=vec3(1.0,.985,.95)*pow(edge,4.0)*.16;
    col*=.72+.55*u_intensity;
    col=vec3(1.0)-exp(-max(col,vec3(0.0))*1.22);
    col=pow(col,vec3(.80));
    fragColor=vec4(clamp(col,0.0,1.0),1.0);
}
"""


class ContinuousCARenderer:
    """Stateful GPU continuous CA with Lenia/SmoothLife-inspired update families.

    The Lenia modes use a finite 16-sample ring-kernel approximation for realtime
    projector use; this is an artistic realtime baseline rather than a numerical
    reproduction of every reference Lenia kernel.
    """

    def __init__(self, width: int, height: int, *, mode: str = "lenia_ring", palette: str = "bio", seed: int = 23) -> None:
        import moderngl

        if mode not in CONTINUOUS_CA_MODES:
            raise ValueError(mode)
        if palette not in CONTINUOUS_CA_PALETTES:
            raise ValueError(palette)
        self.moderngl = moderngl
        self.width = int(width)
        self.height = int(height)
        self.mode = mode
        self.palette = palette
        self.ctx, self.context_info = create_context(require=330)
        self.backend = self.context_info.backend
        self.update_program = self.ctx.program(vertex_shader=_VERTEX, fragment_shader=_UPDATE)
        self.display_program = self.ctx.program(vertex_shader=_VERTEX, fragment_shader=_DISPLAY)
        vertices = np.asarray([-1.0, -1.0, 3.0, -1.0, -1.0, 3.0], dtype="f4")
        self.vbo = self.ctx.buffer(vertices.tobytes())
        self.update_vao = self.ctx.simple_vertex_array(self.update_program, self.vbo, "in_pos")
        self.display_vao = self.ctx.simple_vertex_array(self.display_program, self.vbo, "in_pos")
        self.state = [self.ctx.texture((self.width, self.height), 1, dtype="f4") for _ in range(2)]
        for texture in self.state:
            texture.repeat_x = True
            texture.repeat_y = True
            texture.filter = (self.moderngl.LINEAR, self.moderngl.LINEAR)
        self.state_fbo = [self.ctx.framebuffer(color_attachments=[texture]) for texture in self.state]
        self.target = self.ctx.texture((self.width, self.height), 3, dtype="f1")
        self.target_fbo = self.ctx.framebuffer(color_attachments=[self.target])
        texel = (1.0 / self.width, 1.0 / self.height)
        self.update_program["u_texel"].value = texel
        self.display_program["u_texel"].value = texel
        self._front = 0
        self.reset(seed=seed)

    def reset(self, *, seed: int = 23, density: float = 0.22) -> None:
        rng = np.random.default_rng(seed)
        state = (rng.random((self.height, self.width)) < float(np.clip(density, 0.01, 0.95))).astype(np.float32)
        # Blur-ish average gives continuous initial material instead of binary TV snow.
        state = (state + np.roll(state, 1, 0) + np.roll(state, -1, 0) + np.roll(state, 1, 1) + np.roll(state, -1, 1)) / 5.0
        raw = np.flipud(state.astype(np.float32)).tobytes()
        self.state[0].write(raw)
        self.state[1].write(raw)
        self._front = 0

    def render(self, *, t: float, mode: str | None = None, palette: str | None = None, intensity: float = 1.0, dt: float = 0.10, growth_center: float = 0.28, growth_width: float = 0.055, kernel_radius: float = 6.0, drive: float = 0.10, steps: int = 2) -> np.ndarray:
        mode = mode or self.mode
        palette = palette or self.palette
        if mode not in CONTINUOUS_CA_MODES:
            raise ValueError(mode)
        if palette not in CONTINUOUS_CA_PALETTES:
            raise ValueError(palette)
        for _ in range(max(1, int(steps))):
            src = self.state[self._front]
            dst_index = 1 - self._front
            self.state_fbo[dst_index].use()
            self.ctx.viewport = (0, 0, self.width, self.height)
            src.use(location=0)
            p = self.update_program
            p["u_state"].value = 0
            p["u_time"].value = float(t)
            p["u_dt"].value = float(np.clip(dt, 0.005, 0.35))
            p["u_mu"].value = float(np.clip(growth_center, 0.02, 0.95))
            p["u_sigma"].value = float(np.clip(growth_width, 0.008, 0.30))
            p["u_radius"].value = float(np.clip(kernel_radius, 1.0, 18.0))
            p["u_drive"].value = float(np.clip(drive, 0.0, 1.5))
            p["u_mode"].value = CONTINUOUS_CA_MODES.index(mode)
            self.update_vao.render(mode=self.moderngl.TRIANGLES)
            self._front = dst_index

        self.target_fbo.use()
        self.ctx.viewport = (0, 0, self.width, self.height)
        self.state[self._front].use(location=0)
        d = self.display_program
        d["u_state"].value = 0
        d["u_time"].value = float(t)
        d["u_intensity"].value = float(max(intensity, 0.0))
        d["u_palette"].value = CONTINUOUS_CA_PALETTES.index(palette)
        self.display_vao.render(mode=self.moderngl.TRIANGLES)
        data = self.target_fbo.read(components=3, alignment=1)
        return np.flipud(np.frombuffer(data, dtype=np.uint8).reshape(self.height, self.width, 3)).copy()

    def close(self) -> None:
        objects = [*self.state_fbo, *self.state, self.target_fbo, self.target, self.update_vao, self.display_vao, self.vbo, self.update_program, self.display_program]
        for obj in objects:
            try:
                obj.release()
            except Exception:
                pass
        try:
            self.ctx.release()
        except Exception:
            pass


__all__ = ["CONTINUOUS_CA_MODES", "CONTINUOUS_CA_PALETTES", "ContinuousCARenderer"]
