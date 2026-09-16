from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .graphics_runtime import create_context


@dataclass(frozen=True)
class ReactionPreset:
    feed: float
    kill: float
    du: float = 0.16
    dv: float = 0.08


REACTION_PRESETS: dict[str, ReactionPreset] = {
    "coral": ReactionPreset(0.0545, 0.0620),
    "mitosis": ReactionPreset(0.0367, 0.0649),
    "worms": ReactionPreset(0.0780, 0.0610),
    "maze": ReactionPreset(0.0290, 0.0570),
    "solitons": ReactionPreset(0.0300, 0.0620),
    "waves": ReactionPreset(0.0140, 0.0540),
}

REACTION_PALETTES = ("ultraviolet", "bio", "solar", "electric", "mono")

_VERTEX = r"""
#version 330
in vec2 in_pos;
out vec2 v_uv;
void main(){
    v_uv=in_pos*.5+.5;
    gl_Position=vec4(in_pos,0.0,1.0);
}
"""

_UPDATE = r"""
#version 330
uniform sampler2D u_state;
uniform vec2 u_texel;
uniform float u_feed;
uniform float u_kill;
uniform float u_du;
uniform float u_dv;
uniform float u_dt;
uniform float u_time;
uniform float u_drive;
in vec2 v_uv;
out vec2 fragState;

vec2 sampleState(vec2 off){ return texture(u_state,v_uv+off*u_texel).rg; }

void main(){
    vec2 c=texture(u_state,v_uv).rg;
    vec2 lap=-c;
    lap+=.20*(sampleState(vec2(1,0))+sampleState(vec2(-1,0))+sampleState(vec2(0,1))+sampleState(vec2(0,-1)));
    lap+=.05*(sampleState(vec2(1,1))+sampleState(vec2(-1,1))+sampleState(vec2(1,-1))+sampleState(vec2(-1,-1)));
    float u=c.r;
    float v=c.g;
    float uvv=u*v*v;
    float spatial=.5+.5*sin((v_uv.x*1.31+v_uv.y*.77)*12.0+u_time*.11);
    float feed=u_feed + u_drive*.0018*(spatial-.5);
    float kill=u_kill + u_drive*.0012*sin(v_uv.y*9.0-u_time*.09);
    float du=u_du*lap.r-uvv+feed*(1.0-u);
    float dv=u_dv*lap.g+uvv-(feed+kill)*v;
    fragState=clamp(c+vec2(du,dv)*u_dt,0.0,1.0);
}
"""

_DISPLAY = r"""
#version 330
uniform sampler2D u_state;
uniform vec2 u_texel;
uniform float u_time;
uniform float u_intensity;
uniform float u_bass;
uniform float u_mids;
uniform float u_highs;
uniform float u_beat;
uniform float u_drop;
uniform int u_palette;
in vec2 v_uv;
out vec4 fragColor;

#define TAU 6.28318530718
vec3 pal(float t){
    t=fract(t);
    if(u_palette==1) return .50+.50*cos(TAU*(vec3(.82,1.00,.68)*t+vec3(.40,.02,.22)));
    if(u_palette==2) return .50+.50*cos(TAU*(vec3(1.0,.74,.55)*t+vec3(.02,.08,.16)));
    if(u_palette==3) return .50+.50*cos(TAU*(vec3(1.0,.82,.64)*t+vec3(.56,.12,.01)));
    if(u_palette==4) return vec3(.76+.24*cos(TAU*t));
    return .50+.50*cos(TAU*(vec3(.92,.74,1.0)*t+vec3(.72,.20,.03)));
}

void main(){
    vec2 s=texture(u_state,v_uv).rg;
    float v=s.g;
    float u=s.r;
    float dx=texture(u_state,v_uv+vec2(u_texel.x,0)).g-texture(u_state,v_uv-vec2(u_texel.x,0)).g;
    float dy=texture(u_state,v_uv+vec2(0,u_texel.y)).g-texture(u_state,v_uv-vec2(0,u_texel.y)).g;
    float edge=sqrt(dx*dx+dy*dy);
    float phase=v*1.72-u*.36+edge*4.2+u_time*.008;
    vec3 col=pal(phase)*(v*1.45+edge*2.4);
    col+=pal(.64+phase*.28)*pow(max(v-.18,0.0),1.8)*1.2;
    col+=vec3(1.0,.98,.94)*pow(clamp(edge*5.0,0.0,1.0),3.0)*(.24+.36*u_highs+.32*u_beat);
    col*=.78+.40*u_intensity+.18*u_bass;
    col*=1.0+.25*u_drop;
    col=vec3(1.0)-exp(-max(col,vec3(0.0))*1.22);
    col=pow(col,vec3(.80));
    float peak=max(col.r,max(col.g,col.b));
    col*=smoothstep(.008,.055,peak);
    fragColor=vec4(clamp(col,0.0,1.0),1.0);
}
"""


class ReactionDiffusionRenderer:
    """Stateful Gray-Scott reaction-diffusion simulation on ping-pong GPU textures."""

    def __init__(
        self,
        width: int,
        height: int,
        *,
        preset: str = "coral",
        palette: str = "ultraviolet",
        seed: int = 7,
    ) -> None:
        import moderngl

        if preset not in REACTION_PRESETS:
            raise ValueError(f"unknown reaction preset: {preset}")
        if palette not in REACTION_PALETTES:
            raise ValueError(f"unknown reaction palette: {palette}")
        self.moderngl = moderngl
        self.width = int(width)
        self.height = int(height)
        self.preset = preset
        self.palette = palette
        self.ctx, self.context_info = create_context(require=330)
        self.backend = self.context_info.backend
        self.update_program = self.ctx.program(vertex_shader=_VERTEX, fragment_shader=_UPDATE)
        self.display_program = self.ctx.program(vertex_shader=_VERTEX, fragment_shader=_DISPLAY)
        vertices = np.asarray([-1.0, -1.0, 3.0, -1.0, -1.0, 3.0], dtype="f4")
        self.vbo = self.ctx.buffer(vertices.tobytes())
        self.update_vao = self.ctx.simple_vertex_array(self.update_program, self.vbo, "in_pos")
        self.display_vao = self.ctx.simple_vertex_array(self.display_program, self.vbo, "in_pos")
        self.state = [
            self.ctx.texture((self.width, self.height), 2, dtype="f4"),
            self.ctx.texture((self.width, self.height), 2, dtype="f4"),
        ]
        for tex in self.state:
            tex.filter = (moderngl.NEAREST, moderngl.NEAREST)
            tex.repeat_x = True
            tex.repeat_y = True
        self.state_fbo = [
            self.ctx.framebuffer(color_attachments=[self.state[0]]),
            self.ctx.framebuffer(color_attachments=[self.state[1]]),
        ]
        self.target = self.ctx.texture((self.width, self.height), 3, dtype="f1")
        self.target_fbo = self.ctx.framebuffer(color_attachments=[self.target])
        self._index = 0
        self._seed = int(seed)
        self.reset(seed=self._seed)
        texel = (1.0 / self.width, 1.0 / self.height)
        self.update_program["u_texel"].value = texel
        self.display_program["u_texel"].value = texel
        self.update_program["u_state"].value = 0
        self.display_program["u_state"].value = 0

    def reset(self, *, seed: int | None = None) -> None:
        rng = np.random.default_rng(self._seed if seed is None else int(seed))
        state = np.zeros((self.height, self.width, 2), dtype=np.float32)
        state[..., 0] = 1.0
        yy, xx = np.mgrid[0 : self.height, 0 : self.width]
        centers = [
            (.50, .50, .075),
            (.34, .42, .042),
            (.67, .58, .050),
            (.50, .72, .030),
        ]
        for cx, cy, rr in centers:
            d2 = ((xx / self.width - cx) ** 2 + (yy / self.height - cy) ** 2)
            mask = d2 <= rr * rr
            state[..., 0][mask] = 0.48 + rng.random(np.count_nonzero(mask)) * 0.08
            state[..., 1][mask] = 0.24 + rng.random(np.count_nonzero(mask)) * 0.30
        noise = rng.normal(0.0, 0.008, size=(self.height, self.width)).astype(np.float32)
        state[..., 1] = np.clip(state[..., 1] + noise, 0.0, 1.0)
        self.state[0].write(state.tobytes())
        self.state[1].write(state.tobytes())
        self._index = 0

    def render(
        self,
        *,
        t: float,
        preset: str | None = None,
        palette: str | None = None,
        intensity: float = 1.0,
        drive: float = 0.0,
        steps: int = 8,
        dt: float = 1.0,
        signals=None,
    ) -> np.ndarray:
        preset = preset or self.preset
        palette = palette or self.palette
        if preset not in REACTION_PRESETS:
            raise ValueError(preset)
        if palette not in REACTION_PALETTES:
            raise ValueError(palette)
        pr = REACTION_PRESETS[preset]
        bass = mids = highs = beat = drop = 0.0
        if signals is not None:
            bass = float(getattr(signals, "bass", 0.0))
            mids = float(getattr(signals, "mids", 0.0))
            highs = float(getattr(signals, "highs", 0.0))
            beat = float(getattr(signals, "beat", 0.0))
            drop = float(getattr(signals, "drop", 0.0))
        drive_value = float(np.clip(drive + 0.55 * bass + 0.35 * mids + 0.65 * drop, 0.0, 2.5))
        p = self.update_program
        p["u_feed"].value = float(pr.feed)
        p["u_kill"].value = float(pr.kill)
        p["u_du"].value = float(pr.du)
        p["u_dv"].value = float(pr.dv)
        p["u_dt"].value = float(np.clip(dt, 0.05, 1.5))
        p["u_time"].value = float(t)
        p["u_drive"].value = drive_value
        self.ctx.viewport = (0, 0, self.width, self.height)
        for _ in range(max(1, int(steps))):
            src = self._index
            dst = 1 - src
            self.state[src].use(location=0)
            self.state_fbo[dst].use()
            self.update_vao.render(mode=self.moderngl.TRIANGLES)
            self._index = dst

        d = self.display_program
        d["u_time"].value = float(t)
        d["u_intensity"].value = float(max(intensity, 0.0))
        d["u_bass"].value = float(np.clip(bass, 0.0, 1.0))
        d["u_mids"].value = float(np.clip(mids, 0.0, 1.0))
        d["u_highs"].value = float(np.clip(highs, 0.0, 1.0))
        d["u_beat"].value = float(np.clip(beat, 0.0, 1.0))
        d["u_drop"].value = float(np.clip(drop, 0.0, 1.0))
        d["u_palette"].value = REACTION_PALETTES.index(palette)
        self.state[self._index].use(location=0)
        self.target_fbo.use()
        self.target_fbo.clear(0.0, 0.0, 0.0, 1.0)
        self.display_vao.render(mode=self.moderngl.TRIANGLES)
        data = self.target_fbo.read(components=3, alignment=1)
        return np.flipud(np.frombuffer(data, dtype=np.uint8).reshape(self.height, self.width, 3)).copy()

    def close(self) -> None:
        objects = [
            self.target_fbo,
            self.target,
            *self.state_fbo,
            *self.state,
            self.display_vao,
            self.update_vao,
            self.vbo,
            self.display_program,
            self.update_program,
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


__all__ = [
    "REACTION_PRESETS",
    "REACTION_PALETTES",
    "ReactionPreset",
    "ReactionDiffusionRenderer",
]
