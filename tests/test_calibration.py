import numpy as np
from projection_mapping.calibration import gray_to_binary, decode_gray_pairs, HomographyCalibration
from projection_mapping.patterns import gray_encode


def test_gray_roundtrip():
    x = np.arange(256, dtype=np.uint32)
    assert np.array_equal(gray_to_binary(gray_encode(x)), x)


def test_decode_gray_pairs():
    vals = np.arange(8, dtype=np.uint32)[None, :]
    gray = gray_encode(vals)
    normal, inverse = [], []
    for bit in [2,1,0]:
        a = (((gray >> bit) & 1) * 255).astype(np.uint8)
        normal.append(a); inverse.append(255-a)
    dec, valid = decode_gray_pairs(normal, inverse)
    assert np.array_equal(dec, vals)
    assert valid.all()


def test_homography_identity():
    pts = np.array([[0,0],[100,0],[100,100],[0,100]], np.float32)
    cal = HomographyCalibration.fit(pts, pts)
    assert cal.reprojection_error < 1e-4
    assert np.allclose(cal.matrix / cal.matrix[2,2], np.eye(3), atol=1e-4)
