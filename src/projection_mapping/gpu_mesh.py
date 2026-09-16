from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path

import numpy as np

from .graphics_runtime import create_context
from .mesh_assets import MeshAsset, load_mesh_asset


_VERTEX = r"""
#version 330
in vec3 in_pos;
in vec3 in_normal;
uniform mat4 u_model;
uniform mat4 u_view;
uniform mat4 u_proj;
out vec3 v_world;
out vec3 v_normal;
void main(){
    vec4 world=u_model*vec4(in_pos,1.0);
    v_world=world.xyz;
    mat3 normalMat=mat3(transpose(inverse(u_model)));
    v_normal=normalize(normalMat*in_normal);
    gl_Position=u_proj*u_view*world;
}
"""

_FRAGMENT = r"""
#version 330
uniform vec3 u_base;
uniform vec3 u_emissive;
uniform vec3 u_camera;
uniform float u_time;
uniform float u_energy;
in vec3 v_world;
in vec3 v_normal;
out vec4 fragColor;
void main(){
    vec3 N=normalize(v_normal);
    vec3 V=normalize(u_camera-v_world);
    vec3 L=normalize(vec3(-.35,.78,1.0));
    float ndl=max(dot(N,L),0.0);
    float rim=pow(1.0-max(dot(N,V),0.0),2.4);
    vec3 H=normalize(L+V);
    float spec=pow(max(dot(N,H),0.0),38.0);
    float scan=.82+.18*sin(v_world.y*18.0-u_time*1.7);
    vec3 col=u_base*(.10+.80*ndl)*scan;
    col+=vec3(.94,.98,1.0)*spec*.62;
    col+=u_emissive*(.18+.82*rim)*u_energy;
    col=col/(1.0+col);
    col=pow(max(col,vec3(0.0)),vec3(.86));
    fragColor=vec4(clamp(col,0.0,1.0),1.0);
}
"""


@dataclass
class _GPUPrimitive:
    vao: object
    vertex_buffer: object
    index_buffer: object
    index_count: int


@dataclass
class GPUModel:
    asset: MeshAsset
    primitives: list[_GPUPrimitive]

    def release(self) -> None:
        for primitive in self.primitives:
            for obj in (primitive.vao, primitive.index_buffer, primitive.vertex_buffer):
                try:
                    obj.release()
                except Exception:
                    pass
        self.primitives.clear()


def perspective(fov_y_degrees: float, aspect: float, near: float = 0.05, far: float = 100.0) -> np.ndarray:
    f=1.0/math.tan(math.radians(fov_y_degrees)*0.5)
    a=max(float(aspect),1e-6)
    out=np.zeros((4,4),dtype=np.float32)
    out[0,0]=f/a
    out[1,1]=f
    out[2,2]=(far+near)/(near-far)
    out[2,3]=(2.0*far*near)/(near-far)
    out[3,2]=-1.0
    return out


def look_at(eye: tuple[float,float,float], target=(0.0,0.0,0.0), up=(0.0,1.0,0.0)) -> np.ndarray:
    e=np.asarray(eye,dtype=np.float32)
    t=np.asarray(target,dtype=np.float32)
    u=np.asarray(up,dtype=np.float32)
    f=t-e
    f/=max(float(np.linalg.norm(f)),1e-8)
    s=np.cross(f,u)
    s/=max(float(np.linalg.norm(s)),1e-8)
    u2=np.cross(s,f)
    out=np.eye(4,dtype=np.float32)
    out[0,:3]=s
    out[1,:3]=u2
    out[2,:3]=-f
    out[:3,3]=-out[:3,:3]@e
    return out


def transform_matrix(
    *,
    position=(0.0,0.0,0.0),
    rotation=(0.0,0.0,0.0),
    scale=(1.0,1.0,1.0),
) -> np.ndarray:
    sx,sy,sz=(float(x) for x in scale)
    rx,ry,rz=(float(x) for x in rotation)
    cx,sx_=math.cos(rx),math.sin(rx)
    cy,sy_=math.cos(ry),math.sin(ry)
    cz,sz_=math.cos(rz),math.sin(rz)
    Rx=np.array([[1,0,0,0],[0,cx,-sx_,0],[0,sx_,cx,0],[0,0,0,1]],dtype=np.float32)
    Ry=np.array([[cy,0,sy_,0],[0,1,0,0],[-sy_,0,cy,0],[0,0,0,1]],dtype=np.float32)
    Rz=np.array([[cz,-sz_,0,0],[sz_,cz,0,0],[0,0,1,0],[0,0,0,1]],dtype=np.float32)
    S=np.diag([sx,sy,sz,1.0]).astype(np.float32)
    T=np.eye(4,dtype=np.float32)
    T[:3,3]=np.asarray(position,dtype=np.float32)
    return T@Rz@Ry@Rx@S


def _normalise_asset_transform(asset: MeshAsset) -> tuple[np.ndarray,float]:
    lo=np.asarray(asset.bounds_min,dtype=np.float32)
    hi=np.asarray(asset.bounds_max,dtype=np.float32)
    centre=(lo+hi)*.5
    extent=max(float(np.max(hi-lo)),1e-5)
    return centre,2.0/extent


class GPUMeshRenderer:
    """Small open GLB/glTF geometry renderer for generated mixed-reality assets.

    It intentionally starts with geometry/normals + emissive cyber material. Texture/PBR/skin
    support belongs to the next layer, while this first path proves generated 3D assets can be
    loaded, normalized, attached and rendered without an external engine.
    """

    def __init__(self,width:int,height:int)->None:
        import moderngl

        self.moderngl=moderngl
        self.width=int(width)
        self.height=int(height)
        self.ctx,self.context_info=create_context(require=330)
        self.program=self.ctx.program(vertex_shader=_VERTEX,fragment_shader=_FRAGMENT)
        self.target=self.ctx.texture((self.width,self.height),3,dtype="f1")
        self.depth=self.ctx.depth_renderbuffer((self.width,self.height))
        self.fbo=self.ctx.framebuffer(color_attachments=[self.target],depth_attachment=self.depth)
        self.models:list[GPUModel]=[]

    def upload(self,asset:MeshAsset|str|Path)->GPUModel:
        loaded=load_mesh_asset(asset) if isinstance(asset,(str,Path)) else asset
        primitives:list[_GPUPrimitive]=[]
        for primitive in loaded.primitives:
            vertices=np.asarray(primitive.vertices,dtype=np.float32)
            normals=primitive.normals
            if normals is None or len(normals)!=len(vertices):
                normals=np.zeros_like(vertices,dtype=np.float32)
                normals[:,2]=1.0
            interleaved=np.concatenate([vertices,np.asarray(normals,dtype=np.float32)],axis=1).astype("f4")
            indices=np.asarray(primitive.faces,dtype=np.int32).reshape(-1).astype("i4")
            vbo=self.ctx.buffer(interleaved.tobytes())
            ibo=self.ctx.buffer(indices.tobytes())
            vao=self.ctx.vertex_array(self.program,[(vbo,"3f 3f","in_pos","in_normal")],index_buffer=ibo,index_element_size=4)
            primitives.append(_GPUPrimitive(vao,vbo,ibo,int(indices.size)))
        model=GPUModel(loaded,primitives)
        self.models.append(model)
        return model

    def render(
        self,
        model:GPUModel,
        *,
        t:float,
        screen_position=(0.0,0.0,0.0),
        rotation=(0.0,0.0,0.0),
        scale:float=1.0,
        base_color=(0.08,0.22,0.34),
        emissive=(0.10,0.80,1.00),
        energy:float=1.0,
        camera_distance:float=3.2,
    )->np.ndarray:
        m=self.moderngl
        centre,unit=_normalise_asset_transform(model.asset)
        normalize=transform_matrix(position=(-float(centre[0]),-float(centre[1]),-float(centre[2])),scale=(unit,unit,unit))
        world=transform_matrix(position=screen_position,rotation=rotation,scale=(scale,scale,scale))@normalize
        camera=(0.0,0.0,float(camera_distance))
        view=look_at(camera)
        proj=perspective(43.0,self.width/max(self.height,1))

        p=self.program
        # ModernGL expects OpenGL column-major matrix bytes; transpose our row-major arrays.
        p["u_model"].write(np.ascontiguousarray(world.T,dtype="f4").tobytes())
        p["u_view"].write(np.ascontiguousarray(view.T,dtype="f4").tobytes())
        p["u_proj"].write(np.ascontiguousarray(proj.T,dtype="f4").tobytes())
        p["u_base"].value=tuple(float(x) for x in base_color)
        p["u_emissive"].value=tuple(float(x) for x in emissive)
        p["u_camera"].value=camera
        p["u_time"].value=float(t)
        p["u_energy"].value=float(max(energy,0.0))

        self.fbo.use()
        self.ctx.viewport=(0,0,self.width,self.height)
        self.fbo.clear(0.0,0.0,0.0,1.0,depth=1.0)
        self.ctx.enable(m.DEPTH_TEST)
        self.ctx.enable(m.CULL_FACE)
        for primitive in model.primitives:
            primitive.vao.render(mode=m.TRIANGLES,vertices=primitive.index_count)
        self.ctx.disable(m.CULL_FACE)
        self.ctx.disable(m.DEPTH_TEST)
        data=self.fbo.read(components=3,alignment=1)
        frame=np.frombuffer(data,dtype=np.uint8).reshape(self.height,self.width,3)
        return np.flipud(frame).copy()

    def close(self)->None:
        for model in list(self.models):
            model.release()
        self.models.clear()
        for obj in (self.fbo,self.depth,self.target,self.program):
            try: obj.release()
            except Exception: pass
        try: self.ctx.release()
        except Exception: pass


__all__=["GPUModel","GPUMeshRenderer","perspective","look_at","transform_matrix"]
