"""Performer FX v1: open whole-body tracking -> spell grammar -> GPU particles + SDF spells.

The default path uses RTMLib RTMW/Wholebody semantics rather than guessed silhouette anchors.
Semantic landmarks create continuous emitters; SpellGrammar contributes sparse high-level events.
Our own ModernGL pipeline renders persistent particles plus analytic portals/shields/sigils.
F11 toggles fullscreen; ESC exits.
"""
from __future__ import annotations

import argparse
import math
import time

import cv2
import numpy as np

from projection_mapping.capture import Camera
from projection_mapping.gpu_particles import GPUParticleField, ParticleEmitter
from projection_mapping.gpu_sdf_spells import SDFSpell, SDFSpellRenderer
from projection_mapping.pose_tracking import MediaPipeTaskTracker, RTMPoseWholeBodyTracker
from projection_mapping.runtime import FullscreenSink
from projection_mapping.spell_grammar import SpellGrammar


PALETTE_BY_STYLE={"cyber":"cyber","solar":"solar","bio":"bio","prismatic":"prismatic"}
HUE_BY_STYLE={"cyber":0.78,"solar":0.04,"bio":0.38,"prismatic":0.90}


def _make_tracker(name:str,confidence:float,smoothing:float):
    if name=="rtmpose":
        return RTMPoseWholeBodyTracker(mode="lightweight",backend="onnxruntime",device="cpu",confidence=confidence,smoothing=smoothing)
    if name=="mediapipe":
        return MediaPipeTaskTracker(confidence=confidence,smoothing=smoothing)
    if name=="auto":
        errors=[]
        try:
            tracker=RTMPoseWholeBodyTracker(mode="lightweight",backend="onnxruntime",device="cpu",confidence=confidence,smoothing=smoothing)
            print("[performer-fx] tracker=rtmpose-wholebody",flush=True)
            return tracker
        except Exception as exc:
            errors.append(f"rtmpose: {type(exc).__name__}: {exc}")
        try:
            tracker=MediaPipeTaskTracker(confidence=confidence,smoothing=smoothing)
            print("[performer-fx] tracker=mediapipe-tasks",flush=True)
            return tracker
        except Exception as exc:
            errors.append(f"mediapipe: {type(exc).__name__}: {exc}")
        raise RuntimeError(
            "No semantic performer tracker is available. Install `.[performer]` for the fully-open "
            "RTMPose path or `.[mediapipe]` for the optional MediaPipe backend. "+" | ".join(errors)
        )
    raise ValueError(name)


def _decay(value:float,dt:float,rate:float)->float:
    return value*math.exp(-dt*rate)


def _anchor_emitters(state,style:str,intensity:float)->list[ParticleEmitter]:
    emitters=[]
    specs=(
        ("left_palm",0.05,1.00,0.020),("right_palm",0.62,1.00,0.020),
        ("chest",0.80,0.62,0.026),("head",0.48,0.36,0.014),
        ("left_ankle",0.26,0.34,0.013),("right_ankle",0.70,0.34,0.013),
    )
    if style=="bio":
        specs=tuple((name,(hue+0.28)%1.0,energy,radius) for name,hue,energy,radius in specs)
    elif style=="solar":
        specs=tuple((name,(hue*0.20+0.04)%1.0,energy,radius) for name,hue,energy,radius in specs)
    for name,hue,base_energy,radius in specs:
        a=state.anchor(name,0.35)
        if a is None:
            continue
        speed=min(a.speed/1.3,1.0)
        emitters.append(ParticleEmitter.from_anchor(a,energy=(base_energy+speed*0.55)*intensity,hue=hue,radius=radius*(1.0+speed*0.75)))
    return emitters[:8]


def _portal_emitters(event,t:float,style:str)->list[ParticleEmitter]:
    cx=float(event.payload.get("cx",0.5)); cy=float(event.payload.get("cy",0.5)); radius=float(event.payload.get("radius",0.16))
    hue0=HUE_BY_STYLE[style]
    out=[]
    for i in range(8):
        a=t*1.5+i*math.tau/8.0
        tangent=0.42+0.42*event.strength
        out.append(ParticleEmitter(cx+math.cos(a)*radius,cy+math.sin(a)*radius,-math.sin(a)*tangent,math.cos(a)*tangent,0.75+0.45*event.strength,(hue0+i*0.035)%1.0,0.016))
    return out


def _particle_material(*,release:float,slash:float,portal:float,shield:float,ascension:float,charge:float)->str:
    # Sparse semantic events are allowed to change the material language. Normal tracking stays
    # plasma; velocity becomes comet light; impacts become rings; defense/ascension become motes.
    if release>0.16:
        return "shock_ring"
    if slash>0.12:
        return "comet"
    if portal>0.18:
        return "comet"
    if shield>0.18 or ascension>0.22:
        return "mote"
    if charge>0.72:
        return "spark"
    return "plasma"


def main()->None:
    ap=argparse.ArgumentParser()
    ap.add_argument("--camera",type=int,default=0)
    ap.add_argument("--tracker",choices=["auto","rtmpose","mediapipe"],default="rtmpose")
    ap.add_argument("--display",type=int,default=1)
    ap.add_argument("--projector-width",type=int,default=1920)
    ap.add_argument("--projector-height",type=int,default=1080)
    ap.add_argument("--capture-width",type=int,default=640)
    ap.add_argument("--capture-height",type=int,default=360)
    ap.add_argument("--render-width",type=int,default=768)
    ap.add_argument("--render-height",type=int,default=432)
    ap.add_argument("--particles",type=int,default=32768)
    ap.add_argument("--style",choices=sorted(PALETTE_BY_STYLE),default="cyber")
    ap.add_argument("--intensity",type=float,default=1.0)
    ap.add_argument("--madness",type=float,default=0.48)
    ap.add_argument("--feedback",type=float,default=0.94)
    ap.add_argument("--bloom",type=float,default=1.20)
    ap.add_argument("--glyphs",action=argparse.BooleanOptionalAction,default=True)
    ap.add_argument("--camera-mix",type=float,default=0.06)
    ap.add_argument("--confidence",type=float,default=0.35)
    ap.add_argument("--smoothing",type=float,default=0.58)
    ap.add_argument("--mirror",action="store_true")
    args=ap.parse_args()

    tracker=_make_tracker(args.tracker,args.confidence,args.smoothing)
    grammar=SpellGrammar()
    field=GPUParticleField(args.render_width,args.render_height,capacity=args.particles,palette=PALETTE_BY_STYLE[args.style])
    glyph_renderer=SDFSpellRenderer(args.render_width,args.render_height) if args.glyphs else None
    sink=FullscreenSink(window="ProjectionMapping-PerformerFX",display=args.display,fullscreen=True)
    print(
        f"[performer-fx] tracker={args.tracker} particles={field.capacity} glyphs={args.glyphs} "
        f"gl={field.context_info.gl_version} renderer={field.context_info.renderer} backend={field.backend}",flush=True,
    )

    t0=time.perf_counter(); last=t0; report=t0; frames=0
    release_energy=shield_energy=ascension_energy=portal_energy=slash_energy=0.0
    portal_emitters=[]; portal_center=(0.5,0.5); portal_radius=0.16; release_center=(0.5,0.5)
    try:
        with Camera(args.camera,args.capture_width,args.capture_height) as cam:
            while True:
                now=time.perf_counter(); t=now-t0; dt=float(np.clip(now-last,1e-4,0.08)); last=now
                frame=cam.read(); frame=cv2.resize(frame,(args.capture_width,args.capture_height),interpolation=cv2.INTER_AREA)
                if args.mirror: frame=cv2.flip(frame,1)
                state=tracker.submit(frame,now) if hasattr(tracker,"submit") else tracker.update(frame,now)
                state=grammar.update(state)

                release_energy=_decay(release_energy,dt,4.5); shield_energy=_decay(shield_energy,dt,2.2)
                ascension_energy=_decay(ascension_energy,dt,2.0); portal_energy=_decay(portal_energy,dt,1.6)
                slash_energy=_decay(slash_energy,dt,7.0)
                portal_emitters=portal_emitters if portal_energy>0.05 else []
                charge=0.0
                for event in state.gestures:
                    if event.name=="charge_orb": charge=max(charge,event.strength)
                    elif event.name=="charge_release":
                        release_energy=max(release_energy,event.strength)
                        left=state.anchor("left_palm",0.25); right=state.anchor("right_palm",0.25)
                        if left and right: release_center=((left.position.x+right.position.x)*.5,(left.position.y+right.position.y)*.5)
                    elif event.name=="slash_trail": slash_energy=max(slash_energy,event.strength)
                    elif event.name=="shield_dome" and event.phase!="release": shield_energy=max(shield_energy,event.strength)
                    elif event.name=="ascension_aura" and event.phase!="release": ascension_energy=max(ascension_energy,event.strength)
                    elif event.name=="portal_open":
                        portal_energy=max(portal_energy,event.strength)
                        portal_center=(float(event.payload.get("cx",.5)),float(event.payload.get("cy",.5)))
                        portal_radius=float(event.payload.get("radius",.16)); portal_emitters=_portal_emitters(event,t,args.style)

                emitters=_anchor_emitters(state,args.style,args.intensity)
                left=state.anchor("left_palm",0.35); right=state.anchor("right_palm",0.35)
                if charge>0.0 and left and right:
                    cx=(left.position.x+right.position.x)*.5; cy=(left.position.y+right.position.y)*.5
                    emitters.insert(0,ParticleEmitter(cx,cy,0.0,-0.04,0.8+charge*.7,.93,.025+.030*charge))
                if portal_emitters: emitters=portal_emitters[:8]
                emitters=emitters[:8]

                motion_energy=float(np.mean([math.hypot(e.vx,e.vy) for e in emitters])) if emitters else 0.0
                macro=max(release_energy,portal_energy,ascension_energy)
                emission=(3200+5200*min(motion_energy*1.8,1.0)+6200*charge+15000*release_energy+9000*slash_energy+10000*portal_energy)*(0.70+0.65*args.intensity)
                turbulence=0.16+0.26*args.madness+0.24*slash_energy+0.12*ascension_energy
                feedback=float(np.clip(args.feedback+0.020*shield_energy,0.0,0.985))
                bloom=args.bloom*(1.0+0.35*macro+0.18*shield_energy)
                material=_particle_material(release=release_energy,slash=slash_energy,portal=portal_energy,shield=shield_energy,ascension=ascension_energy,charge=charge)
                field.set_material(material)
                fx=field.render(
                    emitters,t=t,dt=dt,emission_rate=emission,turbulence=turbulence,
                    drag=0.95+0.30*(1.0-args.madness),feedback=feedback,bloom=bloom,
                    energy=0.9+0.45*args.intensity+0.4*macro,bass=charge,
                    strike=max(release_energy,slash_energy),drop=portal_energy,
                )

                if glyph_renderer is not None:
                    spells=[]; hue=HUE_BY_STYLE[args.style]
                    if charge>0.03 and left and right:
                        cx=(left.position.x+right.position.x)*.5; cy=(left.position.y+right.position.y)*.5
                        spells.append(SDFSpell("orb",cx,cy,.035+.055*charge,.35+charge,t*1.8,hue))
                    if shield_energy>0.05 and left and right:
                        cx=(left.position.x+right.position.x)*.5; cy=(left.position.y+right.position.y)*.5
                        radius=max(math.hypot(left.position.x-right.position.x,left.position.y-right.position.y)*.62,.14)
                        spells.append(SDFSpell("shield",cx,cy,radius,shield_energy*.95,-t*.28,hue+.12,1.18))
                    if portal_energy>0.04:
                        spells.append(SDFSpell("portal",portal_center[0],portal_center[1],max(portal_radius,.06),portal_energy*1.25,t*.65,hue))
                    head=state.anchor("head",0.30)
                    if ascension_energy>0.04 and head is not None:
                        spells.append(SDFSpell("ascension",head.position.x,max(head.position.y-.08,.04),.10+.05*ascension_energy,ascension_energy,-t*.48,hue+.2,.62))
                    if release_energy>0.04:
                        spells.append(SDFSpell("impact",release_center[0],release_center[1],.08+(1.0-release_energy)*.20,release_energy,t,hue+.08))
                    if spells:
                        glyphs=glyph_renderer.render(spells,t=t)
                        fx=np.clip(fx.astype(np.float32)+glyphs.astype(np.float32)*.92,0,255).astype(np.uint8)

                mix=float(np.clip(args.camera_mix,0.0,.9))
                if mix>0.0:
                    cam_rgb=cv2.cvtColor(cv2.resize(frame,(args.render_width,args.render_height),interpolation=cv2.INTER_AREA),cv2.COLOR_BGR2RGB)
                    fx=cv2.addWeighted(fx,1.0,cam_rgb,mix,0.0)
                out=cv2.resize(fx,(args.projector_width,args.projector_height),interpolation=cv2.INTER_CUBIC)
                if sink(cv2.cvtColor(out,cv2.COLOR_RGB2BGR)) is False: break

                frames+=1
                if now-report>=2.0:
                    gestures=",".join(e.name for e in state.gestures) or "-"
                    print(
                        f"[performer-fx] fps={frames/(now-report):.1f} source={state.source} anchors={len(state.anchors)} "
                        f"conf={state.performer_confidence:.2f} emitters={len(emitters)} material={material} gestures={gestures} "
                        f"charge={charge:.2f} release={release_energy:.2f} portal={portal_energy:.2f}",flush=True,
                    )
                    report=now; frames=0
    finally:
        try: tracker.close()
        except Exception: pass
        field.close()
        if glyph_renderer is not None: glyph_renderer.close()
        sink.close(); cv2.destroyAllWindows()


if __name__=="__main__":
    main()
