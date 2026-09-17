from __future__ import annotations

import numpy as np

from .graphics_runtime import create_context


WAVE_MODES = (
    "membrane_drop",
    "chladni_drive",
    "multi_source_resonance",
    "spiral_wave",
    "chaotic_boundary",
    "audio_plate",
)
WAVE_PALETTES = ("spectral", "electric", "solar", "bio", "ultraviolet", "icefire")

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
uniform float u_drive;
uniform float u_tension;
uniform float u_damping;
uniform int u_mode;
in vec2 v_uv;
out vec2 out_state;
#define PI 3.141592653589793
#define TAU 6.283185307179586

float pulse(vec2 p, vec2 c, float radius){
    float d=length(p-c);
    return exp(-d*d/max(radius*radius,1e-5));
}

void main(){
    vec2 uv=v_uv;
    vec2 s=texture(u_state,uv).rg;
    float cur=s.r;
    float prev=s.g;
    float l=texture(u_state,uv-vec2(u_texel.x,0)).r;
    float r=texture(u_state,uv+vec2(u_texel.x,0)).r;
    float d=texture(u_state,uv-vec2(0,u_texel.y)).r;
    float u=texture(u_state,uv+vec2(0,u_texel.y)).r;
    float lap=l+r+d+u-4.0*cur;
    float next=(2.0-u_damping)*cur-(1.0-u_damping)*prev+u_tension*lap;

    vec2 p=uv*2.0-1.0;
    float forcing=0.0;
    if(u_mode==0){
        float beat=pow(max(sin(u_time*.72),0.0),18.0);
        forcing=pulse(p,vec2(.35*sin(u_time*.17),.28*cos(u_time*.13)),.055)*beat*.30;
    }else if(u_mode==1){
        float m=3.0+floor(1.5+.5*sin(u_time*.07));
        float n=5.0+floor(1.5+.5*cos(u_time*.061));
        forcing=sin((p.x+1.0)*PI*.5*m)*sin((p.y+1.0)*PI*.5*n)*sin(u_time*2.2)*.010;
    }else if(u_mode==2){
        for(int i=0;i<5;i++){
            float fi=float(i);
            float a=fi*TAU/5.0+u_time*.11;
            vec2 c=.54*vec2(cos(a),sin(a));
            forcing+=pulse(p,c,.045)*sin(u_time*(1.6+.07*fi)+fi)*.036;
        }
    }else if(u_mode==3){
        float a=atan(p.y,p.x);
        float rr=length(p);
        forcing=sin(a*5.0-rr*17.0-u_time*2.1)*exp(-abs(rr-.48)*11.0)*.012;
    }else if(u_mode==4){
        float edge=max(abs(p.x),abs(p.y));
        float gate=smoothstep(.82,.98,edge);
        forcing=gate*sin((p.x*7.0+p.y*11.0)+sin(u_time*.37)*4.0+u_time*1.8)*.018;
    }else{
        float m=2.0+floor(u_drive*5.0);
        float n=3.0+floor(u_drive*7.0);
        forcing=sin((p.x+1.0)*PI*.5*m)*sin((p.y+1.0)*PI*.5*n)*sin(u_time*(1.2+u_drive*3.4))*(.006+.022*u_drive);
    }
    next+=forcing*(.30+.90*u_drive);
    next=clamp(next,-1.8,1.8);
    out_state=vec2(next,cur);
}
"""

_DISPLAY = r"""
#version 330
uniform sampler2D u_state;
uniform vec2 u_texel;
uniform float u_time;
uniform float u_intensity;
uniform float u_drive;
uniform int u_palette;
in vec2 v_uv;
out vec4 fragColor;
#define TAU 6.283185307179586
vec3 pal(float t){
    t=fract(t);
    if(u_palette==1)return .50+.50*cos(TAU*(vec3(1.0,.82,.63)*t+vec3(.56,.11,.02)));
    if(u_palette==2)return .50+.50*cos(TAU*(vec3(1.0,.74,.55)*t+vec3(.02,.08,.16)));
    if(u_palette==3)return .50+.50*cos(TAU*(vec3(.84,1.0,.70)*t+vec3(.42,.03,.20)));
    if(u_palette==4)return .50+.50*cos(TAU*(vec3(.94,.74,1.0)*t+vec3(.72,.21,.03)));
    if(u_palette==5)return .50+.50*cos(TAU*(vec3(1.0,.72,.82)*t+vec3(.55,.90,.12)));
    return .50+.50*cos(TAU*(vec3(1.0,.87,.72)*t+vec3(.01,.17,.44)));
}
void main(){
    float c=texture(u_state,v_uv).r;
    float cx=texture(u_state,v_uv+vec2(u_texel.x,0)).r-texture(u_state,v_uv-vec2(u_texel.x,0)).r;
    float cy=texture(u_state,v_uv+vec2(0,u_texel.y)).r-texture(u_state,v_uv-vec2(0,u_texel.y)).r;
    float slope=length(vec2(cx,cy));
    float node=exp(-abs(c)*(26.0+18.0*u_drive));
    float ridge=pow(clamp(abs(c)*1.8+slope*2.8,0.0,1.0),.65);
    vec3 col=pal(c*.21+slope*.18+u_time*.006)*(ridge*.82+node*.42);
    col+=vec3(1.0,.985,.95)*pow(node,5.0)*.20;
    col*=.72+.55*u_intensity;
    col=vec3(1.0)-exp(-max(col,vec3(0.0))*1.25);
    col=pow(col,vec3(.79));
    fragColor=vec4(clamp(col,0.0,1.0),1.0);
}
"""


class WaveEquationRenderer:
    """Persistent damped 2-D wave equation with cymatic/eigenmode forcing."""

    def __init__(self, width: int, height: int, *, mode: str = "membrane_drop", palette: str = "spectral", seed: int = 19) -> None:
        import moderngl

        if mode not in WAVE_MODES:
            raise ValueError(mode)
        if palette not in WAVE_PALETTES:
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
        self.state = [self.ctx.texture((self.width, self.height), 2, dtype="f4") for _ in range(2)]
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

    def reset(self, *, seed: int = 19) -> None:
        rng = np.random.default_rng(seed)
        y, x = np.mgrid[0:self.height, 0:self.width].astype(np.float32)
        x = x / max(self.width - 1, 1) * 2.0 - 1.0
        y = y / max(self.height - 1, 1) * 2.0 - 1.0
        cur = np.zeros((self.height, self.width), dtype=np.float32)
        for _ in range(5):
            cx, cy = rng.uniform(-0.65, 0.65, size=2)
            rr = (x - cx) ** 2 + (y - cy) ** 2
            cur += np.exp(-rr / rng.uniform(0.0018, 0.009)).astype(np.float32) * rng.uniform(-0.45, 0.45)
        state = np.stack([cur, cur], axis=2).astype(np.float32)
        raw = np.flipud(state).tobytes()
        self.state[0].write(raw)
        self.state[1].write(raw)
        self._front = 0

    def render(self, *, t: float, mode: str | None = None, palette: str | None = None, intensity: float = 1.0, drive: float = 0.35, tension: float = 0.22, damping: float = 0.018, steps: int = 3) -> np.ndarray:
        mode = mode or self.mode
        palette = palette or self.palette
        if mode not in WAVE_MODES:
            raise ValueError(mode)
        if palette not in WAVE_PALETTES:
            raise ValueError(palette)
        drive = float(np.clip(drive, 0.0, 1.5))
        tension = float(np.clip(tension, 0.01, 0.48))
        damping = float(np.clip(damping, 0.0001, 0.20))
        for _ in range(max(1, int(steps))):
            src = self.state[self._front]
            dst_index = 1 - self._front
            self.state_fbo[dst_index].use()
            self.ctx.viewport = (0, 0, self.width, self.height)
            src.use(location=0)
            p = self.update_program
            p["u_state"].value = 0
            p["u_time"].value = float(t)
            p["u_drive"].value = drive
            p["u_tension"].value = tension
            p["u_damping"].value = damping
            p["u_mode"].value = WAVE_MODES.index(mode)
            self.update_vao.render(mode=self.moderngl.TRIANGLES)
            self._front = dst_index

        self.target_fbo.use()
        self.ctx.viewport = (0, 0, self.width, self.height)
        self.state[self._front].use(location=0)
        d = self.display_program
        d["u_state"].value = 0
        d["u_time"].value = float(t)
        d["u_intensity"].value = float(max(intensity, 0.0))
        d["u_drive"].value = drive
        d["u_palette"].value = WAVE_PALETTES.index(palette)
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


__all__ = ["WAVE_MODES", "WAVE_PALETTES", "WaveEquationRenderer"]
