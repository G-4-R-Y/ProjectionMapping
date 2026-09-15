from __future__ import annotations

import numpy as np


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
uniform sampler2D u_tex;
uniform float u_time;
uniform float u_intensity;
uniform int u_background;
in vec2 v_uv;
out vec4 fragColor;

float hash21(vec2 p) {
    p = fract(p * vec2(123.34, 456.21));
    p += dot(p, p + 45.32);
    return fract(p.x * p.y);
}

float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    float a = hash21(i);
    float b = hash21(i + vec2(1.0, 0.0));
    float c = hash21(i + vec2(0.0, 1.0));
    float d = hash21(i + vec2(1.0, 1.0));
    return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}

float fbm(vec2 p) {
    float v = 0.0;
    float a = 0.5;
    mat2 r = mat2(0.80, -0.60, 0.60, 0.80);
    for (int i = 0; i < 5; ++i) {
        v += a * noise(p);
        p = r * p * 2.02 + 0.17;
        a *= 0.5;
    }
    return v;
}

vec3 palette(float t) {
    vec3 a = vec3(0.45, 0.38, 0.55);
    vec3 b = vec3(0.45, 0.42, 0.45);
    vec3 c = vec3(1.0, 0.82, 0.74);
    vec3 d = vec3(0.02, 0.28, 0.58);
    return a + b * cos(6.28318 * (c * t + d));
}

void main() {
    vec2 uv = v_uv;
    vec2 p = uv - 0.5;
    float r = length(p);

    // Subtle lens warp keeps the centre calm but gives the field a cinematic depth.
    vec2 warped = 0.5 + p * (1.0 + 0.055 * r * r * u_intensity);
    vec2 ca = normalize(p + vec2(1e-5)) * (0.0013 + 0.0022 * u_intensity);
    float rr = texture(u_tex, warped + ca).r;
    float gg = texture(u_tex, warped).g;
    float bb = texture(u_tex, warped - ca).b;
    vec3 src = vec3(rr, gg, bb);

    // Cheap wide bloom. The CPU path already emits glows; this shader adds a coherent halo.
    vec2 px = 1.0 / vec2(textureSize(u_tex, 0));
    vec3 bloom = vec3(0.0);
    bloom += texture(u_tex, warped + px * vec2( 3.0, 0.0)).rgb;
    bloom += texture(u_tex, warped + px * vec2(-3.0, 0.0)).rgb;
    bloom += texture(u_tex, warped + px * vec2(0.0,  3.0)).rgb;
    bloom += texture(u_tex, warped + px * vec2(0.0, -3.0)).rgb;
    bloom += texture(u_tex, warped + px * vec2( 2.0,  2.0)).rgb;
    bloom += texture(u_tex, warped + px * vec2(-2.0,  2.0)).rgb;
    bloom += texture(u_tex, warped + px * vec2( 2.0, -2.0)).rgb;
    bloom += texture(u_tex, warped + px * vec2(-2.0, -2.0)).rgb;
    bloom *= 0.125;

    vec3 bg = vec3(0.0);
    if (u_background == 1) {
        vec2 q = p * vec2(2.7, 1.6);
        q += vec2(0.14 * sin(u_time * 0.11), -0.08 * cos(u_time * 0.13));
        float n1 = fbm(q * 2.1 + vec2(u_time * 0.035, 0.0));
        float n2 = fbm(q * 4.7 - vec2(0.0, u_time * 0.045));
        float ridge = pow(max(0.0, 1.0 - abs(n1 - n2) * 2.25), 4.0);
        bg = palette(n1 + n2 * 0.35 + u_time * 0.015) * ridge * 0.20;
    } else if (u_background == 2) {
        vec2 g = abs(fract(p * vec2(22.0, 13.0)) - 0.5);
        float line = 1.0 - smoothstep(0.465, 0.50, min(g.x, g.y));
        float wave = 0.5 + 0.5 * sin(length(p) * 32.0 - u_time * 1.2);
        bg = vec3(0.03, 0.16, 0.22) * line * wave * 0.32;
    } else if (u_background == 3) {
        vec2 q = p * 3.0;
        float n = fbm(q + 0.35 * vec2(sin(u_time * 0.18), cos(u_time * 0.15)));
        float caustic = pow(1.0 - abs(sin((q.x + n * 2.0) * 4.0) * cos((q.y - n) * 5.0)), 7.0);
        bg = mix(vec3(0.01, 0.02, 0.06), vec3(0.03, 0.32, 0.44), caustic) * 0.45;
    }

    float srcEnergy = max(src.r, max(src.g, src.b));
    vec3 col = src + bloom * (0.45 + 0.35 * u_intensity) + bg * (1.0 - smoothstep(0.05, 0.55, srcEnergy));

    // Filmic-ish contrast and projector-safe vignette.
    col = col / (1.0 + col);
    col = pow(max(col, vec3(0.0)), vec3(0.88));
    float vignette = smoothstep(0.90, 0.22, r);
    col *= mix(0.72, 1.0, vignette);
    fragColor = vec4(clamp(col, 0.0, 1.0), 1.0);
}
"""


class ModernGLPostFX:
    """Optional offscreen ModernGL post-processer.

    The project still owns fullscreen/window lifecycle through OpenCV, which keeps display
    placement/F11 behavior consistent. ModernGL handles the shader work and reads one final
    RGB frame back for the existing sink. On systems without ModernGL/EGL the caller can
    simply skip this stage.
    """

    def __init__(self, width: int, height: int) -> None:
        import moderngl

        self.moderngl = moderngl
        self.width = int(width)
        self.height = int(height)
        errors: list[str] = []
        self.ctx = None
        for backend in ("egl", None):
            try:
                if backend is None:
                    self.ctx = moderngl.create_standalone_context(require=330)
                    self.backend = "default"
                else:
                    self.ctx = moderngl.create_standalone_context(require=330, backend=backend)
                    self.backend = backend
                break
            except Exception as exc:  # pragma: no cover - backend depends on machine
                errors.append(f"{backend or 'default'}: {exc}")
        if self.ctx is None:
            raise RuntimeError("could not create ModernGL context: " + " | ".join(errors))

        self.program = self.ctx.program(vertex_shader=_VERTEX, fragment_shader=_FRAGMENT)
        vertices = np.asarray([-1.0, -1.0, 3.0, -1.0, -1.0, 3.0], dtype="f4")
        self.vbo = self.ctx.buffer(vertices.tobytes())
        self.vao = self.ctx.simple_vertex_array(self.program, self.vbo, "in_pos")
        self.texture = self.ctx.texture((self.width, self.height), 3, dtype="f1")
        self.texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self.texture.repeat_x = False
        self.texture.repeat_y = False
        self.target = self.ctx.texture((self.width, self.height), 3, dtype="f1")
        self.fbo = self.ctx.framebuffer(color_attachments=[self.target])
        self.program["u_tex"].value = 0

    def render(self, rgb: np.ndarray, *, t: float, intensity: float = 1.0, background: int = 1) -> np.ndarray:
        frame = np.ascontiguousarray(np.asarray(rgb, dtype=np.uint8))
        if frame.shape[:2] != (self.height, self.width):
            raise ValueError(f"shader input must be {self.width}x{self.height}")
        self.texture.write(frame.tobytes())
        self.texture.use(location=0)
        self.program["u_time"].value = float(t)
        self.program["u_intensity"].value = float(intensity)
        self.program["u_background"].value = int(background)
        self.fbo.use()
        self.ctx.viewport = (0, 0, self.width, self.height)
        self.fbo.clear(0.0, 0.0, 0.0, 1.0)
        self.vao.render(mode=self.moderngl.TRIANGLES)
        data = self.fbo.read(components=3, alignment=1)
        out = np.frombuffer(data, dtype=np.uint8).reshape(self.height, self.width, 3)
        return np.flipud(out).copy()

    def close(self) -> None:
        for obj in (self.fbo, self.target, self.texture, self.vao, self.vbo, self.program):
            try:
                obj.release()
            except Exception:
                pass
