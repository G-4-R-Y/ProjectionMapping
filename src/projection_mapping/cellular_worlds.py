from __future__ import annotations

import numpy as np

from .graphics_runtime import create_context


CELLULAR_MODES = ("conway_life", "brians_brain", "cyclic_8", "seeds")
CELLULAR_PALETTES = ("electric", "bio", "solar", "ultraviolet", "icefire")

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
uniform ivec2 u_size;
uniform int u_mode;
uniform float u_time;
uniform float u_drive;
in vec2 v_uv;
out float fragState;

float h21(vec2 p){
    p=fract(p*vec2(123.34,345.45));
    p+=dot(p,p+34.345);
    return fract(p.x*p.y);
}

float cell(ivec2 q){
    q=(q%u_size+u_size)%u_size;
    return texelFetch(u_state,q,0).r;
}

void main(){
    ivec2 q=ivec2(gl_FragCoord.xy);
    float s=cell(q);
    int live=0;
    for(int y=-1;y<=1;y++){
        for(int x=-1;x<=1;x++){
            if(x==0 && y==0) continue;
            if(cell(q+ivec2(x,y))>.75) live++;
        }
    }

    float next=s;
    if(u_mode==0){
        bool alive=s>.5;
        next=((alive && (live==2 || live==3)) || (!alive && live==3))?1.0:0.0;
    } else if(u_mode==1){
        // Brian's Brain: 1=on, .5=dying, 0=off; births require exactly two on neighbours.
        if(s>.75) next=.5;
        else if(s>.25) next=0.0;
        else next=(live==2)?1.0:0.0;
    } else if(u_mode==2){
        int level=int(floor(s*7.0+.5));
        int target=(level+1)%8;
        int followers=0;
        for(int y=-1;y<=1;y++){
            for(int x=-1;x<=1;x++){
                if(x==0 && y==0) continue;
                int n=int(floor(cell(q+ivec2(x,y))*7.0+.5));
                if(n==target) followers++;
            }
        }
        if(followers>=2) level=target;
        next=float(level)/7.0;
    } else {
        // Seeds B2/S0: every live cell dies; exactly two neighbours create a new cell.
        next=(s<=.5 && live==2)?1.0:0.0;
    }

    // Rare deterministic stimulation prevents long-running installation states from collapsing.
    // It is intentionally much slower than frame-rate noise and can be disabled with drive=0.
    float tick=floor(u_time*.45);
    float impulse=h21(vec2(q)+vec2(tick*13.17,tick*3.71));
    float rate=clamp(u_drive,0.0,2.5)*.00016;
    if(impulse>1.0-rate){
        if(u_mode==2) next=fract(s+1.0/7.0);
        else next=1.0;
    }
    fragState=next;
}
"""

_DISPLAY = r"""
#version 330
uniform sampler2D u_state;
uniform vec2 u_texel;
uniform int u_mode;
uniform int u_palette;
uniform float u_time;
uniform float u_intensity;
uniform float u_bass;
uniform float u_mids;
uniform float u_highs;
uniform float u_beat;
uniform float u_drop;
in vec2 v_uv;
out vec4 fragColor;
#define TAU 6.28318530718

vec3 pal(float t){
    t=fract(t);
    if(u_palette==1) return .50+.50*cos(TAU*(vec3(.84,1.0,.70)*t+vec3(.42,.03,.20)));
    if(u_palette==2) return .50+.50*cos(TAU*(vec3(1.0,.74,.55)*t+vec3(.02,.08,.16)));
    if(u_palette==3) return .50+.50*cos(TAU*(vec3(.94,.74,1.0)*t+vec3(.72,.21,.03)));
    if(u_palette==4) return .50+.50*cos(TAU*(vec3(1.0,.72,.82)*t+vec3(.55,.90,.12)));
    return .50+.50*cos(TAU*(vec3(1.0,.82,.63)*t+vec3(.56,.11,.02)));
}

void main(){
    float s=texture(u_state,v_uv).r;
    float sx=texture(u_state,v_uv+vec2(u_texel.x,0)).r-texture(u_state,v_uv-vec2(u_texel.x,0)).r;
    float sy=texture(u_state,v_uv+vec2(0,u_texel.y)).r-texture(u_state,v_uv-vec2(0,u_texel.y)).r;
    float edge=clamp(length(vec2(sx,sy)),0.0,1.0);
    float value=s;
    float hue=s*.73+u_time*.006+u_mids*.12;
    if(u_mode==1){
        value=s>.75?1.0:(s>.25?.42:0.0);
        hue=s>.75?.54:.78;
    } else if(u_mode==2){
        value=.36+.64*s;
        hue=s+u_time*.009;
    }
    vec3 col=pal(hue)*(value*(1.15+.22*u_bass)+edge*(.62+.46*u_highs));
    col+=vec3(1.0,.985,.95)*pow(edge,3.0)*(.14+.32*u_beat+.28*u_drop);
    col*=.78+.42*u_intensity;
    col=vec3(1.0)-exp(-max(col,vec3(0.0))*1.26);
    col=pow(col,vec3(.78));
    float peak=max(col.r,max(col.g,col.b));
    col*=smoothstep(.006,.052,peak);
    fragColor=vec4(clamp(col,0.0,1.0),1.0);
}
"""


class CellularWorldRenderer:
    """Stateful discrete cellular automata using ping-pong GPU textures."""

    def __init__(
        self,
        width: int,
        height: int,
        *,
        mode: str = "conway_life",
        palette: str = "electric",
        density: float = 0.18,
        seed: int = 17,
    ) -> None:
        import moderngl

        if mode not in CELLULAR_MODES:
            raise ValueError(mode)
        if palette not in CELLULAR_PALETTES:
            raise ValueError(palette)
        self.moderngl=moderngl
        self.width=int(width)
        self.height=int(height)
        self.mode=mode
        self.palette=palette
        self.density=float(np.clip(density,0.001,0.95))
        self._seed=int(seed)
        self.ctx,self.context_info=create_context(require=330)
        self.backend=self.context_info.backend
        self.update_program=self.ctx.program(vertex_shader=_VERTEX,fragment_shader=_UPDATE)
        self.display_program=self.ctx.program(vertex_shader=_VERTEX,fragment_shader=_DISPLAY)
        vertices=np.asarray([-1.0,-1.0,3.0,-1.0,-1.0,3.0],dtype="f4")
        self.vbo=self.ctx.buffer(vertices.tobytes())
        self.update_vao=self.ctx.simple_vertex_array(self.update_program,self.vbo,"in_pos")
        self.display_vao=self.ctx.simple_vertex_array(self.display_program,self.vbo,"in_pos")
        self.state=[
            self.ctx.texture((self.width,self.height),1,dtype="f4"),
            self.ctx.texture((self.width,self.height),1,dtype="f4"),
        ]
        for tex in self.state:
            tex.filter=(moderngl.NEAREST,moderngl.NEAREST)
            tex.repeat_x=True
            tex.repeat_y=True
        self.state_fbo=[
            self.ctx.framebuffer(color_attachments=[self.state[0]]),
            self.ctx.framebuffer(color_attachments=[self.state[1]]),
        ]
        self.target=self.ctx.texture((self.width,self.height),3,dtype="f1")
        self.target_fbo=self.ctx.framebuffer(color_attachments=[self.target])
        self._index=0
        self.update_program["u_state"].value=0
        self.update_program["u_size"].value=(self.width,self.height)
        self.display_program["u_state"].value=0
        self.display_program["u_texel"].value=(1.0/self.width,1.0/self.height)
        self.reset(seed=self._seed)

    def reset(self, *, seed: int | None = None, density: float | None = None) -> None:
        rng=np.random.default_rng(self._seed if seed is None else int(seed))
        density=self.density if density is None else float(np.clip(density,0.001,0.95))
        if self.mode=="cyclic_8":
            state=rng.integers(0,8,size=(self.height,self.width),dtype=np.int16).astype(np.float32)/7.0
        elif self.mode=="brians_brain":
            r=rng.random((self.height,self.width))
            state=np.zeros((self.height,self.width),dtype=np.float32)
            state[r<density]=1.0
            state[(r>=density)&(r<density*1.22)]=.5
        else:
            state=(rng.random((self.height,self.width))<density).astype(np.float32)
        payload=state[...,None]
        self.state[0].write(payload.tobytes())
        self.state[1].write(payload.tobytes())
        self._index=0

    def render(
        self,
        *,
        t: float,
        intensity: float = 1.0,
        drive: float = 0.12,
        steps: int = 1,
        signals=None,
    ) -> np.ndarray:
        bass=mids=highs=beat=drop=0.0
        if signals is not None:
            bass=float(getattr(signals,"bass",0.0))
            mids=float(getattr(signals,"mids",0.0))
            highs=float(getattr(signals,"highs",0.0))
            beat=float(getattr(signals,"beat",0.0))
            drop=float(getattr(signals,"drop",0.0))
        mode_index=CELLULAR_MODES.index(self.mode)
        p=self.update_program
        p["u_mode"].value=mode_index
        p["u_time"].value=float(t)
        p["u_drive"].value=float(np.clip(drive+.35*beat+.45*drop,0.0,2.5))
        self.ctx.viewport=(0,0,self.width,self.height)
        for _ in range(max(1,int(steps))):
            src=self._index
            dst=1-src
            self.state[src].use(location=0)
            self.state_fbo[dst].use()
            self.update_vao.render(mode=self.moderngl.TRIANGLES)
            self._index=dst

        d=self.display_program
        d["u_mode"].value=mode_index
        d["u_palette"].value=CELLULAR_PALETTES.index(self.palette)
        d["u_time"].value=float(t)
        d["u_intensity"].value=float(max(intensity,0.0))
        d["u_bass"].value=float(np.clip(bass,0.0,1.0))
        d["u_mids"].value=float(np.clip(mids,0.0,1.0))
        d["u_highs"].value=float(np.clip(highs,0.0,1.0))
        d["u_beat"].value=float(np.clip(beat,0.0,1.0))
        d["u_drop"].value=float(np.clip(drop,0.0,1.0))
        self.state[self._index].use(location=0)
        self.target_fbo.use()
        self.target_fbo.clear(0.0,0.0,0.0,1.0)
        self.display_vao.render(mode=self.moderngl.TRIANGLES)
        data=self.target_fbo.read(components=3,alignment=1)
        return np.flipud(np.frombuffer(data,dtype=np.uint8).reshape(self.height,self.width,3)).copy()

    def close(self) -> None:
        for obj in (
            self.target_fbo,self.target,*self.state_fbo,*self.state,
            self.display_vao,self.update_vao,self.vbo,self.display_program,self.update_program,
        ):
            try:
                obj.release()
            except Exception:
                pass
        try:
            self.ctx.release()
        except Exception:
            pass


__all__=["CELLULAR_MODES","CELLULAR_PALETTES","CellularWorldRenderer"]
