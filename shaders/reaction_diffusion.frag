#version 330 core
// Minimal Gray-Scott reaction-diffusion update shader.
uniform sampler2D stateTex; // RG = U,V
uniform vec2 texel;
uniform float dt;
uniform float feed;
uniform float kill;
in vec2 uv;
out vec4 fragColor;

vec2 state(vec2 p) { return texture(stateTex, p).rg; }

void main() {
    vec2 c = state(uv);
    vec2 lap = -c;
    lap += 0.2 * (state(uv + vec2(texel.x,0)) + state(uv - vec2(texel.x,0)) + state(uv + vec2(0,texel.y)) + state(uv - vec2(0,texel.y)));
    lap += 0.05 * (state(uv + texel) + state(uv - texel) + state(uv + vec2(texel.x,-texel.y)) + state(uv + vec2(-texel.x,texel.y)));
    float u = c.r, v = c.g;
    float reaction = u*v*v;
    float du = 0.16*lap.r - reaction + feed*(1.0-u);
    float dv = 0.08*lap.g + reaction - (feed+kill)*v;
    vec2 next = clamp(c + dt*vec2(du,dv), 0.0, 1.0);
    fragColor = vec4(next, 0.0, 1.0);
}
