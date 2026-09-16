from __future__ import annotations

from dataclasses import dataclass, field, replace
import math

from .performance_bus import GestureEvent, PerformanceState, Vec3


@dataclass(frozen=True)
class Transform3D:
    position: Vec3 = Vec3(0.0, 0.0, 0.0)
    rotation_euler: Vec3 = Vec3(0.0, 0.0, 0.0)
    scale: Vec3 = Vec3(1.0, 1.0, 1.0)


@dataclass(frozen=True)
class MREntity:
    id: str
    asset_pack: str
    asset_id: str
    transform: Transform3D
    attachment: str = "world"
    lifetime: float | None = None
    age: float = 0.0
    opacity: float = 1.0
    emissive: float = 1.0
    tags: tuple[str, ...] = ()
    state: dict[str, float | str | bool] = field(default_factory=dict)


@dataclass(frozen=True)
class SpawnRequest:
    asset_pack: str
    asset_id: str
    position: Vec3
    attachment: str = "world"
    lifetime: float | None = None
    scale: float = 1.0
    emissive: float = 1.0
    tags: tuple[str, ...] = ()


class MixedRealityScene:
    """Small deterministic entity scene graph for generated sprites/meshes and portals.

    Rendering is intentionally separate. This layer owns IDs, lifetimes, attachments and event
    routing so a future OpenGL/gltf renderer, projection-space renderer or neural compositor can
    consume the same scene without duplicating gameplay semantics.
    """

    def __init__(self) -> None:
        self._entities: dict[str, MREntity] = {}
        self._counter = 0

    @property
    def entities(self) -> tuple[MREntity, ...]:
        return tuple(self._entities.values())

    def spawn(self, request: SpawnRequest) -> MREntity:
        self._counter += 1
        entity = MREntity(
            id=f"mr_{self._counter:06d}",
            asset_pack=request.asset_pack,
            asset_id=request.asset_id,
            transform=Transform3D(
                position=request.position,
                scale=Vec3(request.scale, request.scale, request.scale),
            ),
            attachment=request.attachment,
            lifetime=request.lifetime,
            emissive=request.emissive,
            tags=request.tags,
        )
        self._entities[entity.id] = entity
        return entity

    def remove(self, entity_id: str) -> None:
        self._entities.pop(entity_id, None)

    def update(self, dt: float, performance: PerformanceState | None = None) -> None:
        dt = max(float(dt), 0.0)
        updated: dict[str, MREntity] = {}
        for entity in self._entities.values():
            age = entity.age + dt
            if entity.lifetime is not None and age >= entity.lifetime:
                continue
            next_entity = replace(entity, age=age)
            if performance is not None and entity.attachment != "world":
                anchor = performance.tracking.anchor(entity.attachment, 0.25)
                if anchor is not None:
                    next_entity = replace(
                        next_entity,
                        transform=replace(next_entity.transform, position=anchor.position),
                    )
            updated[next_entity.id] = next_entity
        self._entities = updated

    def spawn_from_event(self, event: GestureEvent) -> MREntity | None:
        """Map high-level spell events onto the example Neon Core asset pack."""
        if event.name == "portal_open":
            return self.spawn(
                SpawnRequest(
                    "neon_core",
                    "portal_ring",
                    Vec3(
                        float(event.payload.get("cx", 0.5)),
                        float(event.payload.get("cy", 0.5)),
                        0.0,
                    ),
                    lifetime=2.4,
                    scale=max(float(event.payload.get("radius", 0.16)) * 5.0, 0.4),
                    emissive=2.2,
                    tags=("spell", "portal"),
                )
            )
        if event.name == "charge_release":
            source = event.source_anchor or "right_palm"
            return self.spawn(
                SpawnRequest(
                    "neon_core",
                    "slash_particles",
                    Vec3(0.5, 0.5, 0.0),
                    attachment=source,
                    lifetime=0.75,
                    scale=0.7 + 0.6 * event.strength,
                    emissive=2.4,
                    tags=("spell", "impact"),
                )
            )
        return None

    def route_events(self, performance: PerformanceState) -> tuple[MREntity, ...]:
        spawned: list[MREntity] = []
        for event in performance.tracking.gestures:
            entity = self.spawn_from_event(event)
            if entity is not None:
                spawned.append(entity)
        return tuple(spawned)


__all__ = ["Transform3D", "MREntity", "SpawnRequest", "MixedRealityScene"]
