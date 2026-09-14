from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import shutil
import sys
from typing import Any

try:  # Python 3.11+
    import tomllib
except ModuleNotFoundError:  # Python 3.10 compatibility
    import tomli as tomllib

from .app_runtime import bundle_root, is_frozen


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
    requires_commands: tuple[str, ...] = ()

    def defaults(self) -> dict[str, Any]:
        return {p.key: p.default for p in self.params}

    def supported_on(self, platform: str | None = None) -> bool:
        platform = platform or current_platform()
        return not self.platforms or platform in self.platforms

    def platform_hint(self) -> str:
        return "all supported OSs" if not self.platforms else ", ".join(self.platforms)

    def missing_commands(self) -> tuple[str, ...]:
        """Return optional external executables that are not currently on PATH."""
        return tuple(command for command in self.requires_commands if shutil.which(command) is None)

    def available(self, platform: str | None = None) -> bool:
        return self.supported_on(platform) and not self.missing_commands()

    def availability_hint(self, platform: str | None = None) -> str:
        platform = platform or current_platform()
        if not self.supported_on(platform):
            return f"unsupported on {platform}; supported: {self.platform_hint()}"
        missing = self.missing_commands()
        if missing:
            return f"missing external command(s): {', '.join(missing)}"
        return "available"

    def build_argv(self, values: dict[str, Any] | None = None) -> list[str]:
        if not self.supported_on():
            raise RuntimeError(
                f"{self.name} is not supported on {current_platform()}; "
                f"supported: {self.platform_hint()}"
            )
        missing = self.missing_commands()
        if missing:
            raise RuntimeError(
                f"{self.name} requires external command(s) not found on PATH: {', '.join(missing)}"
            )

        values = values or {}
        if self.command and self.command[0] == "python":
            if is_frozen():
                # A frozen app has no standalone Python executable. Relaunch the
                # desktop binary in hidden child-runner mode instead.
                argv = [sys.executable, "--pm-child", *self.command[1:]]
            else:
                argv = [sys.executable, *self.command[1:]]
        else:
            argv = list(self.command)

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
    candidates = [
        bundle_root() / "configs" / "features.toml",
        Path.cwd() / "configs" / "features.toml",
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
                requires_commands=tuple(raw.get("requires_commands", [])),
            )
        )
    return FeatureRegistry(tuple(features))
