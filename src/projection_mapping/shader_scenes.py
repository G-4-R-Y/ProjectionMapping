from __future__ import annotations

import numpy as np

from .graphics_runtime import create_context


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
#define TAU 6.28318530718

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
    return 0.50 + 0.50*cos(TAU*(vec3(0.96,0.81,0.68)*t + phase));
}
float lineGlow(float d,float gain){
    return exp(-abs(d)*gain) + .45*exp(-abs(d)*gain*.22);
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
    c += vec3(0.36,0.02,0.62)*pow(inner,3.0)*0.45;
    return c;
}

vec3 auroraVoid(vec2 p, float t) {
    vec2 q = p*vec2(1.25,1.9);
    float n = fbm(q*1.7 + vec2(t*0.045,-t*0.025));
    float n2 = fbm(q*3.1 - vec2(t*0.018,t*0.032));
    float y = q.y + 0.34*sin(q.x*2.2+t*0.25+n*2.4) + 0.18*sin(q.x*5.1-t*0.18+n2);
    float curtain = exp(-7.0*abs(y))* (0.4+0.6*n);
    float curtain2 = exp(-10.0*abs(y-0.28*sin(q.x*1.4-t*0.19)))*(0.3+0.7*n2);
    vec3 c1 = vec3(0.00,1.00,0.88);
    vec3 c2 = vec3(0.92,0.03,1.00);
    vec3 c = mix(c1,c2,clamp(n2*1.2,0.0,1.0))*curtain*1.55;
    c += mix(vec3(0.02,0.20,1.0),vec3(1.0,0.03,0.48),n)*curtain2*0.88;
    float stars = pow(hash21(floor((p+0.5)*u_resolution/5.0)),38.0);
    c += vec3(stars)*0.8;
    return c;
}

vec3 liquidChrome(vec2 p, float t) {
    vec2 q=p*2.6;
    float n=fbm(q+vec2(t*0.10,-t*0.07));
    q += vec2(sin(q.y*2.3+n*4.0+t*0.3), cos(q.x*2.1-n*3.0-t*0.25))*0.42;
    float n2=fbm(q*2.0-vec2(t*0.06,t*0.04));
    float ridge=1.0-abs(2.0*n2-1.0);
    ridge=pow(ridge,5.0);
    vec3 chrome=mix(vec3(0.003,0.006,0.018),vec3(0.50,0.88,1.0),ridge);
    chrome += pal(n+n2+t*0.02,vec3(0.03,0.31,0.61))*pow(max(0.0,ridge-0.42),2.0)*1.10;
    float spec=pow(max(0.0,1.0-abs(n-n2)*4.0),14.0);
    chrome += vec3(1.0,0.96,0.86)*spec*1.1;
    return chrome;
}

vec3 neonCathedral(vec2 p, float t) {
    // Rebuilt as a moving radial vault: polar arches + perspective floor + travelling caustics.
    float slow=t*.23;
    float breathe=.94+.055*sin(t*.31);
    p*=breathe;
    p.x += .035*sin(t*.17) + .012*sin(p.y*5.0+t*.31);
    float r=length(p)+1e-4;
    float a=atan(p.y,p.x);

    vec3 c=vec3(0.0);
    // Concentric vault ribs moving through depth.
    float z=-log(r+.08);
    float ribs=pow(.5+.5*cos(z*13.0 - slow*2.1 + .65*sin(a*8.0+slow)),18.0);
    float spokes=pow(.5+.5*cos(a*14.0 + z*1.8 - slow*.72),24.0);
    float vault=(ribs*.92 + spokes*.42)*exp(-r*.72);
    c += pal(z*.12+a/TAU*.14+t*.012,vec3(.58,.10,.02))*vault*1.25;

    // Pointed-arch interference: mirrored harmonic lobes instead of static box lines.
    float archShape = abs(r - (.35 + .11*cos(a*6.0 + slow*.55) + .035*cos(a*12.0-slow*.33)));
    float arches=lineGlow(archShape,64.0)*(.56+.44*pow(.5+.5*cos(a*6.0),5.0));
    c += mix(vec3(.00,.90,1.0),vec3(1.0,.02,.72),.5+.5*sin(a*3.0+t*.11))*arches*1.15;

    // Perspective floor/ceiling grid streams outward from the central vanishing point.
    float perspective=1.0/max(.12,abs(p.y+.02)+.10);
    float floorMask=smoothstep(.02,.80,-p.y);
    float floorRays=pow(.5+.5*cos(p.x*perspective*9.0),28.0)*floorMask;
    float floorBands=pow(.5+.5*cos(perspective*1.85-t*.66),22.0)*floorMask;
    c += vec3(.03,.32,1.0)*(floorRays*.42+floorBands*.52);

    // Travelling stained-light caustics keep the structure continuously alive.
    float n=fbm(p*3.3+vec2(t*.08,-t*.055));
    float n2=fbm(p*6.2+vec2(-t*.041,t*.067));
    float caustic=pow(max(0.0,1.0-abs(n-n2)*3.2),7.0);
    vec3 glass=pal(n*.72+n2*.36+t*.021,vec3(.03,.26,.61));
    c += glass*caustic*(.28+.42*exp(-r*.65));

    // White-hot altar/oculus pulses rather than a flat magenta dot.
    float oculus=exp(-r*11.0)*(1.0+.35*sin(t*1.25));
    float halo=exp(-42.0*abs(r-(.17+.018*sin(t*.43))));
    c += vec3(1.0,.965,.92)*oculus*.58;
    c += pal(t*.025+.84,vec3(.10,.18,.54))*halo*.95;
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

    float vignette=smoothstep(1.45,0.18,length(p));
    c *= mix(0.72,1.0,vignette);
    c *= 0.86 + 0.40*u_intensity;
    // Hue-preserving emissive transform: vivid highlights, clean black floor.
    c = vec3(1.0)-exp(-max(c,vec3(0.0))*1.18);
    c = pow(c,vec3(0.78));
    float peak=max(c.r,max(c.g,c.b));
    c *= smoothstep(.008,.045,peak);
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
        self.ctx, info = create_context(require=330)
        self.backend = info.backend
        self.context_info = info

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
        self.fbo.clear(0.0,0.0,0.0,1.0)
        self.vao.render(mode=self.moderngl.TRIANGLES)
        data=self.fbo.read(components=3,alignment=1)
        return np.flipud(np.frombuffer(data,dtype=np.uint8).reshape(self.height,self.width,3)).copy()

    def close(self) -> None:
        for obj in (self.fbo,self.target,self.vao,self.vbo,self.program):
            try:
                obj.release()
            except Exception:
                pass
        try:
            self.ctx.release()
        except Exception:
            pass
