import numpy as np
from projection_mapping.runtime import run_loop


def test_runtime_pipeline():
    n = {"x": 0}
    def source():
        n["x"] += 1
        return np.array([n["x"]], dtype=np.float32)
    got = []
    def sink(frame):
        got.append(float(frame[0]))
        return True
    stats = run_loop(source, sink, processors=[lambda x: x * 2], max_frames=3)
    assert got == [2.0, 4.0, 6.0]
    assert stats.frames == 3
