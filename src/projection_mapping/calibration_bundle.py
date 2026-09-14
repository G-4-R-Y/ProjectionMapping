from __future__ import annotations

from dataclasses import dataclass, asdict
import json
from pathlib import Path
import numpy as np


@dataclass
class CalibrationBundle:
    projector_width: int
    projector_height: int
    camera_width: int
    camera_height: int
    homography: list[list[float]] | None = None
    notes: str = ""

    def save(self, directory: str | Path, dense_map: np.ndarray | None = None, confidence: np.ndarray | None = None) -> None:
        out = Path(directory)
        out.mkdir(parents=True, exist_ok=True)
        (out / "calibration.json").write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")
        if dense_map is not None:
            np.save(out / "dense_map.npy", dense_map)
        if confidence is not None:
            np.save(out / "confidence.npy", confidence)

    @classmethod
    def load(cls, directory: str | Path) -> "CalibrationBundle":
        data = json.loads((Path(directory) / "calibration.json").read_text(encoding="utf-8"))
        return cls(**data)


def save_capture_manifest(directory: str | Path, metadata: dict, frames: list[dict]) -> None:
    out = Path(directory)
    out.mkdir(parents=True, exist_ok=True)
    payload = {"metadata": metadata, "frames": frames}
    (out / "manifest.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
