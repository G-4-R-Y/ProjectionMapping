import numpy as np
from projection_mapping.patterns import checkerboard, gray_encode, graycode_sequence, grid


def test_shapes():
    assert checkerboard(64, 32, 8).shape == (32, 64, 3)
    assert grid(64, 32, 8).shape == (32, 64, 3)


def test_gray_encode_known_values():
    x = np.arange(8, dtype=np.uint32)
    assert gray_encode(x).tolist() == [0, 1, 3, 2, 6, 7, 5, 4]


def test_gray_sequence_pairs():
    seq = graycode_sequence(8, 4, include_inverse=True)
    assert len(seq) == 2 * (3 + 2)
    for a, b in zip(seq[::2], seq[1::2]):
        assert np.all((a.image.astype(int) + b.image.astype(int)) == 255)
