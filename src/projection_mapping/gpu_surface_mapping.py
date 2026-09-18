from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from .shader_scenes import FRAGMENT_SHADER as SCENE_FRAGMENT_SHADER
from .shader_scenes import SCENE_IDS
from .shader_scenes import VERTEX_SHADER as SCENE_VERTEX_SHADER
from .surface_mapping import MappedSurface, SurfaceMapProfile

_QUAD_VERTEX = r"""
#version 330
in vec2 in_pos;
out vec2 v_uv;
void main(){
    v_uv=in_pos*.5+.5;
    gl_Position=vec4(in_pos,0.0,1.0);
}
"""

_MAP_FRAGMENT = r"""
#version 330
uniform sampler2D u_source;
uniform mat3 u_projector_to_source;
uniform vec2 u_resolution;
uniform vec2 u_dst0;
uniform vec2 u_dst1;
uniform vec2 u_dst2;
uniform vec2 u_dst3;
uniform vec2 u_src0;
uniform vec2 u_src1;
uniform vec2 u_src2;
uniform vec2 u_src3;
uniform float u_opacity;
uniform float u_feather;
in vec2 v_uv;
out vec4 fragColor;

float cross2(vec2 a,vec2 b){return a.x*b.y-a.y*b.x;}
bool insideQuad(vec2 p,vec2 a,vec2 b,vec2 c,vec2 d){
    float s0=cross2(b-a,p-a),s1=cross2(c-b,p-b);
    float s2=cross2(d-c,p-c),s3=cross2(a-d,p-d);
    bool positive=s0>=-1e-5&&s1>=-1e-5&&s2>=-1e-5&&s3>=-1e-5;
    bool negative=s0<=1e-5&&s1<=1e-5&&s2<=1e-5&&s3<=1e-5;
    return positive||negative;
}
float segmentDistance(vec2 p,vec2 a,vec2 b){
    vec2 ab=b-a;
    float h=clamp(dot(p-a,ab)/max(dot(ab,ab),1e-6),0.0,1.0);
    return length(p-a-ab*h);
}
void main(){
    if(!insideQuad(v_uv,u_dst0,u_dst1,u_dst2,u_dst3)) discard;
    vec3 projected=u_projector_to_source*vec3(v_uv,1.0);
    vec2 sourceUV=projected.xy/max(abs(projected.z),1e-7)*sign(projected.z);
    if(!insideQuad(sourceUV,u_src0,u_src1,u_src2,u_src3)) discard;

    vec2 pixel=v_uv*u_resolution;
    float edge=min(min(segmentDistance(pixel,u_dst0*u_resolution,u_dst1*u_resolution),
                       segmentDistance(pixel,u_dst1*u_resolution,u_dst2*u_resolution)),
                   min(segmentDistance(pixel,u_dst2*u_resolution,u_dst3*u_resolution),
                       segmentDistance(pixel,u_dst3*u_resolution,u_dst0*u_resolution)));
    float featherPixels=u_feather*min(u_resolution.x,u_resolution.y);
    float alpha=u_opacity*(featherPixels>.5?smoothstep(0.0,featherPixels,edge):1.0);
    vec4 color=texture(u_source,sourceUV);
    fragColor=vec4(color.rgb,alpha*color.a);
}
"""


def homography_matrix(source: np.ndarray, destination: np.ndarray) -> np.ndarray:
    """Solve the projective transform mapping four 2-D source points to destination points."""
    src = np.asarray(source, dtype=np.float64)
    dst = np.asarray(destination, dtype=np.float64)
    if src.shape != (4, 2) or dst.shape != (4, 2):
        raise ValueError("homography requires two arrays of four x/y points")
    rows = []
    values = []
    for (x, y), (u, v) in zip(src, dst):
        rows.append((x, y, 1.0, 0.0, 0.0, 0.0, -u * x, -u * y))
        rows.append((0.0, 0.0, 0.0, x, y, 1.0, -v * x, -v * y))
        values.extend((u, v))
    try:
        solution = np.linalg.solve(np.asarray(rows), np.asarray(values))
    except np.linalg.LinAlgError as exc:
        raise ValueError("surface corners do not define a stable homography") from exc
    matrix = np.append(solution, 1.0).reshape(3, 3)
    if not np.isfinite(matrix).all() or abs(np.linalg.det(matrix)) < 1e-10:
        raise ValueError("surface corners do not define a stable homography")
    return matrix


def _gl_points(surface_points: tuple[tuple[float, float], ...]) -> np.ndarray:
    points = np.asarray(surface_points, dtype=np.float32).copy()
    points[:, 1] = 1.0 - points[:, 1]
    return points


@dataclass
class _CompiledSurface:
    surface: MappedSurface
    projector_to_source: np.ndarray
    source: np.ndarray
    destination: np.ndarray


class ShaderScenePass:
    """Render one promoted procedural scene into a texture without reading it back."""

    def __init__(self, ctx: Any, width: int, height: int):
        self.ctx = ctx
        self.width = int(width)
        self.height = int(height)
        self.program = ctx.program(
            vertex_shader=SCENE_VERTEX_SHADER,
            fragment_shader=SCENE_FRAGMENT_SHADER,
        )
        vertices = np.asarray([-1.0, -1.0, 3.0, -1.0, -1.0, 3.0], dtype="f4")
        self.vbo = ctx.buffer(vertices.tobytes())
        self.vao = ctx.simple_vertex_array(self.program, self.vbo, "in_pos")
        self.texture = ctx.texture((self.width, self.height), 4, dtype="f1")
        self.texture.filter = (ctx.LINEAR, ctx.LINEAR)
        self.fbo = ctx.framebuffer(color_attachments=[self.texture])
        self.program["u_resolution"].value = (float(self.width), float(self.height))

    def render(self, scene: str, *, t: float, intensity: float, chaos: float) -> Any:
        if scene not in SCENE_IDS:
            raise ValueError(f"unknown shader scene: {scene}")
        self.program["u_time"].value = float(t)
        self.program["u_intensity"].value = float(max(intensity, 0.0))
        self.program["u_chaos"].value = float(np.clip(chaos, 0.0, 2.5))
        self.program["u_scene"].value = int(SCENE_IDS[scene])
        self.fbo.use()
        self.ctx.viewport = (0, 0, self.width, self.height)
        self.fbo.clear(0.0, 0.0, 0.0, 1.0)
        self.vao.render(mode=self.ctx.TRIANGLES)
        return self.texture

    def close(self) -> None:
        for resource in (self.fbo, self.texture, self.vao, self.vbo, self.program):
            resource.release()


class GPUSurfaceCompositor:
    """Apply a SurfaceMapProfile entirely on GPU in the active OpenGL context."""

    def __init__(self, ctx: Any, profile: SurfaceMapProfile):
        self.ctx = ctx
        self.profile = profile
        self.program = ctx.program(vertex_shader=_QUAD_VERTEX, fragment_shader=_MAP_FRAGMENT)
        vertices = np.asarray([-1.0, -1.0, 3.0, -1.0, -1.0, 3.0], dtype="f4")
        self.vbo = ctx.buffer(vertices.tobytes())
        self.vao = ctx.simple_vertex_array(self.program, self.vbo, "in_pos")
        self.program["u_source"].value = 0
        self._signature: tuple[Any, ...] | None = None
        self._compiled: list[_CompiledSurface] = []

    def _profile_signature(self) -> tuple[Any, ...]:
        return tuple(
            (
                surface.projector_corners,
                surface.source_corners,
                surface.opacity,
                surface.feather,
                surface.enabled,
            )
            for surface in self.profile.surfaces
        )

    def _compile(self) -> None:
        compiled = []
        for surface in self.profile.surfaces:
            if not surface.enabled or surface.opacity <= 0.0:
                continue
            source = _gl_points(surface.source_corners)
            destination = _gl_points(surface.projector_corners)
            source_to_projector = homography_matrix(source, destination)
            compiled.append(
                _CompiledSurface(
                    surface=surface,
                    projector_to_source=np.linalg.inv(source_to_projector),
                    source=source,
                    destination=destination,
                )
            )
        self._compiled = compiled
        self._signature = self._profile_signature()

    @staticmethod
    def _write_matrix(uniform: Any, matrix: np.ndarray) -> None:
        uniform.write(np.asarray(matrix, dtype="f4").T.tobytes())

    def render(self, source_texture: Any, width: int, height: int, target: Any | None = None) -> None:
        signature = self._profile_signature()
        if signature != self._signature:
            self._compile()
        if target is None:
            self.ctx.screen.use()
        else:
            target.use()
        self.ctx.viewport = (0, 0, int(width), int(height))
        self.ctx.clear(0.0, 0.0, 0.0, 1.0)
        self.ctx.enable(self.ctx.BLEND)
        self.ctx.blend_func = (self.ctx.SRC_ALPHA, self.ctx.ONE_MINUS_SRC_ALPHA)
        source_texture.use(location=0)
        self.program["u_resolution"].value = (float(width), float(height))
        for item in self._compiled:
            self._write_matrix(self.program["u_projector_to_source"], item.projector_to_source)
            for index in range(4):
                self.program[f"u_dst{index}"].value = tuple(item.destination[index])
                self.program[f"u_src{index}"].value = tuple(item.source[index])
            self.program["u_opacity"].value = item.surface.opacity
            self.program["u_feather"].value = item.surface.feather
            self.vao.render(mode=self.ctx.TRIANGLES)
        self.ctx.disable(self.ctx.BLEND)

    def close(self) -> None:
        for resource in (self.vao, self.vbo, self.program):
            resource.release()


__all__ = [
    "GPUSurfaceCompositor",
    "ShaderScenePass",
    "homography_matrix",
]
