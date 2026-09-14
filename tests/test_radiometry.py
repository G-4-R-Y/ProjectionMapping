import numpy as np
from projection_mapping.radiometry import RGBRadiometricCalibration


def test_identity_lut():
    levels = np.array([0, 64, 128, 192, 255], np.float32)
    obs = np.stack([levels, levels, levels], axis=1)
    cal = RGBRadiometricCalibration.fit(levels, obs)
    target = np.array([[[32, 100, 220]]], np.float32)
    out = cal.compensate(target)
    assert np.allclose(out, target, atol=1e-5)
