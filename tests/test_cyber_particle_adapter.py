from projection_mapping.cyber_particle_adapter import (
    CYBER_PARTICLE_MODES,
    profile_for_mode,
    tracked_point_emitters,
)
from projection_mapping.gpu_particles import GPUParticleField
from projection_mapping.point_tracker import TrackedPoint


def test_gpu_particle_registry_has_cyber_point_language():
    assert GPUParticleField.PALETTES["cyan_magenta"] == GPUParticleField.PALETTES["cyber"]
    assert "data_point" in GPUParticleField.MATERIALS
    assert "circuit" in GPUParticleField.FIELD_MODES


def test_cyber_profiles_use_dense_point_modes():
    assert "data_swarm" in CYBER_PARTICLE_MODES
    assert profile_for_mode("data_swarm").material == "data_point"
    assert profile_for_mode("circuit_grid").field_mode == "circuit"


def test_tracked_points_become_bounded_diverse_emitters():
    points = [
        TrackedPoint(1, 10.0, 10.0, 2.0, 0.0, 2.0, 20, 0.95),
        TrackedPoint(2, 90.0, 10.0, -1.0, 1.0, 1.4, 18, 0.90),
        TrackedPoint(3, 10.0, 90.0, 0.5, -1.5, 1.6, 12, 0.85),
        TrackedPoint(4, 90.0, 90.0, 0.0, 3.0, 3.0, 30, 0.98),
    ]
    emitters = tracked_point_emitters(points, 100, 100, intensity=1.0, limit=4)
    assert len(emitters) == 4
    # First emitter is the coherent cloud/core centroid.
    assert abs(emitters[0].x - 0.5) < 1e-6
    assert abs(emitters[0].y - 0.5) < 1e-6
    assert all(0.0 <= e.x <= 1.0 and 0.0 <= e.y <= 1.0 for e in emitters)
    assert all(e.energy > 0.0 and e.radius > 0.0 for e in emitters)


def test_empty_tracks_produce_no_emitters():
    assert tracked_point_emitters([], 640, 360) == []
