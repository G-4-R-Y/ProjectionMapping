from __future__ import annotations

import numpy as np


VERTEX_SHADER = r"""
#version 330
in vec2 in_pos;
out vec2 v_uv;
void main() {
    v_uv = in_pos * 0.5 + 0.5;
    gl_Position = vec4(in_pos, 0.0, 1.0);
}
"""

FRAGMENT_SHADER = r"""
#version 330
uniform float u_time;
uniform float u_intensity;
uniform vec2 u_resolution;
uniform int u_scene;
in vec2 v_uv;
out vec4 fragColor;

#define PI 3.14159265359

float hash21(vec2 p) {
    p = fract(p * vec2(123.34, 345.45));
    p += dot(p, p + 34.345);
    return fract(p.x * p.y);
}

float noise(vec2 p) {
    vec2 i = floor(p), f = fract(p);
    f = f*f*(3.0-2.0*f);
    float a=hash21(i), b=hash21(i+vec2(1,0)), c=hash21(i+vec2(0,1)), d=hash21(i+vec2(1,1));
    return mix(mix(a,b,f.x), mix(c,d,f.x), f.y);
}

float fbm(vec2 p) {
    float f=0.0, a=0.5;
    mat2 r=mat2(0.80,-0.60,0.60,0.80);
    for(int i=0;i<6;i++) {
        f += a*noise(p);
        p = r*p*2.03 + 0.13;
        a *= 0.5;
    }
    return f;
}

vec3 pal(float t, vec3 phase) {
    return 0.48 + 0.48*cos(6.28318*(vec3(0.92,0.78,0.66)*t + phase));
}

vec3 eventHorizon(vec2 p, float t) {
    float r = length(p) + 1e-5;
    float a = atan(p.y,p.x);
    float ring = exp(-22.0*abs(r - (0.39 + 0.025*sin(t*0.37))));
    float inner = smoothstep(0.43,0.08,r);
    float swirl = fbm(vec2(log(r)*3.5 - t*0.16, a*6.0/PI));
    float spokes = 0.5 + 0.5*cos(a*12.0 + 13.0/r - t*1.35 + swirl*2.0);
    float filaments = pow(spokes, 6.0) * exp(-2.2*r);
    float lens = pow(max(0.0,1.0-abs(r-0.47)*7.0),4.0);
    vec3 c = pal(swirl*0.8 + t*0.025, vec3(0.03,0.28,0.58));
    c *= ring*2.0 + filaments*(0.35+u_intensity*0.45) + lens*0.5;
    c += vec3(0.02,0.00,0.05)*inner;
    c += vec3(0.35,0.05,0.55)*pow(inner,3.0)*0.45;
    return c;
}

vec3 auroraVoid(vec2 p, float t) {
    vec2 q = p*vec2(1.25,1.9);
    float n = fbm(q*1.7 + vec2(t*0.045,-t*0.025));
    float n2 = fbm(q*3.1 - vec2(t*0.018,t*0.032));
    float y = q.y + 0.34*sin(q.x*2.2+t*0.25+n*2.4) + 0.18*sin(q.x*5.1-t*0.18+n2);
    float curtain = exp(-7.0*abs(y))* (0.4+0.6*n);
    float curtain2 = exp(-10.0*abs(y-0.28*sin(q.x*1.4-t*0.19)))*(0.3+0.7*n2);
    vec3 c1 = vec3(0.02,0.90,0.82);
    vec3 c2 = vec3(0.80,0.08,1.00);
    vec3 c = mix(c1,c2,clamp(n2*1.2,0.0,1.0))*curtain*1.4;
    c += mix(vec3(0.08,0.20,1.0),vec3(1.0,0.10,0.50),n)*curtain2*0.75;
    float stars = pow(hash21(floor((p+0.5)*u_resolution/5.0)),38.0);
    c += vec3(stars)*0.7;
    return c;
}

vec3 liquidChrome(vec2 p, float t) {
    vec2 q=p*2.6;
    float n=fbm(q+vec2(t*0.10,-t*0.07));
    q += vec2(sin(q.y*2.3+n*4.0+t*0.3), cos(q.x*2.1-n*3.0-t*0.25))*0.42;
    float n2=fbm(q*2.0-vec2(t*0.06,t*0.04));
    float ridge=1.0-abs(2.0*n2-1.0);
    ridge=pow(ridge,5.0);
    vec3 chrome=mix(vec3(0.015,0.02,0.04),vec3(0.65,0.86,1.0),ridge);
    chrome += pal(n+n2+t*0.02,vec3(0.03,0.31,0.61))*pow(max(0.0,ridge-0.45),2.0)*0.85;
    float spec=pow(max(0.0,1.0-abs(n-n2)*4.0),14.0);
    chrome += vec3(1.0,0.92,0.78)*spec*0.8;
    return chrome;
}

float sdBox(vec2 p, vec2 b) {
    vec2 d=abs(p)-b;
    return length(max(d,0.0))+min(max(d.x,d.y),0.0);
}

vec3 neonCathedral(vec2 p, float t) {
    p.x=abs(p.x);
    vec2 q=p;
    q.y += 0.13;
    float columns=exp(-30.0*abs(fract((q.x+0.04)*5.0)-0.5))*smoothstep(0.8,-0.75,q.y);
    float archR=length(vec2(fract(q.x*2.5)-0.5,q.y*0.85+0.13));
    float arches=exp(-42.0*abs(archR-(0.36+0.018*sin(t*0.33))));
    float floorLine=exp(-35.0*abs(q.y+0.55));
    float perspective=pow(max(0.0,1.0-abs(fract((q.x/(0.18+abs(q.y+0.66)*0.22))+t*0.025)-0.5)*2.0),9.0);
    float fog=fbm(vec2(q.x*3.0,q.y*2.0-t*0.045));
    vec3 c=vec3(0.0);
    c += vec3(0.05,0.72,1.0)*columns*0.42;
    c += vec3(1.0,0.08,0.72)*arches*1.15;
    c += vec3(0.20,0.32,1.0)*floorLine*(0.4+0.6*perspective);
    c += vec3(0.12,0.04,0.24)*fog*0.35;
    float altar=exp(-18.0*length(vec2(q.x,q.y+0.17)));
    c += vec3(0.9,0.18,1.0)*altar*0.55;
    return c;
}

void main() {
    vec2 p=(gl_FragCoord.xy*2.0-u_resolution)/u_resolution.y;
    float t=u_time;
    vec3 c;
    if(u_scene==0) c=eventHorizon(p,t);
    else if(u_scene==1) c=auroraVoid(p,t);
    else if(u_scene==2) c=liquidChrome(p,t);
    else c=neonCathedral(p,t);

    float vignette=smoothstep(1.35,0.25,length(p));
    c *= mix(0.52,1.0,vignette);
    c *= 0.82 + 0.32*u_intensity;
    c = c/(1.0+c);
    c = pow(max(c,vec3(0.0)),vec3(0.82));
    fragColor=vec4(clamp(c,0.0,1.0),1.0);
}
"""


SCENE_IDS = {
    "event_horizon": 0,
    "aurora_void": 1,
    "liquid_chrome": 2,
    "neon_cathedral": 3,
}


class ShaderSceneRenderer:
    def __init__(self, width: int, height: int) -> None:
        import moderngl

        self.moderngl = moderngl
        self.width = int(width)
        self.height = int(height)
        errors: list[str] = []
        self.ctx = None
        for backend in ("egl", None):
            try:
                self.ctx = (
                    moderngl.create_standalone_context(require=330, backend=backend)
                    if backend is not None
                    else moderngl.create_standalone_context(require=330)
                )
                self.backend = backend or "default"
                break
            except Exception as exc:  # pragma: no cover
                errors.append(f"{backend or 'default'}: {exc}")
        if self.ctx is None:
            raise RuntimeError("could not create ModernGL scene context: " + " | ".join(errors))

        self.program = self.ctx.program(vertex_shader=VERTEX_SHADER, fragment_shader=FRAGMENT_SHADER)
        vertices = np.asarray([-1.0,-1.0, 3.0,-1.0, -1.0,3.0],dtype="f4")
        self.vbo = self.ctx.buffer(vertices.tobytes())
        self.vao = self.ctx.simple_vertex_array(self.program,self.vbo,"in_pos")
        self.target = self.ctx.texture((self.width,self.height),3,dtype="f1")
        self.fbo = self.ctx.framebuffer(color_attachments=[self.target])
        self.program["u_resolution"].value = (float(self.width),float(self.height))

    def render(self, scene: str, *, t: float, intensity: float = 1.0) -> np.ndarray:
        self.program["u_time"].value=float(t)
        self.program["u_intensity"].value=float(intensity)
        self.program["u_scene"].value=int(SCENE_IDS[scene])
        self.fbo.use()
        self.ctx.viewport=(0,0,self.width,self.height)
        self.vao.render(mode=self.moderngl.TRIANGLES)
        data=self.fbo.read(components=3,alignment=1)
        return np.flipud(np.frombuffer(data,dtype=np.uint8).reshape(self.height,self.width,3)).copy()

    def close(self) -> None:
        for obj in (self.fbo,self.target,self.vao,self.vbo,self.program):
            try: obj.release()
            except Exception: pass
