from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import sys
from typing import Any

try:  # Python 3.11+
    import tomllib
except ModuleNotFoundError:  # Python 3.10 compatibility
    import tomli as tomllib


def current_platform() -> str:
    """Return the stable platform names used by configs/features.toml."""
    if sys.platform.startswith("win"):
        return "windows"
    if sys.platform.startswith("linux"):
        return "linux"
    if sys.platform == "darwin":
        return "macos"
    return "other"


@dataclass(frozen=True)
class FeatureParam:
    key: str
    flag: str
    label: str
    type: str = "text"
    default: Any = ""
    choices: tuple[str, ...] = ()
    min: float | int | None = None
    max: float | int | None = None
    help: str = ""

    def coerce(self, value: Any) -> Any:
        if self.type == "bool":
            return bool(value)
        if self.type == "int":
            value = int(value)
        elif self.type == "float":
            value = float(value)
        else:
            value = str(value)

        if self.type in {"int", "float"}:
            if self.min is not None and value < self.min:
                raise ValueError(f"{self.label} must be >= {self.min}")
            if self.max is not None and value > self.max:
                raise ValueError(f"{self.label} must be <= {self.max}")
        if self.type == "choice" and self.choices and value not in self.choices:
            raise ValueError(f"{self.label} must be one of {', '.join(self.choices)}")
        return value


@dataclass(frozen=True)
class Feature:
    id: str
    name: str
    category: str
    description: str
    command: tuple[str, ...]
    fullscreen: bool = False
    params: tuple[FeatureParam, ...] = field(default_factory=tuple)
    platforms: tuple[str, ...] = ()

    def defaults(self) -> dict[str, Any]:
        return {p.key: p.default for p in self.params}

    def supported_on(self, platform: str | None = None) -> bool:
        platform = platform or current_platform()
        return not self.platforms or platform in self.platforms

    def platform_hint(self) -> str:
        return "all supported OSs" if not self.platforms else ", ".join(self.platforms)

    def build_argv(self, values: dict[str, Any] | None = None) -> list[str]:
        if not self.supported_on():
            raise RuntimeError(
                f"{self.name} is not supported on {current_platform()}; "
                f"supported: {self.platform_hint()}"
            )
        values = values or {}
        # Registry entries use the portable token `python`; always execute the exact
        # interpreter running the console so virtualenv/conda selection is preserved.
        argv = [sys.executable if token == "python" else token for token in self.command]
        for param in self.params:
            value = param.coerce(values.get(param.key, param.default))
            if param.type == "bool":
                if value:
                    argv.append(param.flag)
                continue
            if value == "":
                continue
            argv.extend([param.flag, str(value)])
        return argv


@dataclass(frozen=True)
class FeatureRegistry:
    features: tuple[Feature, ...]

    def by_id(self, feature_id: str) -> Feature:
        for feature in self.features:
            if feature.id == feature_id:
                return feature
        raise KeyError(feature_id)

    @property
    def categories(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys(feature.category for feature in self.features))


def _default_registry_path() -> Path:
    # Running editable from repo is the primary workflow. Fall back to cwd so the
    # UI remains usable when launched through the project script entry point.
    candidates = [
        Path.cwd() / "configs" / "features.toml",
        Path(__file__).resolve().parents[2] / "configs" / "features.toml",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def load_registry(path: str | Path | None = None) -> FeatureRegistry:
    registry_path = Path(path) if path else _default_registry_path()
    if not registry_path.exists():
        raise FileNotFoundError(f"feature registry not found: {registry_path}")
    data = tomllib.loads(registry_path.read_text(encoding="utf-8"))
    features: list[Feature] = []
    seen: set[str] = set()
    for raw in data.get("feature", []):
        feature_id = raw["id"]
        if feature_id in seen:
            raise ValueError(f"duplicate feature id: {feature_id}")
        seen.add(feature_id)
        params = tuple(
            FeatureParam(
                key=p["key"],
                flag=p["flag"],
                label=p.get("label", p["key"]),
                type=p.get("type", "text"),
                default=p.get("default", False if p.get("type") == "bool" else ""),
                choices=tuple(p.get("choices", [])),
                min=p.get("min"),
                max=p.get("max"),
                help=p.get("help", ""),
            )
            for p in raw.get("param", [])
        )
        features.append(
            Feature(
                id=feature_id,
                name=raw["name"],
                category=raw.get("category", "Other"),
                description=raw.get("description", ""),
                command=tuple(raw["command"]),
                fullscreen=bool(raw.get("fullscreen", False)),
                params=params,
                platforms=tuple(raw.get("platforms", [])),
            )
        )
    return FeatureRegistry(tuple(features))
