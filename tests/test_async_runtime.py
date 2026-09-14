import time

from projection_mapping.async_runtime import LatestFrameWorker


def test_latest_frame_worker_processes_and_returns_latest():
    with LatestFrameWorker(lambda x: x * 2) as worker:
        seq = worker.submit(3)
        deadline = time.time() + 1.0
        latest = None
        while time.time() < deadline:
            latest = worker.latest()
            if latest is not None:
                break
            time.sleep(0.005)
        assert latest is not None
        assert latest[0] == seq
        assert latest[1] == 6
        assert worker.stats.processed == 1


def test_latest_frame_worker_bounds_pending_queue():
    def slow(x):
        time.sleep(0.03)
        return x

    with LatestFrameWorker(slow) as worker:
        worker.submit(0)
        time.sleep(0.005)
        for i in range(1, 8):
            worker.submit(i)
        deadline = time.time() + 1.0
        while time.time() < deadline:
            latest = worker.latest()
            if latest is not None and latest[1] == 7:
                break
            time.sleep(0.005)
        latest = worker.latest()
        assert latest is not None
        assert latest[1] == 7
        assert worker.stats.dropped > 0
        assert worker.stats.processed < worker.stats.submitted
