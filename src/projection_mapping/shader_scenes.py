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
uniform float u_chaos;
uniform vec2 u_resolution;
uniform int u_scene;
in vec2 v_uv;
out vec4 fragColor;

#define PI 3.14159265359
#define TAU 6.28318530718

float sat(float x){ return clamp(x,0.0,1.0); }

float hash21(vec2 p) {
    p = fract(p * vec2(123.34, 345.45));
    p += dot(p, p + 34.345);
    return fract(p.x * p.y);
}

vec2 hash22(vec2 p){
    float n=sin(dot(p,vec2(41.0,289.0)));
    return fract(vec2(262144.0,32768.0)*n);
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

float ridged(vec2 p){
    float n=fbm(p);
    return 1.0-abs(2.0*n-1.0);
}

mat2 rot(float a){
    float c=cos(a), s=sin(a);
    return mat2(c,-s,s,c);
}

vec2 cmul(vec2 a, vec2 b){
    return vec2(a.x*b.x-a.y*b.y, a.x*b.y+a.y*b.x);
}

vec2 harmonic(vec2 unitDir, int n){
    // cos(n*theta), sin(n*theta) without ever exposing atan()'s -PI/PI branch cut.
    vec2 z=vec2(1.0,0.0);
    for(int i=0;i<24;i++){
        if(i<n) z=cmul(z,unitDir);
    }
    return z;
}

vec3 pal(float t, vec3 phase) {
    return 0.50 + 0.50*cos(TAU*(vec3(0.96,0.81,0.68)*t + phase));
}

float lineGlow(float d,float gain){
    return exp(-abs(d)*gain) + .45*exp(-abs(d)*gain*.22);
}

vec3 eventHorizon(vec2 p, float t) {
    // Deliberately atan-free. The old version fed raw atan() into fbm and created a visible
    // horizontal branch-cut seam on the negative X axis. Everything angular here is encoded as
    // periodic unit-circle harmonics, so the field is continuous around the full circle.
    float chaos=clamp(u_chaos,0.0,2.5);
    float r0=length(p)+1e-5;
    float n0=fbm(p*1.35+vec2(t*.035,-t*.028));
    float spin=(1.15+1.25*chaos)*exp(-r0*.70)+.24*sin(r0*8.0-t*.37)+.36*(n0-.5)*chaos;
    vec2 q=rot(spin+t*.065)*p;

    vec2 warp=vec2(
        fbm(q*3.2+vec2(t*.060,1.7)),
        fbm(q*3.0+vec2(-2.1,-t*.052))
    )-.5;
    q += warp*(.035+.075*chaos)*smoothstep(.05,1.25,r0);

    float r=length(q)+1e-4;
    vec2 d=q/r;
    vec2 h7=harmonic(d,7);
    vec2 h11=harmonic(d,11);
    vec2 h17=harmonic(d,17);

    float turb=fbm(q*4.6+vec2(t*.045,-t*.032));
    float ringR=.405+.023*sin(t*.37)+.020*chaos*h7.x+.014*chaos*h11.y+.030*(turb-.5);
    float ring=exp(-30.0*abs(r-ringR));
    float ringHot=exp(-82.0*abs(r-ringR));

    float radialPhase=12.5/(r+.075)-t*1.34+turb*3.1;
    vec2 phaseDir=vec2(cos(radialPhase),sin(radialPhase));
    float spiral7=.5+.5*dot(h7,phaseDir);
    float spiral11=.5+.5*dot(h11,vec2(phaseDir.x,-phaseDir.y));
    float filaments=(pow(spiral7,13.0)+.72*pow(spiral11,17.0))*exp(-r*1.55);

    float lens=pow(max(0.0,1.0-abs(r-.50)*6.5),4.0);
    float corona=lineGlow(r-(.49+.018*h17.x+.012*sin(t*.21)),34.0)*(.28+.72*ridged(q*5.8+t*.018));
    float accretion=ring*(.58+.42*ridged(q*8.0+vec2(t*.05,0.0)));

    vec3 c=pal(turb*.90+r*.24+h11.x*.055+t*.022,vec3(.03,.28,.58));
    c*=accretion*2.25+filaments*(.42+u_intensity*.42)+lens*.34+corona*.62;
    c+=vec3(1.0,.97,.88)*ringHot*(.52+.35*chaos);

    float core=1.0-smoothstep(.055,.31,r);
    c+=vec3(.30,.015,.67)*pow(core,3.2)*(.28+.26*chaos);
    float singular=exp(-r*15.0)*(1.0+.30*sin(t*1.17));
    c+=vec3(.78,.90,1.0)*singular*.26;
    return c;
}

vec3 auroraVoid(vec2 p, float t) {
    float chaos=clamp(u_chaos,0.0,2.5);
    vec2 q=p*vec2(1.18,1.80);
    vec2 w1=vec2(fbm(q*1.35+vec2(t*.045,2.4)),fbm(q*1.55+vec2(-1.3,-t*.038)))-.5;
    q += w1*(.22+.24*chaos);
    vec2 w2=vec2(fbm(q*2.8+vec2(-t*.023,4.1)),fbm(q*3.1+vec2(3.2,t*.029)))-.5;
    q += w2*(.08+.16*chaos);

    float n=fbm(q*1.8+vec2(t*.040,-t*.022));
    float n2=fbm(q*3.5-vec2(t*.018,t*.031));
    vec3 c=vec3(0.0);
    for(int i=0;i<4;i++){
        float fi=float(i);
        float y=q.y + (.22+.05*fi)*sin(q.x*(1.7+fi*.86)+t*(.19+.035*fi)+n*(1.9+.4*fi));
        y += .08*sin(q.x*(5.4+fi*.7)-t*.21+n2*2.4+fi);
        float curtain=exp(-(7.0+fi*2.2)*abs(y-(fi-1.5)*.15));
        float shred=.50+.50*ridged(q*(3.0+fi*.75)+vec2(t*.025*fi,-t*.021));
        vec3 hue=pal(n*.54+n2*.31+fi*.17+t*.018,vec3(.48,.05,.68));
        c+=hue*curtain*shred*(.72+.16*chaos);
    }
    float lightning=pow(ridged(q*8.0+vec2(t*.11,-t*.07)),9.0)*exp(-abs(q.y)*1.25);
    c+=vec3(.55,.88,1.0)*lightning*(.10+.32*chaos);
    float stars=pow(hash21(floor((p+.5)*u_resolution/4.0)),44.0);
    c+=vec3(stars)*.68;
    return c;
}

vec3 liquidChrome(vec2 p, float t) {
    // Keep the successful visual language, but expose extra domain-warp depth through u_chaos.
    float chaos=clamp(u_chaos,0.0,2.5);
    vec2 q=p*2.55;
    float n=fbm(q+vec2(t*.10,-t*.07));
    q += vec2(sin(q.y*2.3+n*4.0+t*.30),cos(q.x*2.1-n*3.0-t*.25))*(.38+.08*chaos);
    float n2=fbm(q*2.0-vec2(t*.06,t*.04));
    q += (vec2(fbm(q*2.7+t*.015),fbm(q*2.9-t*.017))-.5)*(.05+.10*chaos);
    float n3=fbm(q*3.9+vec2(-t*.025,t*.031));
    float ridge=1.0-abs(2.0*n2-1.0);
    ridge=pow(ridge,4.4);
    float micro=pow(1.0-abs(2.0*n3-1.0),7.0);
    vec3 chrome=mix(vec3(.002,.004,.014),vec3(.44,.86,1.0),ridge);
    chrome+=pal(n+n2+t*.02,vec3(.03,.31,.61))*pow(max(0.0,ridge-.36),2.0)*1.18;
    float spec=pow(max(0.0,1.0-abs(n-n2)*3.8),13.0);
    chrome+=vec3(1.0,.96,.86)*spec*1.15;
    chrome+=pal(n3+t*.015,vec3(.62,.11,.05))*micro*(.05+.15*chaos);
    return chrome;
}

vec3 neonCathedral(vec2 p, float t) {
    float chaos=clamp(u_chaos,0.0,2.5);
    float slow=t*.23;
    float breathe=.94+.055*sin(t*.31);
    p*=breathe;
    p.x+=.035*sin(t*.17)+.012*sin(p.y*5.0+t*.31);
    vec2 warp=vec2(fbm(p*2.4+vec2(t*.027,3.0)),fbm(p*2.7+vec2(-2.0,-t*.024)))-.5;
    p+=warp*.035*chaos;
    float r=length(p)+1e-4;
    float a=atan(p.y,p.x);
    vec2 d=p/r;
    vec2 h3=harmonic(d,3);
    vec2 h6=harmonic(d,6);
    vec2 h8=harmonic(d,8);

    vec3 c=vec3(0.0);
    float z=-log(r+.08);
    float ribs=pow(.5+.5*cos(z*13.0-slow*2.1+.65*h8.y+fbm(p*4.2)*chaos),18.0);
    float spokes=pow(.5+.5*h6.x,24.0);
    float vault=(ribs*.92+spokes*.42)*exp(-r*.72);
    c+=pal(z*.12+h8.x*.065+t*.012,vec3(.58,.10,.02))*vault*1.25;

    float archShape=abs(r-(.35+.11*h6.x+.035*harmonic(d,12).x));
    float arches=lineGlow(archShape,64.0)*(.56+.44*pow(.5+.5*h6.x,5.0));
    c+=mix(vec3(.00,.90,1.0),vec3(1.0,.02,.72),.5+.5*h3.x)*arches*1.18;

    float perspective=1.0/max(.12,abs(p.y+.02)+.10);
    float floorMask=smoothstep(.02,.80,-p.y);
    float floorRays=pow(.5+.5*cos(p.x*perspective*9.0),28.0)*floorMask;
    float floorBands=pow(.5+.5*cos(perspective*1.85-t*.66),22.0)*floorMask;
    c+=vec3(.03,.32,1.0)*(floorRays*.42+floorBands*.52);

    float n=fbm(p*3.3+vec2(t*.08,-t*.055));
    float n2=fbm(p*6.2+vec2(-t*.041,t*.067));
    float caustic=pow(max(0.0,1.0-abs(n-n2)*3.2),7.0);
    vec3 glass=pal(n*.72+n2*.36+t*.021,vec3(.03,.26,.61));
    c+=glass*caustic*(.28+.42*exp(-r*.65))*(.85+.18*chaos);

    float oculus=exp(-r*11.0)*(1.0+.35*sin(t*1.25));
    float halo=exp(-42.0*abs(r-(.17+.018*sin(t*.43))));
    c+=vec3(1.0,.965,.92)*oculus*.58;
    c+=pal(t*.025+.84,vec3(.10,.18,.54))*halo*.95;
    return c;
}

vec3 wormholeChoir(vec2 p,float t){
    float chaos=clamp(u_chaos,0.0,2.5);
    float r0=length(p)+.015;
    float sink=(.75+1.10*chaos)*exp(-r0*.72)+.22*sin(r0*10.0-t*.3);
    vec2 q=rot(sink+t*.09)*p;
    vec2 warp=vec2(fbm(q*2.5+vec2(t*.06,1.0)),fbm(q*2.8+vec2(-2.0,-t*.05)))-.5;
    q+=warp*(.06+.12*chaos);
    float r=length(q)+.018;
    vec2 d=q/r;
    float lr=log(r);
    vec3 c=vec3(0.0);
    int harmonics[4]=int[4](5,8,13,21);
    for(int i=0;i<4;i++){
        float fi=float(i);
        vec2 h=harmonic(d,harmonics[i]);
        float phase=(10.0+fi*3.2)*lr-t*(.72+fi*.19)+fi*.8+fbm(q*(2.4+fi))*1.7*chaos;
        vec2 ph=vec2(cos(phase),sin(phase));
        float w=.5+.5*dot(h,ph);
        float ridge=pow(w,13.0+fi*2.0)*exp(-r*(.72+.11*fi));
        c+=pal(fi*.21+r*.28+t*.018,vec3(.02,.24,.58))*ridge*(.72+.18*fi);
    }
    float rings=pow(.5+.5*cos(r*(42.0+8.0*chaos)-t*1.35+fbm(q*5.2)*3.0),20.0);
    c+=pal(r*.47+t*.02,vec3(.58,.04,.18))*rings*exp(-r*.82)*(.22+.22*chaos);
    c+=vec3(1.0,.97,.92)*exp(-r*11.0)*(.34+.18*chaos);
    return c;
}

vec3 plasmaSingularity(vec2 p,float t){
    float chaos=clamp(u_chaos,0.0,2.5);
    vec2 q=p*2.15;
    for(int i=0;i<3;i++){
        float fi=float(i);
        float n=fbm(q*(1.15+fi*.42)+vec2(t*(.045+.012*fi),-t*(.032+.009*fi)));
        q=rot((n-.5)*(.55+.34*chaos)+.18*sin(t*.17+fi))*q;
        q+=vec2(sin(q.y*(2.0+fi)+n*4.0),cos(q.x*(2.4+fi)-n*3.5))*(.10+.055*chaos)/(1.0+fi*.35);
    }
    float r=length(p)+1e-4;
    float n1=ridged(q*1.8+t*.025);
    float n2=ridged(q*4.3-vec2(t*.038,-t*.027));
    float web=pow(sat(n1*n2),3.0);
    float shells=pow(.5+.5*cos(r*(35.0+7.0*chaos)-t*.92+n1*5.0),18.0);
    vec3 c=pal(n1*.54+n2*.37+t*.021,vec3(.63,.08,.28))*web*1.55;
    c+=pal(n2+r*.4-t*.014,vec3(.05,.37,.68))*shells*(.18+.20*chaos)*exp(-r*.58);
    float hot=pow(max(0.0,n2-.66),5.0);
    c+=vec3(1.0,.95,.82)*hot*(.55+.55*chaos);
    c+=vec3(.24,.03,.62)*exp(-r*7.0)*.42;
    return c;
}

vec3 vortexCrown(vec2 p,float t){
    float chaos=clamp(u_chaos,0.0,2.5);
    vec3 c=vec3(0.0);
    for(int k=0;k<5;k++){
        float fk=float(k);
        float orbit=.23+.065*sin(t*.21+fk*1.7);
        float ang=t*(.12+.025*fk)+fk*TAU/5.0;
        vec2 center=vec2(cos(ang),sin(ang))*orbit;
        vec2 q=p-center;
        float r=length(q)+1e-4;
        vec2 d=q/r;
        vec2 h=harmonic(d,5+k*2);
        float phase=9.0/(r+.10)-t*(.7+.12*fk)+fbm(q*5.0+t*.02)*2.0*chaos;
        float wave=.5+.5*dot(h,vec2(cos(phase),sin(phase)));
        float crown=pow(wave,15.0)*exp(-r*4.3);
        float ring=exp(-46.0*abs(r-(.105+.014*sin(t*.5+fk))));
        c+=pal(fk*.16+t*.018+h.x*.04,vec3(.02,.31,.64))*(crown*.72+ring*.65);
        c+=vec3(1.0,.97,.90)*exp(-r*20.0)*.08;
    }
    float central=ridged(p*(5.0+chaos*1.8)+vec2(t*.04,-t*.03));
    c+=pal(central+t*.015,vec3(.61,.02,.29))*pow(central,8.0)*(.16+.28*chaos);
    return c;
}

vec3 collapseFlower(vec2 p,float t){
    float chaos=clamp(u_chaos,0.0,2.5);
    float r=length(p)+1e-4;
    vec2 d=p/r;
    vec2 h5=harmonic(d,5);
    vec2 h8=harmonic(d,8);
    vec2 h13=harmonic(d,13);
    float n=fbm(p*3.7+vec2(t*.04,-t*.035));
    vec3 c=vec3(0.0);
    for(int i=0;i<5;i++){
        float fi=float(i);
        float base=.18+fi*.12;
        float petal=.065*h5.x+.035*h8.y+.022*h13.x;
        float target=base+petal*(1.0+.25*chaos)+(.018+.010*fi)*(n-.5)*chaos;
        float g=lineGlow(r-target,58.0-fi*5.5);
        float pulse=.62+.38*cos(r*(12.0+fi*3.0)-t*(.34+.08*fi)+h13.y*1.8);
        c+=pal(fi*.14+h8.x*.05+t*.018,vec3(.04,.22,.62))*g*pulse*(.60+.16*fi);
    }
    float fracture=pow(.5+.5*(h13.x*cos(r*48.0-t*.73)-h13.y*sin(r*48.0-t*.73)),20.0);
    c+=pal(r*.4+t*.017,vec3(.61,.08,.14))*fracture*exp(-r*1.3)*(.12+.32*chaos);
    c+=vec3(1.0,.97,.91)*exp(-r*12.0)*(.25+.20*sin(t*.8)*sin(t*.8));
    return c;
}

vec3 crystalCavern(vec2 p,float t){
    float chaos=clamp(u_chaos,0.0,2.5);
    vec2 q=rot(.08*sin(t*.11))*p*2.65;
    vec2 drift=vec2(fbm(q*.72+vec2(t*.025,1.7)),fbm(q*.78+vec2(-2.3,-t*.021)))-.5;
    q+=drift*(.12+.12*chaos);
    vec2 cell=floor(q), local=fract(q);
    float nearest=9.0,second=9.0,identity=0.0;
    for(int y=-1;y<=1;y++) for(int x=-1;x<=1;x++){
        vec2 neighbor=vec2(float(x),float(y));
        vec2 seed=hash22(cell+neighbor);
        vec2 pulse=.22*sin(t*(.12+.05*seed.x)+TAU*seed+vec2(0.0,1.7));
        float distanceToSeed=length(neighbor+seed+pulse-local);
        if(distanceToSeed<nearest){second=nearest;nearest=distanceToSeed;identity=seed.x+seed.y*.7;}
        else if(distanceToSeed<second) second=distanceToSeed;
    }
    float edge=second-nearest;
    float crystal=exp(-edge*(17.0+5.0*chaos));
    float core=exp(-edge*58.0);
    float facets=pow(.5+.5*cos(nearest*20.0-identity*8.0+t*.23),7.0);
    float vault=exp(-24.0*abs(length(p)-(.54+.055*sin(t*.17))));
    vec3 cyan=vec3(.02,.82,1.0),violet=vec3(.72,.04,1.0),rose=vec3(1.0,.05,.42);
    vec3 hue=mix(cyan,violet,.5+.5*sin(identity*9.0+t*.09));
    hue=mix(hue,rose,.22+.18*sin(identity*17.0));
    vec3 c=hue*crystal*(.48+.54*facets);
    c+=vec3(.88,.97,1.0)*core*(.50+.42*facets);
    c+=mix(violet,cyan,.5+.5*sin(t*.12))*vault*(.14+.30*crystal);
    c*=.38+.62*(1.0-smoothstep(.08,1.35,length(p)));
    return c;
}

vec3 solarLoom(vec2 p,float t){
    float chaos=clamp(u_chaos,0.0,2.5);
    vec2 q=p;
    q+=vec2(.035*sin(t*.13),.025*cos(t*.17));
    float r=length(q)+1e-4;
    vec2 d=q/r;
    vec2 h9=harmonic(d,9),h14=harmonic(d,14),h19=harmonic(d,19);
    float turbulence=fbm(q*4.0+vec2(t*.035,-t*.027));
    float coronaRadius=.34+.024*h9.x+.016*h14.y+.025*(turbulence-.5)*chaos;
    float corona=exp(-38.0*abs(r-coronaRadius));
    float hot=exp(-105.0*abs(r-coronaRadius));
    float magneticPhase=10.0/(r+.12)-t*.74+turbulence*2.4;
    vec2 magnetic=vec2(cos(magneticPhase),sin(magneticPhase));
    float threads=pow(.5+.5*dot(h19,magnetic),18.0)*exp(-r*1.25);
    float prominences=pow(.5+.5*dot(h9,vec2(magnetic.x,-magnetic.y)),12.0);
    prominences*=exp(-20.0*abs(r-(.48+.05*h14.x)));
    float inner=exp(-r*8.5)*(1.0+.28*sin(t*.83));
    vec3 c=vec3(.96,.08,.008)*(corona*.82+threads*.42);
    c+=vec3(1.0,.40,.025)*(corona*.66+prominences*.88);
    c+=vec3(1.0,.91,.48)*hot*.92+vec3(1.0,.98,.86)*inner*.72;
    float sparks=pow(hash21(floor((p+1.4)*u_resolution/5.0)),55.0)*exp(-r*.8);
    c+=vec3(1.0,.47,.08)*sparks*(.15+.30*chaos);
    return c;
}

vec3 abyssalGarden(vec2 p,float t){
    float chaos=clamp(u_chaos,0.0,2.5);
    vec2 q=p;
    q.y+=.18+.035*sin(t*.12);
    vec3 c=vec3(0.0);
    for(int i=0;i<7;i++){
        float fi=float(i),seed=fi*1.731;
        float root=(fi-3.0)*.215;
        float sway=.055*sin(q.y*(2.4+fi*.17)+t*(.16+.025*fi)+seed);
        sway+=.024*sin(q.y*7.0-t*.13+seed*2.0)*chaos;
        float taper=(1.0-smoothstep(-.72,.92,q.y))*smoothstep(-1.08,-.46,q.y);
        float strand=exp(-abs(q.x-root-sway)*(42.0+fi*2.0))*taper;
        float nodes=pow(.5+.5*cos(q.y*(13.0+fi*.55)-t*(.36+.025*fi)+seed),16.0);
        vec3 hue=mix(vec3(.00,.92,.57),vec3(.02,.42,1.0),fi/6.0);
        hue=mix(hue,vec3(.72,.05,1.0),.18+.12*sin(seed));
        c+=hue*strand*(.50+.85*nodes);
        c+=vec3(.80,1.0,.92)*strand*pow(nodes,3.0)*.52;
    }
    float caustic=pow(ridged(p*4.8+vec2(t*.025,-t*.038)),10.0);
    caustic*=(1.0-smoothstep(-.55,.75,p.y))*(.12+.20*chaos);
    c+=mix(vec3(.00,.42,.34),vec3(.05,.22,.85),.5+.5*p.x)*caustic;
    float spores=pow(hash21(floor((p+vec2(1.7,t*.025))*u_resolution/7.0)),62.0);
    c+=vec3(.42,1.0,.76)*spores*.72;
    return c;
}

vec3 prismMirage(vec2 p,float t){
    float chaos=clamp(u_chaos,0.0,2.5);
    vec2 q=rot(t*.035)*p;
    q.x=abs(q.x);
    q=rot(-.52)*q;
    q.x=abs(q.x);
    q=rot(.31+.06*sin(t*.12))*q;
    vec2 warp=vec2(fbm(q*2.2+vec2(t*.025,1.0)),fbm(q*2.5-vec2(2.0,t*.021)))-.5;
    q+=warp*(.04+.08*chaos);
    vec2 tiles=abs(fract(q*2.35)-.5);
    float diagonal=abs(tiles.x+tiles.y-.46);
    float facets=exp(-diagonal*(42.0+8.0*chaos));
    float blades=exp(-55.0*abs(tiles.x-tiles.y));
    float rings=exp(-42.0*abs(length(p)-(.31+.13*sin(t*.18))));
    float shimmer=pow(ridged(q*6.0+vec2(t*.04,-t*.031)),8.0);
    vec3 c=pal(q.x*.24+q.y*.17+t*.018,vec3(.03,.28,.61))*facets*(.58+.48*shimmer);
    c+=pal(length(q)*.32-t*.014,vec3(.62,.07,.18))*blades*.66;
    c+=vec3(.92,.98,1.0)*facets*blades*.74;
    c+=vec3(.28,.08,1.0)*rings*(.18+.25*facets);
    c*=.40+.60*(1.0-smoothstep(.12,1.25,length(p)));
    return c;
}

void main() {
    vec2 p=(gl_FragCoord.xy*2.0-u_resolution)/u_resolution.y;
    float t=u_time;
    vec3 c;
    if(u_scene==0) c=eventHorizon(p,t);
    else if(u_scene==1) c=auroraVoid(p,t);
    else if(u_scene==2) c=liquidChrome(p,t);
    else if(u_scene==3) c=neonCathedral(p,t);
    else if(u_scene==4) c=wormholeChoir(p,t);
    else if(u_scene==5) c=plasmaSingularity(p,t);
    else if(u_scene==6) c=vortexCrown(p,t);
    else if(u_scene==7) c=collapseFlower(p,t);
    else if(u_scene==8) c=crystalCavern(p,t);
    else if(u_scene==9) c=solarLoom(p,t);
    else if(u_scene==10) c=abyssalGarden(p,t);
    else c=prismMirage(p,t);

    float vignette=1.0-smoothstep(.20,1.47,length(p));
    c*=mix(.70,1.0,vignette);
    c*=.84+.42*u_intensity;
    c=vec3(1.0)-exp(-max(c,vec3(0.0))*1.20);
    c=pow(c,vec3(.77));
    float peak=max(c.r,max(c.g,c.b));
    c*=smoothstep(.007,.042,peak);
    fragColor=vec4(clamp(c,0.0,1.0),1.0);
}
"""


SCENE_IDS = {
    "event_horizon": 0,
    "aurora_void": 1,
    "liquid_chrome": 2,
    "neon_cathedral": 3,
    "wormhole_choir": 4,
    "plasma_singularity": 5,
    "vortex_crown": 6,
    "collapse_flower": 7,
    "crystal_cavern": 8,
    "solar_loom": 9,
    "abyssal_garden": 10,
    "prism_mirage": 11,
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
        vertices = np.asarray([-1.0, -1.0, 3.0, -1.0, -1.0, 3.0], dtype="f4")
        self.vbo = self.ctx.buffer(vertices.tobytes())
        self.vao = self.ctx.simple_vertex_array(self.program, self.vbo, "in_pos")
        self.target = self.ctx.texture((self.width, self.height), 3, dtype="f1")
        self.fbo = self.ctx.framebuffer(color_attachments=[self.target])
        self.program["u_resolution"].value = (float(self.width), float(self.height))

    def render(
        self,
        scene: str,
        *,
        t: float,
        intensity: float = 1.0,
        chaos: float = 1.0,
    ) -> np.ndarray:
        if scene not in SCENE_IDS:
            raise ValueError(f"unknown shader scene: {scene}")
        self.program["u_time"].value = float(t)
        self.program["u_intensity"].value = float(max(intensity, 0.0))
        self.program["u_chaos"].value = float(np.clip(chaos, 0.0, 2.5))
        self.program["u_scene"].value = int(SCENE_IDS[scene])
        self.fbo.use()
        self.ctx.viewport = (0, 0, self.width, self.height)
        self.fbo.clear(0.0, 0.0, 0.0, 1.0)
        self.vao.render(mode=self.moderngl.TRIANGLES)
        data = self.fbo.read(components=3, alignment=1)
        return np.flipud(np.frombuffer(data, dtype=np.uint8).reshape(self.height, self.width, 3)).copy()

    def close(self) -> None:
        for obj in (self.fbo, self.target, self.vao, self.vbo, self.program):
            try:
                obj.release()
            except Exception:
                pass
        try:
            self.ctx.release()
        except Exception:
            pass
