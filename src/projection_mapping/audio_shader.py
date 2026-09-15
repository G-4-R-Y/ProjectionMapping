from __future__ import annotations

import time

import numpy as np

from .music_reactivity import MusicalSignals


SCENES = ("journey", "aurora", "liquid", "pulse", "void", "cathedral")
PALETTES = ("neon_aurora", "solar_flare", "bioluminescent", "intelli", "mono_accent", "prismatic")

_VERTEX = r"""
#version 330
in vec2 in_pos;
out vec2 v_uv;
void main() {
    v_uv = in_pos * 0.5 + 0.5;
    gl_Position = vec4(in_pos, 0.0, 1.0);
}
"""

_FRAGMENT = r"""
#version 330
uniform vec2 u_resolution;
uniform float u_time;
uniform float u_loud;
uniform float u_bass;
uniform float u_mids;
uniform float u_highs;
uniform float u_beat;
uniform float u_strike;
uniform float u_drop;
uniform float u_phase;
uniform float u_bar_phase;
uniform float u_tempo;
uniform float u_color;
uniform float u_madness;
uniform int u_palette;
uniform int u_scene_a;
uniform int u_scene_b;
uniform float u_scene_mix;
in vec2 v_uv;
out vec4 fragColor;

#define PI 3.141592653589793
#define TAU 6.283185307179586

float hash21(vec2 p) {
    p = fract(p * vec2(123.34, 456.21));
    p += dot(p, p + 45.32);
    return fract(p.x * p.y);
}

float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f*f*(3.0-2.0*f);
    float a = hash21(i);
    float b = hash21(i + vec2(1.0, 0.0));
    float c = hash21(i + vec2(0.0, 1.0));
    float d = hash21(i + vec2(1.0, 1.0));
    return mix(mix(a,b,f.x), mix(c,d,f.x), f.y);
}

float fbm(vec2 p) {
    float v = 0.0;
    float a = 0.5;
    mat2 rot = mat2(0.80,-0.60,0.60,0.80);
    for (int i=0; i<5; ++i) {
        v += a * noise(p);
        p = rot * p * 2.03 + vec2(0.17, -0.11);
        a *= 0.5;
    }
    return v;
}

float ridge(float x, float width) {
    return exp(-abs(x) * width);
}

vec3 cosinePalette(float t, vec3 a, vec3 b, vec3 c, vec3 d) {
    return a + b*cos(TAU*(c*t+d));
}

vec3 palette(float t) {
    t += u_color*0.18;
    if (u_palette == 1)
        return cosinePalette(t, vec3(.55,.32,.18), vec3(.48,.34,.22), vec3(1.0,.72,.55), vec3(.00,.04,.10));
    if (u_palette == 2)
        return cosinePalette(t, vec3(.26,.43,.42), vec3(.30,.48,.50), vec3(.82,1.0,.78), vec3(.47,.08,.18));
    if (u_palette == 3)
        return cosinePalette(t, vec3(.38,.28,.48), vec3(.42,.35,.44), vec3(.90,.82,.74), vec3(.55,.18,.02));
    if (u_palette == 4) {
        float v = clamp(.14 + .86*t, 0.0, 1.0);
        return mix(vec3(v*.16, v*.22, v*.28), vec3(.24,.82,1.0), smoothstep(.70,1.0,t));
    }
    if (u_palette == 5)
        return cosinePalette(t, vec3(.50), vec3(.50), vec3(1.0,.82,.67), vec3(.00,.16,.39));
    return cosinePalette(t, vec3(.42,.36,.53), vec3(.40,.44,.46), vec3(.92,.80,.72), vec3(.56,.12,.02));
}

vec2 centeredUV() {
    vec2 p = v_uv - 0.5;
    p.x *= u_resolution.x / max(u_resolution.y, 1.0);
    return p;
}

vec3 auroraScene(vec2 p) {
    float t = u_time*(0.08 + 0.10*u_mids);
    vec2 q = p*1.55;
    float n1 = fbm(q*1.6 + vec2(t, -t*.37));
    float n2 = fbm(q*2.7 + vec2(-t*.41, t*.72) + n1*1.6);
    q += vec2(n1-.5, n2-.5) * (0.42 + 0.52*u_bass);
    float bands = sin(q.y*8.0 + n1*5.0 + sin(q.x*2.4 + u_time*.18)*2.2);
    float veil = pow(max(0.0, 1.0-abs(bands)), 3.0);
    float filament = ridge(sin(q.y*17.0 + n2*9.0 + q.x*3.0), 5.0) * u_highs;
    float breath = .68 + .32*cos(TAU*u_phase);
    float energy = veil*(.38 + 1.15*u_loud)*(0.78+.22*breath) + filament*.85;
    energy += pow(n2, 5.0)*(.12+.45*u_mids);
    vec3 col = palette(n1*.55+n2*.32+u_time*.014) * energy;
    col += vec3(1.0,.90,.98) * u_strike * exp(-dot(p,p)*2.8) * .45;
    return col;
}

vec3 liquidScene(vec2 p) {
    float t = u_time*(.10+.08*u_mids);
    vec2 q = p*2.1;
    float n = fbm(q*1.7 + vec2(t,-t*.6));
    q += vec2(sin(q.y*2.7+t*2.0), cos(q.x*2.4-t*1.4))*(.10+.18*u_bass);
    q += (n-.5)*(.35+.35*u_madness);
    float a = sin(q.x*5.5 + sin(q.y*3.1+t)*2.2);
    float b = cos(q.y*6.2 + sin(q.x*2.8-t*.8)*2.4);
    float caustic = pow(clamp(1.0-abs(a*b),0.0,1.0), 7.0);
    float chrome = .5+.5*sin((a+b)*3.0+n*7.0);
    vec3 base = palette(chrome*.62+n*.38+u_time*.01);
    float spec = pow(caustic, .65) * (.55+1.2*u_loud);
    vec3 col = base*(.12+.66*spec);
    col += vec3(.82,.96,1.0)*pow(caustic,3.0)*(1.0+.85*u_highs);
    col += palette(.1+u_bar_phase)*u_beat*.18*(1.0-smoothstep(.15,1.35,length(p)));
    return col;
}

vec3 pulseScene(vec2 p) {
    float r = length(p)+1e-4;
    float a = atan(p.y,p.x);
    // Integer angular harmonics are periodic across atan's branch cut: no portal seam.
    float angular = sin(a*8.0 + u_time*.10) * .55 + sin(a*12.0-u_time*.07)*.25;
    float z = -log(r);
    float phaseDrive = u_phase*TAU;
    float rings = pow(.5+.5*sin(z*(13.0+4.0*u_bass)-phaseDrive*1.4+angular), 8.0);
    float ribs = pow(.5+.5*cos(a*12.0 + z*2.2 + u_time*.12), 10.0);
    float core = exp(-r*(4.4-1.25*u_bass));
    float pulse = exp(-pow(r-(.20+.72*u_phase),2.0)/(.0018+.004*u_beat));
    float energy = rings*(.18+.88*u_loud) + ribs*(.08+.35*u_mids) + core*(.20+.95*u_bass) + pulse*u_beat*1.2;
    vec3 col = palette(z*.15+a/TAU+u_time*.008)*energy;
    col += vec3(1.0,.82,.94)*u_strike*exp(-pow(r-.46,2.0)/.010)*.55;
    return col;
}

vec3 voidScene(vec2 p) {
    vec2 q = p*2.1;
    float n = fbm(q*.85 + vec2(u_time*.018,-u_time*.012));
    float n2 = fbm(q*1.75 + vec2(-u_time*.011,u_time*.020)+n*.7);
    float neb = pow(max(0.0,n*.68+n2*.52-.52), 2.4);

    vec2 cell = floor((p+vec2(3.0))*vec2(42.0,24.0));
    vec2 f = fract((p+vec2(3.0))*vec2(42.0,24.0))-.5;
    float h = hash21(cell);
    float star = h>.965 ? pow(max(0.0,1.0-length(f)*3.0),10.0) : 0.0;
    star *= .40 + .60*sin(u_time*(1.2+h*2.0)+h*20.0)*.5+.5;
    star *= .38 + 1.25*u_highs;

    float r = length(p);
    float orbit = exp(-pow(r-(.40+.07*sin(u_time*.11)),2.0)/.0018) * (.12+.72*u_bass);
    vec3 col = palette(n*.35+n2*.45+u_time*.006)*neb*(.25+1.15*u_loud);
    col += vec3(.80,.92,1.0)*star;
    col += palette(.72+u_color*.2)*orbit;
    col += vec3(1.0,.92,.98)*u_drop*exp(-r*1.7)*.42;
    return col;
}

vec3 cathedralScene(vec2 p) {
    vec2 q = p;
    q.y += .08;
    float perspective = 1.0/max(.32, 1.35-q.y*.38);
    float repeatX = mod(q.x*perspective + .28, .56)-.28;
    float column = exp(-abs(repeatX)*42.0) * smoothstep(-.75,.50,q.y);
    float archR = length(vec2(repeatX, q.y+.08));
    float arch = exp(-abs(archR-(.24+.018*u_bass))*70.0) * smoothstep(-.60,.18,-q.y);
    float floorLine = exp(-abs(fract((q.y+.74)*perspective*8.0)-.5)*30.0) * smoothstep(.02,.85,q.y);
    float vertical = exp(-abs(fract((q.x*perspective+.5)*8.0)-.5)*34.0) * smoothstep(.0,.95,q.y);
    float structure = column*.72 + arch*1.18 + floorLine*.20 + vertical*.17;
    float fog = fbm(q*1.8 + vec2(u_time*.025,0.0));
    float wave = .72+.28*cos(TAU*u_phase);
    vec3 col = palette(.48+q.y*.12+fog*.18)*structure*(.35+u_loud*.95)*wave;
    col += palette(.05+u_bar_phase)*u_beat*exp(-abs(q.y+.55)*8.0)*.30;
    col += vec3(.94,.96,1.0)*u_strike*arch*.42;
    return col;
}

vec3 scene(int id, vec2 p) {
    if (id == 0) return auroraScene(p);
    if (id == 1) return liquidScene(p);
    if (id == 2) return pulseScene(p);
    if (id == 3) return voidScene(p);
    return cathedralScene(p);
}

void main() {
    vec2 p = centeredUV();
    vec3 a = scene(u_scene_a, p);
    vec3 b = scene(u_scene_b, p);
    float m = u_scene_mix*u_scene_mix*(3.0-2.0*u_scene_mix);
    vec3 col = mix(a,b,m);

    // Rare macro events should alter the whole composition, not create per-pixel noise.
    col *= 1.0 + u_drop*.28;
    col += palette(.95)*u_drop*.10*(1.0-smoothstep(.0,1.25,length(p)));

    // Filmic compression + projector-safe blacks. Preserve dark negative space.
    col = max(col, vec3(0.0));
    col = col / (1.0 + col);
    col = pow(col, vec3(.86));
    float vignette = smoothstep(1.22,.20,length(p));
    col *= mix(.56,1.0,vignette);
    fragColor = vec4(clamp(col,0.0,1.0),1.0);
}
"""


class AudioShaderRenderer:
    """ModernGL music renderer with seamless scene crossfades and drop-aware journey mode."""

    _SCENE_IDS = {"aurora": 0, "liquid": 1, "pulse": 2, "void": 3, "cathedral": 4}

    def __init__(
        self,
        width: int,
        height: int,
        *,
        scene: str = "journey",
        palette: str = "neon_aurora",
        madness: float = 0.45,
        transition_seconds: float = 2.4,
        auto_scene_seconds: float = 28.0,
    ) -> None:
        if scene not in SCENES:
            raise ValueError(f"unknown audio shader scene: {scene}")
        if palette not in PALETTES:
            raise ValueError(f"unknown audio shader palette: {palette}")
        import moderngl

        self.moderngl = moderngl
        self.width = int(width)
        self.height = int(height)
        self.scene_name = scene
        self.palette_index = PALETTES.index(palette)
        self.madness = float(np.clip(madness, 0.0, 1.0))
        self.transition_seconds = float(max(transition_seconds, 0.15))
        self.auto_scene_seconds = float(max(auto_scene_seconds, 5.0))

        self.ctx = None
        errors: list[str] = []
        for backend in ("egl", None):
            try:
                if backend is None:
                    self.ctx = moderngl.create_standalone_context(require=330)
                    self.backend = "default"
                else:
                    self.ctx = moderngl.create_standalone_context(require=330, backend=backend)
                    self.backend = backend
                break
            except Exception as exc:  # pragma: no cover - machine dependent
                errors.append(f"{backend or 'default'}: {exc}")
        if self.ctx is None:
            raise RuntimeError("could not create ModernGL context: " + " | ".join(errors))

        self.program = self.ctx.program(vertex_shader=_VERTEX, fragment_shader=_FRAGMENT)
        vertices = np.asarray([-1.0, -1.0, 3.0, -1.0, -1.0, 3.0], dtype="f4")
        self.vbo = self.ctx.buffer(vertices.tobytes())
        self.vao = self.ctx.simple_vertex_array(self.program, self.vbo, "in_pos")
        self.target = self.ctx.texture((self.width, self.height), 3, dtype="f1")
        self.fbo = self.ctx.framebuffer(color_attachments=[self.target])

        if scene == "journey":
            self.scene_a = 0
            self.scene_b = 0
        else:
            sid = self._SCENE_IDS[scene]
            self.scene_a = sid
            self.scene_b = sid
        self._transition_start: float | None = None
        self._last_switch = time.perf_counter()
        self._drop_armed = True

    def _maybe_transition(self, now: float, s: MusicalSignals) -> float:
        if self.scene_name != "journey":
            return 0.0

        if s.drop < 0.18:
            self._drop_armed = True
        due = now - self._last_switch >= self.auto_scene_seconds
        drop_switch = self._drop_armed and s.drop >= 0.62 and now - self._last_switch >= 6.0
        if self._transition_start is None and (due or drop_switch):
            self.scene_b = (self.scene_a + 1) % len(self._SCENE_IDS)
            self._transition_start = now
            self._drop_armed = False

        if self._transition_start is None:
            return 0.0
        mix = float(np.clip((now - self._transition_start) / self.transition_seconds, 0.0, 1.0))
        if mix >= 1.0:
            self.scene_a = self.scene_b
            self._transition_start = None
            self._last_switch = now
            return 0.0
        return mix

    def render(self, s: MusicalSignals, *, t: float, now: float | None = None) -> np.ndarray:
        now = float(time.perf_counter() if now is None else now)
        mix = self._maybe_transition(now, s)

        p = self.program
        p["u_resolution"].value = (float(self.width), float(self.height))
        p["u_time"].value = float(t)
        p["u_loud"].value = float(s.loudness)
        p["u_bass"].value = float(s.bass)
        p["u_mids"].value = float(s.mids)
        p["u_highs"].value = float(s.highs)
        p["u_beat"].value = float(s.beat)
        p["u_strike"].value = float(s.strike)
        p["u_drop"].value = float(s.drop)
        p["u_phase"].value = float(s.beat_phase)
        p["u_bar_phase"].value = float(s.bar_phase)
        p["u_tempo"].value = float(s.tempo_bpm)
        p["u_color"].value = float(s.color)
        p["u_madness"].value = self.madness
        p["u_palette"].value = int(self.palette_index)
        p["u_scene_a"].value = int(self.scene_a)
        p["u_scene_b"].value = int(self.scene_b)
        p["u_scene_mix"].value = float(mix)

        self.fbo.use()
        self.ctx.viewport = (0, 0, self.width, self.height)
        self.fbo.clear(0.0, 0.0, 0.0, 1.0)
        self.vao.render(mode=self.moderngl.TRIANGLES)
        data = self.fbo.read(components=3, alignment=1)
        frame = np.frombuffer(data, dtype=np.uint8).reshape(self.height, self.width, 3)
        return np.flipud(frame).copy()

    @property
    def current_scene(self) -> str:
        names = ("aurora", "liquid", "pulse", "void", "cathedral")
        return names[self.scene_a]

    def close(self) -> None:
        for obj in (self.fbo, self.target, self.vao, self.vbo, self.program):
            try:
                obj.release()
            except Exception:
                pass


__all__ = ["AudioShaderRenderer", "SCENES", "PALETTES"]
